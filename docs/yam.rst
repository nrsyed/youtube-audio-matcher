yam
=====

The **Y**\ outube **A**\ udio **M**\ atcher command line tool ``yam``
is the package's main command line utility. It combines the functionality of
the :doc:`youtube_audio_matcher.download`, :doc:`youtube_audio_matcher.audio`,
and :doc:`youtube_audio_matcher.database` modules to download videos as audio
from YouTube channels/users as MP files3, obtain the audio fingerprint of
downloaded files (or local files), and add the fingerprints to a database or
match the fingerprints against existing fingerprints in a database.

Most of the options available for ``yam`` (detailed below in the
:ref:`yam-usage` section) are the same as those found in the individual
sub-module command line tools :doc:`yamdl`, :doc:`yamfp`, and :doc:`yamdb`.

.. _yam-usage:

Usage
-----

.. code-block:: none

  usage: yam [-h] [-N <database_name>] [-C <dialect>] [-R <driver>] [-H <host>]
             [-P <password>] [-O <port>] [-U <username>] [-d <path>]
             [-L <seconds>] [-S <seconds>] [-i] [-p <seconds>] [-r <num>] [-y]
             [--start <seconds>] [--end <seconds>] [--duration <seconds>]
             [--erosion-iterations <int>] [-f <int>]
             [--filter-connectivity {1,2}] [--filter-dilation <int>] [-l <int>]
             [--max-time-delta <float>] [--min-time-delta <float>] [-a <dB>]
             [--spectrogram-backend {scipy,matplotlib}]
             [--win-overlap-ratio <float>] [--win-size <int>] [-A] [-c <float>]
             [-D] [--max-processes <num>] [--max-threads <num>] [-o [path]]
             [--debug] [-s]
             inputs [inputs ...]

  positional arguments:
    inputs                One or more space-separated input sources (YouTube
                          channel/user URL, local path to audio file, or local
                          path to a directory of audio files)

  optional arguments:
    -h, --help            show this help message and exit
    -A, --add-to-database
                          Add files to the database after fingerprinting instead
                          of searching the database for matches (default: False)
    -c <float>, --conf-thresh <float>
                          Confidence threshold for matches (default: 0.05)
    -D, --delete          Delete downloaded files after fingerprinting (default:
                          False)
    --max-processes <num>
                          Max number of CPUs for parallel processing (default:
                          None)
    --max-threads <num>   Max number of threads for concurrent tasks (default:
                          None)
    -o [path], --output [path]
                          Path to output file containing matches in JSON format;
                          if this option is provided without an argument, a
                          timestamped filename is generated and written to the
                          current directory (default: None)

  database arguments:
    -N <database_name>, --db-name <database_name>
                          Database name (default: yam)
    -C <dialect>, --dialect <dialect>
                          SQL dialect (default: postgresql)
    -R <driver>, --driver <driver>
                          SQL dialect driver (default: None)
    -H <host>, --host <host>
                          Database hostname (default: localhost)
    -P <password>, --password <password>
                          Database password (default: None)
    -O <port>, --port <port>
                          Database port number (default: None)
    -U <username>, --user <username>
                          Database user name (default: None)

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

  fingerprint arguments:
    --erosion-iterations <int>
                          Number of times to apply binary erosion for peak
                          finding (default: 1)
    -f <int>, --fanout <int>
                          Number of adjacent peaks to consider for generating
                          hashes (default: 10)
    --filter-connectivity {1,2}
                          Max filter neighborhood connectivity for peak finding
                          (default: 1)
    --filter-dilation <int>
                          Max filter dilation (neighborhood size) for peak
                          finding (default: 10)
    -l <int>, --hash-length <int>
                          Truncate fingerprint SHA1 hashes to --hash-length (max
                          40) (default: 40)
    --max-time-delta <float>
                          Target zone max time offset difference for hashes
                          (default: 100)
    --min-time-delta <float>
                          Target zone min time offset difference for hashes
                          (default: 0)
    -a <dB>, --min-amplitude <dB>
                          Spectogram peak minimum amplitude in dB (default: 10)
    --spectrogram-backend {scipy,matplotlib}
                          Library to use for computing spectrogram (default:
                          scipy)
    --win-overlap-ratio <float>
                          Window overlap as a fraction of window size, in the
                          range [0, 1) (default: 0.5)
    --win-size <int>      Number of samples per FFT window (default: 4096)

  Verbosity arguments:
    --debug               Print verbose debugging info (default: False)
    -s, --silent          Suppress youtube-audio-matcher terminal output
                          (default: False)

