Architecture
============

Youtube Audio Matcher leverages Python asynchronous functions and coroutines, combined
with multithreading and multiprocessing, to efficiently download and/or process
files, summarized in the flow diagram below.

.. image:: img/yam_diagram.png

Any number of YouTube channel/user URLs and local files/directories can be
provided as input. A webscraping coroutine (the "get video metadata from page
source" block in the diagram) gets (via `Selenium`_) and parses (via
`BeautifulSoup`_)
the complete page source for each URL and extracts information on each video
on the channel/user Videos page, namely the YouTube ID, duration, title. The
videos are filtered based on criteria supplied by the user (e.g., exclude
videos longer and/or shorter than a certain duration), after which they're
added to a download queue. A download coroutine ("download videos as mp3")
kicks off each download in a thread pool, in which each video is downloaded
via youtube-dl and converted to MP3 by ffmpeg. As each download completes, it's
added to a fingerprint queue. Any local files provided as input are
added directly to the fingerprint queue, since they don't need to be
downloaded. A third coroutine ("fingerprint songs") consumes songs from the
fingerprint queue and sends them to a process pool, where they are
fingerprinted using all available CPUs (see the
[Audio fingerprinting](#audio-fingerprinting) sub-section below). After
fingerprinting, each video is added to a database queue.

If the user opted to add songs to the database, the fingerprinted files are
passed to a coroutine that uses the process pool to add songs and their
fingerprints to the database.

If the user instead opted to match the input songs against the fingerprints
already in the database, the songs are passed to a coroutine that uses the
process pool to query the database and determine if there's a match. All
matches are ultimately returned (and optionally written to a text file as
JSON).

By offloading I/O-heavy downloads to a thread pool and CPU-heavy fingerprinting
and matching to other CPUs, a large number of files can be processed quickly.

.. _`BeautifulSoup`:
  https://www.crummy.com/software/BeautifulSoup/

.. _`Selenium`:
  https://github.com/SeleniumHQ/selenium/
