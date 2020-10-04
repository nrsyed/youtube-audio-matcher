import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import math
import os
import pathlib
import re
import time

import bs4
import selenium.webdriver
import youtube_dl


def get_videos_page_url(url):
    """
    Get a valid videos page URL from a YouTube channel/user URL. See
    https://support.google.com/youtube/answer/6180214?hl=en

    Args:
        url (str): URL for a YouTube channel or user. The end of the URL may
            contain extra parameters or a subpath to a different page on the
            channel—these are stripped and the suffix "/videos" is added to
            the end of the core URL.
    Returns:
        URL for videos page if valid URL, else None.

    Examples:
        >>> url = 'youtube.com/channel/UCUZHFZ9jIKrLroW8LcyJEQQ'
        >>> get_videos_page_url(url)
        'https://www.youtube.com/channel/UCUZHFZ9jIKrLroW8LcyJEQQ/videos'

        >>> url2 = 'www.youtube.com/c/creatoracademy/community'
        >>> get_videos_page_url(url2)
        'https://www.youtube.com/c/creatoracademy/videos'

        >>> url3 = 'https://youtube.com/u/foobar?param1=val1&param2=val2'
        >>> get_videos_page_url(url3)
        'https://www.youtube.com/u/foobar/videos'
    """
    expr = r"^.*(/(c(hannel)?|u(ser)?)/[a-zA-Z0-9-_]+)"
    match = re.match(expr, url)

    if match:
        videos_page_path = match.groups()[0]
        return f"https://www.youtube.com{videos_page_path}/videos"
    return None


def get_source(url, init_wait_time=2, scroll_wait_time=1):
    """
    Get source for the page at `url` by scrolling to the end of the page.

    Args:
        url (str): URL for webpage.
        init_wait_time (float): Initial wait time (in seconds) for page load.
        scroll_wait_time (float): Subsequent wait time (in seconds) for
            page scrolls.

    Returns:
        String containing page source code.
    """
    # TODO: incorporate timeout
    # TODO: hide browser window
    # TODO: options for wait time in higher level functions and CLI?
    logging.info(f"Grabbing page source for URL {url}")
    try:
        driver = selenium.webdriver.Chrome()
        driver.get(url)
        time.sleep(init_wait_time)

        source = None
        scroll_by = 5000
        while source != driver.page_source:
            source = driver.page_source
            driver.execute_script(f"window.scrollBy(0, {scroll_by});")
            time.sleep(scroll_wait_time)
        driver.quit()
    except Exception as e:
        logging.error(f"Error getting page source for URL {url}")
        raise e
    finally:
        return source


def get_videos_page_metadata(
    source, exclude_longer_than=None, exclude_shorter_than=None
):
    """
    Given the page source for a channel/user Videos page, extract video id,
    video title, and video duration (in seconds) for each video.

    Args:
        source (str): Page source.
        exclude_longer_than (float): Only return metadata for videos shorter
            than the given duration (in seconds). If None, return all videos.
        exclude_shorter_than (float): Only return metadata for videos longer
            than the given duration (in seconds). If None, return all videos.

        `exclude_longer_than` and `exclude_shorter_than` may both be supplied
        to return videos meeting both criteria.

    Returns:
        A list of videos, where each video is represented by a dict:
        {
            "id": str,
            "title": str,
            "duration": int
        }
    """
    max_duration = exclude_longer_than
    if max_duration is None:
        max_duration = math.inf

    min_duration = exclude_shorter_than
    if min_duration is None:
        min_duration = 0

    logging.debug(
        f"Getting videos page metadata. max_duration={max_duration}, "
        f"min_duration={min_duration}"
    )

    soup = bs4.BeautifulSoup(source, "html.parser")

    videos = []
    video_id_expr = r"^.*/watch\?v=([a-zA-Z0-9_-]+)"

    video_renderer_elements = soup.findAll("ytd-grid-video-renderer")
    for renderer in video_renderer_elements:
        # Get video title and YT video id from title <a> element.
        title_tag = renderer.find("a", {"id": "video-title"})
        video_title = title_tag["title"]

        # Get video id from title tag hyperlink href value.
        video_id = None
        video_id_match = re.match(video_id_expr, title_tag["href"])
        if video_id_match:
            video_id = video_id_match.groups()[0]

        # Get video duration from duration <span> element.
        duration_tag = renderer.find(
            "span", {"class": "ytd-thumbnail-overlay-time-status-renderer"}
        )
        duration_str = duration_tag.text.strip()

        # Extract time units from duration string and compute total seconds.
        duration_vals = duration_str.split(":")
        seconds = int(duration_vals[-1])
        minutes = int(duration_vals[-2])
        hours = int(duration_vals[-3]) if len(duration_vals) > 2 else 0
        duration = seconds + (minutes * 60) + (hours * 3600)

        if min_duration <= duration <= max_duration:
            videos.append(
                {"id": video_id, "title": video_title, "duration": duration}
            )
    return videos