Examples
--------

To add songs to the database, provide the ``-A``/``--add-to-database`` switch
along with any number of YouTube channel/user URLs and/or any number of paths
to local audio files or local directories containing audio files. The following
example demonstrates the command for adding a local file ``file1.mp3``, all
files from a local directory ``sample_directory``, and a YouTube channel to a
PostgreSQL database (with the credentials `user` = ``yam``,
`database name` = ``yam``, `databse password` = ``yam``), as well as sample
terminal output:

*Command*

.. code-block:: bash

  yam -A www.youtube.com/c/sample_channel file1.mp3 sample_directory \
  -U yam -N yam -P yam

*Output*

.. code-block:: none

  [INFO] Fingerprinted /home/sample_directory/file3.mp3 (44570 hashes)
  [INFO] Fingerprinted /home/sample_directory/file2.mp3 (89020 hashes)
  [INFO] Fingerprinted /home/file1.mp3 (216960 hashes)
  [INFO] Successfully downloaded /home/Z6_7orLq0D.mp3
  [INFO] Added /home/sample_directory/file3.mp3 to database (4.56 s)
  [INFO] Fingerprinted /home/Z6_7orLq0D.mp3 (75470 hashes)
  [INFO] Successfully downloaded /home/s71A5oUut3.mp3
  [INFO] Successfully downloaded /home/wFoxOcQU60.mp3
  [INFO] Added /home/sample_directory/file2.mp3 to database (9.04 s)
  [INFO] Fingerprinted /home/wFoxOcQU60.mp3 (89020 hashes)
  [INFO] Fingerprinted /home/s71A5oUut3.mp3 (216960 hashes)
  [INFO] Added /home/Z6_7orLq0D.mp3 to database (8.06 s)
  [INFO] Added /home/wFoxOcQU60.mp3 to database (8.89 s)
  [INFO] Added /home/file1.mp3 to database (21.22 s)
  [INFO] Added /home/s71A5oUut3.mp3 to database (19.88 s)
  [INFO] All songs added to database (25.13 s)


To match songs against those already in the database, omit the
``-A`` switch. To delete any downloaded songs after they've been fingerprinted,
include the ``-D``/``--delete`` switch. The following command fingerprints a
local file `file4.mp3` and the audio from all videos on two YouTube
users/channels, compares them to the database, and prints any matches to the
terminal (as well as deletes the downloaded files):

*Command*

.. code-block:: bash

  yam youtube.com/c/some_channel youtube.com/u/some_user file4.mp3 \
    -D -U yam -N yam -P yam

*Output*

