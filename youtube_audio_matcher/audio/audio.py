import copy
import hashlib
import os

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import pydub
import scipy.io.wavfile
import scipy.ndimage
import scipy.signal


def hash_file(fpath, block_size=2**16):
    """
    Get the SHA1 hash of a file.

    Args:
        fpath (str): Path to file.
        block_size (int): Number of bytes to read from the file at a time.

    Returns:
        str: hash
            SHA1 digest as a hex string.
    """
    hash_ = hashlib.sha1()
    with open(fpath, "rb") as f:
        while (buf := f.read(block_size)):
            hash_.update(buf)
    return hash_.hexdigest()


def read_file(fpath):
    """
    Read an audio file and extract audio information and file SHA-1 hash.

    Args:
        fpath (str): Path to file.

    Returns:
        tuple: (channel_data, sample_rate, sha1_hash)
            - channel_data (List[np.ndarray]): Data for each audio channel.
            - sample_rate (int): Audio sample rate (Hz, i.e., samples per second).
            - sha1_hash (str): SHA-1 hash of the file.

    .. note::
        Does not support 24-bit (use wavio for 24-bit files).
    """
    audio_seg = pydub.AudioSegment.from_file(fpath)
    raw_data = np.frombuffer(audio_seg.raw_data, np.int16)

    num_channels = audio_seg.channels
    channel_data = [raw_data[ch::num_channels] for ch in range(num_channels)]
    sample_rate = audio_seg.frame_rate

    return channel_data, sample_rate, hash_file(fpath)


def get_spectrogram(
    samples, sample_rate=44100, win_size=4096, win_overlap_ratio=0.5,
    backend="scipy"
):
    """
    Obtain the spectrogram for an audio signal.

    Args:
        samples (np.ndarray): Array representing the audio signal.
        sample_rate (int): Audio sample rate (Hz).
        win_size (int): Number of samples per FFT window.
        win_overlap_ratio (float): Number of samples to overlap between windows
            (as a fraction of window size).
        backend (str): {"scipy", "matplotlib"}
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
        ValueError: If an invalid option for `backend` is specified.

    .. _`scipy.signal.spectrogram`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.spectrogram.html
    .. _`matplotlib.mlab.specgram`:
        https://matplotlib.org/api/mlab_api.html#matplotlib.mlab.specgram
    """
    if backend == "matplotlib":
        spectrogram, freq, t = mlab.specgram(
            samples, NFFT=win_size, Fs=sample_rate, window=mlab.window_hanning,
            noverlap=int(win_size * win_overlap_ratio)
        )
    elif backend == "scipy":
        freq, t, spectrogram = scipy.signal.spectrogram(
            samples, fs=sample_rate, window="hann", nperseg=win_size,
            noverlap=int(win_size * win_overlap_ratio)
        )
    else:
        raise ValueError("Invalid backend")

    # Convert to dB by taking log and multiplying by 10.
    # https://stackoverflow.com/a/5730830
    # Handle log of zero values by setting them to -np.inf in output array.
    spectrogram = 10 * np.log10(
        spectrogram, out=(-np.inf * np.ones_like(spectrogram)),
        where=(spectrogram != 0)
    )
    return spectrogram, t, freq