def download_video_mp3(
    video_id, dst_dir, start_time=None, duration=None, end_time=None,
    ignore_existing=False, quiet=False
):
    """
    Download a YouTube video as an mp3 using youtube-dl.

    Args:
        video_id (str): The video id, i.e., www.youtube.com/watch?v=<video_id>
        dst_dir (str): Path to destination directory for downloaded file.
        start_time (float): Start time (in seconds) of the portion of the
            video to extract. Zero (beginning of video) if omitted.
        duration (float): Duration of video (in seconds) to extract. Whole
            video extracted if omitted.
        end_time (float): End time (in seconds) of the portion of the video to
            extract. Note that `duration` takes precedence over `end_time` (as
            defined in ffmpeg usage) if both are provided. Whole video is
            extracted if `duration` and `end_time` are both omitted.
        ignore_existing (bool): Skip existing files.
        quiet (bool): Suppress youtube_dl/ffmpeg terminal output.

    Returns:
        Path (str) to output file if download successful, else None.
    """
    # youtube_dl output file template/path.
    out_template = os.path.join(dst_dir, f"{video_id}.%(ext)s")

    # ffmpeg postprocessor args, if any.
    postprocessor_args = []
    if start_time is not None:
        postprocessor_args.extend(["-ss", str(start_time)])
    if duration is not None:
        postprocessor_args.extend(["-t", str(duration)])
    if end_time is not None:
        postprocessor_args.extend(["-to", str(end_time)])

    # youtube_dl.YoutubeDL options.
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": postprocessor_args,
        "quiet": quiet,
        "no_warnings": quiet,
    }

    dst_path = os.path.join(dst_dir, f"{video_id}.mp3")
    if os.path.exists(dst_path):
        logging.info(
            f"Skipping video id {video_id}; file {dst_path} already exists"
        )
    else:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except youtube_dl.utils.DownloadError as e:
            logging.error(f"Error downloading video id {video_id}")
            return None
        else:
            logging.info(
                f"Successfully downloaded file {dst_path} (video id {video_id})"
            )

    return dst_path


def download_video_mp3s(
    video_ids, dst_dir, max_workers=None, start_time=None, duration=None,
    end_time=None, ignore_existing=False, quiet=False
):
    """
    Multithreaded wrapper for download_video_mp3 to download/convert multiple videos
    concurrently. This function exists because, although
    youtube_dl.YoutubeDL.download() accepts a list of video URLs, it is not
    multithreaded and downloads each video sequentially.

    Args:
        video_ids (List[str]): A list of YouTube video ids to download.
        dst_dir (str): Path to destination directory for downloaded files.
        max_workers (int): Max threads to spawn.
        start_time (float): See `download_video_mp3`.
        duration (float): See `download_video_mp3`.
        end_time (float): See `download_video_mp3`.

        `start_time`, `duration`, and `end_time` (if specified) are applied
        to all videos (see `download_video_mp3`).

    Returns:
        A list of paths (one per video) returned by `download_video_mp3`.
    """
    thread_pool = ThreadPoolExecutor(max_workers=max_workers)
    futures = []

    for video_id in video_ids:
        futures.append(
            thread_pool.submit(
                download_video_mp3, video_id, dst_dir, start_time=start_time,
                duration=duration, end_time=end_time,
                ignore_existing=ignore_existing, quiet=quiet
            )
        )
        # TODO: add sleep between option
    thread_pool.shutdown()

    # Get paths to output files returned by calls to download_video_mp3().
    paths = [future.result() for future in futures]
    return paths


