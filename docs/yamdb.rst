yamdb
=====

The **Y**\ outube **A**\ udio **M**\ atcher **D**\ ata\ **b**\ ase
command line tool ``yamdb`` enables simple user interaction with the
SQL database that contains songs and fingerprints. Refer to
:doc:`youtube_audio_matcher.database` for more information on supported SQL
dialects/drivers.

Usage
-----

.. code-block:: none

  usage: yamdb [-h] [-N <database_name>] [-C <dialect>] [-R <driver>]
               [-H <host>] [-P <password>] [-O <port>] [-U <username>]
               [-d | -r | -o <path> | -s]

  optional arguments:
    -h, --help            show this help message and exit

  database arguments:
    -N <database_name>, --db-name <database_name>
                          Database name (default: yam)
    -C <dialect>, --dialect <dialect>
                          SQL dialect (default: postgresql)
    -R <driver>, --driver <driver>
                          SQL dialect driver (default: None)
    -H <host>, --host <host>
                          Database hostname (default: localhost)
    -P <password>, --password <password>
                          Database password (default: None)
    -O <port>, --port <port>
                          Database port number (default: None)
    -U <username>, --user <username>
                          Database user name (default: None)

  actions:
    -d, --delete          Delete all rows (default: False)
    -r, --drop            Drop all tables (default: False)
    -o <path>, --output <path>
                          Write the contents of the database to an output file
                          as JSON (default: None)
    -s, --songs           Print a list of songs in the database (default: False)

Examples
--------

To print all songs in the database as a JSON-formatted list, use the
``-s``/``--songs`` switch. This is demonstrated by the following sample command
and its terminal output, assuming the database name, username, and password are
all ``yam``.

*Command*

.. code-block:: bash

  yamdb -s -U yam -N yam -P yam


*Output*

.. code-block:: none

  [
    {
      "id": 3,
      "duration": 155.0,
      "filehash": "6ba1139a7fc8cde33ff30065b45ed3c9f457f5a6",
      "filepath": "/home/a92_Uxy5mq.mp3",
      "title": "Some other video on youtube",
      "youtube_id": "a92_Uxy5mq",
    },
    {
      "id": 8,
      "duration": 436.0,
      "filehash": "c12b119ab98caee4a24eef5e7b3f4d7bf2b38f99",
      "filepath": "/home/song2.mp3",
      "title": null,
      "youtube_id": null,
    }
  ]


The database can also be reset using the ``-d``/``--delete`` switch (which
retains the database schema/tables but deletes all rows in the ``song`` and
``fingerprint`` tables) or the ``-r``/``--drop`` switch (which drops the
``song`` and ``fingerprint`` tables altogether), as demonstrated in the
following examples:

.. code:: bash

  yamdb -U yam -N yam -P yam -d

.. code:: bash

  yamdb -U yam -N yam -P yam -r
