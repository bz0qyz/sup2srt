import os
import logging
import subprocess
import sqlite3
from functions import find_binary_in_path, ConverterError

class supTrackExporter:
    def __init__(self, mkv_path, logger):
        self.logger = logger
        self.mkv_path = mkv_path
        self.mkvfilename = None
        self.mkvinfo_bin = find_binary_in_path('mkvinfo')
        self.mkvextract_bin = find_binary_in_path('mkvextract')
        self.table_name = 'track'

        self.field_map = {
            "start": "Track number:",
            "fields": {
                "Track type:": ["subtitles"],
                "Codec ID:": ["S_HDMV/PGS", "S_VOBSUB"],
                "Language:": ["eng"]
            },
            "end": "Language:"
        }

        if not self.mkvinfo_bin:
            raise ConverterError(f"'mkvinfo' binary was not found in PATH")

        if not self.mkvextract_bin:
            raise ConverterError(f"'mkviextract' binary was not found in PATH")

        if not os.path.isdir(mkv_path):
            self.mkv_filename = mkv_path

    def __initdb__(self):
        self.db_con = sqlite3.connect(self.db_file)
        self.db = self.db_con.cursor()
        self.db.execute(f"CREATE TABLE {self.table_name}(id, type, lang, filename, codec)")

    def prompt_user_to_select(self, options):
        # Display the options to the user
        print("\n\nPlease select an option:")
        for i, option in enumerate(options, start=1):
            if isinstance(option, str):
                print(f"{i}. {option}")
        
        # Prompt the user for a selection
        while True:
            try:
                choice = int(input("Enter the number of your choice: "))
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
        return {parts.pop(0): ': '.join(parts)}

    def export(self, working_dir, language='en'):
        self.working_dir = f"{working_dir}/tracks"
        self.sup_filename = f"{self.working_dir}/subtitles.sup"
        self.db_file = f"{self.working_dir}/tracks.db"
        
        if not self.mkvfilename:
            self.logger.debug("Directory passed in.")
            mkv_files = [f for f in os.listdir(self.mkv_path ) if f.endswith('.mkv')]
            mkv_files_full_path = [os.path.join(self.mkv_path , f) for f in mkv_files]
            print(os.listdir(self.mkv_path))
            print(mkv_files)
            print(mkv_files_full_path)

            if len(mkv_files_full_path) == 0:
                raise ConverterError(f"No mkv files found in {self.mkv_path}")
            elif len(mkv_files_full_path) > 1:
                self.mkv_filename = self.prompt_user_to_select(mkv_files_full_path)
            else:
                self.mkv_filename = f"{mkv_files_full_path[0]}"

        if not os.path.isdir(self.working_dir):
            os.makedirs(self.working_dir)

        self.logger.info(f"Extracting subtitle tracks from {self.mkv_filename}")
        
        mkvinfo_result = subprocess.run([self.mkvinfo_bin, f"{self.mkv_filename}"], capture_output=True, text=True)
        # from pprint import pprint
        # pprint(mkvinfo_result.stdout)

        if not mkvinfo_result:
            return None
        
        self.__initdb__()

        in_track = False
        for line in mkvinfo_result.stdout.splitlines():
            line_dict = self.line_to_dict(line)
            if not line_dict:
                continue

            # Detect the beginning of a track
            if self.field_map['start'] in line:
                track_info = line_dict
                in_track = True

            # Set all the track fields
            if in_track:
                for field, values in self.field_map['fields'].items():
                    if field not in line:
                        continue
                    else:
                        for value in values:
                            if value in line:
                                track_info.update(line_dict)

            # Detect the end of a track
            if self.field_map['end'] in line:
                in_track = False
                if "Track type" in track_info.keys():
                    track = mkvTrack(track_info=track_info, mkv_filename=self.mkv_filename, table_name=self.table_name)
                    self.logger.debug(f"Saving track: {track.filename}")
                    self.db.execute(track.insert)

        if self.db_con:            
            self.db_con.commit()
            res = self.db.execute(f"SELECT * FROM {self.table_name} WHERE type='subtitles'")
            print(res.fetchall())
            # prompt_user_to_select()

        if self.db_con:
            self.db_con.close()

        return None
        return self.sup_filename

class mkvTrack:
    CODEC_MAP = {
        "S_HDMV/PGS": "sup",
        "S_VOBSUB": "srt"
    }
    FUNC_MAP = {
        "Track number": "__set_track_id__",
        "Codec ID": "__set_codec_ext__",
        "Track type": "__set_track_type__"
    }

    def __init__(self, track_info, mkv_filename, table_name):
        self.mkv_filename = os.path.basename(mkv_filename)
        self.table_name = table_name
        self.type = None
        self.id = None
        self.language = None
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

    @property
    def insert(self):
        return f"INSERT INTO {self.table_name} VALUES('{self.id}', '{self.type}', '{self.language}', '{self.filename}', '{self.codec}')"

    def __set_track_filename__(self):
        return f"{self.mkv_filename.replace('mkv', f't{self.id}.{self.ending}')}"

    def __set_track_id__(self, field, value):
        # See if there is an ID for mkvextract
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