import logging
import math
import os
import re

import bs4
import youtube_dl


def get_videos_page_url(url):
    """
    Get a valid videos page URL from a YouTube channel/user URL. See
    `Understand Your Channel URLs`_.

    Args:
        url (str): URL for a YouTube channel or user. The end of the URL may
            contain extra parameters or a subpath to a different page on the
            channel; these are stripped and the suffix "/videos" is added to
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

    .. _`Understand Your Channel URLs`:
        https://support.google.com/youtube/answer/6180214?hl=en
    """
    expr = r"^.*(/(c(hannel)?|u(ser)?)/[a-zA-Z0-9-_]+)"
    match = re.match(expr, url)

    if match:
        videos_page_path = match.groups()[0]
        return f"https://www.youtube.com{videos_page_path}/videos"
    return None


def video_metadata_from_source(
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

    Returns:
        A list of videos, where each video is represented by a dict::

            {
                "id": str,
                "title": str,
                "duration": int
            }

    .. note::
        ``exclude_longer_than`` and ``exclude_shorter_than`` may both be
        supplied to return videos meeting both criteria.
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
    ignore_existing=False, num_retries=3, quiet=False
):
    """
    Download a YouTube video as an mp3 using youtube-dl.

    Args:
        video_id (str): The video id, i.e., www.youtube.com/watch?v=<video_id>
        dst_dir (str): Path to destination directory for downloaded file.
        start_time (float): Start time (in seconds) of the portion of the
            video to extract. ``0`` (beginning of video) if omitted.
        duration (float): Duration of video (in seconds) to extract.
        end_time (float): End time (in seconds) of the portion of the video to
            extract.
        ignore_existing (bool): Skip existing files.
        num_retries (int): Number of times to re-attempt failed download. Pass
            ``num_retries=None`` to retry indefinitely.
        quiet (bool): Suppress youtube_dl/ffmpeg terminal output.

    Returns:
        Path (str) to output file if download successful, else None.

    .. note::
        ``duration`` takes precedence over ``end_time`` (as defined in
        `ffmpeg usage`_) if both are provided. If both ``duration`` and
        ``end_time`` are omitted, the whole video is extracted (beginning
        at ``start_time``).

    .. _`ffmpeg usage`:
        https://ffmpeg.org/ffmpeg.html#Main-options
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
    if ignore_existing and os.path.exists(dst_path):
        logging.info(
            f"[{video_id}] Skipping video. File {dst_path} already exists."
        )
    else:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        if num_retries is None:
            num_retries = math.inf

        tries = 0
        download_successful = False
        while not download_successful and tries <= num_retries:
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
            except youtube_dl.utils.DownloadError:
                log_msg = f"[{video_id}] Error downloading video."
                log_msg += f" (attempt {tries + 1} of {num_retries + 1})."
                if tries < num_retries:
                    log_msg += " Retrying download."
                    logging.info(log_msg)
                else:
                    log_msg += " Max attempts reached."
                    logging.error(log_msg)
                    logging.error(str(e))
                    return None
            else:
                logging.info(
                    f"[{video_id}] Successfully downloaded {dst_path}"
                )
                download_successful = True
            finally:
                tries += 1
    return dst_path
