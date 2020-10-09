import copy
import hashlib
import os
import pdb

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import pydub
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


def fingerprint(
    samples, sample_rate=44100, win_size=4096, win_overlap_ratio=0.5,
    fan_value=5, min_amplitude=10
):
    spectrogram, t, freq = get_spectrogram(
        samples, sample_rate, win_size, win_overlap_ratio
    )
    plot_spectrogram(spectrogram, t, freq)
    plt.show()
