import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import json
import logging
import multiprocessing
import os
import time

import youtube_audio_matcher as yam

# TODO: add max threads/max processes/max queue size arguments
# TODO: summary of results (successful downloads, fingerprinting, etc.)
# TODO: chunk long songs into segments and match segments in parallel
# TODO: add duration (and actual file duration instead of YT duration) when
#   adding songs to DB.


def match_fingerprints(song, db_kwargs):
    """
    Opens a database connection and matches a song against the database.

    Args:
        song (dict): Dict corresponding to a fingerprinted song. Must contain
            a ``fingerprints`` key containing a list of fingerprints
            (hash/offset pairs) returned by
            :func:`youtube_audio_matcher.audio.fingerprint_from_file`.
        db_kwargs (dict): Keyword arguments for instantiating a
            :class:`youtube_audio_matcher.database.Database` class instance.

    Returns:
        dict: song
            Returns the input dict. If a match was found in the database,
            a ``matching_song`` key (containing the song dict for the matching
            song from the database) and a ``match_stats`` key (containing
            metrics/statistics related to the match) are added to the dict.
            The ``fingerprints`` key is deleted. The resulting dict has the
            following structure::

                {
                    "channel_url": str,
                    "duration": float,
                    "filehash": str,
                    "num_fingerprints": int,
                    "path": str,
                    "title": str,
                    "youtube_id": str,
                    "matching_song": {
                        "id": int,
                        "duration": float,
                        "filehash": str,
                        "filepath": str,
                        "title": str,
                        "youtube_id": str,
                        "num_fingerprints": int
                    },
                    "match_stats": {
                        "num_matching_fingerprints": int,
                        "confidence": float,
                        "iou": float,
                        "relative_offset": float
                    }
                }
    """
    db = yam.database.Database(**db_kwargs)
    song["num_fingerprints"] = len(song["fingerprints"])

    # List of hashes (for the database query) and a list of dicts
    # containing the hash and offset (to align matches).
    hashes = []
    fingerprints = []

    for hash_, offset in song["fingerprints"]:
        hashes.append(hash_)
        fingerprints.append({"hash": hash_, "offset": offset})

    # Free up some memory
    del song["fingerprints"]

    unique_hashes = list(set(hashes))
    db_matches = db.query_fingerprints(unique_hashes)

    if db_matches:
        # Filter out all input hashes that don't have a database match.
        matching_hashes = set(fp["hash"] for fp in db_matches)
        fingerprints = [
            fp for fp in fingerprints if fp["hash"] in matching_hashes
        ]

        logging.info(f"Aligning hash matches for {song['path']}")
        result = yam.audio.align_matches(fingerprints, db_matches)
        if result is not None:
            # Query the database for the matching song.
            match_song = db.query_songs(
                id_=result["song_id"], include_fingerprints=True
            )[0]
            del match_song["fingerprints"]
            song["matching_song"] = match_song

            num_matching_fingerprints = result["num_matching_fingerprints"]

            # Compute confidence as number of matching hashes divided by
            # number of song hashes.
            confidence = num_matching_fingerprints / song["num_fingerprints"]

            # Compute IOU as another metric.
            inter = num_matching_fingerprints
            union = (
                (song["num_fingerprints"] + match_song["num_fingerprints"])
                - num_matching_fingerprints
            )
            iou = inter / union

            song["match_stats"] = {
                "num_matching_fingerprints": num_matching_fingerprints,
                "confidence": confidence,
                "iou": iou,
                "relative_offset": result["relative_offset"],
            }
        logging.info(f"Finished aligning hash matches for {song['path']}")
    del db
    return song


async def _match_song(song, loop, executor, db_kwargs):
    """
    Helper function for :func:`match_songs`.
    """
    start_t = time.time()
    logging.info(f"Matching fingerprints for {song['path']}")
    matched_song = await loop.run_in_executor(
        executor, match_fingerprints, song, db_kwargs
    )
    elapsed = time.time() - start_t
    logging.info(
        f"Finished matching fingerprints for {matched_song['path']} "
        f"in {elapsed:.2f} s"
    )
    return matched_song


