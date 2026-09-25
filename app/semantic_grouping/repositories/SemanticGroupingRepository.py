from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.SemanticGroupingDecisionModel import (
    SemanticGroupingDecisionModel,
)
from app.semantic_grouping.models.SemanticGroupingRunModel import (
    SemanticGroupingRunModel,
)


class SemanticGroupingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_candidate_articles(
        self,
        published_after: datetime,
    ) -> list[ArticleModel]:
        result = await self._session.scalars(
            select(ArticleModel)
            .where(
                ArticleModel.is_active.is_(True),
                ArticleModel.published_at >= published_after,
            )
            .order_by(ArticleModel.published_at)
        )
        return list(result)

    def add_run(
        self,
        run: SemanticGroupingRunModel,
        decisions: list[SemanticGroupingDecisionModel],
    ) -> None:
        self._session.add(run)
        self._session.add_all(decisions)

    async def list_boundary_decisions(
        self,
        limit: int = 100,
    ) -> list[SemanticGroupingDecisionModel]:
        result = await self._session.scalars(
            select(SemanticGroupingDecisionModel)
            .where(
                SemanticGroupingDecisionModel.is_boundary_candidate.is_(
                    True
                )
            )
            .order_by(
                SemanticGroupingDecisionModel.created_at.desc(),
                SemanticGroupingDecisionModel.similarity,
            )
            .limit(limit)
        )
        return list(result)
