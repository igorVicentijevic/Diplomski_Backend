from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel
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

    async def add_run(
        self,
        run: SemanticGroupingRunModel,
        decisions: list[SemanticGroupingDecisionModel],
    ) -> None:
        self._session.add(run)
        await self._session.flush()
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

    async def get_run(
        self,
        run_id: str,
    ) -> SemanticGroupingRunModel | None:
        return await self._session.get(
            SemanticGroupingRunModel,
            run_id,
        )

    async def get_latest_run(
        self,
    ) -> SemanticGroupingRunModel | None:
        return await self._session.scalar(
            select(SemanticGroupingRunModel)
            .order_by(SemanticGroupingRunModel.created_at.desc())
            .limit(1)
        )

    async def list_grouped_decisions(
        self,
        run_id: str,
    ) -> list[SemanticGroupingDecisionModel]:
        result = await self._session.scalars(
            select(SemanticGroupingDecisionModel)
            .where(
                SemanticGroupingDecisionModel.run_id == run_id,
                SemanticGroupingDecisionModel.proposed_group_id.is_not(
                    None
                ),
            )
            .order_by(
                SemanticGroupingDecisionModel.proposed_group_id,
                SemanticGroupingDecisionModel.similarity.desc(),
            )
        )
        return list(result)

    async def list_articles_by_ids(
        self,
        article_ids: set[str],
    ) -> list[ArticleModel]:
        if not article_ids:
            return []

        result = await self._session.scalars(
            select(ArticleModel).where(
                ArticleModel.id.in_(article_ids)
            )
        )
        return list(result)

    async def list_active_analyzed_articles_by_ids(
        self,
        article_ids: set[str],
    ) -> list[ArticleModel]:
        if not article_ids:
            return []

        result = await self._session.scalars(
            select(ArticleModel)
            .join(ArticleModel.analysis)
            .join(ArticleAnalysisModel.tone)
            .options(
                selectinload(ArticleModel.analysis).selectinload(
                    ArticleAnalysisModel.tone
                )
            )
            .where(
                ArticleModel.id.in_(article_ids),
                ArticleModel.is_active.is_(True),
            )
        )
        return list(result)
