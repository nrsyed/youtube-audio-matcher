from collections import defaultdict

import sqlalchemy

from .schema import Audio, Base, Fingerprint


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

    def add_audio_file(self, attributes):
        """
        Args:
            attributes (dict): A dict containing the database Audio table
                attributes for the audio file to be inserted:
                    {
                        "duration": float,
                        "filepath": str,
                        "filehash": str,
                        "title": str,
                        "youtube_id": str
                    }

        Returns:
            int: id of the inserted audio file.
        """
        new_audio = Audio(**attributes)
        self.session.add(new_audio)
        self.session.commit()
        return new_audio.id

    def add_fingerprint(self, attributes):
        """
        Args:
            attributes (dict): A dict containing the database Fingerprint table
                attributes for the fingerprint to be inserted:
                    {
                        "audio_id": int,
                        "hash": str,
                        "offset": float
                    }
                The "audio_id" value should correspond to the id of an audio
                file in the Audio table.

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
        self._drop_tables([Audio.__table__, Fingerprint.__table__])

    def drop_audio_table(self):
        self._drop_tables([Audio.__table__])

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

        # Compute relative offsets, mapping each relative offset to audio ids;
        # map each audio id to an int representing the number of matching
        # hashes. Simultaneously keep track of the total number of matches
        # across all audio ids for each relative offset.
        map_ = defaultdict(lambda: defaultdict(int))
        matches_per_rel_offset = defaultdict(int)

        for result in query:
            hash_ = result.hash

            inp_offset = inp_hash_to_offset[hash_]
            abs_offset = result.offset
            rel_offset = int(abs_offset - inp_offset)
            audio_id = result.audio_id

            map_[rel_offset][audio_id] += 1
            matches_per_rel_offset[rel_offset] += 1

        if map_:
            # Only consider the relative offset with the most matches.
            max_matches = -1
            max_matches_rel_offset = None
            for rel_offset, num_matches in matches_per_rel_offset.items():
                if num_matches > max_matches:
                    max_matches = num_matches
                    max_matches_rel_offset = rel_offset

            # Find the audio/song id with the most matches of that relative
            # offset.
            max_matches = -1
            max_matches_audio_id = None
            for audio_id, num_matches in map_[max_matches_rel_offset].items():
                if num_matches > max_matches:
                    max_matches = num_matches
                    max_matches_audio_id = audio_id

            # Use the audio id to fetch the corresponding audio/song
            # information from the database.
            query = self.session.query(Audio).filter(
                Audio.id == max_matches_audio_id
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
