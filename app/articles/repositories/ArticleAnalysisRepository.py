from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel
from app.articles.models.ArticleModel import ArticleModel
from app.articles.models.ArticleToneAnalysisModel import (
    ArticleToneAnalysisModel,
)
from app.articles.repositories.models.StoredToneAnalysis import (
    StoredToneAnalysis,
)


class ArticleAnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_tone_analyses_by_normalized_urls(
        self,
        normalized_urls: list[str],
    ) -> dict[str, StoredToneAnalysis]:
        if not normalized_urls:
            return {}

        result = await self._session.execute(
            select(
                ArticleModel.normalized_url,
                ArticleToneAnalysisModel,
                ArticleAnalysisModel.processed_at,
            )
            .join(ArticleModel.analysis)
            .join(ArticleAnalysisModel.tone)
            .where(ArticleModel.normalized_url.in_(normalized_urls))
        )

        return {
            normalized_url: StoredToneAnalysis(
                tone=tone_analysis,
                processed_at=processed_at,
            )
            for normalized_url, tone_analysis, processed_at in result
        }

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
            existing.tone.input_hash = analysis.tone.input_hash
            existing.tone.provider = analysis.tone.provider
            existing.tone.model_name = analysis.tone.model_name
            existing.tone.prompt_version = analysis.tone.prompt_version
