import asyncio
import math
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from sqlalchemy import select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models.ArticleModel import ArticleModel
from app.config.Settings import Settings
from app.database.Base import Base
from app.semantic_grouping.embedding_engine.EmbeddingEngine import (
    EmbeddingEngine,
)
from app.semantic_grouping.grouping.ArticleEmbeddingGenerator import (
    ArticleEmbeddingGenerator,
)
from app.semantic_grouping.grouping.ArticleTextBuilder import (
    ArticleTextBuilder,
)
from app.semantic_grouping.grouping.CandidateArticlePairGenerator import (
    CandidateArticlePairGenerator,
)
from app.semantic_grouping.grouping.ProposedGroupAssigner import (
    ProposedGroupAssigner,
)
from app.semantic_grouping.grouping.SemanticGroupingRunFactory import (
    SemanticGroupingRunFactory,
)
from app.semantic_grouping.grouping.SemanticPairEvaluator import (
    SemanticPairEvaluator,
)
from app.semantic_grouping.models.SemanticGroupingConfiguration import (
    SemanticGroupingConfiguration,
)
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
from app.semantic_grouping.repositories.SemanticGroupingRepository import (
    SemanticGroupingRepository,
)
from app.semantic_grouping.services.ShadowSemanticGroupingService import (
    ShadowSemanticGroupingService,
)
from app.semantic_grouping.services.ArticleGroupService import (
    ArticleGroupService,
)
from app.semantic_grouping.services.SemanticGroupingExportService import (
    SemanticGroupingExportService,
)
from app.services.news_sources.NewsSourcePollingService import (
    NewsSourcePollingService,
)
from experiments.semantic_grouping.compare_models import (
    evaluate_calibration_readiness,
)


