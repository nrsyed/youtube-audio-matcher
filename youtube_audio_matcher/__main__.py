import argparse


from . import audio, database, download


def get_parser():
    # Get core arguments from download module parser.
    dl_parser = download.__main__.get_core_parser()

    # Get core fingerprint arguments from audio module parser and add args.
    fp_parser = audio.__main__.get_core_parser()
    fp_parser.add_argument(
        "-f", "--fanout", type=int, default=10, metavar="<int>",
        help="Number of adjacent peaks to consider for generating hashes"
    )
    fp_parser.add_argument(
        "-l", "--hash-length", type=int, default=20, metavar="<int>",
        help="Length to truncate each fingerprint SHA1 hash to (max 40)"
    )
    fp_parser.add_argument(
        "--max-time-delta", type=float, default=100, metavar="<float>",
        help="Target zone max time offset difference for hashes"
    )
    fp_parser.add_argument(
        "--min-time-delta", type=float, default=0, metavar="<float>",
        help="Target zone min time offset difference for hashes"
    )

    # Get core database arguments from database module parser.
    db_parser = database.__main__.get_core_parser()

    # Construct main parser from sub-parsers and add necessary arguments.
    parser = argparse.ArgumentParser(
        description=None,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[dl_parser, fp_parser, db_parser]
    )

    """
    TODO:
    input <url/path>
    log
    delete_after
    """
