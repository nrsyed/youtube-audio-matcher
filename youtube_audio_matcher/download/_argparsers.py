import argparse
import pathlib


def get_core_parser():
    """
    Sub-parser containing core download module arguments. Used by both yamdl
    in this module and by the top-level yam command.
    """
    core_parser = argparse.ArgumentParser(add_help=False)

    download_args = core_parser.add_argument_group(title="Download arguments")
    download_args.add_argument(
        "-d", "--dst-dir", type=pathlib.Path, metavar="<path>", default=".",
        help="Path to destination directory for downloaded files"
    )
    download_args.add_argument(
        "-i", "--ignore-existing", action="store_true",
        help="Do not download files that already exist"
    )
    download_args.add_argument(
        "-p", "--page-load-wait", type=float, default=1, metavar="<seconds>",
        help="Time to wait (in seconds) to allow page to load on initial page "
        "load and and after each page scroll"
    )
    download_args.add_argument(
        "-r", "--retries", type=int, default=3, metavar="<num>",
        dest="num_retries",
        help="Number of times to re-attempt failed downloads. Pass -1 to "
        "retry indefinitely until successful"
    )
    download_args.add_argument(
        "-L", "--exclude-longer-than", type=float, metavar="<seconds>",
        help="Do not download/convert videos longer than specified duration. "
        "This does NOT truncate videos to a maximum desired length; to "
        "extract or truncate specific segments of audio from downloaded "
        "videos, use --start, --end, and/or --duration"
    )
    download_args.add_argument(
        "-S", "--exclude-shorter-than", type=float, metavar="<seconds>",
        help="Do not download/convert videos shorter than specified duration"
    )
    download_args.add_argument(
        "--start", type=float, metavar="<seconds>", dest="start_time",
        help="Extract audio beginning at the specified video time (in seconds)"
    )
    download_args.add_argument(
        "--end", type=float, metavar="<seconds>", dest="end_time",
        help="Extract audio up to the specified video time (in seconds)"
    )
    download_args.add_argument(
        "--duration", type=float, metavar="<seconds>",
        help="Duration (in seconds) of audio to extract beginning at 0 if "
        "--start not specified, otherwise at --start. If --duration is used "
        "with --end, --duration takes precedence."
    )

    verbose_args = core_parser.add_argument_group("Verbosity arguments")
    verbose_args.add_argument(
        "-y", "--youtubedl-verbose", action="store_true",
        help="Enable youtube-dl and ffmpeg terminal output"
    )
    verbose_args.add_argument(
        "--debug", action="store_true", help="Print verbose debugging info"
    )
    verbose_args.add_argument(
        "-s", "--silent", action="store_true",
        help="Suppress youtube-audio-matcher terminal output"
    )

    return core_parser


def get_parser():
    core_parser = get_core_parser()
    parser = argparse.ArgumentParser(
        parents=[core_parser],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""Efficiently and quickly download the audio from all
            videos on one or more YouTube channels, filter based on video
            length, and extract audio only from the segments of interest."""
    )
    parser.add_argument(
        "urls", type=str, nargs="+",
        help="One or more space-separated channel/user URLs (e.g., "
        "www.youtube.com/c/YouTubeCreators). Options apply to all URLs."
    )
    return parser
