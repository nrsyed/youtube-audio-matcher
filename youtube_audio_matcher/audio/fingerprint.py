import asyncio
import collections
import copy
import functools
import hashlib
import logging
import os

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage
import scipy.signal

from . import util

# TODO: get duration on file read


def align_matches(song_fingerprints, db_fingerprints, offset_bin_size=0.2):
    """
    Args:
        song_fingerprints (List[dict]): List of fingerprints for the song to
            be matched, where each fingerprint is a dict containing the hash
            and the time offset in seconds::

                {
                    "hash": str,
                    "offset": float
                }
        db_fingerprints (List[dict]): List of fingerprints from the database
            with matching hashes, where each fingerprint is a dict containing
            the database song id, hash, and offset::
                
                {
                    "song_id": int,
                    "hash": str,
                    "offset": float
                }
        offset_bin_size (float): Size of offset bin in seconds;
            each offset is divided by this value and converted to an
            integer to prevent floating point errors and inaccuracies from
            affecting the results.

    Returns:
        result: dict|None
            Dict containing song id, number of matching fingerprints, and
            offset of the input song relative to the matched song from the
            database if a match was found, else returns ``None``::

                {
                    "song_id": int,
                    "num_matching_fingerprints": int,
                    "relative_offset": float
                }

    .. note::
        ``db_fingerprints`` and ``song_fingerprints`` are assumed to be
        `matches`, i.e., both lists should contain the same set of hashes;
        fingerprints with non-matching hashes should be filtered out before
        being passed to this function.
    """
    # Map input song hashes to a list of offsets for each hash.
    inp_hash_to_offsets = collections.defaultdict(list)
    for fp in song_fingerprints:
        offset =  int(fp["offset"] / offset_bin_size)
        inp_hash_to_offsets[fp["hash"]].append(offset)

    # Do the same as above but for each song in the database that's a potential
    # match (ie, map each song id to its hashes; map each hash to a list of
    # offsets of that hash). Result is a dict of dict of lists.
    db_song_to_hashes_offsets = dict()
    for fp in db_fingerprints:
        song_id = fp["song_id"]
        hash_ = fp["hash"]
        offset = int(fp["offset"] / offset_bin_size)

        if song_id not in db_song_to_hashes_offsets:
            db_song_to_hashes_offsets[song_id] = collections.defaultdict(list)
        db_song_to_hashes_offsets[song_id][hash_].append(offset)

    # For each database song (song id), construct a list of relative offsets.
    db_song_to_rel_offsets = collections.defaultdict(list)

    # In the event of hash collisions (multiple offsets for an input song hash
    # and/or multiple offsets for a database song hash), we compute a relative
    # offset for all offset pair combinations. Example for a hash "abcdefg"
    # and a database song id 1:
    #
    # hash = "abcdefg"
    # inp_hash_to_offsets[hash] = [0, 3, 12]
    # db_song_to_hashes_offsets[1][hash] = [1, 4]
    # 
    # We compute a relative offset for offset pairs (0, 1), (0, 4), (3, 1),
    # (3, 4), (12, 1), (12, 4), i.e., we end up with
    # len(inp_hash_to_offsets[hash]) * len(db_song_to_hashes_offsets[1]["hash"])
    # relative offsets even though there are only two actual offsets in the
    # database song. We use all relative offsets for computing the histogram,
    # which may result in there being more matching hashes than the total
    # number of hashes in the input song (especially if `offset bin size` is
    # relatively large). To compensate for this, we limit `num_matching_offsets`
    # returned at the end of the function to the total number of offsets in the
    # input song, i.e., len(song_fingerprints).

    for song_id in db_song_to_hashes_offsets:
        for hash_ in db_song_to_hashes_offsets[song_id]:
            if hash_ in inp_hash_to_offsets:
                for song_offset in db_song_to_hashes_offsets[song_id][hash_]:
                    for inp_offset in inp_hash_to_offsets[hash_]:
                        rel_offset = song_offset - inp_offset
                        db_song_to_rel_offsets[song_id].append(rel_offset)

    # The previous step effectively constructed a histogram of relative offsets
    # for each song id. Determine which song id contains the largest number of
    # relative offsets in the same bin (ie, which song id histogram has the
    # greatest peak).
    num_matching_fingerprints = 0
    match_song_id = None
    match_rel_offset = None

    for song_id, rel_offsets in db_song_to_rel_offsets.items():
        # Get the relative offset with the greatest frequency for this song.
        counter = collections.Counter(rel_offsets)
        peak_rel_offset, peak_count = counter.most_common(1)[0]

        if peak_count > num_matching_fingerprints:
            num_matching_fingerprints = peak_count
            match_rel_offset = peak_rel_offset
            match_song_id = song_id

    result = None
    if num_matching_fingerprints:
        result = {
            "song_id": match_song_id,
            "num_matching_fingerprints":
                min(num_matching_fingerprints, len(song_fingerprints)),
            "relative_offset": match_rel_offset * offset_bin_size,
        }
    return result

