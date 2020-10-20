import argparse
import os
import pathlib

import matplotlib.pyplot as plt
import numpy as np

import youtube_audio_matcher.audio


def get_parser():
    parser = argparse.ArgumentParser(
        description="Visualize an audio file fingerprint by plotting its "
        "spectrogram and the spectrogram peaks."
    )
    parser.add_argument(
        "filepath", type=pathlib.Path, help="Path to audio file"
    )
    # TODO: rename to spectrogram_backend
    parser.add_argument(
        "--backend", type=str, choices=("scipy", "matplotlib"),
        default="scipy",
        help="Library to use for computing spectrogram "
        "{matplotlib, scipy (default)}"
    )
    parser.add_argument(
        "-c", "--filter-connectivity", type=int, default=1, choices=(1, 2),
        help="Max filter neighborhood connectivity for peak finding. "
        "{1 (diamond, default), 2 (square)"
    )
    parser.add_argument(
        "-D", "--filter-dilation", type=int, default=10,
        help="Max filter dilation (neighborhood size) for peak finding "
        "(default 10)"
    )
    parser.add_argument(
        "-e", "--erosion-iterations", type=int, default=1,
        help="Number of times to apply binary erosion for peak finding "
        "(default 1)"
    )
    parser.add_argument(
        "-m", "--min-amplitude", type=float, default=10,
        help="Spectogram peak minimum amplitude in dB"
    )
    parser.add_argument(
        "-o", "--win-overlap-ratio", type=float, default=0.5,
        help="Number of samples to overlap between windows as a fraction of "
        "window size (default 0.5)"
    )
    parser.add_argument(
        "-w", "--win-size", type=int, default=4096,
        help="Number of samples per FFT window (default 4096)"
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    fpath = args.filepath.expanduser().resolve()

    channels, sample_rate, _ = youtube_audio_matcher.audio.read_file(fpath)

    num_channels = len(channels)
    fig, axes = plt.subplots(nrows=num_channels, ncols=1, sharex=True)
    fig.subplots_adjust(right=0.97, hspace=0.05)

    for i, channel in enumerate(channels):
        samples = channel
        spectrogram, t, freq = youtube_audio_matcher.audio.get_spectrogram(
            samples, sample_rate=sample_rate, win_size=args.win_size,
            win_overlap_ratio=args.win_overlap_ratio, backend=args.backend
        )

        title = ""
        if i == 0:
            fname = os.path.split(fpath)[1]
            title = f"{fname} spectrogram ({num_channels} channels)"

        show_xlabel = i == (num_channels - 1)

        youtube_audio_matcher.audio.plot_spectrogram(
            spectrogram, t, freq, title=title, ax=axes[i], fig=fig,
            show_xlabel=show_xlabel
        )

        peaks = youtube_audio_matcher.audio.find_peaks_2d(
            spectrogram, filter_connectivity=args.filter_connectivity,
            filter_dilation=args.filter_dilation,
            erosion_iterations=args.erosion_iterations,
            min_amplitude=args.min_amplitude
        )

        peak_freq_idxs, peak_time_idxs = np.where(peaks)
        peak_t = t[peak_time_idxs]
        peak_freq = freq[peak_freq_idxs]
        youtube_audio_matcher.audio.plot_peaks(peak_t, peak_freq, ax=axes[i])
    plt.show()
