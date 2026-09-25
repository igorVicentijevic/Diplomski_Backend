import asyncio
import logging
from contextlib import suppress

from app.news_sources.NewsSource import NewsSource
from app.pipeline.NewsArticleProcessingPipeline import (
    NewsArticleProcessingPipeline,
)
from app.services.news_sources.ArticlePersistenceService import (
    ArticlePersistenceService,
)
from app.semantic_grouping.services.ShadowSemanticGroupingService import (
    ShadowSemanticGroupingService,
)
from app.tone_analysis.services.ExistingToneAnalysisLoader import (
    ExistingToneAnalysisLoader,
)

logger = logging.getLogger(__name__)


class NewsSourcePollingService:
    REFRESH_INTERVAL_SECONDS = 15 * 60

    def __init__(
        self,
        sources: list[NewsSource],
        preprocessing_pipeline: NewsArticleProcessingPipeline,
        analysis_pipeline: NewsArticleProcessingPipeline,
        existing_tone_analysis_loader: ExistingToneAnalysisLoader,
        persistence_service: ArticlePersistenceService,
        shadow_grouping_service: ShadowSemanticGroupingService | None = None,
        refresh_interval_seconds: int = REFRESH_INTERVAL_SECONDS,
    ) -> None:
        self._sources = sources
        self._preprocessing_pipeline = preprocessing_pipeline
        self._analysis_pipeline = analysis_pipeline
        self._existing_tone_analysis_loader = (
            existing_tone_analysis_loader
        )
        self._persistence_service = persistence_service
        self._shadow_grouping_service = shadow_grouping_service
        self._refresh_interval_seconds = refresh_interval_seconds
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._poll())

    async def stop(self) -> None:
        if self._task is None:
            return

        self._task.cancel()

        with suppress(asyncio.CancelledError):
            await self._task

        self._task = None

    async def refresh_once(self) -> int:
        changed_count = 0

        #going through each news source to refresh articles
        for source in self._sources:
            try:
                #fetching from RSS feed
                articles = await source.fetch_articles()
                preprocessed_articles = (
                    await self._preprocessing_pipeline.process(articles)
                )
                prepared_articles = (
                    await self._existing_tone_analysis_loader.load_existing(
                        preprocessed_articles
                    )
                )
                processed_articles = (
                    await self._analysis_pipeline.process_contexts(
                        prepared_articles
                    )
                )

                #persist the converted domain models to the database
                changed_count += await self._persistence_service.persist(
                    processed_articles,
                    source_id=source.id,
                )

            except Exception:
                logger.exception(
                    "Could not refresh news source %s",
                    source.display_name,
                )

        if self._shadow_grouping_service is not None:
            try:
                await self._shadow_grouping_service.run()
            except Exception:
                logger.exception(
                    "Could not run semantic grouping in shadow mode."
                )

        return changed_count

    async def _poll(self) -> None:
        while True:
            await self.refresh_once()
            await asyncio.sleep(self._refresh_interval_seconds)
