import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools
import logging

import selenium.webdriver

from .common import (
    download_video_mp3, get_videos_page_url, video_metadata_from_page_source
)


async def async_get_source(url, init_wait_time=1, scroll_wait_time=1):
    try:
        driver = selenium.webdriver.Chrome()
        driver.get(url)
        await asyncio.sleep(init_wait_time)

        source = None
        scroll_by = 5000
        while source != driver.page_source:
            source = driver.page_source
            driver.execute_script(f"window.scrollBy(0, {scroll_by});")
            await asyncio.sleep(scroll_wait_time)
        driver.quit()
    except Exception as e:
        logging.error(f"Error getting page source for URL {url}")
        raise e
    finally:
        return source


async def async_video_metadata_from_urls(
    urls, download_queue, init_wait_time=1, scroll_wait_time=1,
    exclude_longer_than=None, exclude_shorter_than=None
):
    """
    TODO
    """
    tasks = [async_get_source(url, init_wait_time, scroll_wait_time) for url in urls]
    for url, task in zip(urls, asyncio.as_completed(tasks)):
        source = await task
        videos = video_metadata_from_page_source(
            source, exclude_longer_than=exclude_longer_than,
            exclude_shorter_than=exclude_shorter_than
        )
        for video in videos:
            video["url"] = url
            await download_queue.put(video)
    await download_queue.put(None)


async def _async_download_video_mp3(
    video, dst_dir, loop, executor, out_queue=None, **kwargs
):
    """
    async wrapper for :func:`download_video_mp3` and helper function for
    :func:`async_download_video_mp3s`.
    """
    download_func_partial = functools.partial(
        download_video_mp3, video["id"], dst_dir, **kwargs
    )
    fpath = await loop.run_in_executor(executor, download_func_partial)
    video["fpath"] = fpath
    if out_queue:
        await out_queue.put(video)


async def async_download_video_mp3s(
    dst_dir, loop, executor, in_queue, out_queue=None, **kwargs
):
    """
    Args:
        kwargs: Keyword arguments for :func:`download_video_mp3`.
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


def async_download_channels(
    urls, dst_dir, loop=None, executor=None, out_queue=None,
    video_metadata_from_urls_kwargs=None, download_video_mp3_kwargs=None
):
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

    loop.run_until_complete(asyncio.gather(get_videos_task, download_task))
