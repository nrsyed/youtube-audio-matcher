yamdb
=====

YAM database tool

Usage
-----

.. code-block:: bash

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