# TODO: Rename wrapper functions, helper functions, core algo functions?
async def match_songs(loop, executor, db_kwargs, in_queue):
    """
    Coroutine that consumes songs from a queue and matches them against
    the database.

    Args:
        loop (asyncio.BaseEventLoop): asyncio EventLoop.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor.
        db_kwargs (dict): Keyword arguments for instantiating a
            :class:`youtube_audio_matcher.database.Database` class instance.
        in_queue (asyncio.queues.Queue): Download queue from which song
            data is fetched for each song to be matched.

    Returns:
        List[dict]: results
            A list of dicts where each dict represents an input song and
            database match information returned by :func:`match_fingerprints`.
    """
    tasks = []
    while True:
        song = await in_queue.get()
        if song is None:
            break

        task = loop.create_task(_match_song(song, loop, executor, db_kwargs))
        tasks.append(task)

    # Wrap asyncio.wait() in if statement to avoid error if no tasks.
    if tasks:
        await asyncio.wait(tasks)

    return [task.result() for task in tasks]


def main(
    inputs, add_to_database=False, conf_thresh=0.01, out_fpath=None,
    max_processes=None, max_threads=None, **kwargs
):
    """
    Fingerprint local files and/or the audio from videos on any number of
    YouTube channels, and either add the songs to a database or match them
    against existing songs in the database.

    Args:
        inputs (List[str]): List of input YouTube channel/user URLs and/or
            local paths to audio files or directories of audio files.
        add_to_database (bool): If ``True``, input songs (and their
            fingerprints to database after fingerprinting. If ``False``, match
            songs against database after fingerprinting.
        conf_thresh (float): Match confidence threshold in the range [0, 1].
            Matches with a confidence <= ``conf_thresh`` are not returned.
            Match confidence for a song is computed as the number of matching
            fingerprints divided by the total number of fingerprints (belonging
            to the input song).
        out_fpath (str): Path to output file where matches will be written
            as JSON.
        max_processes (int): Maximum number of cores to utilize for parallel
            processing. Defaults to all available CPUs.
        max_threads (int): Maximum number of threads to spawn for concurrent
            tasks and downloads. Defaults to the maximum defined in
            `concurrent.futures.ThreadPoolExecutor`_.
        **kwargs: Any keyword arguments for
            :class:`youtube_audio_matcher.database.Database`,
            :func:`youtube_audio_matcher.download.download_channels`,
            and :func:`youtube_audio_matcher.audio.fingerprint_songs`.

    Returns:
        List[dict]|None: matches
            If ``add_to_database=True``, a list of dicts returned by
            :func:`match_fingerprints`, where each dict corresponds to a song
            with a match in the database. If ``add_to_database=False``,
            ``None``.

    .. _`concurrent.futures.ThreadPoolExecutor`:
        https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
    """
    # NOTE: THIS IS ABSOLUTELY CRITICAL! Without changing mp start method to
    # spawn (from default fork), download task deadlocks/hangs. Reason unclear.
    multiprocessing.set_start_method("spawn")

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

    if not max_processes:
        max_processes = multiprocessing.cpu_count()

    proc_pool = ProcessPoolExecutor(max_workers=max_processes)
    thread_pool = ThreadPoolExecutor(max_workers=max_threads)

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

    # Add local files, if any, to fingerprint queue.
    for file_ in files:
        fingerprint_queue.put_nowait(
            {
                "youtube_id": None,
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
        "min_amplitude", "fanout", "min_time_delta", "max_time_delta",
        "hash_length", "time_bin_size", "freq_bin_size", "delete",
    ]
    fingerprint_kwargs = {
        k: v for k, v in kwargs.items() if k in fingerprint_keys
    }

    # Add fingerprint task to the task list.
    fingerprint_task = yam.audio.fingerprint_songs(
        loop=loop, executor=proc_pool, in_queue=fingerprint_queue,
        out_queue=db_queue, **fingerprint_kwargs
    )
    tasks.append(fingerprint_task)

    if add_to_database:
        update_db_task = yam.database.update_database(
            loop, proc_pool, db_kwargs, in_queue=db_queue
        )
        tasks.append(update_db_task)
    else:
        match_task = match_songs(
            loop, proc_pool, db_kwargs, in_queue=db_queue
        )
        tasks.append(match_task)

    task_group = asyncio.gather(*tasks)
    loop.run_until_complete(task_group)

    if not add_to_database:
        matches = []
        for matched_song in task_group.result()[-1]:
            if (
                "match_stats" in matched_song
                and matched_song["match_stats"]["confidence"] > conf_thresh
            ):
                matches.append(matched_song)

        if out_fpath:
            with open(out_fpath, "w") as f:
                json.dump(matches, f, indent=2),
            logging.info(f"Matches written to {out_fpath}")
        elif matches:
            # If no output file specified, print matches.
            for i, matched_song in enumerate(matches, start=1):
                json_match = json.dumps(matched_song, indent=4)
                logging.info(f"Match {i}:\n" + json_match + "\n")
        else:
            logging.info("No matches found")
        return matches