def fingerprint_from_signal(samples, **kwargs):
    """
    Fingerprint an audio signal by obtaining its spectrogram and returning
    its hashes.

    Args:
        samples (np.ndarray): Array representing the audio signal.
        sample_rate (int): Audio signal sample rate (in Hz).
        **kwargs: Optional keyword args for :func:`get_spectrogram`,
            :func:`find_peaks_2d`, and :func:`hash_peaks`.

    Returns:
        List[Tuple[str, float]]: hashes
            List of tuples where each tuple is a (hash, absolute_offset) pair.
            See :func:`hash_peaks`.
    """
    get_spectrogram_keys = [
        "sample_rate", "win_size", "win_overlap_ratio", "spectrogram_backend",
    ]
    get_spectrogram_kwargs = {
        k: v for k, v in kwargs.items() if k in get_spectrogram_keys
    }
    spectrogram, t, freq = get_spectrogram(samples, **get_spectrogram_kwargs)

    find_peaks_2d_keys = [
        "filter_connectivity", "filter_dilation", "erosion_iterations",
        "min_amplitude",
    ]
    find_peaks_2d_kwargs = {
        k: v for k, v in kwargs.items() if k in find_peaks_2d_keys
    }
    peaks = find_peaks_2d(spectrogram, **find_peaks_2d_kwargs)

    peak_freq_idxs, peak_time_idxs = np.where(peaks)

    peak_times = t[peak_time_idxs]
    peak_freqs = freq[peak_freq_idxs]
    peak_amplitudes = spectrogram[peaks]

    hash_peaks_keys = [
        "fanout", "min_time_delta", "max_time_delta", "hash_length",
        "time_bin_size", "freq_bin_size",
    ]
    hash_peaks_kwargs = {
        k: v for k, v in kwargs.items() if k in hash_peaks_keys
    }
    hashes = hash_peaks(peak_times, peak_freqs, **hash_peaks_kwargs)

    return hashes


def fingerprint_from_file(fpath, delete=False, **kwargs):
    """
    Fingerprint an audio file by reading the file and obtaining the fingerprint
    for each audio channel. Wraps :func:`fingerprint_from_signal`.

    Args:
        fpath (str): Path to audio file.
        delete (bool): Delete file after fingerprinting.
        **kwargs: Keyword args for :func:`fingerprint_from_signal`.

    Returns:
        tuple: (hashes, filehash)
            - hashes (List[Tuple[str, float]]): List of tuples where each tuple
              is a (hash, absolute_offset) pair. See :func:`hash_peaks`.
            - filehash (str): SHA1 hash of the file.

    .. note::
        Sample rate is obtained from the file. ``sample_rate`` should not be
        passed as part of ``**kwargs``.
    """
    channels, sample_rate, filehash = util.read_file(fpath)

    hashes = []
    for channel in channels:
        samples = channel
        hashes.extend(
            fingerprint_from_signal(samples, sample_rate=sample_rate, **kwargs)
        )
    if delete:
        os.remove(fpath)
        logging.info(f"Deleted file {fpath}")
    return hashes, filehash


