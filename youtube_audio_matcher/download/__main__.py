import logging
import pathlib

import youtube_audio_matcher.download
from ._argparsers import get_parser


def main():
    parser = get_parser()
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
        "verbose": args.youtubedl_verbose,
    }

    youtube_audio_matcher.download.run_download_channels(
        args.url, dst_dir,
        video_metadata_from_urls_kwargs=video_metadata_from_urls_kwargs,
        download_video_mp3_kwargs=download_video_mp3_kwargs
    )
