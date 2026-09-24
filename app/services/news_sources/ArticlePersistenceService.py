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
    ) -> int:
        processed_models = [
            self._article_mapper.to_models(context)
            for context in contexts
        ]

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

        return upsert_result.changed_count
