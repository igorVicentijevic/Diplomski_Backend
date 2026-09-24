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
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at
`http://127.0.0.1:8000/docs`.

When the API starts, it immediately reads the RTS news RSS feed and stores
new or changed articles in PostgreSQL. The feed is checked again every 15
minutes while the API process is running.

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

## Tone analysis

Tone analysis uses the random strategy by default. Configure it in `.env`:

```env
TONE_ANALYSIS_PROVIDER=random
TONE_ANALYSIS_PROMPT_VERSION=v1
```

To use Groq:

```env
GROQ_API_KEY=gsk_your_api_key
TONE_ANALYSIS_PROVIDER=groq
TONE_ANALYSIS_MODEL=openai/gpt-oss-20b
TONE_ANALYSIS_PROMPT_VERSION=v1
TONE_ANALYSIS_TIMEOUT_SECONDS=30
TONE_ANALYSIS_MAX_RETRIES=2
```

The application fails during startup when Groq is selected without an API
key. Existing tone analysis is reused while the article input, provider,
model, and prompt version remain unchanged.

## Database commands

Create a migration after changing SQLAlchemy models:

```powershell
alembic revision --autogenerate -m "Describe the schema change"
```

Apply all migrations:

```powershell
alembic upgrade head
```
