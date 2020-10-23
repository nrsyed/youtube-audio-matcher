import argparse
from datetime import datetime
import logging
import os

import youtube_audio_matcher
from .database import _argparsers as db_argparsers
from .download import _argparsers as dl_argparsers
from .audio import _argparsers as fp_argparsers


def get_parser():
    """
    TODO
    """
    # TODO: add log arg.

    # Get core database arguments from database module parser.
    db_parser = db_argparsers.get_core_parser()

    # Get core arguments from download module parser.
    dl_parser = dl_argparsers.get_core_parser(extra_args=True)

    # Get core fingerprint arguments from audio module parser and add args.
    fp_parser = fp_argparsers.get_core_parser(extra_args=True)

    # Construct main parser from sub-parsers and add necessary arguments.
    parser = argparse.ArgumentParser(
        description=None,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[db_parser, dl_parser, fp_parser]
    )
    
    parser.add_argument(
        "inputs", type=str, nargs="+",
        help="One or more space-separated input sources (YouTube channel/user "
        "URL, local path to audio file, or local path to a directory of "
        "audio files)"
    )

    parser.add_argument(
        "-A", "--add-to-database", action="store_true",
        help="Add fingerprinted files to the database instead of searching "
        "the database for matches"
    )
    parser.add_argument(
        "-c", "--conf-thresh", type=float, default=0.01, metavar="<float>",
        help="Confidence threshold for matches"
    )
    parser.add_argument(
        "-o", "--output", nargs="?", metavar="path", const=0,
        help="Path to output file containing matches in JSON format; if this "
        "option is provided without an argument, a timestamped filename is "
        "generated and written to the current directory"
    )

    verbose_args = parser.add_argument_group("Verbosity arguments")
    verbose_args.add_argument(
        "--debug", action="store_true", help="Print verbose debugging info"
    )
    verbose_args.add_argument(
        "-s", "--silent", action="store_true",
        help="Suppress youtube-audio-matcher terminal output"
    )

    return parser


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

    inputs = args["inputs"]

    # If --output was called without an argument, it will hold the const
    # value 0 (an integer), and we generate an output filename.
    out_fpath = None
    if isinstance(args["output"], int):
        out_fpath = "{}_matches.json".format(
            datetime.now().strftime("%Y%m%d%H%M%S")
        )
    elif isinstance(args["output"], str):
        out_fpath = os.path.abspath(os.path.expanduser(args["output"]))

    del args["inputs"], args["debug"], args["output"], args["silent"]
    breakpoint()

    try:
        youtube_audio_matcher.main(inputs, out_fpath=out_fpath, **args)
    except Exception as e:
        raise e
    finally:
        os.system("stty sane")
