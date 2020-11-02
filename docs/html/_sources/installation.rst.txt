Setup and Installation
======================

Requirements
------------

* Python ≥ 3.6
* `Chromium <https://www.chromium.org>`_ or
  `Google Chrome <https://www.google.com/chrome/>`_ browser, and
  `ChromeDriver <http://chromedriver.chromium.org/home>`_
* `FFmpeg <https://ffmpeg.org/download.html>`_
* PostgreSQL or MySQL client/driver; see list of
  `SQLAlchemy–supported drivers/backends
  <https://docs.sqlalchemy.org/en/13/core/engines.html>`_


Installation
------------

First, install the Python package.

.. code:: bash

  git clone https://github.com/nrsyed/youtube-audio-matcher.git
  cd youtube-audio-matcher
  pip install .

Next, install a PostgreSQL or MySQL client and development files. These must
be installed before the SQL driver is installed with ``pip``, as the
``pip install`` requires them to build the relevant Python packages. Example
instructions for installing PostgreSQL/psycopg2 and MySQL/mysqlclient on Ubuntu
are shown below.

**PostgreSQL and psycopg2**

.. code:: bash

  sudo apt install libpq-dev
  pip install psycopg2


**MySQL and mysqlclient**

.. code:: bash

  sudo apt install libmysqlclient-dev mysql-client-core-8.0
  pip install mysqlclient
