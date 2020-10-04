# YouTube Audio Matcher

This package, which is still in-progress, contains efficient and lightweight
tools for concurrently downloading the audio from all of the videos on one
or more YouTube channels. Ultimately, audio fingerprinting functionality will
be incorporated to compare the downloaded audio files to a database and
determine if there are any matches.

* [Requirements](#requirements)
* [Installation](#installation)
* [Examples](#examples)
  * [Command line interface](#cli-examples)
  * [Python](#python-examples)
* [Usage](#usage)
  * [Command line interface](#cli)
  * [Import as Python package](#import)
* [Acknowledgments](#acknowledgments)

# <span id="requirements">Requirements</span>
* Python &ge; 3.6
* FFmpeg (install from your distribution's package repository, if on a
  Unix-based system, or from
  [https://ffmpeg.org](https://ffmpeg.org/download.html).)

# <span id="installation">Installation</span>
```
git clone https://github.com/nrsyed/youtube-audio-matcher.git
cd youtube-audio-matcher
pip install .
```

# <span id="examples">Examples</examples>

For complete usage, see the [Usage](#usage) section.

## <span id="cli-examples">Command line interface</span>
The following example demonstrates the command and sample output for
downloading up to the first 60 seconds (`--duration 60`) of audio from all
videos from two YouTube users/channels to the `~/yt_mp3s` directory
(`-d ~/yt_mp3s`), excluding videos that are longer than 300 seconds (`-L 300`)
or shorter than 5 seconds (`-S 5`). youtube-dl and ffmpeg produce verbose
output that can be suppressed with the `-q` switch.

```
yamdl youtube.com/user/rBfKc48QOY7hw_lwEiVUQGe youtube.com/c/ExampleYTChannel123/featured \
  -d ~/yt_mp3s -L 300 -S 5 --duration 60 -q

[INFO] Grabbing page source for URL https://www.youtube.com/user/rBfKc48QOY7hw_lwEiVUQGe/videos
[INFO] Grabbing page source for URL https://www.youtube.com/c/ExampleYTChannel123/videos
[INFO] Downloading files from https://www.youtube.com/user/rBfKc48QOY7hw_lwEiVUQGe/videos (attempt #1)
[INFO] Downloading files from https://www.youtube.com/c/ExampleYTChannel123/videos (attempt #1)
[INFO] Successfully downloaded file /home/najam/yt_mp3s/yLm01NY6uo.mp3 (video id yLm01NY6uo)
[INFO] Successfully downloaded file /home/najam/yt_mp3s/-BNfV34P7t.mp3 (video id -BNfV34P7t)
[INFO] Successfully downloaded file /home/najam/yt_mp3s/SVNXhv040J.mp3 (video id SVNXhv040J)
[ERROR] Error downloading video id vMfko2L_N_
[WARNING] Failed to download video id vMfko2L_N_ Download will be retried.
[INFO] Downloading files from https://www.youtube.com/c/ExampleYTChannel123/videos (attempt #2)
[INFO] Successfully downloaded file /home/najam/yt_mp3s/vMfko2L_N_.mp3 (video id vMfko2L_N_)
[INFO] Successfully downloaded audio from 2 of 2 videos for URL https://www.youtube.com/user/rBfKc48QOY7hw_lwEiVUQGe/videos
[INFO] Successfully downloaded file /home/najam/yt_mp3s/HtAk9CHy6n.mp3 (video id HtAk9CHy6n)
[INFO] Successfully downloaded audio from 3 of 3 videos for URL https://www.youtube.com/c/ExampleYTChannel123/videos
[INFO] Successfully downloaded audio from 5 of 5 total videos
```

## <span id="python-examples">Python</span>

The following Python code performs the same actions as the command line example
above:

```
import youtube_audio_matcher as yam

urls = [
    "youtube.com/user/rBfKc48QOY7hw_lwEiVUQGe",
    "youtube.com/c/ExampleYTChannel123/featured"
]
dst_dir = "/home/najam/yt_mp3s"

# Function returns metadata for videos that were attempted to be downloaded.
metadata = yam.download.download_channels(
    urls, dst_dir, exclude_longer_than=300, exclude_shorter_than=5,
    duration=60, quiet=True
)

print(metadata[0])
```

This would produce the following output:
```
{
    'id': 'HtAk9CHy6n',
    'title': 'Example video title',
    'duration': 57,
    'channel_url': 'https://www.youtube.com/c/ExampleYTChannel123/videos',
    'path': '/home/najam/yt_mp3s/HtAk9CHy6n.mp3'
}
```

The `yam.download.download_channels()` function returns metadata for each
downloaded video in the form of a list of dicts like the one above. If a video
was not downloaded successfully, its path will be `None`.

# <span id="usage">Usage</span>

This package contains tools for batch downloading audio from multiple YouTube
channels, which can be called via the command line using the `yamdl`
(**Y**ouTube **A**udio **M**atcher **d**own**l**oad tool) command or directly
in Python by importing `youtube_audio_matcher`. Tools for audio fingerprinting
will be added in future versions.

## <span id="cli">Command line interface</span>
```
usage: yamdl [-h] [-d <path>] [-i] [-r <num>] [-L <seconds>] [-S <seconds>]
             [--start <seconds>] [--end <seconds>] [--duration <seconds>] [-q]
             [--debug | -s]
             url [url ...]

Efficiently and quickly download the audio from all videos on one or more
YouTube channels, filter based on video length, and extract audio only from
the segments of interest.

positional arguments:
  url                   One or more channel/user URLs (e.g.,
                        www.youtube.com/c/YouTubeCreators). All options apply
                        to all URLs.

optional arguments:
  -h, --help            show this help message and exit
  -d <path>, --dst-dir <path>
                        Path to destination directory for downloaded files
                        (default: current directory)
  -i, --ignore-existing
                        Do not download files that already exist
  -r <num>, --retries <num>
                        Number of times to re-attempt failed downloads
                        (default: 3). Pass -1 to retry indefinitely until
                        successful (not recommended)
  -L <seconds>, --exclude-longer-than <seconds>
                        Do not download/convert videos longer than specified
                        duration. This does NOT truncate videos to a maximum
                        desired length; to extract or truncate specific
                        segments of audio from downloaded videos, use --start,
                        --end, and/or --duration
  -S <seconds>, --exclude-shorter-than <seconds>
                        Do not download/convert videos shorter than specified
                        duration
  --start <seconds>     Extract audio beginning at the specified video time
                        (in seconds)
  --end <seconds>       Extract audio up to the specified video time (in
                        seconds)
  --duration <seconds>  Duration (in seconds) of audio to extract beginning at
                        0 if --start not specified, otherwise at --start. If
                        --duration is used with --end, --duration takes
                        precedence.
  -q, --youtubedl-quiet
                        Disable all youtube-dl and ffmpeg terminal output.
                        This option does NOT control the terminal output of
                        this program (youtube-audio-matcher); to set this
                        program's output, use --silent or --debug

verbosity options:
  --debug               Print verbose debugging info
  -s, --silent          Suppress terminal output for this program
```

## <span id="import">Import as Python package</span>

The package can be imported and used directly in a Python program. This exposes
lower-level functionality than the command-line interface. Refer to the
docstrings in the source code for complete documentation.

# <span id="acknowledgments">Acknowledgments</span>
This project and a couple bits of code were inspired by
[Ben-0-mad's YT-TMS-Finder](https://github.com/Ben-0-mad/YT-TMS-Finder) repo.
