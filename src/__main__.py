import sys
import os
import logging
from pprint import pprint
from config import Config
from mkv import supTrackExporter
from sup import supFileConverter
from sub import SubFileProcessor

# Main entry point
if __name__=="__main__":
    # try:
    config = Config()
    logger = config.logger
    pprint(config.__dict__)
    # except Exception as e:
        # print(f"[FATAL ERROR]: {e}")
        # sys.exit(1)

    # Process each input type as needed
    if config.mkv_dirname or config.mkv_filename:
        if config.mkv_filename:
            logger.info(f"MKV file detected: {config.mkv_filename}")
            mkv_path = config.mkv_filename
        else:
            logger.info(f"MKV directory detected: {config.mkv_dirname}")
            mkv_path = config.mkv_dirname

        config.sup_filename = supTrackExporter(
            logger = logger,
            mkv_path=mkv_path
            ).export(working_dir=config.working_dir.name)

    if config.sup_filename:
        logger.info(f"SUP file detected: '{config.sup_filename}'")
        config.sub_filename = supFileConverter(
            logger = logger,
            bdsup2sub_jar=config.bdsup2sub_jar,
            sup_filename=config.sup_filename
            ).convert(config.working_dir.name)

    if config.sub_filename:
        logger.info(f"SUB file detected: '{config.sub_filename}'")
        config.outfile = SubFileProcessor(
            logger = logger,
            in_file=config.sub_filename,
            out_file=config.output_filename
        ).process(
            working_dir=config.working_dir.name,
            limit=config.limit,
            progress=config.progress,
            overwrite=config.force
            )

        if not config.outfile:
            sys.exit(1)
        sys.exit(0)

