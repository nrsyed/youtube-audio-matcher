import asyncio
import logging
import time

import sqlalchemy
from sqlalchemy.pool import NullPool

from .schema import Base, Fingerprint, Song


def database_obj_to_py(obj, fingerprints_in_song=False):
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
            song["fingerprints"] = [database_obj_to_py(fp) for fp in obj.fingerprints]
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
        youtube_id=song.get("id")
    )
    db.add_fingerprints(song_id, song["fingerprints"])
    del db
    del song["fingerprints"]


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
# TODO: handle delete after
async def update_database(loop, executor, db_kwargs, in_queue):
    start_t = time.time()
    tasks = []
    while True:
        song = await in_queue.get()
        if song is None:
            break

        task = loop.create_task(_update_database(song, loop, executor, db_kwargs))
        tasks.append(task)

    # Wrap asyncio.wait() in if statement to avoid ValueError if no tasks.
    if tasks:
        await asyncio.wait(tasks)
    elapsed = time.time() - start_t
    logging.info(f"All songs added to database ({elapsed:.2f} s)")


# TODO: try/except, db rollbacks
class Database:
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
        # Construct database URL.
        # TODO: check/add sqlite support.

        driver = f"+{driver}" if driver else ""
        port = f":{port}" if port is not None else ""
        url = f"{dialect}{driver}://{user}:{password}@{host}{port}/{db_name}"

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
        Return the database as a Python dictionary.

        Args:
            combine_tables (bool): If True, the returned dict will have a
                single ``songs`` field containing a list of songs, and each
                song will have a ``fingerprints`` field containing the list
                of fingerprints belonging to it. If False, the returned dict
                will contain a ``songs`` field and a ``fingerprints`` field.

        Returns:
            dict: tables
        """
        songs_table = self.session.query(Song).all()
        fingerprints_table = self.session.query(Fingerprint).all()

        if combine_tables:
            return {
                "songs": database_obj_to_py(songs_table, fingerprints_in_song=True),
            }
        else:
            return {
                "songs": database_obj_to_py(songs_table),
                "fingerprints": database_obj_to_py(fingerprints_table),
            }

    def delete_all(self):
        self.session.query(Fingerprint).delete()
        self.session.query(Song).delete()
        self.session.commit()

    def _drop_tables(self, tables):
        self.base.metadata.drop_all(bind=self.engine, tables=tables)
        self.session.commit()

    def drop_all_tables(self):
        self._drop_tables([Fingerprint.__table__, Song.__table__])

    def drop_song_table(self):
        self._drop_tables([Song.__table__])

    def drop_fingerprint_table(self):
        self._drop_tables([Fingerprint.__table__])

    def query_fingerprints(self, hashes):
        """
        Args:
            hashes (str|List[str]): Hash or list of hashes from a
                fingerprinted audio signal.
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
        TODO
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
