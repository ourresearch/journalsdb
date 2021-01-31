# JournalsDB API

This is the API for JournalsDB.

## Developer Instructions

### Setup

1. `pip install -f requirements.txt`
2. Set `DATABASE_URL` environment variable to point to postgresql database
3. Ingest data

### Ingest data

Ingest data using [flask CLI commands](https://flask.palletsprojects.com/en/1.1.x/cli/#custom-commands). All ingest functions are stored in the `/ingest` directory.

To see a list of available cli commands:

```bash
$ flask
Commands:
  db                         Perform database migrations.
  import_extension_requests  Extension requests:...
  import_journals            Journal metadata:...
  import_open_access         Open access data:...
  import_permissions         Google sheet from...
  import_repositories        Repository article counts:...
```

Run a command:

```bash
$ flask import_journals
```

Most data is imported from hosted CSV files using [Pandas `read_csv`](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html).

### CORS

CORS is enabled for the entire project via [flask-CORS](https://flask-cors.readthedocs.io/en/latest/).

### Code Formatting

All code is formatted with [black](https://github.com/psf/black).

```bash
$ black .
```

### Tests

Run tests with:

```bash
$ pytest
```

You must point to a local postgresql database for testing, as sqlite does not support jsonb columsn.

### Database Migrations

Migrations are managed with [flask-migrate](https://flask-migrate.readthedocs.io/en/latest/).

View current migration status with:

```bash
$ flask db current
```

Add or remove models, then:

1. Create a new migration file

```bash
$ flask db migrate -m "Add title field"
```

2. Run the migration file
```bash
$ flask db upgrade
```