import os
from tempfile import TemporaryDirectory
from functions import find_binary_in_path
from command import RunCommand
from job_queue import QueueItem
from exceptions import MissingDependencyError, SupConverterError

class supFileConverter:
    def __init__(self, queue, next_queue, bdsup2sub_jar, working_dir, logger):
        self.logger = logger
        self.queue = queue
        self.next_queue = next_queue
        self.bdsup2sub_jar = bdsup2sub_jar
        self.working_dir = f"{os.path.join(working_dir, 'subtitles')}"
        self.java_bin = find_binary_in_path('java')
        self.cmd = RunCommand()
        self.credits = [
            " * URL: https://github.com/mjuhasz/BDSup2Sub",
            " * Documentation: https://github.com/mjuhasz/BDSup2Sub/wiki"
        ]
        if 'JAVA_HOME' in os.environ:
                self.java_bin = f"{os.environ['JAVA_HOME']}/bin/java"

        if not os.path.exists(self.java_bin):
            raise MissingDependencyError("Java JRE not found.")   
        self.logger.debug(f"Using java binary: '{self.java_bin}'")

        # create the working directory
        if not os.path.isdir(self.working_dir):
            os.makedirs(self.working_dir)

        # Append command version string to the credits
        cmdline = [f"{self.java_bin}", "-jar", f"{self.bdsup2sub_jar}", "--version"]
        self.credits.insert(
            0, self.cmd.run_command_return_output(command=cmdline)[1].strip()
        )

        while not self.queue.empty():
            job_item = self.queue.get()
            output_filename = self.convert(job_item)
            self.logger.info(f"Finished converting track: '{job_item}'")
            self.next_queue.put(QueueItem(input_file=output_filename, output_path=job_item.output_path))
            self.queue.task_done()


    def convert(self, job_item):
        working_dir = TemporaryDirectory(dir=self.working_dir, delete=False).name
        output_filename = f"{os.path.join(working_dir, os.path.basename(job_item.input_file.replace('sup', 'xml')))}"
                
        self.logger.info(f"Converting {job_item.input_file} to SUB/XML format")
        self.credits.append(f" - Converting SUP File: '{os.path.basename(job_item.input_file)}'")
        self.cmd.run_command_with_scroll_window(
            command = [
                self.java_bin, "-jar", f"{self.bdsup2sub_jar}",
                "-o", output_filename,
                job_item.input_file
            ],
            header=self.credits,
            height=None
        )
        if not os.path.exists(output_filename):
            self.logger.error(f"File Not Found: '{output_filename}'")
            raise SupConverterError(f"Failed to convert SUP: '{job_item.input_file}' to SUB")

        return output_filename