.. code-block:: none

  [INFO] Fingerprinted /home/file4.mp3 (11520 hashes)
  [INFO] Matching fingerprints for /home/file4.mp3
  [INFO] Successfully downloaded /home/pzvDf_H7db.mp3
  [INFO] Successfully downloaded /home/Rv4nWAZw8V.mp3
  [INFO] Successfully downloaded /home/iPTmeNCao7.mp3
  [INFO] Fingerprinted /home/pzvDf_H7db.mp3 (32650 hashes)
  [INFO] Matching fingerprints for /home/pzvDf_H7db.mp3
  [INFO] Fingerprinted /home/Rv4nWAZw8V.mp3 (22520 hashes)
  [INFO] Matching fingerprints for /home/Rv4nWAZw8V.mp3
  [INFO] Fingerprinted /home/iPTmeNCao7.mp3 (73860 hashes)
  [INFO] Matching fingerprints for /home/iPTmeNCao7.mp3
  [INFO] Finished matching fingerprints for /home/file4.mp3 in 10.28 s
  [INFO] Finished matching fingerprints for /home/Rv4nWAZw8V.mp3 in 2.68 s
  [INFO] Finished matching fingerprints for /home/iPTmeNCao7.mp3 in 7.21 s
  [INFO] Finished matching fingerprints for /home/pzvDf_H7db.mp3 in 10.14 s
  [INFO] Match 1:
  {
      "youtube_id": null,
      "title": null,
      "duration": null,
      "channel_url": null,
      "path": "/home/file4.mp3",
      "filehash": "e0bf9d28e9b2409b7ad181b97f532569d27c9633",
      "num_fingerprints": 11520,
      "matching_song": {
          "id": 8,
          "duration": 436.0,
          "filehash": "c12b119ab98caee4a24eef5e7b3f4d7bf2b38f99",
          "filepath": "/home/song2.mp3",
          "title": null,
          "youtube_id": null,
          "num_fingerprints": 812890
      },
      "match_stats": {
          "num_matching_fingerprints": 3352,
          "confidence": 0.29097222222222224,
          "iou": 0.004082537409050274,
          "relative_offset": 300.0
      }
  }

  [INFO] Match 2:
  {
      "youtube_id": "iPTmeNCao7",
      "title": "Sample YT video title",
      "duration": 177,
      "channel_url": "https://www.youtube.com/c/some_channel/videos",
      "path": "/home/iPTmeNCao7.mp3",
      "filehash": "6b59b4c301de5ad3f7dddcdb78fbf62bd1618cab",
      "num_fingerprints": 73860,
      "matching_song": {
          "id": 3,
          "duration": 155.0,
          "filehash": "6ba1139a7fc8cde33ff30065b45ed3c9f457f5a6",
          "filepath": "/home/a92_Uxy5mq.mp3",
          "title": "Some other video on youtube",
          "youtube_id": "a92_Uxy5mq",
          "num_fingerprints": 216960
      },
      "match_stats": {
          "num_matching_fingerprints": 73821,
          "confidence": 0.9994719740048741,
          "iou": 0.3401905077903585,
          "relative_offset": 0.0
      }
  }

The output contains matches (if any) as well as information on each match,
including the `confidence` (number of matching fingerprints divided by total
number of fingerprints in the input song) and `relative_offset` (which part of
the matched song the input song corresponds to, in seconds); in other words, a
`relative_offset` of 300 means that the beginning of the input song corresponds
to the 300-second mark in the matched song from the database.

The confidence threshold for determining what's considered a match can be
adjusted using the ``-c``/``--confidence`` option. To write the matches to a
text file, use the ``-o``/``--output`` option:

.. code-block:: bash

  yam youtube.com/c/some_channel youtube.com/u/some_user file4.mp3 \
    -D -U yam -N yam -P yam -c 0.25 -o matches.txt


Troubleshooting
---------------

High RAM usage
^^^^^^^^^^^^^^

Because the ``yam`` command uses all available CPUs to compute and match
fingerprints and each set of fingerprints consumes a certain amount of memory,
running the command on a large number of songs with a large number of available
CPUs may end up using up all available RAM. If this becomes an issue, limit the
number of processes with the ``--max-processes`` option.

429 Too Many Requests
^^^^^^^^^^^^^^^^^^^^^

YouTube sometimes detects and prevents a large number of simultaneous
downloads, which can cause the youtube-dl download attempt to fail. By default,
``yam`` will retry any failed downloads up to (a default of) 5 times, but this
number can be adjusted with the ``-r``/``--retries`` option. If downloads are
still failing due to a `429 Too Many Requests` HTTP error, you can try limiting
the number of concurrent downloads by specifying a maximum number of threads
with the ``--max-threads`` option (all downloads are handled by a thread pool).
