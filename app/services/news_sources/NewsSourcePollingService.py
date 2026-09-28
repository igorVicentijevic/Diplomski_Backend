import asyncio
import logging

from app.news_sources.INewsSource import INewsSource
from app.pipeline.NewsArticleProcessingPipeline import (
    NewsArticleProcessingPipeline,
)
from app.services.news_sources.ArticlePersistenceService import (
    ArticlePersistenceService,
)
from app.services.news_sources.models.NewsSourceFetchResult import (
    NewsSourceFetchResult,
)

logger = logging.getLogger(__name__)


class NewsSourcePollingService:
    """Fetches every configured feed once and persists the articles.

    Scheduling is intentionally not handled here; a PeriodicScheduler
    owns the cadence so that this service stays responsible only for a
    single refresh.
    """

    FETCH_TIMEOUT_SECONDS = 60.0

    def __init__(
        self,
        sources: list[INewsSource],
        pipeline: NewsArticleProcessingPipeline,
        persistence_service: ArticlePersistenceService,
        fetch_timeout_seconds: float = FETCH_TIMEOUT_SECONDS,
    ) -> None:
        self._sources = sources
        self._pipeline = pipeline
        self._persistence_service = persistence_service
        self._fetch_timeout_seconds = fetch_timeout_seconds

    async def refresh_once(self) -> int:
        fetch_results = await self._fetch_all()

        changed_count = 0
        for fetch_result in fetch_results:
            if fetch_result.failed:
                continue

            changed_count += await self._process_and_persist(
                fetch_result
            )

        return changed_count

    async def _fetch_all(self) -> list[NewsSourceFetchResult]:
        #feeds are independent, so their network waits are overlapped
        return list(
            await asyncio.gather(
                *(
                    self._fetch_source(source)
                    for source in self._sources
                )
            )
        )

    async def _fetch_source(
        self,
        source: INewsSource,
    ) -> NewsSourceFetchResult:
        try:
            async with asyncio.timeout(self._fetch_timeout_seconds):
                articles = await source.fetch_articles()
        except TimeoutError:
            logger.warning(
                "Timed out after %s seconds while fetching news "
                "source %s",
                self._fetch_timeout_seconds,
                source.display_name,
            )
            return NewsSourceFetchResult(source=source, failed=True)
        except Exception:
            logger.exception(
                "Could not fetch news source %s",
                source.display_name,
            )
            return NewsSourceFetchResult(source=source, failed=True)

        return NewsSourceFetchResult(source=source, articles=articles)

    async def _process_and_persist(
        self,
        fetch_result: NewsSourceFetchResult,
    ) -> int:
        source = fetch_result.source
        try:
            processed_articles = await self._pipeline.process(
                fetch_result.articles
            )

            return await self._persistence_service.persist(
                processed_articles,
                source_id=source.id,
            )
        except Exception:
            logger.exception(
                "Could not refresh news source %s",
                source.display_name,
            )
            return 0
