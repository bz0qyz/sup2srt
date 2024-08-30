import os
import pytesseract
import cv2
from PIL import Image
import numpy as np
import xml.etree.ElementTree as ET
from functions import convert_to_srt_time, print_progress_bar, ConverterError

class SubFileProcessor:
    def __init__(self, in_file, out_file, logger):
        self.logger = logger
        self.in_file = in_file
        self.out_file = out_file
        # get the directory of the input file
        self.sub_dir = os.path.dirname(in_file)

    def process(self, working_dir, limit=None, progress=True, overwrite=False):
        if os.path.exists(self.out_file) and not overwrite:
            self.logger.error(f"SRT File: {self.out_file} exists and overwrite is False.")
            return None

        # Load and parse the XML file containing the subtitle data
        tree = ET.parse(self.in_file)
        root = tree.getroot()

        # Get the framerate and language
        metadata = root.find('Description')
        frame_rate = metadata.find('Format').attrib['FrameRate']
        video_format = metadata.find('Format').attrib['VideoFormat']
        language = metadata.find('Language').attrib['Code']
        self.logger.info(f"Format: '{video_format}' Subtitle Language: '{language}', Frame Rate: '{frame_rate}'")

        # Iterate over each subtitle entry
        ittr_limit = limit
        ittr = 0
        out_tmp_file = f"{working_dir}/subtitles.{language}.srt"
        self.logger.debug(f"Writing to temporary output file: {out_tmp_file}")
        output_file = open(f'{out_tmp_file}', 'w')

        for subtitle in root.findall('Events'):
            total_subtitles = len(subtitle) if not ittr_limit else ittr_limit
            self.logger.info(f"OCR Processing {total_subtitles} subtitles")

            for event in subtitle.findall('Event'):
                ittr += 1
                # Show a progress bar
                if progress:
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

                filename = f"{self.sub_dir}/{image_file}"
                subimg = cv2.imread(filename)
                subimg = cv2.cvtColor(subimg, cv2.COLOR_BGR2GRAY)
                subimg = cv2.resize(subimg, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                subimg = cv2.GaussianBlur(subimg, (5, 5), 0)
                subimg = cv2.bitwise_not(subimg)

                custom_config = r"--oem 3 --psm 6 -c tessedit_char_whitelist='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789♪♩♫♬,.`~[](){}!@#$%^&*<>?+:-_/\ \n'"
                subtext = pytesseract.image_to_string(subimg, config=custom_config).strip()

                # print(f"Subtitle from {start_time} to {end_time}, Image: {image_file} Text: '{subtext}'")
                output_file.write(f"{ittr}\n{start_time} --> {end_time}\n{subtext}\n\n")
                if ittr_limit and ittr == ittr_limit:
                    break

        output_file.close()
        # move the temporary outfile top the final outfile location
        os.rename(out_tmp_file, self.out_file)
        self.logger.info(f"SRT creation complete. {ittr} subtitles created.")
        return self.out_file
