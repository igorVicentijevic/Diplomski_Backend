import asyncio
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.articles.models.ArticleModel import ArticleModel
from app.articles.seed import SEED_ARTICLES
from app.database.Base import Base
from app.database.session import get_session
from app.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def test_database(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    database_path: Path = tmp_path_factory.mktemp("database") / "test.db"
    database_url = URL.create(
        drivername="sqlite+aiosqlite",
        database=str(database_path),
    )
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async def prepare_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with session_factory() as session:
            session.add_all(
                ArticleModel(**article) for article in SEED_ARTICLES
            )
            await session.commit()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(prepare_database())
    app.dependency_overrides[get_session] = override_get_session

    yield

    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_articles() -> None:
    response = client.get("/api/articles")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["articles"]) == 2
    assert payload["articles"][0] == {
        "id": "article-1",
        "title": "Prva vest",
        "summary": "Privremeni clanak za prvu iteraciju Articles API-ja.",
        "source": "Demo izvor",
        "category": "SERBIA",
        "publishedAt": "2026-09-23T18:00:00Z",
        "imageUrl": None,
        "articleUrl": "https://example.com/articles/1",
        "relatedCityIds": ["beograd"],
    }


def test_get_article() -> None:
    response = client.get("/api/articles/article-2")

    assert response.status_code == 200
    assert response.json()["id"] == "article-2"


def test_get_missing_article() -> None:
    response = client.get("/api/articles/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}
