import sys
import os
import argparse
import tempfile
import pytesseract
import cv2
from PIL import Image
import numpy as np
import xml.etree.ElementTree as ET

video_filename = 'The Fifth Element (1997) - 1080p.h264.mp4'
APP = {
    "name": "sub2srt",
    "description": "sub to srt subtitle converter",
    "version": "1.0.0"
}

parser = argparse.ArgumentParser(description=f"{APP['name']} v{APP['version']}: {APP['description']}")
parser.add_argument('-i', '--infile', metavar='subtitles.xml', default='subtitles.xml',
    help="The full path to the import SUB format XML file.")
parser.add_argument('-o', '--outfile', metavar='subtitles.srt', default='subtitles.xml',
    help="The full path to the generated SRT file.")
parser.add_argument('-t', '--tmpdir', metavar='/tmp', default=f'{tempfile.gettempdir()}',
    help="The temp path/working directory")
parser.add_argument('-l', '--limit', metavar=100, default=None, type=int,
    help="Only process this many subtitles")
parser.add_argument('-f','--force', action="store_true", default=False, 
    help='Force the overwrite of the output file if it exists.')
parser.add_argument('-p','--progress', action="store_true", default=True, 
    help='Show a progress bar.')
parser.add_argument('-v','--verbose', action="store_true", default=True, 
    help='Show verbose output.')

args = parser.parse_args()
from pprint import pprint
pprint(args)

# Get the full path of the input and output files
working_dir = tempfile.TemporaryDirectory(prefix=f"{APP['name']}-", dir=args.tmpdir)
print(f"Working Dir: {working_dir.name}")
input_filename = os.path.realpath(f'{args.infile}')
output_filename = os.path.realpath(f'{args.outfile}')
print(f"Input file: {input_filename}")
print(f"Output file: {output_filename}")

quit()

# Functions
def print_progress_bar(iteration, total, bar_length=40):
    # Calculate progress
    progress = (iteration / total)
    percent = round(progress*100)
    arrow = '=' * int(round(progress * bar_length) - 1)
    spaces = ' ' * (bar_length - len(arrow))
    # Build the progress bar string
    progress_bar = f"[{arrow}{spaces}] {iteration}/{total} ({percent}%)"
    # Print progress bar with carriage return to overwrite the previous line
    sys.stdout.write('\r' + progress_bar)
    sys.stdout.flush()

def convert_to_srt_time(time_str, frame_rate=25):
    if not isinstance(frame_rate, int):
        frame_rate = int(frame_rate)
    # Split the input time string into hours, minutes, seconds, and frames
    hours, minutes, seconds, frames = map(int, time_str.split(':'))
    # Convert frames to milliseconds
    # milliseconds = round((frames / frame_rate) * 1000)
    milliseconds = frames * (1000 // frame_rate)
    # Format the time in SRT format: HH:MM:SS,mmm
    srt_time = f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    return srt_time


# Main

# Load and parse the XML file containing the subtitle data
tree = ET.parse('./subtitles/subtitles.xml')
root = tree.getroot()

# Get the framerate and language
metadata = root.find('Description')
frame_rate = metadata.find('Format').attrib['FrameRate']
video_format = metadata.find('Format').attrib['VideoFormat']
language = metadata.find('Language').attrib['Code']
print(f"Format: '{video_format}' Subtitle Language: '{language}', Frame Rate: '{frame_rate}'")

# Iterate over each subtitle entry
ittr_limit = args.limit
ittr = 0
out_tmp_file = f"{working_dir}/subtitles.{language}.srt"
if args.verbose:
    print(f"Writing to temporary output file: {out_tmp_file}")
output_file = open(f'{out_tmp_file}', 'w')

for subtitle in root.findall('Events'):
    total_subtitles = len(subtitle) if not ittr_limit else ittr_limit
    print(f"OCR Processing {total_subtitles} subtitles")

    for event in subtitle.findall('Event'):
        ittr += 1
        # Show a progress bar
        if args.progress:
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
            print('No image file found: skipping.')
            continue
        
        filename = f"./subtitles/{image_file}"
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
os.rename(out_tmp_file, output_filename)
print(f"SRT creation complete. {ittr} subtitles created.")