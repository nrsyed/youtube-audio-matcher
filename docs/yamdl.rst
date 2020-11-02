yamdl
=====

The **Y**\ outube **A**\ udio **M**\ atcher **D**\ own\ **l**\ oad
command line tool ``yamdl`` can be used to efficiently and asynchronously
download the audio from any number of YouTube channels/users as MP3s.

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

Examples
--------

The following command downloads all videos from two YouTube channels/users
(``youtube.com/user/ytuser`` and ``youtube.com/c/somechannel``) as MP3 files
to the current directory.

.. code:: bash

  yamdl youtube.com/user/ytuser youtube.com/c/somechannel

To specify a destination directory, use the ``-d``/``--dst-dir`` option. To
ignore existing files and skip downloading them, use the
``-i``/``--ignore-existing`` switch.

.. code:: bash

  yamdl youtube.com/user/ytuser youtube.com/c/somechannel -d ~/downloads -i

Use the ``-L``/``--exclude-longer-than`` option to ignore any videos longer
than the specified number of seconds. Use the ``-S``/``--exclude-shorter-than``
option to ignore videos shorter than the specified number of seconds. The
following commands downloads all videos shorter than 15 seconds and longer than
5 minutes:

.. code:: bash

  yamdl youtube.com/user/ytuser youtube.com/c/somechannel -S 15 -L 300

Use ``--start``, ``--end``, and/or ``--duration`` options to select a specific
segment of audio from the downloaded files.

.. note::
  ``--duration`` takes precedence over ``--end`` if both are provided (as
  defined by the `FFmpeg <https://ffmpeg.org/ffmpeg.html#Main-options>`_
  usage). If both ``--duration`` and ``--end`` are omitted, the whole video
  beginning at ``--start`` (or 0, if ``--start`` is also omitted) is converted
  to MP3.

.. important::
  ``--start``, ``--duration``, and ``--end`` specify which segments of audio to
  retain *after* files have been downloaded. They do not control which videos
  are downloaded. In other words, ``-L``/``--exclude-longer-than`` prevents
  videos longer than the specified duration from being downloaded; it does
  **not** truncate them to that length (use ``--duration`` or ``--end`` to
  truncate any downloaded videos to a maximum length).

To download all videos with a duration of at least 15 seconds and less than
5 minutes *and* truncate them to the first 30 seconds of audio, use the
following command:

.. code:: bash

  yamdl youtube.com/user/ytuser youtube.com/c/somechannel -S 15 -L 300 \
    --duration 30

YouTube Audio Matcher utilizes Selenium to scrape YouTube channel/user
web pages by scrolling to the bottom of the Videos page and waiting between
each page scroll event to allow the new videos to load. It compares the page
source after each wait/scroll to the last page source and, if they are
identical, assumes the bottom of the videos list has been reached (i.e.,
that we've scrolled to the bottom of the page). The wait is set to 1 second by
default. On slower internet connections, this may be insufficient, and the
page may not have enough time to load. In this case, increase the page load
wait time using the ``-p``/``--page-load-wait`` option to specify the number
of seconds to wait. The following example sets the between-scroll page load
wait time to 5 seconds:

.. code:: bash

  yamdl youtube.com/user/ytuser youtube.com/c/somechannel -p 5
