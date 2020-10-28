# YouTube Audio Matcher

* [Description](#description)
* [Requirements](#requirements)
* [Installation](#installation)
* [Background](#background)
* [Usage and examples](#usage)
  * [`yam`](#yam-usage)
  * [`yamdb`](#yamdb-usage)
  * [`yamdl`](#yamdl-usage)
  * [`yamfp`](#yamfp-usage)
  * [Import as Python package](#import)
* [Acknowledgments](#acknowledgments)

# <span id="description">Description</span>

YouTube Audio Matcher enables you to download the audio from all content from
any number of YouTube channels or users, perform audio fingerprinting on them,
and compare the audio fingerprints to a SQL database of audio fingerprints
to help identify the audio (like Shazam or any of a number of song
identification apps) or, optionally, add them to the database. It also accepts
files and directories on the local disk.


# <span id="requirements">Requirements</span>
* Python &ge; 3.6
* [Chromium](https://www.chromium.org) or
  [Google Chrome](https://www.google.com/chrome/) browser, and
  [ChromeDriver](http://chromedriver.chromium.org/home)
* FFmpeg (install from your distribution's package repository, if on a
  Unix-based system (e.g., `apt install ffmpeg`), or from
  [https://ffmpeg.org](https://ffmpeg.org/download.html))
* PostgreSQL or MySQL client/driver (see list of
  [SQLAlchemy–supported drivers/backends](https://docs.sqlalchemy.org/en/13/core/engines.html))


# <span id="installation">Installation</span>

@@include[installation.md]


# <span id="background">Background</span>

@@include[background.md]


# <span id="usage">Usage</span>

This package contains four command line tools/commands. The main tool is
`yam` (**Y**ouTube **A**udio **M**atcher).


## <span id="yam-usage">`yam`</span>

@@include[yam_usage.md]


## <span id="yamdb-usage">`yamdb`</span>

@@include[yamdb_usage.md]


## <span id="yamdl-usage">`yamdl`</span>

@@include[yamdl_usage.md]


## <span id="yamfp-usage">`yamfp`</span>

@@include[yamfp_usage.md]


# <span id="import">Import as Python package</span>
The package can be imported and used directly in a Python program. This exposes
lower-level functionality than the command-line interface. Refer to the
docstrings in the source code for complete documentation.


# <span id="acknowledgments">Acknowledgments</span>
This project and a couple bits of code were inspired by
[Ben-0-mad's YT-TMS-Finder](https://github.com/Ben-0-mad/YT-TMS-Finder) repo.
