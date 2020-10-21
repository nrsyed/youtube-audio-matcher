import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import functools
import logging
import multiprocessing
import os
import pathlib

import youtube_audio_matcher as yam


def main(inputs, **kwargs):
    """
    Args:
        inputs (List[str]): List of input YouTube channel/user URLs and/or
            local paths to audio files or directories of audio files.
    """
    urls = []
    files = []

    for inp in inputs:
        # Check if the input refers to a local file or directory.
        inp_as_local_path = os.path.abspath(os.path.expanduser(inp))
        if os.path.exists(inp_as_local_path):
            if os.path.isdir(inp_as_local_path):
                files.extend(os.listdir(inp_as_local_path))
            else:
                files.append(inp_as_local_path)
        else:
            # Assume the input is a YouTube URL.
            urls.append(inp)

    proc_pool = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())
    thread_pool = ThreadPoolExecutor()

    loop = asyncio.get_event_loop()

    # Queue to which files to be fingerprinted are added. Each file will be
    # processed by the ProcessPoolExecutor.
    fingerprint_queue = asyncio.Queue()

    # Add local files, if any, to fingerprint queue.
    for file_ in files:
        fingerprint_queue.put_nowait(
            {
                "id": None,
                "title": None,
                "duration": None,
                "channel_url": None,
                "path": file_,
            }
        )

    # Queue to which files will be added after fingerprinting to compare the
    # fingerprint to the database to determine if there are any matches.
    match_queue = asyncio.Queue()

    # Keyword args for all download-related functions/tasks.
    download_keys = [
        "dst_dir", "start_time", "duration", "end_time", "ignore_existing",
        "num_retries", "youtubedl_verbose", "page_load_wait", "scroll_by",
        "exclude_longer_than", "exclude_shorter_than",
    ]
    download_kwargs = {
        k: v for k, v in kwargs.items() if k in download_keys
    }

    # Tasks for the async pipeline: 1) task for getting video metadata from
    # YouTube channels and 2) task for downloading videos.
    get_videos_task, download_task = yam.download.download_channels(
        loop, urls, executor=thread_pool,
        out_queue=fingerprint_queue, **download_kwargs
    )

    # Keyword args for fingerprint-related functions/task.
    fingerprint_keys = [
        "win_size", "win_overlap_ratio", "spectrogram_backend",
        "filter_connectivity", "filter_dilation", "erosion_iterations",
        "min_amplitude",  "fanout", "min_time_delta", "max_time_delta",
        "hash_length", "time_bin_size", "freq_bin_size",
    ]
    fingerprint_kwargs = {
        k: v for k, v in kwargs.items() if k in fingerprint_keys
    }

    # Tasks for the async pipeline: 3) task for fingerprinting files.
    fingerprint_task = yam.audio.fingerprint_songs(
        loop=loop, executor=proc_pool, in_queue=fingerprint_queue,
        out_queue=match_queue, **fingerprint_kwargs
    )

    task_group = asyncio.gather(
        get_videos_task, download_task, fingerprint_task
    )
    loop.run_until_complete(task_group)
