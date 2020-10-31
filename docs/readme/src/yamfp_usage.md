```
usage: yamfp [-h] [--erosion-iterations <int>] [-f <int>]
             [--filter-connectivity {1,2}] [--filter-dilation <int>]
             [--max-time-delta <float>] [--min-time-delta <float>] [-a <dB>]
             [--spectrogram-backend {scipy,matplotlib}]
             [--win-overlap-ratio <float>] [--win-size <int>]
             [-c <channel> [<channel> ...]] [-p] [-F] [-t <title>]
             [--start <seconds>] [--end <seconds>]
             <path>

Visualize an audio file fingerprint by plotting its spectrogram, spectrogram
peaks, and/or fingerprint (peak pairs).

positional arguments:
  <path>                Path to audio file

optional arguments:
  -h, --help            show this help message and exit
  -c <channel> [<channel> ...], --channels <channel> [<channel> ...]
                        Plot only the specified audio channels (beginning at
                        0) (default: None)
  -p, --no-peaks        Do not plot spectrogram peaks (default: False)
  -F, --plot-fingerprints
                        Plot fingerprint constellations between peak pairs
                        instead of plotting spectrogram (default: False)
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
  -f <int>, --fanout <int>
                        Number of adjacent peaks to consider for generating
                        hashes (default: 3)
  --filter-connectivity {1,2}
                        Max filter neighborhood connectivity for peak finding
                        (default: 1)
  --filter-dilation <int>
                        Max filter dilation (neighborhood size) for peak
                        finding (default: 10)
  --max-time-delta <float>
                        Target zone max time offset difference for hashes
                        (default: 10)
  --min-time-delta <float>
                        Target zone min time offset difference for hashes
                        (default: 1)
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
