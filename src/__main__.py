import sys
import os
import logging
from pprint import pprint
from config import Config
from job_queue import QueueItem
from mkv import supTrackExporter
from sup import supFileConverter
from sub import SubFileProcessor

# Main entry point
if __name__=="__main__":
    try:
        config = Config()
        logger = config.logger
        queue = config.queue
    except Exception as e:
        print(f"[FATAL ERROR]: {e}")
        sys.exit(1)

    # print(config.__dict__)
    # exit()

    # load the first jou into the appropriate queue
    config.logger.debug(f"Loading {config.input_type} queue with the start job.")
    init_queue = getattr(config.queue, config.input_type)
    init_queue.put(
            QueueItem(
                input_file=config.input_file,
                output_path=config.output_path
            )
        )

    # export tracks from MKV file(s) to SUP
    if not config.queue.mkv.empty():
        config.sup_filename = supTrackExporter(
            queue=config.queue.mkv,
            next_queue=config.queue.sup,
            mode=config.mode,
            working_dir=config.working_dir.name,
            language=config.language,
            logger = logger
        )

    # Convert SUP file(s) to SUB
    if not config.queue.sup.empty():
        config.sub_filename = supFileConverter(
            queue=config.queue.sup,
            next_queue=config.queue.sub,
            bdsup2sub_jar=config.bdsup2sub_jar,
            working_dir=config.working_dir.name,
            logger = logger
            )

    # Convert SUB File(s) to SRT
    if not config.queue.sub.empty():
        config.outfile = SubFileProcessor(
            queue=config.queue.sub,
            logger = logger,
            limit=config.limit,
            progress=config.progress,
            overwrite=config.force,
            working_dir=config.working_dir.name,
        )

    # If a uid and or gid was specified, change the ownership of the out files
    if config.uid:
        config.gid = config.uid if not config.gid else config.gid
        for file in os.listdir(config.output_path):
            if file.lower().endswith('.sup') or file.lower().endswith('.srt'):
                os.chown(os.path.join(config.output_path, file), uid=int(config.uid), gid=int(config.gid))
    sys.exit(0)

