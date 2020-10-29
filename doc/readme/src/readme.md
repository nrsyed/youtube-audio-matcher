# YouTube Audio Matcher

* [Description](#description)
* [Design and Background](#background)
* [Requirements](#requirements)
* [Installation](#installation)
* [Examples](#examples)
* [Usage](#usage)
  * [`yam`](#yam-usage)
  * [`yamdb`](#yamdb-usage)
  * [`yamdl`](#yamdl-usage)
  * [`yamfp`](#yamfp-usage)
* [Acknowledgments](#acknowledgments)

# <span id="description">Description</span>

YouTube Audio Matcher enables you to download the audio from all videos on
any number of YouTube channels, perform audio fingerprinting on audio files,
and compare the audio fingerprints to an SQL database of audio fingerprints
to help identify the audio (similar to Shazam) or, optionally, add them to the
database. Local files and directories can also be provided as input.


# <span id="background">Design and Background</span>

@@include[background.md]


# <span id="requirements">Requirements</span>
* Python &ge; 3.6
* [Chromium](https://www.chromium.org) or
  [Google Chrome](https://www.google.com/chrome/) browser, and
  [ChromeDriver](http://chromedriver.chromium.org/home)
* [FFmpeg](https://ffmpeg.org/download.html)
* PostgreSQL or MySQL client/driver (see list of
  [SQLAlchemy–supported drivers/backends](https://docs.sqlalchemy.org/en/13/core/engines.html))


# <span id="installation">Installation</span>

@@include[installation.md]


# <span id="examples">Examples</span>

@@include[examples.md]


# <span id="usage">Usage</span>

This package contains four command line tools/commands. The main tool is
`yam` (**Y**ouTube **A**udio **M**atcher), which combines download,
fingerprinting, and database functionality. Each of these three components
also have their own command line interfaces: `yamdb` (**YAM** **D**ata**b**ase
tool), `yamdl` (**YAM** **D**own**l**oad tool), and `yamfp`
(**YAM** **F**inger**p**rint tool).


## <span id="yam-usage">`yam`</span>

@@include[yam_usage.md]


## <span id="yamdb-usage">`yamdb`</span>

@@include[yamdb_usage.md]


## <span id="yamdl-usage">`yamdl`</span>

@@include[yamdl_usage.md]


## <span id="yamfp-usage">`yamfp`</span>

@@include[yamfp_usage.md]


# <span id="acknowledgments">Acknowledgments</span>
This project was inspired by
[Ben-0-mad's YT-TMS-Finder](https://github.com/Ben-0-mad/YT-TMS-Finder) repo,
whose goal is to try and identify unknown songs by checking YouTube channels
for matching videos.

Projects, articles, and papers I found to be invaluable for learning about
audio fingerprinting include the following:
* [Audio Fingerprinting with Python and Numpy](https://willdrevo.com/fingerprinting-and-audio-recognition-with-python/) and [dejavu](https://github.com/worldveil/dejavu)
* [How does Shazam work](http://coding-geek.com/how-shazam-works/)
* Avery Li-Chun Wang, "An Industrial-Strength Audio Search Algorithm,"
Proc. 2003 ISMIR, Baltimore, MD, Oct. 2003.
https://www.ee.columbia.edu/~dpwe/papers/Wang03-shazam.pdf
