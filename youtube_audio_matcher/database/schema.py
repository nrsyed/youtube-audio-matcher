from sqlalchemy import (
    Column, Float, ForeignKey, Integer, MetaData, String, Table,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

Base = declarative_base()

class Song(Base):
    __tablename__ = "song"

    id = Column("id", Integer, primary_key=True)
    duration = Column("duration", Float)
    filepath = Column("filepath", String)
    filehash = Column("filehash", String)
    title = Column("title", String)
    youtube_id = Column("youtube_id", String(10))

    # One-to-many mapping of audio file to all its associated fingerprints.
    fingerprints = relationship("Fingerprint")


class Fingerprint(Base):
    __tablename__ = "fingerprint"

    id = Column("id", Integer, primary_key=True)
    song_id = Column("song_id", ForeignKey("song.id"), nullable=False)
    hash = Column("hash", String, nullable=False)
    offset = Column("offset", Float, nullable=False)
    UniqueConstraint("song_id", "hash", "offset")
