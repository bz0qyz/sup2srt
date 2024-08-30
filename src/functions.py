import sys
import shutil

def find_binary_in_path(binary_name):
    # Find the binary in the PATH
    binary_path = shutil.which(binary_name)
    if not binary_path:
        # raise ValueError(f"'{binary_name}' Was not found in PATH")
        return None
    return binary_path
        

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

class ConverterError(Exception):
    pass
