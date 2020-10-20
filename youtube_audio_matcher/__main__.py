import argparse


import youtube_audio_matcher
from .database import _argparsers as db_argparsers
from .download import _argparsers as dl_argparsers
from .audio import _argparsers as fp_argparsers


def get_parser():
    """
    TODO
    """
    # Get core arguments from download module parser.
    dl_parser = dl_argparsers.get_core_parser()

    # Get core fingerprint arguments from audio module parser and add args.
    fp_parser = fp_argparsers.get_core_parser(extra_args=True)

    # Get core database arguments from database module parser.
    db_parser = db_argparsers.get_core_parser()

    # Construct main parser from sub-parsers and add necessary arguments.
    parser = argparse.ArgumentParser(
        description=None,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[dl_parser, fp_parser, db_parser]
    )

    # TODO: add input <url/path>, log, and delete after download args.

    return parser


def main():
    # TODO
    #parser = get_parser()
    #args = parser.parse_args()
    raise NotImplementedError
    pass
