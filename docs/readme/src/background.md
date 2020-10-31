The program leverages Python asynchronous functions and coroutines, combined
with multithreading and multiprocessing, to efficiently download and/or process
files, summarized in the flow diagram below.

<img src="docs/img/yam_diagram.png" />

Any number of YouTube channel/user URLs and local files/directories can be
provided as input. A webscraping coroutine (the "get video metadata from page
source" block in the diagram) gets (via
[Selenium](https://github.com/SeleniumHQ/selenium/)) and parses (via
[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/))
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

## Audio fingerprinting

Audio fingerprinting refers to the act of turning audio into a set of hashes.
The first step of this involves obtaining the
[spectrogram](https://en.wikipedia.org/wiki/Spectrogram) of the song/audio,
which is effectively a measure of the intensity of the sound frequencies of the
audio over the course of the song. The spectrogram of the song *Phenomenal* by
Benjai is shown below (the images in this section were generated by the
[`yamfp`](#yamfp-usage) tool).

<img src="docs/img/spec_full.png" />

Next, we find the peaks in the spectrogram, i.e., the points in the spectrogram
with the greatest amplitude. The spectrogram for the first 10 seconds of the
song is shown below, with the peaks represented by red dots.

<img src="docs/img/spec_10_peaks.png" />

The song's fingerprints are generated from peaks of pairs in a process known
as combinatorial hashing, where we iterate through the peaks and, for each
peak, form pairs with its neighbors. The number of neighbors we consider is
termed the *fanout* value. This is shown in the figures below, which are taken
from the paper by Avery Wang, the founder of Shazam (see
[Acknowledgments](#acknowledgments)).

<img src="docs/img/combinatorial_hashing.png" />

The figure defines a "target zone" that determines which neighbors to consider
for each peak. Each peak pair is used to generate a hash based on the frequency
and time difference between each point—this constitutes a fingerprint. If we
use a target zone of +1 s to +10 s (and no restriction on the frequency) with a
fanout value of 2, the first 10 seconds of the song generate the following
*hash constellation*:

<img src="docs/img/fingerprint_hash_pairs_10_fanout2.png" />

If we increase the fanout value to 6, it looks more like the following:

<img src="docs/img/fingerprint_hash_pairs_10_fanout6.png" />

Increasing the fanout value results in more hash pairs, increasing the
robustness of the fingerprints but also increasing storage requirements
and computation time to find matches, since there can be tens or hundreds
of thousands of hash pairs for an entire song.

More on the algorithm used to match audio fingerprints to fingerprints in the
database can be found in the paper and in the source code (see the function
`youtube_audio_matcher.audio.fingerprint.align_matches`).