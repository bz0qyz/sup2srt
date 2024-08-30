import os
import subprocess
from functions import find_binary_in_path, ConverterError

class supFileConverter:
    def __init__(self, bdsup2sub_jar, sup_filename, logger):
        self.logger = logger
        self.bdsup2sub_jar = bdsup2sub_jar
        self.java_bin = find_binary_in_path('java')
        self.sup_filename = sup_filename
        self.sub_filename = None
        if 'JAVA_HOME' in os.environ:
                self.java_bin = f"{os.environ['JAVA_HOME']}/bin/java"

        if not os.path.exists(self.java_bin):
            raise ValueError("Java JRE not found.")   
        self.logger.debug(f"Using java binary: '{self.java_bin}'")             
        

    def convert(self, working_dir):
        self.file_path = f"{working_dir}/subtitles"
        self.sub_filename = f"{self.file_path}/subtitles.xml"
        if not os.path.isdir(self.file_path):
            os.makedirs(self.file_path)
        
        self.logger.info(f"Converting {self.sup_filename} to SUB/XML format")
        subprocess.run([self.java_bin, "-jar", f"{self.bdsup2sub_jar}", "-o", self.sub_filename, self.sup_filename])
        
        if not os.path.exists(self.sub_filename):
            raise ConverterError(f"Failed to convert SUP: '{self.sup_filename}' to SUB")

        return self.sub_filename
