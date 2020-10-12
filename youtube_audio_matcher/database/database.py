import sqlalchemy
from schema import Audio, Base, Fingerprint


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

    def _drop_tables(self, tables):
        self.base.metadata.drop_all(bind=self.engine, tables=tables)

    def drop_all_tables(self):
        self._drop_tables([Audio.__table__, Fingerprint.__table__])

    def drop_audio_table(self):
        self._drop_tables([Audio.__table__])

    def drop_fingerprint_table(self):
        self._drop_tables([Fingerprint.__table__])


if __name__ == "__main__":
    db = Database("yam", "yam", "yam")
