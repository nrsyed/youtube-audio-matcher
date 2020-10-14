import pathlib

import youtube_audio_matcher as yam


def add_song_to_database(db, fpath, song_title=None, fingerprint_kwargs=None):
    """
    Args:
        db (youtube_audio_matcher.database.Database): Database class instance.
        fpath (str): Path to audio file.
        song_title (str): Audio file song title. If None, the file stem will
            be used as the title.
        fingerprint_kwargs (dict): Dict containing keyword argument/value
            pairs for :func:`youtube_audio_matcher.audio.fingerprint`.

    Returns:
        int: num_fingerprints
            Total number of fingerprints extracted from the audio file and
            added to the database.
    """
    fpath = pathlib.Path(fpath).expanduser().resolve()
    channels, sample_rate, filehash = yam.audio.read_file(str(fpath))

    if not song_title:
        song_title = str(fpath.stem)

    # Add song to database Song table and get the id of the newly added song.
    song_id = db.add_song(
        {
            "duration": len(channels[0]) / sample_rate,
            "filepath": str(fpath),
            "filehash": filehash,
            "title": song_title,
        }
    )

    # TODO: handle if song already exists in DB. Update its fingerprints?

    # Obtain fingerprints for each channel in the audio file and add them to
    # the database Fingerprint table.
    if fingerprint_kwargs is None:
        fingerprint_kwargs = dict()

    num_fingerprints = 0
    for channel in channels:
        samples = channel
        fingerprints = yam.audio.fingerprint(
            samples, sample_rate, **fingerprint_kwargs
        )
        num_fingerprints += len(fingerprints)

        # Construct list of fingerprints and bulk insert into the database.
        fingerprint_db_entries = []
        for fp_hash, offset in fingerprints:
            fingerprint_db_entries.append(
                {
                    "song_id": song_id,
                    "hash": fp_hash,
                    "offset": offset,
                }
            )
            db.add_fingerprints(fingerprint_db_entries)
    return num_fingerprints
