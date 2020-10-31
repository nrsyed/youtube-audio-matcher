import asyncio
import logging
import time

import sqlalchemy

from .schema import Base, Fingerprint, Song


def database_obj_to_py(obj, fingerprints_in_song=False):
    """
    Recursively convert Fingerprint and Song sqlalchemy objects to native
    Python types (lists and dicts).

    Args:
        obj (database.schema.Fingerprint|database.schema.Song): ``audio``
            module Fingerprint or Song object.
        fingerprints_in_song (bool): Include each song's fingerprints as a
            list within the song dict.

    Returns:
        py_obj: list|dict
    """
    if isinstance(obj, list):
        return [
            database_obj_to_py(elem, fingerprints_in_song=fingerprints_in_song)
            for elem in obj
        ]
    elif isinstance(obj, Song):
        song = {
            "id": obj.id,
            "duration": obj.duration,
            "filehash": obj.filehash,
            "filepath": obj.filepath,
            "title": obj.title,
            "youtube_id": obj.youtube_id,
        }

        if fingerprints_in_song:
            song["fingerprints"] = [
                database_obj_to_py(fp) for fp in obj.fingerprints
            ]
            song["num_fingerprints"] = len(obj.fingerprints)
        return song
    elif isinstance(obj, Fingerprint):
        return {
            "song_id": obj.song_id,
            "hash": obj.hash,
            "offset": obj.offset,
        }
    else:
        raise ValueError("Unsupported object")


def _threadsafe_add_fingerprints(db_kwargs, song):
    logging.info(f"Adding {song['path']} to database...")
    db = Database(**db_kwargs)
    song_id = db.add_song(
        duration=song.get("duration"), filepath=song.get("path"),
        filehash=song.get("filehash"), title=song.get("title"),
        youtube_id=song.get("youtube_id")
    )
    db.add_fingerprints(song_id, song["fingerprints"])
    del db
    del song["fingerprints"]


# TODO: delete files after fingerprinting
async def _update_database(song, loop, executor, db_kwargs):
    start_t = time.time()
    delete_file = False
    try:
        if "delete" in song:
            delete_file = True
        await loop.run_in_executor(
            executor, _threadsafe_add_fingerprints, db_kwargs, song
        )
        elapsed = time.time() - start_t
        logging.info(f"Added {song['path']} to database ({elapsed:.2f} s)")
    except Exception as e:
        logging.error(f"Error adding {song['path']} to database ({str(e)})")
    finally:
        if delete_file:
            logging.info(f"Deleting file {song['path']}")
            # TODO delete song


# TODO: handle song already existing in database
async def update_database(loop, executor, db_kwargs, in_queue):
    """
    Consume fingerprinted songs from an async input queue and add the songs
    and their fingerprints to the database either concurrently (via a thread
    pool) or in parallel (via a process pool).

    Args:
        loop (asyncio.BaseEventLoop): asyncio EventLoop.
        executor (concurrent.futures.Executor): `concurrent.futures`
            ThreadPoolExecutor or ProcessPoolExecutor in which the database
            connection will be created to update the database.
        db_kwargs (dict): Dict containing keyword args for instantiating a
            :class:`Database` object.
        in_queue (asyncio.queues.Queue): Database queue containing song dicts
            representing songs (and their fingerprints) to be added to the
            database.
    """
    start_t = time.time()
    tasks = []
    while True:
        song = await in_queue.get()
        if song is None:
            break

        task = loop.create_task(
            _update_database(song, loop, executor, db_kwargs)
        )
        tasks.append(task)

    # Wrap asyncio.wait() in if statement to avoid ValueError if no tasks.
    if tasks:
        await asyncio.wait(tasks)
    elapsed = time.time() - start_t
    logging.info(f"All songs added to database ({elapsed:.2f} s)")


