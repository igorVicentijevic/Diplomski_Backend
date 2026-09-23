# News Aggregator Backend

Minimal FastAPI backend.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with interactive documentation at
`http://127.0.0.1:8000/docs`.

Available endpoints:

- `GET /`
- `GET /health`
- `GET /api/v1/articles`
- `GET /api/v1/articles/{article_id}`

Run tests with:

```powershell
pytest
```
