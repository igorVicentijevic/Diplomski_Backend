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

logger = logging.getLogger(__name__)


class NewsSourcePollingService:
    REFRESH_INTERVAL_SECONDS = 15 * 60

    def __init__(
        self,
        sources: list[NewsSource],
        processing_pipeline: NewsArticleProcessingPipeline,
        persistence_service: ArticlePersistenceService,
        refresh_interval_seconds: int = REFRESH_INTERVAL_SECONDS,
    ) -> None:
        self._sources = sources
        self._processing_pipeline = processing_pipeline
        self._persistence_service = persistence_service
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
                
                processed_articles = await self._processing_pipeline.process(
                    articles
                )

                #persist the converted domain models to the database
                changed_count += await self._persistence_service.persist(
                    processed_articles
                )

            except Exception:
                logger.exception(
                    "Could not refresh news source %s",
                    source.display_name,
                )

        return changed_count

    async def _poll(self) -> None:
        while True:
            await self.refresh_once()
            await asyncio.sleep(self._refresh_interval_seconds)
