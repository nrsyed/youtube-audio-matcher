import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import functools
import logging
import multiprocessing
import os

import youtube_audio_matcher as yam


async def _fingerprint_audio(video, loop, executor, out_queue=None, **kwargs):
    """
    Helper function for :func:`fingerprint_audio`. Fingerprints an audio file,
    adds the fingerprints (as a list) and file MD5 hash to the video metadata
    dict, and adds it to an output queue (if provided).

    Args:
        video (dict): Dict corresponding to a video. Must contain a ``path``
            key containing the path to the downloaded audio file (or ``None``)
            if the download wasn't successful and the file doesn't exist.
        loop (asyncio.BaseEventLoop): `asyncio` EventLoop.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor in which the audio file
            will be processed.
        out_queue (asyncio.queues.Queue): Output queue to which video metadata
            will be pushed.
        kwargs: Keyword arguments for
            :func:`youtube_audio_matcher.audio.fingerprint_from_file`.

    Returns:
        dict: video
            Dict representing metadata for the fingerprinted video.
    """
    video["filehash"] = None
    video["fingerprint"] = None

    if video["path"]:
        # Create function partial with keyword args for fingerprint_from_file
        # because loop.run_in_executor only takes function *args, not **kwargs.
        fingerprint_from_file_partial = functools.partial(
            yam.audio.fingerprint_from_file, video["path"], **kwargs
        )

        hashes, filehash = await loop.run_in_executor(
            executor, fingerprint_from_file_partial
        )
        video["fingerprint"] = hashes
        video["filehash"] = filehash

    if out_queue:
        await out_queue.put(video)
    return video


async def fingerprint_videos(loop, executor, in_queue, out_queue=None):
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
    await out_queue.put(None)

def main():
    urls = [
        "https://www.youtube.com/user/Bratisla991",
        #"https://www.youtube.com/channel/UC-HtuYLClaEBnxHxdaTTrmw",
    ]
    urls = [yam.download.get_videos_page_url(url) for url in urls]
    dst_dir = "/home/najam/repos/youtube-audio-matcher/testdl"

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
