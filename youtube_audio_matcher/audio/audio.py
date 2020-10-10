import copy
import hashlib
import os
import pdb

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import pydub
import scipy.ndimage
import scipy.signal


def hash_file(fpath, block_size=2**20):
    hash_ = hashlib.sha1()
    with open(fpath, "rb") as f:
        while (buf := f.read(block_size)):
            hash_.update(buf)
    return hash_.hexdigest().upper()


def read_file(fpath):
    """
    Does not support 24-bit (use wavio instead if necessary).
    """
    audio = pydub.AudioSegment.from_file(fpath)
    raw_data = np.frombuffer(audio.raw_data, np.int16)

    num_channels = audio.channels
    channel_data = [raw_data[ch::num_channels] for ch in range(num_channels)]

    return {
        "channel_data": channel_data,
        "sample_rate": audio.frame_rate,
        "sha1_hash": hash_file(fpath)
    }

def get_spectrogram(
    samples, sample_rate, win_size, win_overlap_ratio, backend="scipy"
):
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
    Returns:
        ax (matplotlib.axes.Axes): Plot axis handle.
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

    return ax


def find_peaks_2d(
    x, filter_connectivity=1, filter_dilation=10, erosion_iterations=1,
    min_amplitude=None
):
    """
    See `Peak detection in a 2D array`_.

    Args:
        filter_connectivity (int): neighborhood connectivity of the maximum
            filter (``1`` produces a diamond, ``2`` produces a square). See
            `scipy.ndimage.generate_binary_structure`_.
        filter_dilation (int): Dilation factor for maximum filter (applied to
            the filter generated by ``filter_connectivity``). ``1`` retains
            the original filter shape. See `scipy.ndimage.iterate_structure`_.
        erosion_iterations (int): Number of times to apply binary erosion.
            See `scipy.ndimage.binary_erosion`_.
        min_amplitude (float): Peak minimum amplitude (ignore peaks with values
            less than ``min_amplitude``). If ``None``, all peaks are returned.

    Returns:
        peaks (np.ndarray): Mask of same shape as ``x`` where peaks are
            denoted by ``True``.

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


def fingerprint(
    samples, sample_rate=44100, win_size=4096, win_overlap_ratio=0.5,
    fan_value=5, min_amplitude=10
):
    spectrogram, t, freq = get_spectrogram(
        samples, sample_rate, win_size, win_overlap_ratio
    )
    peaks = find_peaks_2d(spectrogram, min_amplitude=10)

    peak_freq_idxs, peak_time_idxs = np.where(peaks)

    peak_times = t[peak_time_idxs]
    peak_freqs = freq[peak_freq_idxs]
    peak_amplitudes = spectrogram[peaks]

    return peak_times, peak_freqs, peak_amplitudes
