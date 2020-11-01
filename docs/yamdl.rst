yamdl
=====

YAM download tool

Usage
-----

.. code-block:: none

  usage: yamdl [-h] [-d <path>] [-L <seconds>] [-S <seconds>] [-i]
               [-p <seconds>] [-r <num>] [-y] [--start <seconds>]
               [--end <seconds>] [--duration <seconds>] [--debug] [-s]
               urls [urls ...]

  Efficiently and quickly download the audio from all videos on one or more
  YouTube channels, filter based on video length, and extract audio only from
  the segments of interest.

  positional arguments:
    urls                  One or more space-separated channel/user URLs (e.g.,
                          www.youtube.com/c/YouTubeCreators). Options apply to
                          all URLs.

  optional arguments:
    -h, --help            show this help message and exit

  download arguments:
    -d <path>, --dst-dir <path>
                          Path to destination directory for downloaded files
                          (default: .)
    -L <seconds>, --exclude-longer-than <seconds>
                          Do not download/convert videos longer than specified
                          duration. This does NOT truncate videos to a maximum
                          desired length; to extract or truncate specific
                          segments of audio from downloaded videos, use --start,
                          --end, and/or --duration (default: None)
    -S <seconds>, --exclude-shorter-than <seconds>
                          Do not download/convert videos shorter than specified
                          duration (default: None)
    -i, --ignore-existing
                          Do not download files that already exist (default:
                          False)
    -p <seconds>, --page-load-wait <seconds>
                          Time to wait (in seconds) to allow page to load on
                          initial page load and and after each page scroll
                          (default: 1)
    -r <num>, --retries <num>
                          Number of times to re-attempt failed downloads. Pass
                          -1 to retry indefinitely until successful (default: 5)
    -y, --youtubedl-verbose
                          Enable youtube-dl and ffmpeg terminal output (default:
                          False)
    --start <seconds>     Extract audio beginning at the specified video time
                          (in seconds) (default: None)
    --end <seconds>       Extract audio up to the specified video time (in
                          seconds) (default: None)
    --duration <seconds>  Duration (in seconds) of audio to extract beginning at
                          0 if --start not specified, otherwise at --start. If
                          --duration is used with --end, --duration takes
                          precedence. (default: None)

  Verbosity arguments:
    --debug               Print verbose debugging info (default: False)
    -s, --silent          Suppress youtube-audio-matcher terminal output
                          (default: False)
