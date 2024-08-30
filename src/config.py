import os
import sys
import tempfile
import logging
from arguments import Arguments

class Config:
    APP = {
        "name": "sub2srt",
        "description": "sub to srt subtitle converter",
        "version": "1.0.0"
    }
    INFILE_ALLOWED_EXTENSIONS = {
        'xml': {'description': 'SUB XML Subtitle File', 'property': 'sub_filename'},
        'sup': {'description': 'Blu-ray Subtitle File', 'property': 'sup_filename'},
        'mkv': {'description': 'Matroska Video File', 'property': 'mkv_filename'}
    }

    def __init__(self):
        # Set default properties
        self.args = Arguments(APP=self.APP).get_args()
        self.logger = logging.getLogger(f"{self.APP['name']}")
        self.verbose = False
        self.working_dir = None
        self.output_filename = None
        self.mkv_dirname = None
        self.mkv_filename = None
        self.sup_filename = None
        self.sub_filename = None
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

        # set the working directory
        self.working_dir = tempfile.TemporaryDirectory(prefix=f"{self.APP['name']}-", dir=args.tmpdir)
        in_file = os.path.realpath(getattr(args, 'in', None))
        out_file = os.path.realpath(getattr(args, 'out', None))

        if in_file:
            # get the file extension
            ext = os.path.splitext(in_file.lower())[-1].replace('.', '')
            if os.path.isdir(in_file):
                if not os.path.exists(in_file):
                    raise FileNotFoundError(f"Input directory does not exist: '{in_file}'")
                self.mkv_dirname = os.path.realpath(f'{in_file}')
            elif ext not in self.INFILE_ALLOWED_EXTENSIONS.keys():
                    raise ValueError(f"Invalid file extension: '{ext}'. Allowed extensions: {', '.join(f"'{item}'" for item in self.INFILE_ALLOWED_EXTENSIONS.keys())}")
            else:
                if not os.path.exists(in_file):
                    raise FileNotFoundError(f"Input file does not exist: '{in_file}'")
                elif os.stat(in_file).st_size == 0:
                    raise ValueError(f"Invalid input file:  '{in_file}' is zero bytes in size.")
                setattr(self, self.INFILE_ALLOWED_EXTENSIONS[ext]['property'], in_file)

        if out_file:
            self.output_filename = os.path.realpath(f'{out_file}')
