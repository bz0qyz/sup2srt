import os
import logging
import subprocess
class supTrackExporter:
    def __init__(self, mkv_path):
        self.logger = logging.getLogger(__name__)
        self.mkv_path = mkv_path

    def export(self, working_dir):
        self.file_path = f"{working_dir}/tracks"
        self.sup_filename = f"{self.file_path}/subtitles.sup"
        if not os.path.isdir(self.file_path):
            os.makedirs(self.file_path)

        self.logger.info(f"Extracting subtitle tracks from {self.mkv_path}")

        return self.sup_filename
