# Galactic Conflict API

A deliberately imperfect Star Wars API designed for API automated-testing practice.

## Run it

```bash
uv run uvicorn main:app --reload
```

Open Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The OpenAPI schema is available at `/openapi.json`.

SQLite data is stored locally in `star_wars.db`; it is created and seeded on first start.

### Reset the database

The seed routine records its first successful run in the database. This means it runs exactly once for a brand-new database; restarting the API never overwrites, duplicates, or restores records you created during testing—even if you later delete all planets.

To reset back to the original seeded scenario, stop the server, remove the local database, then start it again:

```bash
rm star_wars.db
uv run uvicorn main:app --reload
```

The API recreates the SQLite schema and loads the seed records only on that first startup. Do not run this command while the server is running.

## Tests

```bash
uv run pytest
```

The integration suite uses an isolated in-memory SQLite database for each test. Healthy-path tests pass; defect tests assert the intended API contract and deliberately fail until the corresponding bug is fixed. This red state is expected for the QA exercise.

## Useful endpoints

- `GET /health`
- `GET` and `POST /planets`
- `GET`, `POST`, `GET /{id}`, `PATCH /{id}`, and `DELETE /{id}` for `/characters`
- `GET` and `POST /missions`
- `PATCH /missions/{id}/status`
- `GET`, `POST`, and `GET /{id}` for `/starships`
- `PATCH /starships/{id}/fuel?level=N`
