import os
import argparse
import tempfile
import shutil


class Arguments:
    RUN_MODES = {
        'first': {"description": "Find the first subtitle track and convert it."},
        'all': {"description": "Find all subtitle tracks and convert them."}
    }
    def __init__(self, APP):
        mode_help = ""
        for mode, metadata in self.RUN_MODES.items():
            mode_help += f"\n\n - '{mode}': {metadata['description']}\n"

        parser = argparse.ArgumentParser(
            prog=f"{APP['name']}",
            description=f"{APP['description']}",
            epilog=f"-- {APP['tagline']} --"
        )
        parser.add_argument('-m', '--mode', default='first', choices=self.RUN_MODES.keys(),
                            help=f"Run Mode: how multiple subtitle tracks in an MKV are handled.{mode_help}. Default: 'first'")
        parser.add_argument('-i', '--in', metavar='subtitles.xml', default='subtitles.xml',
                            help="The full path to the import file. This can be a SUP, XML, MKV file, or a directory containing the MKV file.")
        parser.add_argument('-o', '--out', metavar='/Videos/subtitles', default=None,
                            help="The full path to save the generated SRT file(s). Default uses the path of the input file or directory.")
        parser.add_argument('-u', '--uid', default=None, help="When running in docker, set the output file ownership to this uid.")
        parser.add_argument('-g', '--gid', default=None, help="When running in docker, set the output file ownership to this gid.")            
        parser.add_argument('-t', '--tmpdir', metavar='/tmp', default=f'{tempfile.gettempdir()}',
                            help="The temp path/working directory")
        parser.add_argument('--bdsup2sub-jar', metavar='/opt/BDSup2Sub.jar', default=None,
                            help="The path to the BDSup2Sub.jar file", action=EnvDefault, envvar="BDSUP2SUB")
        # Disabled util this supports languages other than English
        # parser.add_argument('-l', '--language', default=['eng'],
        #                     help="The language of subtitle tracks to extract from an MKV file, in ISO-639-1 format.",
        #                     action="append")
        parser.add_argument('-L', '--limit', metavar=100, default=None, type=int,
                            help="Only process this many subtitles from a SUB file.")
        parser.add_argument('-f', '--force', action="store_true", default=False,
                            help='Force the overwrite of the output file if it exists.')
        parser.add_argument('-p', '--progress', action="store_true", default=True,
                            help='Show a progress bar.')
        parser.add_argument('-v', '--verbose', action="store_true", default=False,
                            help='Show verbose output.')
        parser.add_argument('-V', '--version', action="version", version=f'%(prog)s v{APP['version']}')

        self.args = parser.parse_args()

    def get_args(self):
        return self.args

class EnvDefault(argparse.Action):
    """ Argparse Action that uses ENV Vars for default values """

    def __init__(self, envvar, required=False, default=None, **kwargs):
        bset = {"true": True, "1": True, "false": False, "0": False}
        if envvar:
            # If passed a string, convert to a list
            if isinstance(envvar, str):
                envvar = [envvar]
            # Check for env vars for default values
            for varname in envvar:
                # print("Checking for env var: {}".format(varname))
                if varname in os.environ:
                    # Convert boolean strings to bool
                    if os.environ[varname].lower() in bset.keys() and "type" in kwargs and kwargs["type"] == bool:
                        default = bset[os.environ[varname].lower()]
                    else:
                        default = os.environ[varname]
                    required = False
                    break

        super().__init__(default=default,
                         required=required,
                         **kwargs)
    
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

