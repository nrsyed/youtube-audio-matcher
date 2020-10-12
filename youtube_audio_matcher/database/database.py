import sqlalchemy
from sqlalchemy import (
    Column, Float, ForeignKey, Integer, MetaData, String, Table
)


def get_db_string(
    user, password, db_name, host="localhost", backend="postgres"
):
    if backend == "postgres":
        #db_str = f"postgresql+psycopg2://{user}:{password}@{host}/{db_name}"
        db_str = f"postgresql://{user}:{password}@{host}/{db_name}"
    return db_str

if __name__ == "__main__":
    db_str = get_db_string("yam", "yam", "yam")
    db = sqlalchemy.create_engine(db_str)
    metadata = MetaData(db)

    audio_table = Table(
        "audio", metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String),
        Column("youtube_id", String(10)),
        Column("duration", Float),
    )
    audio_table.create()

    fingerprint_table = Table(
        "fingerprint", metadata,
        Column("id", Integer, primary_key=True),
        Column("hash", String(20), nullable=False),
        Column("offset", Float, nullable=False),
        Column("audio_id", ForeignKey("audio.id"), nullable=False),
    )
    fingerprint_table.create()

    breakpoint()
