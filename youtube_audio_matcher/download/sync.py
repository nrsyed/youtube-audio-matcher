from concurrent.futures import ThreadPoolExecutor
import logging
import time

import selenium.webdriver

from .common import (
    download_video_mp3, get_videos_page_url, video_metadata_from_page_source
)


def get_source(url, init_wait_time=2, scroll_wait_time=1):
    """
    Get source for the page at ``url`` by scrolling to the end of the page.

    Args:
        url (str): URL for webpage.
        init_wait_time (float): Initial wait time (in seconds) for page load.
        scroll_wait_time (float): Subsequent wait time (in seconds) for each
            page scroll.

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


def download_video_mp3s(
    video_ids, dst_dir, max_workers=None, wait_between=0, start_time=None,
    duration=None, end_time=None, ignore_existing=False, num_retries=3,
    quiet=False
):
    """
    Multithreaded wrapper for :func:`download_video_mp3` to download/convert
    multiple videos concurrently. This function exists because, although
    youtube_dl.YoutubeDL.download() accepts a list of video URLs, it is not
    multithreaded and downloads each video sequentially.

    Args:
        video_ids (List[str]): A list of YouTube video ids to download.
        dst_dir (str): Path to destination directory for downloaded files.
        max_workers (int): Max threads to spawn.
        wait_between (float): Seconds to wait before spawning each thread (to
            reduce number of requests made in rapid succession).
        start_time (float): See :func:`download_video_mp3`.
        duration (float): See :func:`download_video_mp3`.
        end_time (float): See :func:`download_video_mp3`.
        ignore_existing (bool): See :func:`download_video_mp3`.
        num_retries (int): See :func:`download_video_mp3`.
        quiet (bool): See :func:`download_video_mp3`.

    Returns:
        A list of paths (one per video) returned by :func:`download_video_mp3`.

    .. note:
        ``start_time``, ``duration``, and ``end_time`` (if specified) are
        applied to all videos (see :func:`download_video_mp3`).
    """
    thread_pool = ThreadPoolExecutor(max_workers=max_workers)
    futures = []

    for video_id in video_ids:
        futures.append(
            thread_pool.submit(
                download_video_mp3, video_id, dst_dir, start_time=start_time,
                duration=duration, end_time=end_time,
                ignore_existing=ignore_existing, num_retries=num_retries,
                quiet=quiet
            )
        )
        if wait_between:
            time.sleep(wait_between)
    thread_pool.shutdown()

    # Get paths to output files returned by calls to download_video_mp3().
    paths = [future.result() for future in futures]
    return paths


def download_channel(
    url, dst_dir, num_retries=3, ignore_existing=False,
    exclude_longer_than=None, exclude_shorter_than=None, wait_between=0,
    start_time=None, duration=None, end_time=None, quiet=False
):
    """
    Download all videos from a YouTube channel/user subject to the specified
    criteria.

    The ``exclude_longer_than`` and ``exclude_shorter_than`` arguments DO NOT
    truncate MP3s but instead prevent them from being downloaded at all (see
    :func:`video_metadata_from_page_source`). To truncate MP3s to only the desired
    segment, use the ``start_time``, ``duration``, and ``end_time`` arguments
    (see :func:`download_video_mp3`). For example, if a video is 3000 seconds
    long and the first 500 seconds are desired, use `duration=500`; providing
    ``exclude_longer_than=500`` would cause the video to NOT be downloaded at
    all.

    Args:
        url (str): URL of the desired channel/user. From this URL, the URL of
            the channel/user's Videos page is automatically constructed.
        dst_dir (str): Path to download destination directory.
        num_retries (int): Number of times to re-attempt failed downloads. Pass
            `None` to retry indefinitely.
        ignore_existing (bool): Skip existing files
            (see :func:`download_video_mp3`).
        exclude_longer_than (float): Exclude videos longer than the
            specified value (in seconds). See :func:`video_metadata_from_page_source`.
        exclude_shorter_than (float): Exclude videos shorter than the
            specified value (in seconds). See :func:`video_metadata_from_page_source`.
        wait_between (float): See :func:`download_video_mp3s`.
        start_time (float): See :func:`download_video_mp3`.
        duration (float): See :func:`download_video_mp3`.
        end_time (float): See :func:`download_video_mp3`.
        quiet (bool): Suppress youtube_dl/ffmpeg terminal output (see
            :func:`download_video_mp3`).

    Returns:
        A list of dicts containing the video id, video title, (original) video
        duration, channel/user videos page URL from which the video was
        downloaded, and path to the downloaded MP3 file on the local machine
        (path will be ``None`` if download was unsuccessful)::

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
    videos = video_metadata_from_page_source(
        videos_page_source, exclude_longer_than=exclude_longer_than,
        exclude_shorter_than=exclude_shorter_than
    )

    video_ids = [video["id"] for video in videos]
    dst_paths = download_video_mp3s(
        video_ids, dst_dir, wait_between=wait_between,
        start_time=start_time, duration=duration, end_time=end_time,
        ignore_existing=ignore_existing, num_retries=num_retries,
        quiet=quiet
    )

    # Add output file path and channel URL to video metadata.
    num_successful_downloads = 0
    for video, dst_path in zip(videos, dst_paths):
        video["channel_url"] = videos_page_url
        video["path"] = dst_path
        if dst_path is not None:
            num_successful_downloads += 1

    logging.info(
        f"Successfully downloaded audio from {num_successful_downloads} of "
        f"{len(videos)} videos for URL {videos_page_url}"
    )
    return videos


def download_channels(urls, dst_dir, *args, **kwargs):
    """
    Multithreaded wrapper for :func:`download_channel`.

    Args:
        urls (List[str]): List of YouTube channel/user URLs.
        *args: See :func:`download_channel`.
        **kwargs: See :func:`download_channel`.

    Returns:
        A list of dicts containing the video id, video title, (original) video
        duration, channel/user videos page URL from which the video was
        downloaded, and path to the downloaded MP3 file on the local machine
        (path will be ``None`` if download was unsuccessful)::

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

    videos = [video for future in futures for video in future.result()]

    num_successful_downloads = len(
        [_ for video in videos if video["path"] is not None]
    )
    logging.info(
        f"Successfully downloaded audio from {num_successful_downloads} of "
        f"{len(videos)} total videos"
    )
    return videos
