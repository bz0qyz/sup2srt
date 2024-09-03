import os
import shutil
import pytesseract
import cv2
from tempfile import NamedTemporaryFile
from PIL import Image
import numpy as np
import xml.etree.ElementTree as ET
from functions import convert_to_srt_time, print_progress_bar
from exceptions import MissingDependencyError, SubConverterError

class SubFileProcessor:
    def __init__(self, queue, logger, working_dir, limit=None, progress=True, overwrite=False):
        self.logger = logger
        self.queue = queue
        self.working_dir = os.path.join(working_dir,'subtitles')
        self.limit = limit
        self.progress = progress
        self.overwrite = overwrite

        # create the working directory
        if not os.path.isdir(self.working_dir):
            os.makedirs(self.working_dir)   

        while not self.queue.empty():
            job_item = self.queue.get()
            output_filename = self.convert(job_item)
            self.logger.info(f"Finished converting subtitles: '{job_item}'")
            self.queue.task_done()

    def convert(self, job_item):
        img_dir = os.path.dirname(job_item.input_file)

        # Load and parse the XML file containing the subtitle data
        tree = ET.parse(job_item.input_file)
        root = tree.getroot()

        # Get the framerate and language
        metadata = root.find('Description')
        frame_rate = metadata.find('Format').attrib['FrameRate']
        video_format = metadata.find('Format').attrib['VideoFormat']
        language = metadata.find('Language').attrib['Code']
        self.logger.info(f"Format: '{video_format}' Subtitle Language: '{language}', Frame Rate: '{frame_rate}'")

        # Build the output file name
        out_file = os.path.join(job_item.output_path, os.path.basename(job_item.input_file.replace('xml', f'{language}.srt')))

        # Verify that the final output file does not already exist
        if os.path.exists(out_file) and not self.overwrite:
            self.logger.error(f"SRT File: {out_file} exists and overwrite is False.")
            return None

        # Iterate over each subtitle entry
        ittr_limit = self.limit
        ittr = 0

        # output_file = open(f'{out_tmp_file}', 'w')
        output_file = NamedTemporaryFile(mode='w', prefix='subtitle', suffix='.srt', dir=self.working_dir, delete=False)

        # Parse the XML SUB file contents
        for subtitle in root.findall('Events'):
            total_subtitles = len(subtitle) if not ittr_limit else ittr_limit
            self.logger.info(f"OCR Scanning {total_subtitles} subtitles")

            for event in subtitle.findall('Event'):
                ittr += 1
                # Show a progress bar
                if self.progress:
                    print_progress_bar(ittr, total_subtitles)

                # Extract the timing information
                start_time = event.attrib['InTC'].strip() if 'InTC' in event.attrib else None
                end_time = event.attrib['OutTC'].strip() if 'OutTC' in event.attrib else None
                image_file = event.find('Graphic').text

                if start_time:
                    start_time = convert_to_srt_time(start_time, frame_rate)
                if end_time:
                    end_time = convert_to_srt_time(end_time, frame_rate)

                if not image_file:
                    self.logger.warning('No image file found: skipping.')
                    continue

                # OCR scan each image file
                filename = f"{os.path.join(img_dir, image_file)}"
                if not os.path.exists(filename):
                    raise SubConverterError(f"SUB format images not found in {img_dir}")
                
                subimg = cv2.imread(filename)
                subimg = cv2.cvtColor(subimg, cv2.COLOR_BGR2GRAY)
                subimg = cv2.resize(subimg, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                subimg = cv2.GaussianBlur(subimg, (5, 5), 0)
                subimg = cv2.bitwise_not(subimg)
                custom_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789♪♩♫♬,.`~[](){}!@#$%^&*<>?+:-_/\ \n'"
                subtext = pytesseract.image_to_string(subimg, config=custom_config).strip()

                # Write the SRT subtitle line
                output_file.write(f"{ittr}\n{start_time} --> {end_time}\n{subtext}\n\n")
                
                # Stop here if there is a limit set
                if ittr_limit and ittr == ittr_limit:
                    break

        output_file.close()
        # move the temporary outfile top the final outfile location
        shutil.copyfile(output_file.name, out_file)
        self.logger.info(f"SRT creation complete. {ittr} subtitles created.")
        self.logger.info(f"Saved File: {out_file}")
        return out_file
