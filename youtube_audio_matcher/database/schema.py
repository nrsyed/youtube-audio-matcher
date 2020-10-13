from sqlalchemy import (
    Column, Float, ForeignKey, Integer, MetaData, String, Table,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Audio(Base):
    __tablename__ = "audio"

    id = Column("id", Integer, primary_key=True)
    duration = Column("duration", Float)
    filepath = Column("filepath", String)
    filehash = Column("filehash", String)
    title = Column("title", String)
    youtube_id = Column("youtube_id", String(10))


class Fingerprint(Base):
    __tablename__ = "fingerprint"

    id = Column("id", Integer, primary_key=True)
    audio_id = Column("audio_id", ForeignKey("audio.id"), nullable=False)
    hash = Column("hash", String(20), nullable=False)
    offset = Column("offset", Integer, nullable=False)
    UniqueConstraint("audio_id", "hash", "offset")
