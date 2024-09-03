import os
import re
import logging
import subprocess
import sqlite3

from functions import find_binary_in_path, get_language
from command import RunCommand
from job_queue import QueueItem
from exceptions import MissingDependencyError, MkvExportError

class supTrackExporter:
    def __init__(self, queue, next_queue, mode, working_dir, language, logger):
        self.logger = logger
        self.working_dir = f"{os.path.join(working_dir, 'tracks')}"
        self.queue = queue
        self.next_queue = next_queue
        self.mode = mode
        self.language = language
        self.mkvinfo_bin = find_binary_in_path('mkvinfo')
        self.mkvextract_bin = find_binary_in_path('mkvextract')
        self.cmd = RunCommand()

        self.field_map = {
            "start_tracks": r'^\|\+ Tracks$',
            "start_track": r'^\|.*Track$',
            "fields": {
                'Track number:': [],
                'Track type:': ['subtitles'],
                'Codec ID:': ['S_HDMV/PGS'],
                'Language:': [],
                '"Default track" flag:': ['0', '1']
            },
            "end_track": r'^\| \+ EBML void:.*$'
        }

        if not self.mkvinfo_bin:
            raise MissingDependencyError(f"'mkvinfo' binary was not found in PATH")

        if not self.mkvextract_bin:
            raise MissingDependencyError(f"'mkviextract' binary was not found in PATH")

        # create the working directory
        if not os.path.isdir(self.working_dir):
            os.makedirs(self.working_dir)

        # Get valid language codes
        for code in self.language:
            lang = get_language(code)
            for prop in ['pt1', 'pt2b']:
                prop_code = getattr(lang, prop)
                if prop_code not in self.field_map['fields']['Language:']:
                    self.logger.info(f"Adding language: {lang.name} ({prop_code}) to track filter")
                    self.field_map['fields']['Language:'].append(prop_code)

        while not self.queue.empty():
            job_item = self.queue.get()
            
            if os.path.isdir(f"{job_item}"):
                # This is a directory we need to find the mkv file(s)
                self.logger.debug("Directory passed in.")
                mkv_dir = job_item.input_file
                mkv_files = [f for f in os.listdir(job_item.input_file) if f.lower().endswith('.mkv')]
                if len(mkv_files) == 0:
                    raise ConverterError(f"No mkv files found in {job_item}")
                elif len(mkv_files) > 1:
                    # Prompt the user to select one of the found files
                    job_item.input_file = self.prompt_user_to_select(
                        mkv_files,
                        header="- Multiple MKV Files found -"
                        )
                
                else:
                    job_item.input_file = f"{mkv_files[0]}"
            
                # append the input_path to the infout file
                job_item.input_file = os.path.join(mkv_dir, job_item.input_file)
                # self.queue.task_done()
                # continue

            # execute the export job
            out_files = self.export(job_item)

            self.logger.info(f"Finished exporting tracks from '{job_item}'")
            self.queue.task_done()
            # Add the jobs to the next queue
            for out_file in out_files:
                self.next_queue.put(QueueItem(input_file=out_file, output_path=job_item.output_path))


    def prompt_user_to_select(self, options, header=None):
        # Display the options to the user
        print("\n\n")
        if header:
            print(header)
        print("Please select an option:")
        for i, option in enumerate(options, start=1):
            if isinstance(option, str):
                print(f"{i}. {option}")
        
        # Prompt the user for a selection
        while True:
            try:
                choice = int(input("\nEnter the number of your choice: "))
                if 1 <= choice <= len(options):
                    return options[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(options)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def line_to_dict(self, line):
        line = line.replace("+", "").replace("|", "").strip()
        if ":" not in line:
            return None
        parts = line.split(':')
        return {parts.pop(0): ': '.join(parts).strip()}


    def export(self, job_item):
        self.sup_filename = f"{os.path.join(self.working_dir, 'subtitles.sup')}"
        self.logger.info(f"Extracting subtitle tracks from '{os.path.basename(job_item.input_file)}'")
        self.logger.info(f"Filtering tracks by language(s): {', '.join(self.language)}")

        
        # Run mkvinfo to get all the subtitle tracks
        return_code, mkvinfo_result, return_error = self.cmd.run_command_return_output(
            command=[self.mkvinfo_bin, f"{job_item.input_file}"]
        )

        if return_code > 0:
            raise MkvExportError(f"{mkvinfo_result} {return_error}")
        # print(mkvinfo_result)

        in_tracks = False
        in_track = False
        subtitle_tracks = []
        subtitle_track = {}
        # Loop the results of mkvinfo and
        # extract the subtitle tracks with the specified language
        for line in mkvinfo_result.splitlines():
            # Detect the beginning of the tracks section
            if re.fullmatch(self.field_map['start_tracks'], line.strip()):
                in_tracks = True
                continue

            if not in_tracks:
                continue        

            # Detect the beginning of a track
            if re.fullmatch(self.field_map['start_track'], line.strip()):
                in_track = True
                subtitle_track = {}
                continue

            # Detect the end of a track
            if re.fullmatch(self.field_map['end_track'], line.strip()) and in_track:
                in_track = False
                if len(subtitle_track) > 0:
                    # create the track object
                    track = mkvTrack(track_info=subtitle_track, mkv_filename=job_item.input_file)
                    self.logger.debug(f"Saving track: {track.filename}")
                    subtitle_tracks.append(track)
                continue

            # Set all the track fields
            if in_track:
                line_dict = self.line_to_dict(line)
                for field, values in self.field_map['fields'].items():
                    if field not in line:
                        continue
                    else:
                        if len(values) > 0:
                            # make sure the value is allowed
                            for value in values:
                                if value in line:
                                    subtitle_track.update(line_dict)
                        else:
                            # an empty list means any value is accepted
                            subtitle_track.update(line_dict)
         
        self.logger.info(f"Found {len(subtitle_tracks)} subtitle track(s) to extract.")
        if self.mode == 'first':
            self.logger.info("Exporting only the first track in order.")

        sup_filenames = []
        for track in subtitle_tracks:
            self.logger.info(f"Extracting Track: id:{track.id}, default: {track.default}, language:{track.language}, codec: {track.codec} file:'{track.filename}'")
            # execute mkvextract to get extract the subtitle tracks
            sup_filename = f'{os.path.join(job_item.output_path, track.filename)}'
            cmd = [
                self.mkvextract_bin,
                'tracks',
                f'{job_item.input_file}',
                f'{track.id}:{sup_filename}'
            ]
            self.cmd.run_command_with_scroll_window(cmd, header=[f"mkvextract: extracting subtitle track: {track.id}"])
            sup_filenames.append(sup_filename)
            if self.mode == 'first':
                break

        return sup_filenames

class mkvTrack:
    CODEC_MAP = {
        "S_HDMV/PGS": "sup",
        "S_VOBSUB": "sub"
    }
    FUNC_MAP = {
        "Track number": "__set_track_id__",
        "Codec ID": "__set_codec_ext__",
        "Track type": "__set_track_type__",
        '"Default track" flag': "__set_default__"
    }

    def __init__(self, track_info, mkv_filename):
        self.mkv_filename = os.path.basename(mkv_filename)
        self.type = None
        self.id = None
        self.language = None
        self.default = None
        self.codec = None
        self.ext = "ukn"
        

        for key, value in track_info.items():
            key = key.strip()
            value = value.strip()
            if key in self.FUNC_MAP.keys():
                func = getattr(self, self.FUNC_MAP[key])
                func(key, value.strip())
            else:
                setattr(self, key.lower().replace(" ", "_"), value.strip())

        self.filename = self.__set_track_filename__()

    @property
    def ending(self):
        return f"{self.language}.{self.ext}"

    def __set_track_filename__(self):
        extra = ".default." if self.default else ""
            
        return f"{self.mkv_filename.replace('mkv', f'{extra}t{self.id}.{self.ending}')}"

    def __set_track_id__(self, field, value):
        # See if there is an ID for mkvextract
        print(f"'{field}' = '{value}'")
        mkey = "mkvextract:"
        if mkey in value:
            value_parts = value.split(mkey)
            self.id = value_parts[-1].strip()[0]

    def __set_codec_ext__(self, field, value):
        if value in self.CODEC_MAP.keys():
            self.codec = value.strip()
            self.ext = self.CODEC_MAP[value]

    def __set_track_type__(self, field, value):
        self.type = value

    def __set_default__(self, field, value):
        self.default = True if int(value) == 1 else False