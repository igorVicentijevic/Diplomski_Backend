from datetime import UTC, datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.models.ArticleAnalysisModel import (
    ArticleAnalysisModel,
)
from app.articles.repositories.ArticleAnalysisRepository import (
    ArticleAnalysisRepository,
)
from app.articles.repositories.ArticleRepository import ArticleRepository
from app.articles.repositories.models.ArticleUpsertResult import (
    ArticleUpsertResult,
)
from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.services.news_sources.ProcessedArticleMapper import (
    ProcessedArticleMapper,
)
from app.services.news_sources.models.ProcessedArticleModels import (
    ProcessedArticleModels,
)

logger = logging.getLogger(__name__)


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
        self._require_single_source(contexts, source_id)

        #every fetched article is stored, even without a tone, so that a
        #busy analysis provider cannot drop it from the feed; the API
        #joins the analysis and keeps it hidden until the tone lands
        mapped_contexts = [
            context
            for context in contexts
            if context.normalized_url is not None
        ]
        feed_normalized_urls = [
            context.normalized_url
            for context in mapped_contexts
            if context.normalized_url is not None
        ]

        seen_at = datetime.now(UTC)
        processed_models = [
            self._article_mapper.to_models(context)
            for context in mapped_contexts
        ]
        for models in processed_models:
            models.article.last_seen_at = seen_at
            models.article.is_active = True

        self._log_pending_analyses(processed_models, source_id)

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

                await analysis_repository.upsert_analyses(
                    self._link_analyses(
                        processed_models,
                        upsert_result,
                    )
                )
                await article_repository.deactivate_articles_not_in_feed(
                    source_id=source_id,
                    active_normalized_urls=feed_normalized_urls,
                )

        return upsert_result.changed_count

    @staticmethod
    def _require_single_source(
        contexts: list[ArticleProcessingContext],
        source_id: str,
    ) -> None:
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

    @staticmethod
    def _log_pending_analyses(
        processed_models: list[ProcessedArticleModels],
        source_id: str,
    ) -> None:
        pending_count = sum(
            1
            for models in processed_models
            if models.analysis is None
        )
        if not pending_count:
            return

        logger.warning(
            "Stored %s article(s) of source %s without a tone "
            "analysis; they stay hidden until it is retried.",
            pending_count,
            source_id,
        )

    @staticmethod
    def _link_analyses(
        processed_models: list[ProcessedArticleModels],
        upsert_result: ArticleUpsertResult,
    ) -> list[ArticleAnalysisModel]:
        analyses: list[ArticleAnalysisModel] = []
        for models in processed_models:
            if models.analysis is None:
                continue

            article_id = upsert_result.article_ids_by_normalized_url[
                models.article.normalized_url
            ]
            models.analysis.article_id = article_id
            if models.analysis.tone is not None:
                models.analysis.tone.article_id = article_id

            analyses.append(models.analysis)

        return analyses
