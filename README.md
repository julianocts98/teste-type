# Galactic Conflict API

A deliberately imperfect Star Wars API designed for API automated-testing practice.

## Run it

```bash
uv run uvicorn main:app --reload
```

Open Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The OpenAPI schema is available at `/openapi.json`.

SQLite data is stored locally in `star_wars.db`; it is created and seeded on first start.

## Tests

```bash
uv run pytest
```

The integration suite uses an isolated in-memory SQLite database for each test. It verifies normal API paths and makes the intentional defects explicit as `known_bug` tests.

## Useful endpoints

- `GET /health`
- `GET` and `POST /planets`
- `GET`, `POST`, `GET /{id}`, `PATCH /{id}`, and `DELETE /{id}` for `/characters`
- `GET` and `POST /missions`
- `PATCH /missions/{id}/status`

See [INTENTIONAL_BUGS.md](INTENTIONAL_BUGS.md) after testing for the answer key.
