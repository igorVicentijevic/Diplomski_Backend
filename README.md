# News Aggregator Backend

FastAPI backend with PostgreSQL persistence.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
docker compose up -d database
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at
`http://127.0.0.1:8000/docs`.

Available endpoints:

- `GET /`
- `GET /health`
- `GET /api/articles`
- `GET /api/articles/{article_id}`

The frontend API contract is documented in
[`docs/API_CONTRACT_V1.md`](docs/API_CONTRACT_V1.md).

Run tests with:

```powershell
pytest
```

Tests use an isolated temporary SQLite database and do not require the
PostgreSQL container.

## Database commands

Create a migration after changing SQLAlchemy models:

```powershell
alembic revision --autogenerate -m "Describe the schema change"
```

Apply all migrations:

```powershell
alembic upgrade head
```

Seed development articles:

```powershell
python -m app.seed
```
