import asyncio
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel
from app.articles.models.ArticleModel import ArticleModel
from app.articles.models.ArticleToneAnalysisModel import (
    ArticleToneAnalysisModel,
)
from app.database.Base import Base
from app.database.session import get_session
from app.main import app
from app.semantic_grouping.models.ArticleGroupMembershipModel import (
    ArticleGroupMembershipModel,
)
from app.semantic_grouping.models.ArticleGroupModel import ArticleGroupModel
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
)
from app.semantic_grouping.models.SemanticGroupingRunModel import (
    SemanticGroupingRunModel,
)

client = TestClient(app)

TEST_ARTICLES = (
    {
        "id": "article-1",
        "source_id": "demo",
        "title": "Prva vest",
        "summary": "Privremeni clanak za prvu iteraciju Articles API-ja.",
        "source": "Demo izvor",
        "category": "SERBIA",
        "published_at": datetime(2026, 9, 23, 18, 0, tzinfo=UTC),
        "image_url": None,
        "article_url": "https://example.com/articles/1",
        "normalized_url": "https://example.com/articles/1",
        "related_city_ids": ["beograd"],
    },
    {
        "id": "article-2",
        "source_id": "demo",
        "title": "Nova tehnoloska vest",
        "summary": "Drugi privremeni clanak za proveru liste.",
        "source": "Demo izvor",
        "category": "TECHNOLOGY",
        "published_at": datetime(
            2026,
            9,
            23,
            17,
            30,
            tzinfo=UTC,
        ),
        "image_url": "https://example.com/images/2.jpg",
        "article_url": "https://example.com/articles/2",
        "normalized_url": "https://example.com/articles/2",
        "related_city_ids": [],
    },
    {
        "id": "inactive-article",
        "source_id": "demo",
        "title": "Stara vest",
        "summary": "Vest vise nije prisutna u RSS feedu.",
        "source": "Demo izvor",
        "category": "SERBIA",
        "published_at": datetime(
            2026,
            9,
            23,
            16,
            0,
            tzinfo=UTC,
        ),
        "image_url": None,
        "article_url": "https://example.com/articles/inactive",
        "normalized_url": "https://example.com/articles/inactive",
        "related_city_ids": [],
        "is_active": False,
    },
)

TEST_ANALYSES = (
    {
        "article_id": "article-1",
        "negative_percentage": 15.0,
        "positive_percentage": 25.0,
        "neutral_percentage": 60.0,
    },
    {
        "article_id": "article-2",
        "negative_percentage": 20.0,
        "positive_percentage": 55.0,
        "neutral_percentage": 25.0,
    },
    {
        "article_id": "inactive-article",
        "negative_percentage": 10.0,
        "positive_percentage": 10.0,
        "neutral_percentage": 80.0,
    },
)


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
                ArticleModel(**article) for article in TEST_ARTICLES
            )
            session.add(
                ArticleModel(
                    id="article-without-analysis",
                    source_id="demo",
                    title="Neanalizirana vest",
                    summary="Ova vest ne treba da bude vidljiva.",
                    source="Demo izvor",
                    category="SERBIA",
                    published_at=TEST_ARTICLES[0]["published_at"],
                    image_url=None,
                    article_url="https://example.com/articles/pending",
                    normalized_url=(
                        "https://example.com/articles/pending"
                    ),
                    related_city_ids=[],
                )
            )
            session.add_all(
                ArticleAnalysisModel(
                    article_id=analysis["article_id"],
                    tone=ArticleToneAnalysisModel(**analysis),
                )
                for analysis in TEST_ANALYSES
            )
            session.add(
                ArticleGroupModel(
                    id="group-1",
                    created_at=datetime(
                        2026,
                        9,
                        23,
                        19,
                        0,
                        tzinfo=UTC,
                    ),
                    updated_at=datetime(
                        2026,
                        9,
                        23,
                        19,
                        0,
                        tzinfo=UTC,
                    ),
                    latest_article_at=TEST_ARTICLES[0]["published_at"],
                    active=True,
                )
            )
            session.add_all(
                [
                    ArticleGroupMembershipModel(
                        group_id="group-1",
                        article_id="article-1",
                    ),
                    ArticleGroupMembershipModel(
                        group_id="group-1",
                        article_id="article-2",
                    ),
                    ArticleGroupMembershipModel(
                        group_id="group-1",
                        article_id="inactive-article",
                    ),
                    ArticleGroupMembershipModel(
                        group_id="group-1",
                        article_id="article-without-analysis",
                    ),
                ]
            )
            session.add(
                SemanticGroupingRunModel(
                    id="latest-run",
                    model_name="test-model",
                    threshold=0.69,
                    boundary_min=0.60,
                    boundary_max=0.80,
                    candidate_window_hours=72,
                    article_count=4,
                    pair_count=3,
                    positive_pair_count=3,
                    boundary_pair_count=0,
                    created_at=datetime(2026, 9, 23, 19, 0, tzinfo=UTC),
                )
            )
            session.add_all(
                [
                    SemanticGroupingDecisionModel(
                        id="decision-1",
                        run_id="latest-run",
                        left_article_id="article-1",
                        right_article_id="article-2",
                        similarity=0.9,
                        predicted_same_event=True,
                        proposed_group_id="group-1",
                        is_boundary_candidate=False,
                    ),
                    SemanticGroupingDecisionModel(
                        id="decision-2",
                        run_id="latest-run",
                        left_article_id="article-1",
                        right_article_id="inactive-article",
                        similarity=0.85,
                        predicted_same_event=True,
                        proposed_group_id="group-1",
                        is_boundary_candidate=False,
                    ),
                    SemanticGroupingDecisionModel(
                        id="decision-3",
                        run_id="latest-run",
                        left_article_id="article-1",
                        right_article_id="article-without-analysis",
                        similarity=0.8,
                        predicted_same_event=True,
                        proposed_group_id="group-1",
                        is_boundary_candidate=True,
                    ),
                ]
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
    first_article = payload["articles"][0]
    assert first_article["analysis"]["tone"] == {
        "negativePercentage": 15.0,
        "positivePercentage": 25.0,
        "neutralPercentage": 60.0,
    }
    assert first_article["analysis"]["processedAt"].endswith("Z")
    assert {
        key: value
        for key, value in first_article.items()
        if key != "analysis"
    } == {
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
    assert response.json()["analysis"]["tone"] == {
        "negativePercentage": 20.0,
        "positivePercentage": 55.0,
        "neutralPercentage": 25.0,
    }


def test_list_article_groups() -> None:
    response = client.get("/api/article-groups")

    assert response.status_code == 200
    groups = response.json()["groups"]
    assert len(groups) == 1
    assert groups[0]["id"] == "group-1"
    articles = groups[0]["articles"]
    assert [article["id"] for article in articles] == [
        "article-1",
        "article-2",
    ]
    assert all(article["analysis"]["tone"] for article in articles)


def test_get_missing_article() -> None:
    response = client.get("/api/articles/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}


def test_get_inactive_article_returns_not_found() -> None:
    response = client.get("/api/articles/inactive-article")

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}


def test_get_article_without_analysis_returns_not_found() -> None:
    response = client.get("/api/articles/article-without-analysis")

    assert response.status_code == 404
    assert response.json() == {"detail": "Article not found"}
