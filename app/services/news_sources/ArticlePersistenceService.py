from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.repositories.ArticleAnalysisRepository import (
    ArticleAnalysisRepository,
)
from app.articles.repositories.ArticleRepository import ArticleRepository
from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.services.news_sources.ProcessedArticleMapper import (
    ProcessedArticleMapper,
)


class ArticlePersistenceService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        article_mapper: ProcessedArticleMapper,
    ) -> None:
        self._session_factory = session_factory
        self._article_mapper = article_mapper

    async def persist(
        self,
        contexts: list[ArticleProcessingContext],
        source_id: str,
    ) -> int:
        unexpected_source_ids = {
            context.article.source_id
            for context in contexts
            if context.article.source_id != source_id
        }
        if unexpected_source_ids:
            raise ValueError(
                "All persisted articles must belong to the requested "
                "news source."
            )

        seen_at = datetime.now(UTC)
        processed_models = [
            self._article_mapper.to_models(context)
            for context in contexts
        ]
        for models in processed_models:
            models.article.last_seen_at = seen_at
            models.article.is_active = True

        async with self._session_factory() as session:
            async with session.begin():
                article_repository = ArticleRepository(session)
                analysis_repository = ArticleAnalysisRepository(session)
                upsert_result = await article_repository.upsert_articles(
                    [
                        models.article
                        for models in processed_models
                    ]
                )

                for model in processed_models:
                    article_id = (
                        upsert_result.article_ids_by_normalized_url[
                            model.article.normalized_url
                        ]
                    )
                    model.analysis.article_id = article_id
                    if model.analysis.tone is not None:
                        model.analysis.tone.article_id = article_id

                await analysis_repository.upsert_analyses(
                    [
                        models.analysis
                        for models in processed_models
                    ]
                )
                await article_repository.deactivate_articles_not_in_feed(
                    source_id=source_id,
                    active_normalized_urls=[
                        models.article.normalized_url
                        for models in processed_models
                    ],
                )

        return upsert_result.changed_count
