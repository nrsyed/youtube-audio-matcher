from sqlalchemy import (
    Column, Float, ForeignKey, Integer, String, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Fingerprint(Base):
    """
    SQLAlchemy class representing database ``fingerprint`` table schema.

    Attributes:
        id (int): ``fingerprint`` table primary key.
        hash (str): SHA1 hash.
        offset (float): Fingerprint offset from beginning of file in seconds.
        song_id (int): Song id from the ``song`` table (:class:`Song`) to which
            this fingerprint belongs.

    .. note::
        There is a `UNIQUE constraint`_  on the combination of
        (``song_id``, ``hash``, ``offset``) keys.

    .. _`UNIQUE constraint`:
        https://docs.sqlalchemy.org/en/13/core/constraints.html#unique-constraint
    """
    __tablename__ = "fingerprint"

    id = Column("id", Integer, primary_key=True)
    song_id = Column("song_id", ForeignKey("song.id"), nullable=False)

    # Indexable String requires a max length to be set. We set it to 40 since
    # this is the max length of a SHA1 hash.
    hash = Column("hash", String(40), nullable=False, index=True)
    offset = Column("offset", Float, nullable=False)
    UniqueConstraint("song_id", "hash", "offset")


class Song(Base):
    """
    SQLAlchemy class representing database ``song`` table schema.

    Attributes:
        id (int): ``song`` table primary key.
        duration (float): Song duration in seconds.
        filehash (str): SHA1 hash of the file.
        filepath (str): Path to the song file on local machine.
        title (str): Song title.
        youtube_id (str): The YouTube id of the song (if the song was
            downloaded from YouTube).

        fingerprints (List[Fingerprint]): A list of fingerprints (Fingerprint
            objects) belonging to this song.
    """
    __tablename__ = "song"

    id = Column("id", Integer, primary_key=True)
    duration = Column("duration", Float)
    filepath = Column("filepath", String)
    filehash = Column("filehash", String)
    title = Column("title", String)
    youtube_id = Column("youtube_id", String)

    # One-to-many mapping of audio file to all its associated fingerprints.
    fingerprints = relationship("Fingerprint")
