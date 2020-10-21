import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import functools
import logging
import multiprocessing
import os
import pathlib

import youtube_audio_matcher as yam


# TODO: delete after download
def main(inputs, add_to_database=False, **kwargs):
    """
    Args:
        inputs (List[str]): List of input YouTube channel/user URLs and/or
            local paths to audio files or directories of audio files.
    """
    # Setup and input parsing.
    urls = []
    files = []

    for inp in inputs:
        # Check if the input refers to a local file or directory.
        inp_as_local_path = os.path.abspath(os.path.expanduser(inp))
        if os.path.exists(inp_as_local_path):
            if os.path.isdir(inp_as_local_path):
                dirpath = inp_as_local_path
                for fname in os.listdir(dirpath):
                    files.append(os.path.join(dirpath, fname))
            else:
                files.append(inp_as_local_path)
        else:
            # Assume the input is a YouTube URL.
            logging.debug(
                f"{inp} path not found on local machine. Treating as URL"
            )
            urls.append(inp)

    proc_pool = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())
    thread_pool = ThreadPoolExecutor()

    loop = asyncio.get_event_loop()

    # Queue to which files to be fingerprinted are added. Each file will be
    # processed by the ProcessPoolExecutor.
    fingerprint_queue = asyncio.Queue()

    # Queue to which files will be added after fingerprinting to add
    # file/fingerprints to database (if add_to_database=True) or to compare
    # file/fingerprints to database and search for matches
    # (if add_to_database=False).
    db_queue = asyncio.Queue()

    # List of all async tasks to run.
    tasks = []

    # Keyword args for database and database functions/tasks.
    db_keys = [
        "db_name", "dialect", "driver", "host", "password", "port", "user"
    ]
    db_kwargs = {k: v for k, v in kwargs.items() if k in db_keys}
    #db = yam.database.Database(**db_kwargs)
    #db.delete_all()
    #db = None

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

    # TODO: validate YouTube URLs here instead of in the download function?

    # If only local files and no URLs, add None to end of fingerprint queue.
    # This internally signifies to the async functions that no more items will
    # be added to the queue (else, async functions wait forever and hang).
    if files and not urls:
        fingerprint_queue.put_nowait(None)

    # TODO: what happens if both files and urls but none of the URLs are valid?

    # Only add download-related tasks to the task list if URLs were provided.
    # TODO: error-handling for invalid URLs
    if urls:
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
        tasks.extend([get_videos_task, download_task])

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

    # Add fingerprint task to the task list.
    #proc_pool = thread_pool
    fingerprint_task = yam.audio.fingerprint_songs(
        loop=loop, executor=proc_pool, in_queue=fingerprint_queue,
        out_queue=db_queue, **fingerprint_kwargs
    )
    tasks.append(fingerprint_task)

    # TODO
    if add_to_database:
        update_db_task = yam.database.update_database(db, in_queue=db_queue)
        tasks.append(update_db_task)
    else:
        # match task
        pass

    task_group = asyncio.gather(*tasks)
    loop.run_until_complete(task_group)
