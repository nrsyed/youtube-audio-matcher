import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
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

async def dl_videos(in_queue, out_queue, loop, executor, dst_dir):
    while True:
        video = await in_queue.get()
        if video is None:
            await in_queue.put(None)
        fpath = await loop.run_in_executor(
            executor, yam.download.download_video_mp3,
            video["id"], dst_dir, 0, None, None, False, True
        )
        if fpath is not None:
            await out_queue.put(fpath)
    await out_queue.put(None)


async def fingerprint_videos(queue, loop, executor):
    while True:
        fpath = await queue.get()
        fingerprint = await loop.run_in_executor()

def main():
    """
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
    dst_dir = "/home/najam/repos/youtube-audio-matcher/testdl"

    start_t = time.time()
    loop = asyncio.get_event_loop()
    dl_queue = asyncio.Queue()
    fp_queue = asyncio.Queue()

    tpe = ThreadPoolExecutor()
    ppe = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())
    y = produce_videos(urls, dl_queue)
    z = dl_videos(dl_queue, fp_queue, loop, tpe, dst_dir)
    loop.run_until_complete(asyncio.gather(y, z))
    end_t = time.time()
    print(f"{end_t - start_t}")
    #loop.close()

if __name__ == "__main__":
    main()
