import argparse
import tempfile


class Arguments:
    def __init__(self, APP):
        parser = argparse.ArgumentParser(description=f"{APP['name']} v{APP['version']}: {APP['description']}")

        parser.add_argument('-i', '--in', metavar='subtitles.xml', default='subtitles.xml',
                            help="The full path to the import file. This can be a SUP, XML, MKV file, or a directory containing the MKV file.")
        parser.add_argument('-o', '--out', metavar='subtitles.srt', default='subtitles.srt',
                            help="The full path to the generated SRT file.")
        parser.add_argument('-t', '--tmpdir', metavar='/tmp', default=f'{tempfile.gettempdir()}',
                            help="The temp path/working directory")
        parser.add_argument('-l', '--limit', metavar=100, default=None, type=int,
                            help="Only process this many subtitles")
        parser.add_argument('-f', '--force', action="store_true", default=False,
                            help='Force the overwrite of the output file if it exists.')
        parser.add_argument('-p', '--progress', action="store_true", default=True,
                            help='Show a progress bar.')
        parser.add_argument('-v', '--verbose', action="store_true", default=True,
                            help='Show verbose output.')

        self.args = parser.parse_args()

    def get_args(self):
        return self.args
