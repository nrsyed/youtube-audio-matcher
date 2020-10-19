import asyncio
from concurrent.futures import ProcessPoolExecutor
import functools
import logging
import multiprocessing
import os

import youtube_audio_matcher as yam


async def _fingerprint_song(song, loop, executor, out_queue=None, **kwargs):
    """
    Helper function for :func:`fingerprint_songs`. Fingerprints an audio file,
    adds the fingerprints (as a list) and file SHA1 hash to the audio file
    metadata dict, and adds it to an output queue (if provided).

    Args:
        song (dict): Dict corresponding to an audio file. Must contain a
            ``path`` key containing the path to the downloaded audio file
            (or ``None``) if the download wasn't successful and the file
            doesn't exist.
        loop (asyncio.BaseEventLoop): `asyncio` EventLoop.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor in which the audio file
            will be processed.
        out_queue (asyncio.queues.Queue): Output queue to which video metadata
            will be pushed.
        kwargs: Keyword arguments for
            :func:`youtube_audio_matcher.audio.fingerprint_from_file`.

    Returns:
        dict: song
            Dict representing metadata for the fingerprinted audio file.
    """
    song["filehash"] = None
    song["fingerprint"] = None

    if song["path"]:
        # Create function partial with keyword args for fingerprint_from_file
        # because loop.run_in_executor only takes function *args, not **kwargs.
        fingerprint_from_file_partial = functools.partial(
            yam.audio.fingerprint_from_file, song["path"], **kwargs
        )

        hashes, filehash = await loop.run_in_executor(
            executor, fingerprint_from_file_partial
        )
        song["fingerprint"] = hashes
        song["filehash"] = filehash

    if out_queue:
        await out_queue.put(song)
    return song


async def fingerprint_songs(
    loop, executor, in_queue, out_queue=None, **kwargs
):
    """
    Args:
        loop (asyncio.BaseEventLoop): `asyncio` EventLoop.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor in which the audio file
            will be processed.
        in_queue (asyncio.queues.Queue): Process queue from which audio
            metadata is fetched for each song to be processed.
        out_queue (asyncio.queues.Queue): Output queue to which audio metadata
            will be pushed.
        kwargs: Keyword arguments for
            :func:`youtube_audio_matcher.audio.fingerprint_from_file`.

    Returns:
        dict: song
            Dict representing metadata for the fingerprinted audio file.
    """
    tasks = []
    while True:
        song = await in_queue.get()
        if song is None:
            break

        task = loop.create_task(
            _fingerprint_song(
                song, loop, executor, out_queue=out_queue, **kwargs
            )
        )
        tasks.append(task)
    await asyncio.wait(tasks)

    if out_queue is not None:
        out_queue.put(None)

    return [task.result() for task in tasks]


def main():
    raise NotImplementedError

if __name__ == "__main__":
    log_format = "[%(levelname)s] %(message)s"
    log_level = logging.INFO
    logging.basicConfig(format=log_format, level=log_level)
    try:
        main()
    except Exception as e:
        raise e
    finally:
        os.system("stty sane")
