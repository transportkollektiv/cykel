# Cykel

Basic backend for a mobility sharing service. First steps made at [CCCamp 2019](https://events.ccc.de/camp/2019/wiki/Main_Page), now developed, daily used and tested in [the City of Ulm](https://ulm.dev/projects/openbike/).

## Prerequisites

* Python (≥3.7)
* A database that supports GIS extensions, for example PostGIS.

### Configuration

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
# set the full URL to the frontend
UI_SITE_URL=http://lvh.me:1234/
# CORS origins to whitelist, i.e. the frontend URL (with scheme, without path)
CORS_ORIGIN_WHITELIST=http://lvh.me:1234
# Set to true if cykel runs behind a reverse proxy, so the `X-Forwarded-Proto` header gets interpreted and URLs are built correctly with https
USE_X_FORWARDED_PROTO=true
```

Install the required packages using `pip install -r requirements.txt`. It is recommended to use a virtualenv with your choice of tool, e.g. `pipenv`, in which case you can run `pipenv install` (and `pipenv shell` or prefix `pipenv run` to run commands).

Then run `manage.py migrate` to create the database tables.

### Database configuration for PostgreSQL/PostGIS

You need to enable the following extensions in the cykel database after installing PostGIS:

```
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```

The DB migration will fail otherwise.

## Running the local server

Run `manage.py runserver`.

### Configuring authentication

For the administration interface you can run `manage.py createsuperuser` to create an user with administrative rights and access the interface at `http://localhost:8080/admin`.

Then, visit `/admin/` and edit the URL of the first Website (`/admin/sites/site/1/change/`).

### Configuring OAuth

Visit `/admin/socialaccount/socialapp/add/` (Add Social Application).

For example, for GitHub select "Provider: GitHub", "Name: github", the Client-Id and Secret are shown in the OAuth application creation process at GitHub.

When you create an OAuth2-Application at a provider, you need to enter a callback URL. This URL is in the format `https://<host>/auth/<name>/login/callback/`.

## Update bike location

For updating the current bike location we provide the `/api/bike/updatelocation` endpoint.

One project which can use this together with TheThingsNetwork is the [`cykel-ttn`](https://github.com/stadtulm/cykel-ttn) adapter. Read the readme in the repository on how to use it - for authentication you need to add a new api key at `/admin/rest_framework_api_key/apikey/`.


## Alternative: using Docker Compose

```
docker-compose pull
docker-compose up -d --build
```

To run the `migrate.py` commands that are shown above, prefix them with `docker-compose exec cykel`:

```
docker-compose exec cykel python manage.py migrate
docker-compose exec cykel python manage.py createsuperuser
```

To use other settings (like `ALLOWED_HOSTS`) from above, add them to the `environment` in `docker-compose.yml`.

Docker Compose runs cykel and [voorwiel](https://github.com/stadtulm/voorwiel) (one frontend implementation), so you can develop and test with a client right away.


## Contributing

We welcome [issues](https://github.com/stadtulm/cykel/issues) and pull requests for new features, bugs or problems you encountered when setting it up. More Documentation or simply small typo fixes are also very appreciated. If you found a vulnerability or other security relevant issue, notify us at `openbike @ ulm.dev`

For general discussion, feel free to hop into the [public matrix channel](https://matrix.to/#/!ghOLficeAycydtkZtA:matrix.org?via=matrix.org) for openbike and related projects.

Generally, the cykel python/django code follows [PEP8](https://www.python.org/dev/peps/pep-0008/). We're using `flake8`, `isort`,
`black` and `docformatter` as style checkers, so those can help you if you're not sure how to format something.

You can run them all at once using `make style`.

### Tests

To get stated with tests, you need to install the development dependencies: `pip install -r requirements-dev.txt`

If you want to run them on your machine, use `pytest`. Tests are also automatically run for pull requests.

`make` will also run all tests.
