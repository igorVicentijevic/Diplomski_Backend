import asyncio
import math
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.dialects import postgresql

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.grouping.CandidateArticlePairGenerator import (
    CandidateArticlePairGenerator,
)
from app.semantic_grouping.grouping.PgvectorCandidatePairFinder import (
    PgvectorCandidatePairFinder,
)
from app.semantic_grouping.grouping.PythonCandidatePairFinder import (
    PythonCandidatePairFinder,
)


def _create_article(
    article_id: str,
    source_id: str,
    published_at: datetime,
) -> ArticleModel:
    return ArticleModel(
        id=article_id,
        source_id=source_id,
        title=f"Title {article_id}",
        summary="Summary",
        source=source_id,
        category="SERBIA",
        published_at=published_at,
        image_url=None,
        article_url=f"https://example.com/{article_id}",
        normalized_url=f"https://example.com/{article_id}",
        related_city_ids=[],
    )


def test_python_candidate_pair_finder_computes_cosine_similarity() -> None:
    async def run_test() -> None:
        published_at = datetime.now(UTC) - timedelta(hours=1)
        articles = [
            _create_article("a", "source-a", published_at),
            _create_article("b", "source-b", published_at),
            _create_article("c", "source-a", published_at),
        ]
        embeddings = {
            "a": [1.0, 0.0],
            "b": [1.0, 0.0],
            "c": [0.0, 1.0],
        }
        finder = PythonCandidatePairFinder(
            pair_generator=CandidateArticlePairGenerator(
                timedelta(hours=72)
            )
        )

        results = await finder.find(articles, embeddings)

        by_pair = {
            (r.left_article_id, r.right_article_id): r.similarity
            for r in results
        }
        assert set(by_pair) == {("a", "b"), ("b", "c")}
        assert math.isclose(by_pair[("a", "b")], 1.0, abs_tol=1e-9)
        assert math.isclose(by_pair[("b", "c")], 0.0, abs_tol=1e-9)

    asyncio.run(run_test())


def test_pgvector_candidate_pair_finder_skips_db_when_too_few_articles() -> (
    None
):
    async def run_test() -> None:
        session_factory = MagicMock()
        finder = PgvectorCandidatePairFinder(
            session_factory=session_factory,
            model_name="model",
            candidate_window=timedelta(hours=72),
        )

        results = await finder.find(
            [_create_article("a", "source-a", datetime.now(UTC))],
            {},
        )

        assert results == []
        session_factory.assert_not_called()

    asyncio.run(run_test())


def test_pgvector_candidate_pair_finder_builds_expected_sql() -> None:
    async def run_test() -> None:
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        fake_result = MagicMock()
        fake_result.all.return_value = [
            MagicMock(
                left_article_id="a",
                right_article_id="b",
                similarity=0.87,
            )
        ]
        session.execute = AsyncMock(return_value=fake_result)
        session_factory = MagicMock(return_value=session)

        finder = PgvectorCandidatePairFinder(
            session_factory=session_factory,
            model_name="my-model",
            candidate_window=timedelta(hours=72),
        )

        results = await finder.find(
            [
                _create_article("a", "source-a", datetime.now(UTC)),
                _create_article("b", "source-b", datetime.now(UTC)),
            ],
            {},
        )

        assert len(results) == 1
        [pair] = results
        assert pair.left_article_id == "a"
        assert pair.right_article_id == "b"
        assert pair.similarity == 0.87

        statement = session.execute.await_args.args[0]
        compiled_sql = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": False},
            )
        )

        assert "<=>" in compiled_sql
        assert "articles_2.id > articles_1.id" in compiled_sql
        assert "model_name" in compiled_sql

    asyncio.run(run_test())
