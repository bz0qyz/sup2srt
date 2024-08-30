import os
import logging
import subprocess
class supFileConverter:
    def __init__(self, sup_filename):
        self.logger = logging.getLogger(__name__)
        self.sup_filename = sup_filename
        self.sub_filename = None

    def convert(self, working_dir):
        self.file_path = f"{working_dir}/subtitles"
        self.sub_filename = f"{self.file_path}/subtitles.xml"
        if not os.path.isdir(self.file_path):
            os.makedirs(self.file_path)
        # subprocess.run(["sup", self.file_path])
        self.logger.info(f"Converting {self.sup_filename} to SUB/XML format")

        return self.sub_filename
