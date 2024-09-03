import os
import sys
import tempfile
import logging
from functions import get_language
from arguments import Arguments
from job_queue import jobQueue
from exceptions import ArgumentError

class Config:
    APP = {
        "name": "sup2srt",
        "description": "MKV SUP to SRT subtitle converter",
        "version": "1.0.0",
        "tagline": "full-service subtitle extraction and conversion"
    }
    INFILE_ALLOWED_EXTENSIONS = {
        'xml': {'queue': 'sub', 'description': 'SUB: XML Subtitle Files'},
        'sup': {'queue': 'sup', 'description': 'SUP: Blu-ray Subtitle File'},
        'mkv': {'queue': 'mkv', 'description': 'MKV: Matroska Video File'}
    }

    def __init__(self):
        # Set default properties
        self.args = Arguments(APP=self.APP).get_args()
        self.logger = logging.getLogger(f"{self.APP['name']}")
        self.verbose = False
        self.working_dir = None
        self.output_path = None
        # Supported language is currently only English
        self.language = ['eng']
        self.queue = jobQueue()
        self.input_file = None
        self.input_type = None
        self.__init_args__(self.args)

    def __logging__(self, verbose=False):
        # Configure logging
        loglevel = logging.DEBUG if verbose else logging.INFO
        self.logger.setLevel(loglevel)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(loglevel)
        formatter = logging.Formatter('%(name)s: [%(levelname)s] - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def __init_args__(self, args):
        # convert args to properties
        not_props = ['in', 'out']
        for key, value in vars(args).items():
            if key not in not_props:
                setattr(self, key, value)

        self.__logging__(self.verbose)

        # Verify languages are valid
        if self.language:
            for code in self.language:
               get_language(code)

        # set the working directory
        self.working_dir = tempfile.TemporaryDirectory(prefix=f"{self.APP['name']}-", dir=args.tmpdir)
        
        # get the input path or filename
        in_file = os.path.realpath(getattr(args, 'in', None))
        
        if os.path.isdir(in_file):
            # if the in_file is a directory it will be treated as an MKV path
            if not os.path.exists(in_file):
                raise FileNotFoundError(f"Input directory does not exist: '{in_file}'")
            self.input_file = in_file
            self.input_type = self.INFILE_ALLOWED_EXTENSIONS['mkv']['queue']
        else:
            # get the file extension
            ext = os.path.splitext(in_file.lower())[-1].replace('.', '')
            if ext not in self.INFILE_ALLOWED_EXTENSIONS.keys():
                allowed_exts = ', '.join(f"'{item}'" for item in self.INFILE_ALLOWED_EXTENSIONS.keys())
                raise ValueError(f"Invalid file extension: '{ext}'. Allowed extensions: {allowed_exts}")
            else:
                if not os.path.exists(in_file):
                    raise FileNotFoundError(f"Input file does not exist: '{in_file}'")
                elif os.stat(in_file).st_size == 0:
                    raise ValueError(f"Invalid input file:  '{in_file}' is zero bytes in size.")
            self.input_file = in_file
            self.input_type = self.INFILE_ALLOWED_EXTENSIONS[ext]['queue']

        # Set the output path
        out_dir = os.path.realpath(getattr(args, 'out')) if args.out else in_file
        self.output_path = out_dir if os.path.isdir(out_dir) else os.path.dirname(out_dir)

