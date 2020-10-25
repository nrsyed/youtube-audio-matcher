import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import functools
import json
import logging
import math
import multiprocessing
import os
import pathlib
import time

import youtube_audio_matcher as yam

# TODO: add max threads/max processes/max queue size arguments
# TODO: summary of results (successful downloads, fingerprinting, etc.)
# TODO: chunk long songs into segments and match segments in parallel

def match_fingerprints(song, db_kwargs):
    db = yam.database.Database(**db_kwargs)
    match = None
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

            song["match"] = {
                "num_matching_fingerprints": num_matching_fingerprints,
                "confidence": confidence,
                "iou": iou,
                "relative_offset": result["relative_offset"] ,
            }
        logging.info(f"Finished aligning hash matches for {song['path']}")
    del db
    return song


async def _match_song(song, loop, executor, db_kwargs):
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
    TODO
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
    inputs, add_to_database=False, conf_thresh=0.1, out_fpath=None,
    max_processes=multiprocessing.cpu_count(), **kwargs
):
    """
    Args:
        inputs (List[str]): List of input YouTube channel/user URLs and/or
            local paths to audio files or directories of audio files.
    """
    # NOTE: THIS IS ABSOLUTELY CRITICAL! Without changing mp start method to
    # spawn (from default fork), download task hangs 99 times out of 100.
    # No idea why this is.
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

    proc_pool = ProcessPoolExecutor(max_workers=max_processes)
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
    db = yam.database.Database(**db_kwargs)

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
            match = matched_song["match"]
            if match and (match["confidence"] > conf_thresh):
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