async def fingerprint_song(song, loop, executor, out_queue=None, **kwargs):
    """
    Helper function for :func:`fingerprint_songs`. Fingerprints an audio file,
    adds the fingerprints (as a list) and file SHA1 hash to the audio file
    metadata dict, and pushes it to an output queue (if provided).

    Args:
        song (dict): Dict corresponding to an audio file. Must contain a
            ``path`` key containing the path to the downloaded audio file
            (or ``None``) if the download wasn't successful and the file
            doesn't exist.
        loop (asyncio.BaseEventLoop): asyncio EventLoop.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor in which the audio file
            will be processed.
        out_queue (asyncio.queues.Queue): Output queue to which video metadata
            will be pushed.
        kwargs: Keyword arguments for :func:`fingerprint_from_file`.

    Returns:
        dict: song
            Input dict with a ``filehash`` key and a ``fingerprints`` key
            containing a list of fingerprints (returned by
            :func:`fingerprint_from_file`) added to it::

                {
                    "filehash": str,
                    "fingerprints": List[Tuple[str, int]],
                }
    """
    song["filehash"] = None
    song["fingerprints"] = None

    if song["path"]:
        # Make partial with kwargs since run_in_executor only takes *args.
        fingerprint_from_file_partial = functools.partial(
            fingerprint_from_file, song["path"], **kwargs
        )

        hashes, filehash = await loop.run_in_executor(
            executor, fingerprint_from_file_partial
        )

        song["fingerprints"] = hashes
        song["filehash"] = filehash
        logging.info(f"Fingerprinted {song['path']} ({len(hashes)} hashes)")

    if out_queue is not None:
        await out_queue.put(song)
    return song


async def fingerprint_songs(
    loop, executor, in_queue, out_queue=None, **kwargs
):
    """
    TODO

    Args:
        loop (asyncio.BaseEventLoop): `asyncio` EventLoop.
        executor (concurrent.futures.Executor): ``concurrent.futures``
            ThreadPoolExecutor or ProcessPoolExecutor in which the audio file
            will be processed.
        in_queue (asyncio.queues.Queue): Process queue from which audio
            metadata is fetched for each song to be processed.
        out_queue (asyncio.queues.Queue): Output queue to which audio metadata
            will be pushed.
        **kwargs: Keyword arguments for :func:`fingerprint_from_file`.

    Returns:
        List[dict]: songs
            List of dicts representing metadata for the fingerprinted audio
            file. See :func:`fingerprint_song`.
    """
    tasks = []
    while True:
        song = await in_queue.get()
        if song is None:
            break

        task = loop.create_task(
            fingerprint_song(
                song, loop, executor, out_queue=out_queue, **kwargs
            )
        )
        tasks.append(task)

    # Wrap asyncio.wait() in if statement to avoid ValueError if no tasks.
    if tasks:
        await asyncio.wait(tasks)

    if out_queue is not None:
        await out_queue.put(None)

    return [task.result() for task in tasks]