def download_channel(
    url, dst_dir, num_retries=3, ignore_existing=False,
    exclude_longer_than=None, exclude_shorter_than=None, start_time=None,
    duration=None, end_time=None, quiet=False
):
    """
    Download all videos from a YouTube channel/user subject to the specified
    criteria.

    The `exclude_longer_than` and `exclude_shorter_than` arguments DO NOT
    truncate MP3s but instead prevent them from being downloaded at all (see
    `get_videos_page_metadata`). To truncate MP3s to only the desired segment,
    use the `start_time`, `duration`, and `end_time` arguments (see
    `download_video_mp3`). For example, if a video is 3000 seconds long and
    the first 500 seconds are desired, use `duration=500`; providing
    `exclude_longer_than=500` would cause the video to NOT be downloaded at all.

    Args:
        url (str): URL of the desired channel/user. From this URL, the URL of
            the channel/user's Videos page is automatically constructed.
        dst_dir (str): Path to download destination directory.
        num_retries (int): Number of times to re-attempt download when one or
            more files fails to download. Only the failed files are retried.
            Pass `None` to retry indefinitely (not recommended).
        ignore_existing (bool): Skip existing files (see `download_video_mp3`).
        exclude_longer_than (float): Exclude videos longer than the
            specified value (in seconds). See `get_videos_page_metadata`.
        exclude_shorter_than (float): Exclude videos shorter than the
            specified value (in seconds). See `get_videos_page_metadata`.
        start_time (float): See `download_video_mp3`.
        duration (float): See `download_video_mp3`.
        end_time (float): See `download_video_mp3`.
        quiet (bool): Suppress youtube_dl/ffmpeg terminal output (see
            `download_video_mp3`).

    Returns:
        A list of dicts containing the video id, video title, (original) video
        duration, channel/user videos page URL from which the video was
        downloaded, and path to the downloaded MP3 file on the local machine
        (path will be `None` if download was unsuccessful):

        {
            "id": str,
            "title": str,
            "duration": int,
            "channel_url": str,
            "path": str
        }
    """
    videos_page_url = get_videos_page_url(url)
    videos_page_source = get_source(videos_page_url)

    # Get metadata for each video in the Videos page source.
    metadata = get_videos_page_metadata(
        videos_page_source, exclude_longer_than=exclude_longer_than,
        exclude_shorter_than=exclude_shorter_than
    )

    # Add output file path and channel URL to video metadata.
    for video in metadata:
        video["channel_url"] = videos_page_url
        video["path"] = None

    # Download all videos. Re-attempt failed videos `num_retries` times.
    if num_retries is None:
        num_retries = math.inf
    tries = 0

    # List of indexes into the list of video metadata [0, ..., num_videos - 1]
    idxs_to_download = [i for i, _ in enumerate(metadata)]

    while (tries < num_retries + 1) and idxs_to_download:
        logging.info(
            f"Downloading files from {videos_page_url} (attempt #{tries + 1})"
        )

        video_ids = [metadata[idx]["id"] for idx in idxs_to_download]
        dst_paths = download_video_mp3s(
            video_ids, dst_dir, start_time=start_time,
            duration=duration, end_time=end_time,
            ignore_existing=ignore_existing, quiet=quiet
        )
        tries += 1

        updated_idxs_to_download = []
        for j, path in enumerate(dst_paths):
            idx = idxs_to_download[j]
            if path is None:
                # File was not downloaded correctly. Re-add its index in
                # `metadata` to the list of indexes to be downloaded.
                failed_video_id = metadata[idx]["id"]
                log_msg = f"Failed to download video id {failed_video_id}."
                if tries >= num_retries + 1:
                    log_msg += " Not retrying (max attempts reached)."
                    logging.error(log_msg)
                else:
                    log_msg += " Download will be retried."
                    logging.warning(log_msg)
                updated_idxs_to_download.append(idx)
            else:
                metadata[idx]["path"] = path
        idxs_to_download = updated_idxs_to_download

    num_successful_downloads = len(
        [video for video in metadata if video["path"] is not None]
    )
    logging.info(
        f"Successfully downloaded audio from {num_successful_downloads} of "
        f"{len(metadata)} videos for URL {videos_page_url}"
    )
    return metadata


def download_channels(urls, dst_dir, *args, **kwargs):
    """
    Multithreaded wrapper for `download_channel`.

    Args:
        urls (List[str]): List of YouTube channel/user URLs.
        *args: See `download_channel`.
        **kwargs: See `download_channel`.

    Returns:
        A list of dicts containing the video id, video title, (original) video
        duration, channel/user videos page URL from which the video was
        downloaded, and path to the downloaded MP3 file on the local machine
        (path will be `None` if download was unsuccessful):

        {
            "id": str,
            "title": str,
            "duration": int,
            "channel_url": str,
            "path": str
        }
    """
    thread_pool = ThreadPoolExecutor()
    futures = []
    for url in urls:
        futures.append(
            thread_pool.submit(download_channel, url, dst_dir, *args, **kwargs)
        )
    thread_pool.shutdown()

    metadata = [video for future in futures for video in future.result()]

    num_successful_downloads = len(
        [video for video in metadata if video["path"] is not None]
    )
    logging.info(
        f"Successfully downloaded audio from {num_successful_downloads} of "
        f"{len(metadata)} total videos"
    )
    return metadata


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
        "-L", "--exclude-longer-than", type=float, metavar="<seconds>",
        help="Do not download/convert videos longer than specified duration. "
        "This does NOT truncate videos to a maximum desired length; to extract "
        "or truncate specific segments of audio from downloaded videos, use "
        "--start, --end, and/or --duration"
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

    download_func_kwargs = {
        "num_retries": args.num_retries if args.num_retries >= 0 else None,
        "exclude_longer_than": args.exclude_longer_than,
        "exclude_shorter_than": args.exclude_shorter_than,
        "ignore_existing": args.ignore_existing,
        "start_time": args.start_time,
        "duration": args.duration,
        "end_time": args.end_time,
        "quiet": args.quiet,
    }
    metadata = download_channels(args.url, dst_dir, **download_func_kwargs)


if __name__ == "__main__":
    main()
