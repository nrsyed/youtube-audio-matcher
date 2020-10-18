import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
import logging
import multiprocessing
import os
import pathlib
import sys
import threading
import time

import bs4
import selenium.webdriver
import youtube_audio_matcher as yam


async def async_get_source(url, init_wait_time=1, scroll_wait_time=1):
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
        source, exclude_shorter_than=12
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

async def dl_video(video, loop, executor, dst_dir, queue):
    fpath = await loop.run_in_executor(
        executor, yam.download.download_video_mp3, video["id"], dst_dir,
        0, None, None, True, 3, False
    )
    video["path"] = fpath
    await queue.put(video)

async def dl_videos(in_queue, out_queue, loop, executor, dst_dir):
    tasks = []
    while True:
        video = await in_queue.get()
        if video is None:
            break

        task = loop.create_task(dl_video(video, loop, executor, dst_dir, out_queue))
        tasks.append(task)
    await asyncio.wait(tasks)
    #await asyncio.gather(*tasks)
    await out_queue.put(None)

def cpu_func(*args, **kwargs):
    start_t = time.time()
    x = 10
    while time.time() - start_t < 10:
        y = x * x
    return [1, 2, 3], "abcdefg"

async def fp_video(video, out_queue, loop, executor):
    func = yam.audio.fingerprint_from_file
    logging.info(f"Fingerprinting {video['id']}")
    hashes, filehash = await loop.run_in_executor(
        executor, func, video["path"]
    )
    video["fingerprint"] = hashes
    video["filehash"] = filehash
    logging.info(f"{video['id']}: {len(hashes)}")
    await out_queue.put(video)

async def fingerprint_videos(in_queue, out_queue, loop, executor):
    tasks = []
    while True:
        video = await in_queue.get()
        if video is None:
            break

        video["fingerprint"] = None
        video["filehash"] = None
        if video["path"] is not None:
            task = loop.create_task(fp_video(video, out_queue, loop, executor))
            tasks.append(task)
        else:
            await out_queue.put(video)
    await asyncio.wait(tasks)
    #await asyncio.gather(*tasks)
    await out_queue.put(None)

def main():
    urls = [
        "https://www.youtube.com/user/Bratisla991",
        #"https://www.youtube.com/channel/UC-HtuYLClaEBnxHxdaTTrmw",
    ]
    urls = [yam.download.get_videos_page_url(url) for url in urls]
    dst_dir = "/home/najam/repos/youtube-audio-matcher/testdl"

    start_t = time.time()
    loop = asyncio.get_event_loop()
    dl_queue = asyncio.Queue()
    fp_queue = asyncio.Queue()
    match_queue = asyncio.Queue()

    tpe = ThreadPoolExecutor()
    ppe = ProcessPoolExecutor()
    x = produce_videos(urls, dl_queue)
    y = dl_videos(dl_queue, fp_queue, loop, tpe, dst_dir)
    z = fingerprint_videos(fp_queue, match_queue, loop, ppe)
    loop.run_until_complete(asyncio.gather(x, y, z))

    end_t = time.time()
    print(f"{end_t - start_t}")
    tpe.shutdown()
    ppe.shutdown()
    loop.close()
    #print(dl_queue)
    #print(fp_queue)
    #print(match_queue)
    #breakpoint()

if __name__ == "__main__":
    log_format = "[%(levelname)s] %(message)s"
    log_level = logging.INFO
    logging.basicConfig(format=log_format, level=log_level)
    try:
        main()
    except Exception as e:
        print(str(e))
    finally:
        os.system("stty sane")