def plot_spectrogram(
    spectrogram, times, frequencies, title=None, ax=None, fig=None
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

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")

    return ax, fig


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


def find_peaks_2d(
    x, filter_connectivity=1, filter_dilation=10, erosion_iterations=1,
    min_amplitude=None
):
    """
    Find peaks in a 2D array. See `Peak detection in a 2D array`_.

    Args:
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


def hash_peaks(
    times, frequencies, fanout=1, min_time_delta=0, max_time_delta=100,
    hashlen=20
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
        hashlen (int): Length to which the final hex hash string should be
            truncated. A smaller hash length reduces memory usage but increases
            likelihood of collisions.

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
                hash_ = hashlib.sha1(f)
                hash_.update(f2)
                hash_.update(t_delta)
                hashes.append((hash_.hexdigest()[:hashlen], t))
    return hashes


def fingerprint(
    samples, sample_rate=44100, win_size=4096, win_overlap_ratio=0.5,
    min_amplitude=10, fanout=10, min_time_delta=0, max_time_delta=100,
    hashlen=20
):
    """
    Fingerprint an audio signal by obtaining its spectrogram and returning
    its hashes.

    Args:
        samples (np.ndarray): Array representing the audio signal.
        sample_rate (int): Audio signal sample rate (in Hz).
        win_size (int): Number of samples per FFT window (see
            :func:`get_spectrogram`).
        win_overlap_ratio (float): Number of samples to overlap between windows
            (see :func:`get_spectrogram`).
        min_amplitude (float): Amplitude threshold (in dB) for spectrogram
            peaks (see :func:`find_peaks_2d`).
        fanout (int): Number of adjacent peaks to consider for generating
            hashes (see :func:`hash_peaks`).
        min_time_delta (float): Target zone minimum time offset for hashes
            (see :func:`hash_peaks`).
        max_time_delta (float): Target zone maximum time offset for hashes
            (see :func:`hash_peaks`).
        hashlen (int): Length to which the hash string should be truncated
            (see :func:`hash_peaks`).

    Returns:
        List[Tuple[str, float]]: hashes
            List of tuples where each tuple is a (hash, absolute_offset) pair.
            See :func:`hash_peaks`.
    """
    spectrogram, t, freq = get_spectrogram(
        samples, sample_rate, win_size, win_overlap_ratio
    )
    peaks = find_peaks_2d(spectrogram, min_amplitude=10)

    peak_freq_idxs, peak_time_idxs = np.where(peaks)

    peak_times = t[peak_time_idxs]
    peak_freqs = freq[peak_freq_idxs]
    peak_amplitudes = spectrogram[peaks]

    hashes = hash_peaks(
        peak_times, peak_freqs, fanout=fanout, min_time_delta=min_time_delta,
        max_time_delta=max_time_delta, hashlen=hashlen
    )
    return hashes


def generate_waveform(
    shape="sine", duration=1, num_samples=None, sample_rate=44100,
    frequency=440, amplitude=1.0, duty_cycle=0.5, width=1, out_path=None
):
    """
    Generate an int16 waveform signal.

    Args:
        shape (str): {"sine", "sawtooth", "square"}
            Type of waveform to generate.
        duration (float): Duration of audio signal in seconds. If `num_samples`
            is provided, `duration` is ignored.
        num_samples (int): Number of samples to generate. If None, `duration`
            is used to compute the number of samples based on `sample_rate`.
        sample_rate (int): Audio signal sample rate in Hz.
        frequency (float): Audio signal frequency in Hz.
        amplitude (float): Amplitude as a fraction [0, 1] of the total range.
            Values are first computed as floats in the range [-1.0, 1.0], then
            scaled to the int16 range [-32768, 32767]. This argument
            effectively sets the volume of the generated audio signal as a
            fraction of maximum possible volume.
        duty_cycle (float): Duty cycle in the range [0, 1] for square wave.
            See `scipy.signal.square`_.
        width (float): Sawtooth wave width argument in the range [0, 1]. See
            `scipy.signal.sawtooth`_.
        out_path (str): Filepath to which the audio signal should be written as
            a WAV file. If None, file is not saved.

    Returns:
        np.ndarray: Array representing the audio signal.

    .. _`scipy.signal.square`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.square.html
    .. _`scipy.signal.sawtooth`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sawtooth.html
    """
    if num_samples is None:
        num_samples = duration * sample_rate

    x = np.arange(num_samples)
    t = 2 * np.pi * frequency * x / sample_rate

    if shape == "sine":
        y = np.sin(t)
    elif shape == "square":
        y = scipy.signal.square(t, duty=duty_cycle)
    elif shape == "sawtooth":
        y = scipy.signal.sawtooth(t, width=width)

    # Scale y from float32 range to int16 range and convert to int16.
    amplitude = max(amplitude, 1.0)
    y = (amplitude * y * 32767).astype(np.int16)

    if out_path is not None:
        scipy.io.wavfile.write(out_path, sample_rate, y)
    return y


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
    ax, _ = plot_spectrogram(spectrogram, t, freq)

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