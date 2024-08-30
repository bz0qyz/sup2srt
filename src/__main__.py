import sys
import os
from pprint import pprint
from config import Config
from mkv import supTrackExporter
from sup import supFileConverter
# from sub import SubFileProcessor

# Main entry point
if __name__=="__main__":
    try:
        config = Config()
        logger = config.logger
        pprint(config.__dict__)
    except Exception as e:
        print(f"[FATAL ERROR]: {e}")
        sys.exit(1)

    # Process each input type as needed
    if config.mkv_dirname or config.mkv_filename:
        if config.mkv_filename:
            logger.info(f"MKV file detected: {config.mkv_filename}")
        else:
            logger.info(f"MKV directory detected: {config.mkv_dirname}")

        config.sup_filename = supTrackExporter(config.mkv_filename).export(config.working_dir.name)

    if config.sup_filename:
        logger.info(f"SUP file detected: '{config.sup_filename}'")
        config.sub_filename = supFileConverter(config.sup_filename).convert(config.working_dir.name)

    if config.sub_filename:
        logger.info(f"SUB file detected: '{config.sub_filename}'")
        # sub_processor = SubProcessor(config.sub_filename, config.output_filename)
        # sub_processor.process()


