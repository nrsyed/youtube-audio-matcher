import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools
import logging

import selenium.webdriver

from .common import (
    download_video_mp3, get_videos_page_url, video_metadata_from_source
)


async def async_get_source(url, page_load_wait=1, scroll_by=5000):
    """
    Async version of :func:`get_source <download.get_source>`.
    """
    try:
        driver = selenium.webdriver.Chrome()
        driver.get(url)
        await asyncio.sleep(page_load_wait)

        source = None
        while source != driver.page_source:
            source = driver.page_source
            driver.execute_script(f"window.scrollBy(0, {scroll_by});")
            await asyncio.sleep(page_load_wait)
        driver.quit()
    except Exception as e:
        logging.error(f"Error getting page source for URL {url}")
        raise e
    finally:
        return source


async def async_video_metadata_from_urls(
    urls, download_queue, get_source_kwargs=None,
    video_metadata_from_source_kwargs=None
):
    """
    Asychronously get information on each video from the YouTube channels
    corresponding to the given YouTube URLs. This function acts as the producer
    of a producer-consumer relationship with :func:`async_download_video_mp3s`.

    Args:
        urls (List[str]): List of YouTube users/channels.
        download_queue (asyncio.queues.Queue): Queue to which video metadata
            for each video is added for download.
        get_source_kwargs (dict): Dict of keyword args for
            :func:`async_get_source`.
        video_metadata_from_source_kwargs (dict): Dict of keyword args for
            :func:`video_metadata_from_source <download.video_metadata_from_source>`

    Returns:
        List[dict]: videos
            List of dicts of video metadata, where each dict represents a
            video processed by this coroutine.
    """
    # All videos produced by this coroutine (returned after completion).
    all_videos = []

    tasks = [
        async_get_source(url, **get_source_kwargs) for url in urls
    ]
    for url, task in zip(urls, asyncio.as_completed(tasks)):
        source = await task
        videos = video_metadata_from_source(
            source, **video_metadata_from_source_kwargs
        )
        for video in videos:
            video["url"] = url
            all_videos.append(video)
            await download_queue.put(video)
    await download_queue.put(None)
    return all_videos


async def _async_download_video_mp3(
    video, dst_dir, loop, executor, out_queue=None, **kwargs
):
    """
    Async wrapper for :func:`download_video_mp3 <download.download_video_mp3>`
    and helper function for :func:`async_download_video_mp3s`. Downloads a
    single video as an mp3, appends the filepath of the downloaded file to the
    video metadata dict, and adds it to a queue (if provided).

    Args:
        kwargs: Keyword arguments for
            :func:`download_video_mp3 <download.download_video_mp3>`.

    Returns:
        dict: video
            Dict representing metadata for the downloaded video.
    """
    # Create function partial with keyword args for download_video_mp3
    # because loop.run_in_executor only takes *args for the function, not
    # **kwargs.
    download_video_mp3_partial = functools.partial(
        download_video_mp3, video["id"], dst_dir, **kwargs
    )
    fpath = await loop.run_in_executor(executor, download_video_mp3_partial)

    # Add filepath of downloaded file to video metadata dict.
    video["fpath"] = fpath

    if out_queue:
        await out_queue.put(video)
    return video


async def async_download_video_mp3s(
    dst_dir, loop, executor, in_queue, out_queue=None, **kwargs
):
    """
    Asynchronously download videos from a queue as they are received. This
    functions acts as the consumer of a producer-consumer relationship with
    :func:`async_video_metadata_from_urls`. A ``path`` key is added to the
    each video metadata dict from the download (input) queue, whose value is
    the filepath of the downloaded file (or ``None`` if the download was
    unsuccessful).

    Args:
        dst_dir (str): Download destination directory.
        loop (asyncio.BaseEventLoop): `asyncio` EventLoop (e.g., as returned by
            ``asyncio.get_event_loop()``.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor in which each download
            will be run.
        in_queue (asyncio.queues.Queue): Download queue from which video
            metadata is fetched for each video to be downloaded.
        out_queue (asyncio.queues.Queue): Output queue to which video metadata
            will be pushed after download attempt. This can be used as a
            process queue for asynchronously post-processing each video after
            it has been downloaded.
        kwargs: Keyword arguments for
            :func:`download_video_mp3 <download.download_video_mp3>`.

    Returns:
        List(dict): videos
            List of dicts of video metadata, where each dict represents a
            video processed by this coroutine.
    """
    tasks = []
    while True:
        video = await in_queue.get()
        if video is None:
            break

        task = loop.create_task(
            _async_download_video_mp3(
                video, dst_dir, loop, executor, out_queue=out_queue, **kwargs
            )
        )
        tasks.append(task)
    await asyncio.wait(tasks)

    if out_queue is not None:
        out_queue.put(None)

    return [task.result() for task in tasks]


def async_download_channels(
    urls, dst_dir, loop=None, executor=None, out_queue=None,
    video_metadata_from_urls_kwargs=None, download_video_mp3_kwargs=None
):
    """
    Async version of :func:`download_channels <download.download_channels>`.

    Args:
        urls (List[str]): List of YouTube channel/user URLs.
        dst_dir (str): Download destination directory.
        loop (asyncio.BaseEventLoop): `asyncio` EventLoop (e.g., as returned by
            ``asyncio.get_event_loop()``.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor in which each download
            will be run.
        out_queue (asyncio.queues.Queue): Output queue to which video metadata
            will be pushed after download attempt. This can be used as a
            process queue for asynchronously post-processing each video after
            it has been downloaded.
        video_metadata_from_urls_kwargs (dict): Keyword args for
            :func:`async_video_data_from_urls`.
        download_video_mp3_kwargs (dict): Keyword args for
            :func:`download_video_mp3 <download.download_video_mp3>`.

    Returns:
        List(dict): videos
            List of dicts of video metadata, where each dict represents a
            downloaded video.
    """
    urls = [get_videos_page_url(url) for url in urls]

    if loop is None:
        loop = asyncio.get_event_loop()
    if executor is None:
        executor = ThreadPoolExecutor()

    if video_metadata_from_urls_kwargs is None:
        video_metadata_from_urls_kwargs = dict()
    if download_video_mp3_kwargs is None:
        download_video_mp3_kwargs = dict()

    download_queue = asyncio.Queue()

    get_videos_task = async_video_metadata_from_urls(
        urls, download_queue, **video_metadata_from_urls_kwargs
    )

    download_task = async_download_video_mp3s(
        dst_dir, loop, executor, download_queue, out_queue=out_queue,
        **download_video_mp3_kwargs
    )

    task_group = asyncio.gather(get_videos_task, download_task)
    loop.run_until_complete(task_group)

    videos = task_group.result()[1]
    return videos
