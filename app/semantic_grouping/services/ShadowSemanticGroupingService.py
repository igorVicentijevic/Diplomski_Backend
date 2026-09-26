from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.SemanticGroupingConfiguration import (
    SemanticGroupingConfiguration,
)
from app.semantic_grouping.models.SemanticGroupingDecision import (
    SemanticGroupingDecision,
)
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
)
from app.semantic_grouping.models.SemanticGroupingRunModel import (
    SemanticGroupingRunModel,
)
from app.semantic_grouping.repositories.SemanticGroupingRepository import (
    SemanticGroupingRepository,
)
from app.semantic_grouping.grouping.ArticleEmbeddingProvider import (
    ArticleEmbeddingProvider,
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


class ShadowSemanticGroupingService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        configuration: SemanticGroupingConfiguration,
        embedding_provider: ArticleEmbeddingProvider,
        pair_generator: CandidateArticlePairGenerator,
        pair_evaluator: SemanticPairEvaluator,
        group_assigner: ProposedGroupAssigner,
        run_factory: SemanticGroupingRunFactory,
    ) -> None:
        self._session_factory = session_factory
        self._configuration = configuration
        self._embedding_provider = embedding_provider
        self._pair_generator = pair_generator
        self._pair_evaluator = pair_evaluator
        self._group_assigner = group_assigner
        self._run_factory = run_factory

    async def run(self) -> SemanticGroupingRunModel:
        created_at = datetime.now(UTC)
        articles = await self._load_articles(
            created_at - self._configuration.candidate_window
        )
        decisions = await self._create_decisions(articles)
        self._group_assigner.assign(decisions)
        run, decision_models = self._run_factory.create(
            articles,
            decisions,
            created_at,
        )
        await self._save_run(run, decision_models)
        return run

    async def _create_decisions(
        self,
        articles: list[ArticleModel],
    ) -> list[SemanticGroupingDecision]:
        if len(articles) < 2:
            return []

        embeddings = await self._embedding_provider.provide(articles)
        pairs = self._pair_generator.generate(articles)
        return self._pair_evaluator.evaluate(pairs, embeddings)

    async def _load_articles(
        self,
        published_after: datetime,
    ) -> list[ArticleModel]:
        async with self._session_factory() as session:
            return await SemanticGroupingRepository(
                session
            ).list_candidate_articles(published_after)

    async def _save_run(
        self,
        run: SemanticGroupingRunModel,
        decisions: list[SemanticGroupingDecisionModel],
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                repository = SemanticGroupingRepository(session)
                await repository.add_run(
                    run,
                    decisions,
                )