def find_peaks_2d(
    x, filter_connectivity=1, filter_dilation=10, erosion_iterations=1,
    min_amplitude=None
):
    """
    Find peaks in a 2D array. See `Peak detection in a 2D array`_.

    Args:
        x (np.ndarray): 2D array, e.g., spectrogram.
        filter_connectivity (int): neighborhood connectivity of the maximum
            filter (``1`` produces a diamond, ``2`` produces a square). See
            `scipy.ndimage.generate_binary_structure`_.
        filter_dilation (int): Dilation factor for maximum filter (applied to
            the filter generated by `filter_connectivity`). ``1`` retains
            the original filter shape. See `scipy.ndimage.iterate_structure`_.
        erosion_iterations (int): Number of times to apply binary erosion.
            See `scipy.ndimage.binary_erosion`_.
        min_amplitude (float): Peak minimum amplitude (ignore peaks with values
            less than `min_amplitude`). If None, all peaks are returned.

    Returns:
        np.ndarray: peaks
            Mask of same shape as `x` where peaks are denoted by True.

    .. _`Peak detection in a 2D array`:
        https://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array
    .. _`scipy.ndimage.generate_binary_structure`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.generate_binary_structure.html
    .. _`scipy.ndimage.iterate_structure`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.iterate_structure.html
    .. _`scipy.ndimage.binary_erosion`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.binary_erosion.html
    """
    binary_struct = scipy.ndimage.generate_binary_structure(
        2, filter_connectivity
    )
    kernel = scipy.ndimage.iterate_structure(binary_struct, filter_dilation)
    maximum_mask = scipy.ndimage.maximum_filter(x, footprint=kernel) == x

    # Erode background of the max filtered image to obtain peaks.
    bg_mask = x == np.min(x)
    eroded_bg_mask = scipy.ndimage.binary_erosion(
        bg_mask, structure=kernel, border_value=1
    )

    # XOR local max mask and background to remove background from local max.
    peaks = maximum_mask ^ eroded_bg_mask

    if min_amplitude is not None:
        peaks &= x >= min_amplitude

    return peaks


def get_spectrogram(
    samples, sample_rate=44100, win_size=4096, win_overlap_ratio=0.5,
    spectrogram_backend="scipy"
):
    """
    Obtain the spectrogram for an audio signal.

    Args:
        samples (np.ndarray): Array representing the audio signal.
        sample_rate (int): Audio sample rate (Hz).
        win_size (int): Number of samples per FFT window.
        win_overlap_ratio (float): Number of samples to overlap between windows
            (as a fraction of window size).
        spectrogram_backend (str): {"scipy", "matplotlib"}
            Whether to use the scipy or matplotlib spectrogram functions to
            compute the spectrogram. See `scipy.signal.spectrogram`_ and
            `matplotlib.mlab.specgram`_.

    Returns:
        tuple: (spectrogram, t, freq)
            - spectrogram (np.ndarray): 2D array representing the signal spectrogram
              (amplitudes are in units of dB).
            - t (np.ndarray): 1D array of time bins (in units of seconds)
              corresponding to index 1 of ``spectrogram``.
            - freq (np.ndarray): 1D array of frequency bins (in units of Hz)
              corresponding to index 0 of ``spectrogram``.

    Raises:
        ValueError: If an invalid option for `spectrogram_backend` is specified.

    .. _`scipy.signal.spectrogram`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.spectrogram.html
    .. _`matplotlib.mlab.specgram`:
        https://matplotlib.org/api/mlab_api.html#matplotlib.mlab.specgram
    """
    if spectrogram_backend == "matplotlib":
        spectrogram, freq, t = mlab.specgram(
            samples, NFFT=win_size, Fs=sample_rate, window=mlab.window_hanning,
            noverlap=int(win_size * win_overlap_ratio)
        )
    elif spectrogram_backend == "scipy":
        freq, t, spectrogram = scipy.signal.spectrogram(
            samples, fs=sample_rate, window="hann", nperseg=win_size,
            noverlap=int(win_size * win_overlap_ratio)
        )
    else:
        raise ValueError("Invalid spectrogram backend")

    # Convert to dB by taking log and multiplying by 10.
    # https://stackoverflow.com/a/5730830
    # Handle log of zero values by setting them to -np.inf in output array.
    spectrogram = 10 * np.log10(
        spectrogram, out=(-np.inf * np.ones_like(spectrogram)),
        where=(spectrogram != 0)
    )
    return spectrogram, t, freq


