import logging
import pathlib

import youtube_audio_matcher.download
from ._argparsers import get_parser


def cli():
    parser = get_parser()
    args = vars(parser.parse_args())

    log_level = logging.INFO
    if args["debug"]:
        log_level = logging.DEBUG
    elif args["silent"]:
        log_level = logging.CRITICAL
    log_format = "[%(levelname)s] %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

    args["dst_dir"] = args["dst_dir"].expanduser().resolve()

    if args["num_retries"] < 0:
        args["num_retries"] = None

    # Remove youtube_audio_matcher verbosity keys/arguments from ``args``
    # so they aren't passed to run_download_channels.
    del args["debug"], args["silent"]

    youtube_audio_matcher.download.run_download_channels(**args)
