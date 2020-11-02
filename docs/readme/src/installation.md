First, install the Python package.

```
git clone https://github.com/nrsyed/youtube-audio-matcher.git
cd youtube-audio-matcher
pip install .
```

Next, install a PostgreSQL or MySQL client and development files. These must
be installed before the SQL driver is installed with `pip`, as the
`pip install` requires them to build the relevant Python packages. Example
instructions for installing PostgreSQL/psycopg2 and MySQL/mysqlclient on Ubuntu
are shown below.

**PostgreSQL and psycopg2**
```
sudo apt install libpq-dev
pip install psycopg2
```

**MySQL and mysqlclient**
```
sudo apt install libmysqlclient-dev mysql-client-core-8.0
pip install mysqlclient
```
