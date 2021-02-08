# JournalsDB API

This is the API for [JournalsDB](http://journalsdb.org/).

## Developer Instructions

### Setup

1. `pip install -f requirements.txt`
2. Set `DATABASE_URL` environment variable to point to a postgresql database
3. Build database with command `flask db upgrade`
4. Ingest initial data by running `flask import_issns`, followed by `flask import_issn_apis` (second command takes 6+ hours for initial load)

### Ingest data

Ingest data using [flask CLI commands](https://flask.palletsprojects.com/en/1.1.x/cli/#custom-commands). All ingest functions are stored in the `/ingest` directory.

To see a list of available cli commands:

```bash
$ flask
Commands:
  db                         Perform database migrations.
  import_author_permissions  Google sheet from...
  import_extension_requests  Extension requests:...
  import_issn_apis           Iterate over issn_metadata table, then fetch...
  import_issns               Master ISSN list:...
  import_open_access         Open access data:...
  import_repositories        Repository article counts:...
```

### Database Migrations

Migrations are managed with [flask-migrate](https://flask-migrate.readthedocs.io/en/latest/).

Run the migration files to build the database:

```bash
$ flask db upgrade
```

View current migration status with:

```bash
$ flask db current
```

To create migrations for changed models:

```bash
$ flask db migrate -m "Add title field"
```

### CORS

CORS is enabled for the entire project via [flask-CORS](https://flask-cors.readthedocs.io/en/latest/).

### Code Formatting

All code is formatted with [black](https://github.com/psf/black).

```bash
$ black .
```

### Tests

You must point to a local postgresql database for testing, as sqlite does not support jsonb columsn. 
The default name is `journalsdb_test`.

Run tests with:

```bash
$ pytest
```