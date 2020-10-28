The program leverages asynchronous programming combined with
multithreading and multiprocessing to efficiently download and/or process
files, summarized in the flow diagram below.

<img src="doc/img/yam_diagram.png" />

It accepts any number of YouTube channel/user URLs and local files/directories
as input. An async function loads (via Selenium) and parses (via BeautifulSoup)
the page source for each URL to obtain video metadata (YouTube ID,
duration, title) for all videos, filters them based on any criteria supplied by
the user (e.g., exclude videos longer and/or shorter than a certain duration),
and adds them to an async download queue. An async download function kicks off
each download in a thread pool, where the video is downloaded via youtube-dl
and converted to MP3. As each download completes, it's added to an
async fingerprint queue. Any local files provided as input are
added directly to the fingerprint queue. Another async function consumes songs
from the fingerprint queue and sends them to a process pool, where they are
fingerprinted (see the [Audio fingerprinting](#audio-fingerprinting)
sub-section below) and added to an async database queue.

If the user opted to add songs to the database, the fingerprinted files are
passed to a function that uses the process pool to add songs and their
fingerprints to the database in parallel.

Otherwise, if the user opted to match the input songs against the fingerprints
already in the database, the songs are passed to a function that uses the
process pool to query the database and determine if there's a match. This
information is returned to the async match function, which ultimately returns
all matches (if any).

By offloading I/O-heavy downloads to a thread pool and CPU-heavy fingerprinting
and matching to other cores, we achieve a high-throughput system that can
process a large number of files quickly.

## Audio fingerprinting

Audio fingerprinting refers to the act of turning audio into a relatively
small set of hashes that can be quickly looked up in a database. The first step
of this involves obtaining the
[spectrogram](https://en.wikipedia.org/wiki/Spectrogram) of the song/audio,
which is effectively a measure of the intensity of the sound frequencies of the
audio over the course of the song. The spectrogram of the song *Phenomenal* by
Benjai is shown below.

<img src="doc/img/spec_full.png" />

The fingerprint of the song is obtained by finding the peaks in the
spectrogram. The spectrogram for the first 10 seconds of the song, along with
the peaks, is shown below.

<img src="doc/img/spec_10_peaks.png" />
