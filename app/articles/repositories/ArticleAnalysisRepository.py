from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel


class ArticleAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_analyses(
        self,
        analyses: list[ArticleAnalysisModel],
    ) -> None:
        if not analyses:
            return

        article_ids = [analysis.article_id for analysis in analyses]
        existing_analyses = await self._session.scalars(
            select(ArticleAnalysisModel)
            .options(selectinload(ArticleAnalysisModel.tone))
            .where(ArticleAnalysisModel.article_id.in_(article_ids))
        )
        existing_by_article_id = {
            analysis.article_id: analysis
            for analysis in existing_analyses
        }

        for analysis in analyses:
            existing = existing_by_article_id.get(analysis.article_id)
            if existing is None:
                self._session.add(analysis)
                continue

            existing.processed_at = analysis.processed_at
            if analysis.tone is None:
                continue

            if existing.tone is None:
                existing.tone = analysis.tone
                continue

            existing.tone.negative_percentage = (
                analysis.tone.negative_percentage
            )
            existing.tone.positive_percentage = (
                analysis.tone.positive_percentage
            )
            existing.tone.neutral_percentage = (
                analysis.tone.neutral_percentage
            )