# TODO: try/except, db rollbacks
class Database:
    """
    Class that holds a database connection to perform read/update/delete
    operations.
    """

    def __init__(
        self, user, password, db_name, host="localhost", port=None,
        dialect="postgresql", driver=None
    ):
        """
        Constructs a sqlalchemy database URL of the form
        `dialect+driver://username:password@host:port/db_name` to create a
        sqlalchemy database engine. Refer to `SQLAlchemy Database URLs`_.

        Args:
            user (str): User name.
            password (str): User password.
            db_name (str): Database name.
            host (str): Database hostname.
            port (int): Port on ``host``.
            dialect (str): SQL database dialect to use. See
                `SQLAlchemy Dialects`_.
            driver (str): SQL database driver to use. See
                `SQLAlchemy Database URLs`_.

        .. _`SQLAlchemy Dialects`:
            https://docs.sqlalchemy.org/en/13/dialects/
        .. _`SQLAlchemy Database URLs`:
            https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
        """
        # TODO: check/add sqlite support.

        # Construct database URL.
        driver = f"+{driver}" if driver else ""
        port = f":{port}" if port is not None else ""

        # MySQL requires localhost to be specified as 127.0.0.1 to correctly
        # use TCP.
        if dialect == "mysql" and host == "localhost":
            host = "127.0.0.1"

        url = f"{dialect}{driver}://{user}:{password}@{host}{port}/{db_name}"
        logging.debug(f"Connecting to database URL {url}")

        engine = sqlalchemy.create_engine(url)
        Session = sqlalchemy.orm.sessionmaker(engine)
        self.session = Session()

        Base.metadata.create_all(engine)
        self.base = Base
        self.engine = engine

    def __del__(self):
        self.session.close()

    def add_song(
        self, duration=None, filepath=None, filehash=None, title=None,
        youtube_id=None
    ):
        """
        Args:
            duration (float): Song duration.
            filepath (str): Path to file on local machine.
            filehash (str): File hash.
            title (str): Song title.
            youtube_id (str): YouTube ID, i.e., watch?v=<youtube_id>.

        Returns:
            int: id of the inserted song.
        """
        new_song = Song(
            duration=duration, filepath=filepath, filehash=filehash,
            title=title, youtube_id=youtube_id
        )
        self.session.add(new_song)
        self.session.commit()
        return new_song.id

    def add_fingerprint(self, song_id, hash_, offset):
        """
        Args:
            song_id (int): Song id corresponding to song in the Song table.
            hash_ (str): Fingerprint hash.
            offset (float): Fingerprint offset.

        Returns:
            int: id of the inserted fingerprint.
        """
        new_fingerprint = Fingerprint(
            song_id=song_id, hash=hash_, offset=offset
        )
        self.session.add(new_fingerprint)
        self.session.commit()
        return new_fingerprint.id

    def add_fingerprints(self, song_id, fingerprints):
        """
        Args:
            song_id (int): Song table song id the fingerprints correspond to.
            fingerprints (List[tuple]): A list of (hash, offset) fingerprints.
        """
        new_fingerprints = [
            Fingerprint(song_id=song_id, hash=hash_, offset=offset)
            for hash_, offset in fingerprints
        ]
        self.session.bulk_save_objects(new_fingerprints)
        self.session.commit()

    def as_dict(self, combine_tables=False):
        """
        Return the database as a Python dictionary. See
        :func:`database_obj_to_py`.

        Args:
            combine_tables (bool): If True, the returned dict will have a
                single ``songs`` field containing a list of songs, and each
                song will have a ``fingerprints`` field containing the list
                of fingerprints belonging to it. If False, the returned dict
                will contain a ``songs`` field and a ``fingerprints`` field.

        Returns:
            dict: tables
                Dict containing database Fingerprint and Song tables::

                    {
                        "songs": list,
                        "fingerprints": list
                    }

                If ``combine_tables=True``, the returned dict will not contain
                a ``fingerprints`` key.
        """
        songs_table = self.session.query(Song).all()
        fingerprints_table = self.session.query(Fingerprint).all()

        if combine_tables:
            return {
                "songs":
                    database_obj_to_py(songs_table, fingerprints_in_song=True),
            }
        else:
            return {
                "songs": database_obj_to_py(songs_table),
                "fingerprints": database_obj_to_py(fingerprints_table),
            }

    def delete_all(self):
        """
        Delete all rows in the Fingerprint and Song tables.
        """
        self.session.query(Fingerprint).delete()
        self.session.query(Song).delete()
        self.session.commit()

    def _drop_tables(self, tables):
        self.base.metadata.drop_all(bind=self.engine, tables=tables)
        self.session.commit()

    def drop_all_tables(self):
        """
        Drop Fingerprint and Song tables.
        """
        self._drop_tables([Fingerprint.__table__, Song.__table__])

    def drop_song_table(self):
        """
        Drop Song table.
        """
        self._drop_tables([Song.__table__])

    def drop_fingerprint_table(self):
        """
        Drop Fingerprint table.
        """
        self._drop_tables([Fingerprint.__table__])

    def query_fingerprints(self, hashes):
        """
        Query the database for a list of matching hashes.

        Args:
            hashes (str|List[str]): Hash or list of hashes from a
                fingerprinted audio signal.

        Returns:
            fingerprints: list
                A list of fingerprints whose hashes match the input hashes.
                Each fingerprint is a dict containing the hash, song id, and
                offset (in seconds)::

                    {
                        "song_id": int,
                        "hash": str,
                        "offset": float
                    }
        """
        # Perform query; this is the equivalent of
        # SELECT * FROM fingerprint WHERE fingerprint.hash IN (`hashes`)
        query = self.session.query(Fingerprint).filter(
            Fingerprint.hash.in_(hashes)
        )
        return database_obj_to_py(query.all())

    def query_songs(
        self, id_=None, duration=None, duration_greater_than=None,
        duration_less_than=None, filehash=None, filepath=None, title=None,
        youtube_id=None, include_fingerprints=False
    ):
        """
        Query the database for songs matching the specified criteria.

        Args:
            id_ (list|int): Int or list of ints corresponding to the id
                primary key field of the database Song table.
            duration (list|float): Float or list of floats corresponding to
                the duration field of the database Song table.
            duration_greater_than (float): Only return songs with a duration
                greater than this value, if one is specified.
            duration_less_than (float): Only return songs with a duration less
                than this value, if one is specified.
            filehash (list|str): A filehash or list of filehashes corresponding
                to the filehash field of the database Song table.
            filepath (list|str): A filepath or list of filepaths corresponding
                to the filepath field of the database Song table.
            title (list|str): A title or list of titles corresponding to the
                title field of the database Song table.
            youtube_id (list|str): A YouTube id or list of YouTube ids
                corresponding to the youtube_id field of the databse Song
                table.
            include_fingerprints (bool): Include the fingerprints of each
                song as a list within the dict corresponding to the song; see
                :meth:`query_fingerprints`.

        Returns:
            results: List[dict]
                A list of dicts where each dict represents a song and contains
                the following keys::

                    {
                        "id": int,
                        "duration": float,
                        "filehash": str,
                        "filepath": str,
                        "title": str,
                        "youtube_id" str,
                        "fingerprints": list[dict],
                        "num_fingerprints": int
                    }

                The ``fingerprints`` and ``num_fingerprints`` keys are only
                included if ``include_fingerprints=True``.

        Raises:
            ValueError: if more than one of ``duration``,
            ``duration_greater_than``, or ``duration_less_than`` are supplied.
        """
        duration_args_bool = [
            duration is not None, duration_greater_than is not None,
            duration_less_than is not None
        ]

        if sum(duration_args_bool) > 1:
            raise ValueError(
                "Can only choose one of duration, duration_greater_than, "
                "or duration_less_than"
            )

        query = self.session.query(Song)

        if duration is not None:
            query = query.filter(Song.duration == duration)
        elif duration_greater_than is not None:
            query = query.filter(Song.duration > duration_greater_than)
        elif duration_less_than is not None:
            query = query.filter(Song.duration < duration_less_than)

        # Handle remaining non-duration args separately.
        other_args = {
            "id": id_,
            "filehash": filehash,
            "filepath": filepath,
            "title": title,
            "youtube_id": youtube_id,
        }

        # Make the Song sqlalchemy DeclarativeMeta a dict so we can iterate
        # over its attributes.
        Song_ = vars(Song)

        for arg, val in other_args.items():
            if val is not None:
                if not isinstance(val, (list, tuple)):
                    val = [val]
                query = query.filter(Song_[arg].in_(val))
        return database_obj_to_py(
            query.all(), fingerprints_in_song=include_fingerprints
        )
