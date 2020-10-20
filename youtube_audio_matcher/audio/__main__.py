import argparse
import os
import pathlib

import matplotlib.pyplot as plt
import numpy as np

import youtube_audio_matcher.audio


def get_core_parser():
    """
    Sub-parser containing core audio module arguments. Used by both yamfp
    in this module and by the top-level yam command.
    """
    core_parser = argparse.ArgumentParser(add_help=False)

    fingerprint_args = core_parser.add_argument_group("Fingerprint args")
    fingerprint_args.add_argument(
        "-a", "--min-amplitude", type=float, default=10, metavar="<dB>",
        help="Spectogram peak minimum amplitude in dB"
    )
    fingerprint_args.add_argument(
        "--erosion-iterations", type=int, default=1, metavar="<int>",
        help="Number of times to apply binary erosion for peak finding"
    )
    fingerprint_args.add_argument(
        "--filter-connectivity", type=int, default=1, choices=(1, 2),
        help="Max filter neighborhood connectivity for peak finding"
    )
    fingerprint_args.add_argument(
        "--filter-dilation", type=int, default=10, metavar="<int>",
        help="Max filter dilation (neighborhood size) for peak finding"
    )
    fingerprint_args.add_argument(
        "--spectrogram-backend", type=str, choices=("scipy", "matplotlib"),
        default="scipy",
        help="Library to use for computing spectrogram"
    )
    fingerprint_args.add_argument(
        "--win-overlap-ratio", type=float, default=0.5, metavar="<float>",
        help="Window overlap as a fraction of window size, in the range [0, 1)"
    )
    fingerprint_args.add_argument(
        "--win-size", type=int, default=4096, metavar="<int>",
        help="Number of samples per FFT window"
    )
    return core_parser


def get_parser():
    core_parser = get_core_parser()
    parser = argparse.ArgumentParser(
        parents=[core_parser],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Visualize an audio file fingerprint by plotting its "
        "spectrogram and the spectrogram peaks."
    )
    parser.add_argument(
        "filepath", type=pathlib.Path, metavar="<path>",
        help="Path to audio file"
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
            win_overlap_ratio=args.win_overlap_ratio,
            spectrogram_backend=args.spectrogram_backend
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
