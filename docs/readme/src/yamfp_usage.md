```
usage: yamfp [-h] [--erosion-iterations <int>] [--filter-connectivity {1,2}]
             [--filter-dilation <int>] [-a <dB>]
             [--spectrogram-backend {scipy,matplotlib}]
             [--win-overlap-ratio <float>] [--win-size <int>]
             [-c <channel> [<channel> ...]] [-P] [-t <title>]
             [--start <seconds>] [--end <seconds>]
             <path>

Visualize an audio file fingerprint by plotting its spectrogram and the
spectrogram peaks.

positional arguments:
  <path>                Path to audio file

optional arguments:
  -h, --help            show this help message and exit
  -c <channel> [<channel> ...], --channels <channel> [<channel> ...]
                        Plot only the specified audio channels (beginning at
                        0) (default: None)
  -P, --no-peaks        Plot only the spectrogram without the spectrogram
                        peaks (default: False)
  -t <title>, --title <title>
                        Set plot title; defaults to filename if omitted
                        (default: None)
  --start <seconds>     Audio segment end time in seconds (beginning of file
                        if omitted) (default: None)
  --end <seconds>       Audio segment end time in seconds (end of file if
                        omitted) (default: None)

fingerprint arguments:
  --erosion-iterations <int>
                        Number of times to apply binary erosion for peak
                        finding (default: 1)
  --filter-connectivity {1,2}
                        Max filter neighborhood connectivity for peak finding
                        (default: 1)
  --filter-dilation <int>
                        Max filter dilation (neighborhood size) for peak
                        finding (default: 10)
  -a <dB>, --min-amplitude <dB>
                        Spectogram peak minimum amplitude in dB (default: 10)
  --spectrogram-backend {scipy,matplotlib}
                        Library to use for computing spectrogram (default:
                        scipy)
  --win-overlap-ratio <float>
                        Window overlap as a fraction of window size, in the
                        range [0, 1) (default: 0.5)
  --win-size <int>      Number of samples per FFT window (default: 4096)
```
