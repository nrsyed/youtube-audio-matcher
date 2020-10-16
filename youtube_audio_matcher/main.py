import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import pathlib
import threading
import time

import bs4
import selenium.webdriver
import youtube_audio_matcher as yam


async def async_get_source(url, init_wait_time=2, scroll_wait_time=1):
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
    return source

async def async_get_metadata(url):
    source = await async_get_source(url)
    videos = yam.download.get_videos_page_metadata(
        source, exclude_longer_than=200
    )
    for video in videos:
        video["url"] = url
    return videos

async def produce_videos(urls, queue):
    for f in asyncio.as_completed([async_get_metadata(url) for url in urls]):
        videos = await f
        for video in videos:
            await queue.put(video)
    await queue.put(None)

async def dl_videos(queue):
    while True:
        video = await queue.get()
        if video is None:
            break

def main():
    """
    1. Concurrently get each page source, extract metadata based on filters.
    2. Add each video (metadata) to an async Download queue.
    3. Async fetch videos from Download queue and run (in a separate process)
       fingerprinting. Add the song's fingerprints to a Fingerprinted queue.
    4. Fetch each set of fingerprint's from the Fingerprint queue and, in the
       main process, query the DB for matching hashes.
    5. Align matches, add/write result (test whether parallelizing this helps?)
    """
    urls = [
        "https://www.youtube.com/user/Bratisla991",
        "https://www.youtube.com/channel/UC-HtuYLClaEBnxHxdaTTrmw",
    ]
    urls = [yam.download.get_videos_page_url(url) for url in urls]
    queue = asyncio.Queue()
    x = asyncio.run(produce_videos(urls, queue))
    breakpoint()

if __name__ == "__main__":
    main()
