import argparse
import logging
import pathlib

import youtube_audio_matcher.download


def main():
    parser = argparse.ArgumentParser(
        description="""Efficiently and quickly download the audio from all
            videos on one or more YouTube channels, filter based on video
            length, and extract audio only from the segments of interest."""
    )
    parser.add_argument(
        "url", type=str, nargs="+",
        help="One or more channel/user URLs (e.g., "
        "www.youtube.com/c/YouTubeCreators). All options apply to all URLs."
    )
    parser.add_argument(
        "-d", "--dst-dir", type=pathlib.Path, metavar="<path>",
        help="Path to destination directory for downloaded files "
        "(default: current directory)"
    )
    parser.add_argument(
        "-i", "--ignore-existing", action="store_true",
        help="Do not download files that already exist"
    )
    parser.add_argument(
        "-r", "--retries", type=int, default=3, metavar="<num>",
        dest="num_retries",
        help="Number of times to re-attempt failed downloads (default: 3). "
        "Pass -1 to retry indefinitely until successful (not recommended)"
    )
    parser.add_argument(
        "-w", "--page-load-wait", type=float, default=1, metavar="<seconds>",
        help="Time to wait (in seconds) to allow page to load on initial page "
        "load and and after each page scroll"
    )
    parser.add_argument(
        "-L", "--exclude-longer-than", type=float, metavar="<seconds>",
        help="Do not download/convert videos longer than specified duration. "
        "This does NOT truncate videos to a maximum desired length; to "
        "extract or truncate specific segments of audio from downloaded "
        "videos, use --start, --end, and/or --duration"
    )
    parser.add_argument(
        "-S", "--exclude-shorter-than", type=float, metavar="<seconds>",
        help="Do not download/convert videos shorter than specified duration"
    )

    parser.add_argument(
        "--start", type=float, metavar="<seconds>", dest="start_time",
        help="Extract audio beginning at the specified video time (in seconds)"
    )
    parser.add_argument(
        "--end", type=float, metavar="<seconds>", dest="end_time",
        help="Extract audio up to the specified video time (in seconds)"
    )
    parser.add_argument(
        "--duration", type=float, metavar="<seconds>",
        help="Duration (in seconds) of audio to extract beginning at 0 if "
        "--start not specified, otherwise at --start. If --duration is used "
        "with --end, --duration takes precedence."
    )

    parser.add_argument(
        "-q", "--youtubedl-quiet", action="store_true", dest="quiet",
        help="Disable all youtube-dl and ffmpeg terminal output. This option "
        "does NOT control the terminal output of this program "
        "(youtube-audio-matcher); to set this program's output, use "
        "--silent or --debug"
    )

    _verbosity_args = parser.add_argument_group("verbosity options")
    verbosity_args = _verbosity_args.add_mutually_exclusive_group()
    verbosity_args.add_argument(
        "--debug", action="store_true", help="Print verbose debugging info"
    )
    verbosity_args.add_argument(
        "-s", "--silent", action="store_true",
        help="Suppress terminal output for this program"
    )
    args = parser.parse_args()

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    elif args.silent:
        log_level = logging.CRITICAL
    log_format = "[%(levelname)s] %(message)s"
    logging.basicConfig(format=log_format, level=log_level)

    if args.dst_dir is None:
        args.dst_dir = pathlib.Path(".")
    dst_dir = args.dst_dir.expanduser().resolve()

    video_metadata_from_urls_kwargs = {
        "video_metadata_from_source_kwargs": {
            "exclude_longer_than": args.exclude_longer_than,
            "exclude_shorter_than": args.exclude_shorter_than,
        },
        "get_source_kwargs": {
            "page_load_wait": args.page_load_wait,
        }
    }

    download_video_mp3_kwargs = {
        "num_retries": args.num_retries if args.num_retries >= 0 else None,
        "ignore_existing": args.ignore_existing,
        "start_time": args.start_time,
        "duration": args.duration,
        "end_time": args.end_time,
        "quiet": args.quiet,
    }

    youtube_audio_matcher.download.async_download_channels(
        args.url, dst_dir,
        video_metadata_from_urls_kwargs=video_metadata_from_urls_kwargs,
        download_video_mp3_kwargs=download_video_mp3_kwargs
    )