class FakeEmbeddingEngine(EmbeddingEngine):
    def encode(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        embeddings = {
            "Title: Article A\nSummary: Event": [1.0, 0.0],
            "Title: Article B\nSummary: Event": [
                0.7,
                math.sqrt(0.51),
            ],
            "Title: Article C\nSummary: Event": [
                0.72,
                math.sqrt(0.4816),
            ],
            "Title: Article D\nSummary: Other": [-1.0, 0.0],
        }
        return [embeddings[text] for text in texts]


def test_semantic_grouping_configuration_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.semantic_grouping_shadow_enabled is True
    assert settings.semantic_grouping_model == (
        "sentence-transformers/distiluse-base-multilingual-cased-v2"
    )
    assert settings.semantic_grouping_threshold == 0.69
    assert settings.semantic_grouping_boundary_min == 0.60
    assert settings.semantic_grouping_boundary_max == 0.80


def test_shadow_grouping_persists_decisions_and_groups(
    tmp_path: Path,
) -> None:
    async def run_test() -> None:
        database_url = URL.create(
            drivername="sqlite+aiosqlite",
            database=str(tmp_path / "semantic-grouping.db"),
        )
        engine = create_async_engine(database_url)
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        published_at = datetime.now(UTC) - timedelta(hours=1)
        async with session_factory() as session:
            session.add_all(
                [
                    _create_article(
                        article_id="a",
                        source_id="source-a",
                        title="Article A",
                        summary="Event",
                        published_at=published_at,
                    ),
                    _create_article(
                        article_id="b",
                        source_id="source-b",
                        title="Article B",
                        summary="Event",
                        published_at=published_at,
                    ),
                    _create_article(
                        article_id="c",
                        source_id="source-c",
                        title="Article C",
                        summary="Event",
                        published_at=published_at,
                    ),
                    _create_article(
                        article_id="d",
                        source_id="source-d",
                        title="Article D",
                        summary="Other",
                        published_at=published_at,
                    ),
                ]
            )
            await session.commit()

        configuration = SemanticGroupingConfiguration(
            model_name="distiluse-test",
            threshold=0.69,
            boundary_min=0.60,
            boundary_max=0.80,
            candidate_window=timedelta(hours=72),
        )
        service = ShadowSemanticGroupingService(
            session_factory=session_factory,
            configuration=configuration,
            embedding_generator=ArticleEmbeddingGenerator(
                embedding_engine=FakeEmbeddingEngine(),
                text_builder=ArticleTextBuilder(),
            ),
            pair_generator=CandidateArticlePairGenerator(
                configuration.candidate_window
            ),
            pair_evaluator=SemanticPairEvaluator(configuration),
            group_assigner=ProposedGroupAssigner(),
            run_factory=SemanticGroupingRunFactory(configuration),
        )
        run = await service.run()
        export_path = (
            tmp_path
            / "exports"
            / "semantic-groups.md"
        )
        exported_path = await SemanticGroupingExportService(
            session_factory
        ).export(
            output=export_path,
            run_id=run.id,
        )

        async with session_factory() as session:
            stored_run = await session.get(
                SemanticGroupingRunModel,
                run.id,
            )
            decisions = list(
                await session.scalars(
                    select(SemanticGroupingDecisionModel).where(
                        SemanticGroupingDecisionModel.run_id == run.id
                    )
                )
            )
            boundary_decisions = await SemanticGroupingRepository(
                session
            ).list_boundary_decisions()

        assert stored_run is not None
        assert stored_run.model_name == "distiluse-test"
        assert stored_run.threshold == 0.69
        assert stored_run.pair_count == 6
        assert stored_run.positive_pair_count == 3
        assert stored_run.boundary_pair_count == 2
        assert len(decisions) == 6
        assert len(boundary_decisions) == 2

        positive_decisions = [
            decision
            for decision in decisions
            if decision.predicted_same_event
        ]
        assert len(
            {
                decision.proposed_group_id
                for decision in positive_decisions
            }
        ) == 1
        assert all(
            decision.proposed_group_id is not None
            for decision in positive_decisions
        )
        assert all(
            decision.proposed_group_id is None
            for decision in decisions
            if not decision.predicted_same_event
        )

        async with session_factory() as session:
            groups = list(
                await session.scalars(select(ArticleGroupModel))
            )
            memberships = list(
                await session.scalars(
                    select(ArticleGroupMembershipModel)
                )
            )

        assert len(groups) == 1
        stable_group_id = groups[0].id
        assert groups[0].active is True
        assert {
            membership.article_id for membership in memberships
        } == {"a", "b", "c"}

        newer_article = _create_article(
            article_id="e",
            source_id="source-e",
            title="Article E",
            summary="Event",
            published_at=published_at + timedelta(minutes=30),
        )
        stale_group = ArticleGroupModel(
            id="stale-group",
            created_at=published_at,
            updated_at=published_at,
            latest_article_at=published_at,
            active=True,
        )
        async with session_factory() as session:
            async with session.begin():
                session.add(newer_article)
                session.add(stale_group)
                await session.flush()
                session.add(
                    ArticleGroupMembershipModel(
                        group_id=stale_group.id,
                        article_id="d",
                        added_at=published_at,
                    )
                )

        reconciled_at = datetime.now(UTC)
        async with session_factory() as session:
            async with session.begin():
                repository = SemanticGroupingRepository(session)
                articles = await repository.list_articles_by_ids(
                    {"b", "c", "e"}
                )
                await ArticleGroupService(repository).reconcile(
                    {"next-proposal": {"b", "c", "e"}},
                    articles,
                    reconciled_at,
                )

        async with session_factory() as session:
            stable_group = await session.get(
                ArticleGroupModel,
                stable_group_id,
            )
            deactivated_group = await session.get(
                ArticleGroupModel,
                "stale-group",
            )
            memberships = list(
                await session.scalars(
                    select(ArticleGroupMembershipModel).where(
                        ArticleGroupMembershipModel.group_id
                        == stable_group_id
                    )
                )
            )

        assert stable_group is not None
        assert stable_group.active is True
        assert stable_group.latest_article_at.replace(
            tzinfo=UTC
        ) == newer_article.published_at
        assert deactivated_group is not None
        assert deactivated_group.active is False
        assert {
            membership.article_id for membership in memberships
        } == {"a", "b", "c", "e"}
        assert exported_path == export_path
        report = export_path.read_text(encoding="utf-8")
        assert "# Semantic grouping export" in report
        assert "## Group 1" in report
        assert "Article A" in report
        assert "Article B" in report
        assert "Article C" in report
        assert "Article D" not in report
        assert "Threshold: 0.6900" in report

        await engine.dispose()

    asyncio.run(run_test())


def test_calibration_requires_positive_pairs_from_multiple_events() -> None:
    ready, reasons = evaluate_calibration_readiness(
        positive_count=49,
        positive_event_count=1,
    )

    assert ready is False
    assert len(reasons) == 2

    ready, reasons = evaluate_calibration_readiness(
        positive_count=50,
        positive_event_count=2,
    )

    assert ready is True
    assert reasons == []


def test_polling_service_runs_grouping_in_shadow_mode() -> None:
    async def run_test() -> None:
        shadow_grouping_service = Mock()
        shadow_grouping_service.run = AsyncMock()
        service = NewsSourcePollingService(
            sources=[],
            preprocessing_pipeline=Mock(),
            analysis_pipeline=Mock(),
            existing_tone_analysis_loader=Mock(),
            persistence_service=Mock(),
            shadow_grouping_service=shadow_grouping_service,
        )

        assert await service.refresh_once() == 0
        shadow_grouping_service.run.assert_awaited_once_with()

    asyncio.run(run_test())


def test_repository_flushes_run_before_adding_decisions() -> None:
    async def run_test() -> None:
        session = Mock(spec=AsyncSession)
        session.flush = AsyncMock()
        run = Mock(spec=SemanticGroupingRunModel)
        decisions = [Mock(spec=SemanticGroupingDecisionModel)]

        await SemanticGroupingRepository(session).add_run(
            run,
            decisions,
        )

        session.add.assert_called_once_with(run)
        session.flush.assert_awaited_once_with()
        session.add_all.assert_called_once_with(decisions)

    asyncio.run(run_test())


def _create_article(
    article_id: str,
    source_id: str,
    title: str,
    summary: str,
    published_at: datetime,
) -> ArticleModel:
    return ArticleModel(
        id=article_id,
        source_id=source_id,
        title=title,
        summary=summary,
        source=source_id,
        category="SERBIA",
        published_at=published_at,
        image_url=None,
        article_url=f"https://example.com/{article_id}",
        normalized_url=f"https://example.com/{article_id}",
        related_city_ids=[],
    )