def hash_peaks(
    times, frequencies, fanout=10, min_time_delta=0, max_time_delta=100,
    hash_length=20, time_bin_size=0.5, freq_bin_size=2
):
    """
    Hash the peaks of a spectrogram. For reference, see:

    * `Audio Fingerprinting with Python and Numpy`_
    * `How Shazam Works`_
    * A. Porter, `Evaluating musical fingerprinting systems`_, Montreal University, 2013. 

    Args:
        times (np.ndarray): Time bins of the peaks. Each element in `times`
            corresponds to an element in `frequencies`.
        frequencies (np.ndarray): Frequency bins of the peaks. Must have the
            same number of elements as `times`.
        fanout (int): Number of adjacent peaks to consider. For each peak,
            hashes will be generated for up to `fanout` peaks within the target
            zone defined by `min_time_delta` and `max_time_delta`.
        min_time_delta (float): Target zone minimum time offset (only generate
            hashes for adjacent peaks that occur at least `min_time_delta`
            after a given peak).
        max_time_delta (float): Target zone maximum time offset (only generate
            hashes for adjacent peaks that occur up to `max_time_delta` after
            a given peak).
        hash_length (int): Length to which the final hex hash string should be
            truncated. A smaller hash length reduces memory usage but increases
            likelihood of collisions.
        time_bin_size (float): Number of seconds per time bin (used to
            convert time deltas from floats to integers before hashing).
        freq_bin_size (float): Frequency range per frequency bin (used to
            convert frequencies from floats to integers before hashing), in Hz.

    Returns:
        List[Tuple[str, float]]: hashes
            List of tuples where each tuple represents a hash. The first
            element of each tuple contains the hash string for the peak pair
            and the second element contains a float representing the absolute
            offset of the reference peak (first peak) from the beginning of the
            audio signal, in seconds.

    .. _`Audio Fingerprinting with Python and Numpy`:
        https://willdrevo.com/fingerprinting-and-audio-recognition-with-python/
    .. _`How Shazam Works`:
        https://medium.com/@treycoopermusic/how-shazam-works-d97135fb4582
    .. _`Evaluating musical fingerprinting systems`:
        https://www.upf.edu/documents/223346843/0/porter2012thesis.pdf
    """
    # Sort peaks by time.
    peaks = sorted(zip(times, frequencies), key=lambda p: p[0])

    hashes = []
    for i, (t, f) in enumerate(peaks):
        for t2, f2 in peaks[(i + 1):(i + 1 + fanout)]:
            t_delta = t2 - t
            if min_time_delta <= t_delta <= max_time_delta:
                # Before hashing, we convert time delta and frequencies to
                # integers to avoid issues with float precision/rounding.
                t_delta_bin = int(t_delta / time_bin_size)
                f_bin = int(f / freq_bin_size)
                f2_bin = int(f2 / freq_bin_size)

                hash_ = hashlib.sha1(
                    f"{f_bin}{f2_bin}{t_delta_bin}".encode("utf-8")
                )
                hashes.append((hash_.hexdigest()[:hash_length], t))
    return hashes


def plot_peaks(times, frequencies, color="r", marker=".", ax=None):
    """
    Plot spectrogram peaks.

    Args:
        times (np.ndarray|List[float]): Array containing time values of peaks.
        frequencies (np.ndarray|List[float]): Array containing frequency values
            of peaks.
        color (str): String or matplotlib color spec representing color of each
            peak marker.
        marker (str): Matplotlib marker type (see `matplotlib.markers`_).
        ax (matplotlib.axes.Axes): Axis handle on which to plot peaks. If None,
            a new figure/axis will be created.

    Returns:
        tuple: (ax, pts)
            - ax (matplotlib.axes.Axes): Axis handle on which peaks were plotted.
            - pts (matplotlib.collections.PathCollection): Object containing the
              points plotted as a scatter plot. See `Axes.scatter`_.

    .. _`matplotlib.markers`:
        https://matplotlib.org/api/markers_api.html
    .. _`Axes.scatter`:
        https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.scatter.html
    """
    if ax is None:
        fig, ax = plt.subplots()
    pts = ax.scatter(times, frequencies, marker=marker, color=color)
    return ax, pts


