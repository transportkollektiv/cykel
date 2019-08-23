# Cykel

Basic backend for a mobility sharing service. Used on [CCCamp2019](https://events.ccc.de/camp/2019/wiki/Main_Page).

## Prerequisites

* Python (≥3.7)
* A database that supports GIS extensions, for example PostGIS or SpatiaLite

Create a file `.env` in the `cykel` subdirectory, with the following contents:

```
# insert your own random string here
SECRET_KEY=f2bf0a4e621a16d9eb8253aa7a540f75ed8787b5
# set to 1 to enable DEBUG output, or 0 to disable
DEBUG=1
# configure your database in a format supported by https://github.com/jacobian/dj-database-url
DATABASE_URL=spatialite:///cykel.sqlite
# it is recommended to use a DNS alias for localhost, instead of "localhost", for CORS reasons
ALLOWED_HOSTS=lvh.me,localhost
```

Install the required packages using `pip install -r requirements.txt`. It is recommended to use a virtualenv with your choice of tool, e.g. `pipenv`, in which case you can run `pipenv install` (and `pipenv shell` or prefix `pipenv run` to run commands).

Then run `manage.py migrate` to create the database tables.

## Running the local server

Run `manage.py runserver`.
