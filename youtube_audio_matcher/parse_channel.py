from concurrent.futures import ThreadPoolExecutor
import math
import os
import re
import time
import pdb

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


def get_source(url, init_wait_time=2, scroll_wait_time=0.5):
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
    return source


def get_videos_page_metadata(source, max_duration=None, min_duration=None):
    """
    Given the page source for a channel/user Videos page, extract video id,
    video title, and video duration (in seconds) for each video.

    Args:
        source (str): Page source.
        max_duration (int): Only return metadata for videos shorter than the
            given duration (in seconds). If None, all videos are returned.
        min_duration (int): Only return metadata for videos longer than the
            given duration (in seconds). If None, all videos are returned.

        `max_duration` and `min_duration` may both be supplied to return videos
        meeting both criteria.

    Returns:
        A list of videos, where each video is represented by a dict:
        {
            "id": str,
            "title": str,
            "duration": int
        }
    """
    if max_duration is None:
        max_duration = math.inf
    if min_duration is None:
        min_duration = 0

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
    video_id, dst_dir, start_time=None, duration=None, end_time=None
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
    }

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except youtube_dl.utils.DownloadError as e:
        # TODO: log error
        return None
    else:
        return os.path.join(dst_dir, f"{video_id}.mp3")


def download_video_mp3s(
    video_ids, dst_dir, start_time=None, duration=None, end_time=None,
    max_workers=None
):
    """
    Threaded wrapper for download_video_mp3 to download/convert multiple videos
    concurrently. This function exists because, although
    youtube_dl.YoutubeDL.download() accepts a list of video URLs, it is not
    multithreaded and downloads each video sequentially.

    Args:
        video_ids (List[str]): A list of YouTube video ids to download.
        dst_dir (str): Path to destination directory for downloaded files.
        start_time (int): See `download_video_mp3`.
        duration (int): See `download_video_mp3`.
        end_time (int): See `download_video_mp3`.
        max_workers (int): Max threads to spawn.

        `start_time`, `duration`, and `end_time` (if specified) are applied
        to all videos.

    Returns:
        A list of paths (one per video) returned by `download_video_mp3`.
    """
    thread_pool = ThreadPoolExecutor(max_workers=max_workers)
    futures = []

    for video_id in video_ids:
        futures.append(
            thread_pool.submit(
                download_video_mp3, video_id, dst_dir, start_time=start_time,
                duration=duration, end_time=end_time
            )
        )
        # TODO: add sleep between option
    thread_pool.shutdown()

    # Get paths to output files returned by calls to download_video_mp3().
    paths = [future.result() for future in futures]
    return paths


def download_channel(
    url, dst_dir, num_retries=3, exclude_longer_than=None, exclude_shorter_than=None,
    start_time=None, duration=None, end_time=None
):
    """
    TODO
    """
    videos_page_url = get_videos_page_url(url)
    videos_page_source = get_source(videos_page_url)

    # Get metadata for each video in the Videos page.
    metadata = get_videos_page_metadata(
        videos_page_source, max_duration=exclude_longer_than,
        min_duration=exclude_shorter_than
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
        video_ids = [metadata[idx]["id"] for idx in idxs_to_download]
        dst_paths = download_video_mp3s(
            video_ids, dst_dir, start_time=start_time,
            duration=duration, end_time=end_time
        )

        updated_idxs_to_download = []
        for j, path in enumerate(dst_paths):
            idx = idxs_to_download[j]
            if path is None:
                # File was not downloaded correctly. Re-add its index in
                # `metadata` to the list of indexes to be downloaded.
                updated_idxs_to_download.append(idx)
            else:
                metadata[idx]["path"] = path

        idxs_to_download = updated_idxs_to_download
        tries += 1

    return metadata


def download_channels(urls, *args, **kwargs):
    """
    Threaded wrapper for `download_channel()`.
    """
    thread_pool = ThreadPoolExecutor()
    futures = []
    for url in urls:
        futures.append(
            thread_pool.submit(download_channel, url, *args, **kwargs)
        )
    thread_pool.shutdown()

    metadata = [video for future in futures for video in future.result()]
    return metadata


if __name__ == "__main__":
    urls = [
        "https://www.youtube.com/channel/UCmSynKP6bHIlBqzBDpCeQPA/featured",
        #"www.youtube.com/c/GlitchxCity/featured",
        #"https://www.youtube.com/c/creatoracademy/",
        #"https://www.youtube.com/user/CAVEMAN2019/morestuff",
        #"https://www.youtube.com/u/dummy/okiedokie",
    ]

    dst_dir = "/home/najam/repos/youtube-audio-matcher/test_download"
    x = download_channels(urls, dst_dir, exclude_longer_than=140)
    breakpoint()
