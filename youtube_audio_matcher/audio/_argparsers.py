import argparse
import pathlib


def get_core_parser(extra_args=False):
    """
    Sub-parser containing core audio module arguments. Used by both yamfp
    in this module and by the top-level yam command.

    Args:
        extra_args (bool): Include extra args required for audio fingerprinting
            but not required for spectrogram/peak visualization. These options
            are placed in alphabetical order with other args via if statements.
    """
    core_parser = argparse.ArgumentParser(add_help=False)

    fingerprint_args = core_parser.add_argument_group("fingerprint arguments")

    fingerprint_args.add_argument(
        "--erosion-iterations", type=int, default=1, metavar="<int>",
        help="Number of times to apply binary erosion for peak finding"
    )

    if extra_args:
        fingerprint_args.add_argument(
            "-f", "--fanout", type=int, default=10, metavar="<int>",
            help="Number of adjacent peaks to consider for generating hashes"
        )

    fingerprint_args.add_argument(
        "--filter-connectivity", type=int, default=1, choices=(1, 2),
        help="Max filter neighborhood connectivity for peak finding"
    )
    fingerprint_args.add_argument(
        "--filter-dilation", type=int, default=10, metavar="<int>",
        help="Max filter dilation (neighborhood size) for peak finding"
    )

    if extra_args:
        fingerprint_args.add_argument(
            "-l", "--hash-length", type=int, default=20, metavar="<int>",
            help="Truncate each fingerprint SHA1 hash to --hash-length (max 40)"
        )
        fingerprint_args.add_argument(
            "--max-time-delta", type=float, default=100, metavar="<float>",
            help="Target zone max time offset difference for hashes"
        )
        fingerprint_args.add_argument(
            "--min-time-delta", type=float, default=0, metavar="<float>",
            help="Target zone min time offset difference for hashes"
        )

    fingerprint_args.add_argument(
        "-a", "--min-amplitude", type=float, default=10, metavar="<dB>",
        help="Spectogram peak minimum amplitude in dB"
    )
    fingerprint_args.add_argument(
        "--spectrogram-backend", type=str, choices=("scipy", "matplotlib"),
        default="scipy",
        help="Library to use for computing spectrogram"
    )
    fingerprint_args.add_argument(
        "--win-overlap-ratio", type=float, default=0.5, metavar="<float>",
        help="Window overlap as a fraction of window size, in the range [0, 1)"
    )
    fingerprint_args.add_argument(
        "--win-size", type=int, default=4096, metavar="<int>",
        help="Number of samples per FFT window"
    )
    return core_parser


def get_parser():
    core_parser = get_core_parser()
    parser = argparse.ArgumentParser(
        parents=[core_parser],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Visualize an audio file fingerprint by plotting its "
        "spectrogram and the spectrogram peaks."
    )
    parser.add_argument(
        "filepath", type=pathlib.Path, metavar="<path>",
        help="Path to audio file"
    )
    return parser
