import os

import matplotlib.pyplot as plt
import numpy as np

import youtube_audio_matcher.audio
from ._argparsers import get_parser

# import matplotlib
# matplotlib.rcParams.update({"font.size": 26})
# matplotlib.rc("text", usetex=True)


def cli():
    parser = get_parser()
    args = parser.parse_args()

    fpath = args.filepath.expanduser().resolve()

    channels, sample_rate, _ = youtube_audio_matcher.audio.read_file(fpath)

    if args.channels:
        channels = [channels[channel_idx] for channel_idx in args.channels]

    # Extract only the desired audio segment from the file (if specified).
    if args.start or args.end:
        start_idx = int(sample_rate * args.start) if args.start else 0
        end_idx = int(sample_rate * args.end) if args.end else len(channels[0])
        channels = [channel[start_idx:end_idx] for channel in channels]

    num_channels = len(channels)
    fig, axes = plt.subplots(nrows=num_channels, ncols=1, sharex=True)

    if args.plot_fingerprints:
        fig.subplots_adjust(right=0.8, hspace=0.05)
    else:
        fig.subplots_adjust(right=0.97, hspace=0.05)

    # plt.subplots() returns an AxesSubplot object if 1 axis, else an array of
    # AxesSubplot objects. Either way, we want to convert it to a list.
    if isinstance(axes, np.ndarray):
        axes = axes.tolist()
    else:
        axes = [axes]

    for i, channel in enumerate(channels):
        samples = channel
        spectrogram, t, freq = youtube_audio_matcher.audio.get_spectrogram(
            samples, sample_rate=sample_rate, win_size=args.win_size,
            win_overlap_ratio=args.win_overlap_ratio,
            spectrogram_backend=args.spectrogram_backend
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

        title = ""
        if i == 0:
            if args.title:
                title = args.title
            else:
                fname = os.path.split(fpath)[1]
                title = f"{fname} spectrogram ({num_channels} channels)"

        if args.plot_fingerprints:
            youtube_audio_matcher.audio.plot_fingerprints(
                peak_t, peak_freq, fanout=args.fanout,
                min_time_delta=args.min_time_delta,
                max_time_delta=args.max_time_delta, ax=axes[i]
            )
            peak_color = "k"
        else:
            youtube_audio_matcher.audio.plot_spectrogram(
                spectrogram, t, freq, title=title, ax=axes[i], fig=fig,
            )
            peak_color = "r"

        if not args.no_peaks:
            youtube_audio_matcher.audio.plot_peaks(
                peak_t, peak_freq, color=peak_color, ax=axes[i]
            )

        axes[i].set_ylim(bottom=0, top=sample_rate / 2)

        show_xlabel = i == (num_channels - 1)
        if show_xlabel:
            axes[i].set_xlabel("Time (s)")
        axes[i].set_ylabel("Frequency (Hz)")

        if title:
            axes[i].set_title(title)
    plt.show()
