youtube\_audio\_matcher.database
================================

The database module utilizes  the `SQLAlchemy <https://www.sqlalchemy.org/>`_
ORM to abstract away the details of SQL operations, enabling the module to be
written purely in Python and to support a variety of SQL backends. YouTube
Audio Matcher has only been tested with PostgreSQL/psycopg2 and
MySQL/mysqlclient, but should work with any SQL dialect and driver that allow
multiple read/write database connections.

Module contents
---------------

.. automodule:: youtube_audio_matcher.database
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: Fingerprint, Song

.. autoclass:: youtube_audio_matcher.database.Fingerprint
  :members:
  :show-inheritance:

.. autoclass:: youtube_audio_matcher.database.Song
  :members:
  :show-inheritance:
