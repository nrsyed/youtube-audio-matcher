from collections import defaultdict

import sqlalchemy

from .schema import Base, Fingerprint, Song


class Database:
    def __init__(
        self, user, password, db_name, host="localhost", backend="postgres"
    ):
        """
        Args:
            user (str): User name.
            password (str): User password.
            db_name (str): Database name.
            host (str): Database hostname.
            backend (str): {"postgres"} SQL database backend to use.
        """

        if backend == "postgres":
            engine_str = f"postgresql://{user}:{password}@{host}/{db_name}"

        engine = sqlalchemy.create_engine(engine_str)
        Session = sqlalchemy.orm.sessionmaker(engine)
        self.session = Session()

        Base.metadata.create_all(engine)
        self.base = Base
        self.engine = engine

    def __del__(self):
        self.session.close()

    def add_song(self, attributes):
        """
        Args:
            attributes (dict): A dict containing the database Song table
                attributes for the audio file to be inserted:
                    {
                        "duration": float,
                        "filepath": str,
                        "filehash": str,
                        "title": str,
                        "youtube_id": str
                    }

        Returns:
            int: id of the inserted song.
        """
        new_song = Song(**attributes)
        self.session.add(new_song)
        self.session.commit()
        return new_song.id

    def add_fingerprint(self, attributes):
        """
        Args:
            attributes (dict): A dict containing the database Fingerprint table
                attributes for the fingerprint to be inserted:
                    {
                        "song_id": int,
                        "hash": str,
                        "offset": float
                    }
                The "song_id" value should correspond to the id of an audio
                file in the Song table.

        Returns:
            int: id of the inserted fingerprint.
        """
        new_fingerprint = Fingerprint(**attributes)
        self.session.add(new_fingerprint)
        self.session.commit()
        return new_fingerprint.id

    def add_fingerprints(self, fingerprints):
        """
        TODO
        """
        new_fingerprints = [Fingerprint(**attrs) for attrs in fingerprints]
        self.session.bulk_save_objects(new_fingerprints)
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

    def match_fingerprint(self, hashes, offsets):
        """
        Args:
            hashes (str|List[str]): Hash or list of hashes from a
                fingerprinted audio signal.
            offsets (float|List[float]): Offset or list of offsets
                corresponding to each hash in `hashes`.
        """
        if not isinstance(hashes, list):
            hashes = [hashes]

        if not isinstance(offsets, list):
            offsets = [offsets]

        # Map input hashes to their offsets.
        inp_hash_to_offset = {
            hash_: offset for hash_, offset in zip(hashes, offsets)
        }

        # Perform query; this is the equivalent of
        # SELECT * FROM fingerprint WHERE fingerprint.hash IN (`hashes`)
        query = self.session.query(Fingerprint).filter(
            Fingerprint.hash.in_(hashes)
        )

        # Compute relative offsets, mapping each relative offset to song ids;
        # map each song id to an int representing the number of matching
        # hashes. Simultaneously keep track of the total number of matches
        # across all song ids for each relative offset.
        map_ = defaultdict(lambda: defaultdict(int))
        matches_per_rel_offset = defaultdict(int)

        for result in query:
            hash_ = result.hash

            inp_offset = inp_hash_to_offset[hash_]
            abs_offset = result.offset
            rel_offset = int(abs_offset - inp_offset)
            song_id = result.song_id

            map_[rel_offset][song_id] += 1
            matches_per_rel_offset[rel_offset] += 1

        if map_:
            # Only consider the relative offset with the most matches.
            max_matches = -1
            max_matches_rel_offset = None
            for rel_offset, num_matches in matches_per_rel_offset.items():
                if num_matches > max_matches:
                    max_matches = num_matches
                    max_matches_rel_offset = rel_offset

            # Find the song id with the most matches of that relative offset.
            max_matches = -1
            max_matches_song_id = None
            for song_id, num_matches in map_[max_matches_rel_offset].items():
                if num_matches > max_matches:
                    max_matches = num_matches
                    max_matches_song_id = song_id

            # Use the song id to fetch the corresponding song information from
            # the database.
            query = self.session.query(Song).filter(
                Song.id == max_matches_song_id
            )
            match = query.first()

            return {
                "id": match.id,
                "duration": match.duration,
                "filepath": match.filepath,
                "filehash": match.filehash,
                "title": match.title,
                "youtube_id": match.youtube_id,
                "num_matches": max_matches,
            }

        return None

    def query_songs(
        self, id_=None, duration=None, duration_greater_than=None,
        duration_less_than=None, filehash=None, filepath=None, title=None,
        youtube_id=None
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
                query = query.filter(Song_[arg].in_(list(val)))
        return query.all()

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

        def _fingerprints_to_python(obj_list):
            return [
                {"song_id": fp.song_id, "hash": fp.hash, "offset": fp.offset}
                for fp in obj_list
            ]

        dict_ = {"songs": []}

        for song_obj in songs_table:
            song = {
                "id": song_obj.id,
                "duration": song_obj.duration,
                "filehash": song_obj.filehash,
                "filepath": song_obj.filepath,
                "title": song_obj.title,
                "youtube_id": song_obj.youtube_id,
            }

            if combine_tables:
                song["fingerprints"] = _fingerprints_to_python(
                    song_obj.fingerprints
                )
            dict_["songs"].append(song)

        if not combine_tables:
            dict_["fingerprints"] = _fingerprints_to_python(fingerprints_table)

        return dict_