def plot_spectrogram(
    spectrogram, times, frequencies, title=None, ax=None, fig=None,
    show_xlabel=True
):
    """
    Plot the spectrogram of an audio signal.

    Args:
        spectrogram (np.ndarray): 2D array representing the spectrogram
            (amplitudes) of the audio signal.
        times (np.ndarray): 1D array of the time bins (corresponding to index
            1 of `spectrogram`) of the audio signal.
        frequencies (np.ndarray): 1D array of the frequency bins (corresponding
            to index 0 of `spectrogram`) of the audio signal.
        title (str): Optional plot title.
        ax (matplotlib.axes.Axes): Matplotlib axis handle in which to plot the
            spectrogram. If None, a new figure/axis is created.
        fig (matplotlib.figure.Figure): Matplotlib figure handle for the figure
            containing `ax` (if any). Used for placing colormap scale beside
            plot. If `ax` is not provided, a new figure and axis are created.
        show_xlabel (bool): Display x-axis label.

    Returns:
        tuple: (ax, fig)
            - ax (matplotlib.axes.Axes): Plot axis handle.
            - fig (matplotlib.figure.Figure): Plot figure handle.
    """
    if ax is None:
        fig, ax = plt.subplots()

    t_min, t_max = times[0], times[-1]
    f_min, f_max = frequencies[0], frequencies[-1]
    extent = [t_min, t_max, f_min, f_max]

    im = ax.imshow(spectrogram, extent=extent, aspect="auto", origin="lower")

    # Set "bad" values (e.g., -np.inf) to the minimum colormap value.
    # copy.copy() due to matplotlib deprecation warning that future versions
    # will prevent bound cmaps from being modified directly.
    cmap = copy.copy(im.cmap)
    min_color = cmap.colors[0]
    cmap.set_bad(color=min_color)
    im.set_cmap(cmap)

    if title:
        ax.set_title(title)

    if fig is not None:
        fig.colorbar(im, ax=ax)

    if show_xlabel:
        ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")

    return ax, fig, im


def _dev_test(fpath=None, samples=None, sample_rate=None):
    """
    Demo function for fingerprinting an audio signal and plotting its
    spectrogram.
    
    Provide either 1) a path to an audio file with `fpath` or 2) both an audio
    signal and its sample rate with `samples` and `sample_rate`, respectively,
    or 3) nothing. If no input file or signal are provided, a sample waveform
    is generated and used.

    Args:
        fpath (str): Path to input audio file.
        samples (np.ndarray): Array representing audio signal.
        sample_rate (int): Sample rate of `samples`.
    """
    if fpath is not None and os.path.exists(fpath):
        samples, sample_rate, _ = read_file(fpath)
        samples = samples[0]
    elif samples is None and sample_rate is None:
        # Get an example waveform.
        sample_rate = 44100
        samples = generate_waveform(
            shape="sawtooth", duration=4, sample_rate=sample_rate, frequency=10000,
            amplitude=0.6, width=0.7
        )

    hashes = fingerprint(samples, sample_rate=sample_rate)

    # Get and plot the spectrogram for the audio.
    spectrogram, t, freq = get_spectrogram(samples, sample_rate, 4096, 0.5)
    ax, _, _ = plot_spectrogram(spectrogram, t, freq)

    # Find peaks in the spectrogram ignoring any with an amplitude < 10 dB.
    # Peaks is a boolean array of the same shape as ``spectrogram`` where
    # ``True`` values indicate peaks.
    peaks = find_peaks_2d(spectrogram, min_amplitude=10)

    # Obtain times and frequencies corresponding to the peaks, then plot them.
    peak_freq_idxs, peak_time_idxs = np.where(peaks)
    peak_t = t[peak_time_idxs]
    peak_freq = freq[peak_freq_idxs]
    plot_peaks(peak_t, peak_freq, ax=ax)

    plt.show()
