import asyncio
import logging
from contextlib import suppress

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.repositories.ArticleRepository import ArticleRepository
from app.news_sources.NewsSource import NewsSource
from app.services.news_sources.NewsArticleDeduplicator import (
    NewsArticleDeduplicator,
)
from app.services.news_sources.NewsArticleMapper import NewsArticleMapper

logger = logging.getLogger(__name__)


class NewsSourcePollingService:
    REFRESH_INTERVAL_SECONDS = 15 * 60

    def __init__(
        self,
        sources: list[NewsSource],
        session_factory: async_sessionmaker[AsyncSession],
        article_mapper: NewsArticleMapper,
        article_deduplicator: NewsArticleDeduplicator,
        refresh_interval_seconds: int = REFRESH_INTERVAL_SECONDS,
    ) -> None:
        self._sources = sources
        self._session_factory = session_factory
        self._article_mapper = article_mapper
        self._article_deduplicator = article_deduplicator
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
                unique_articles = self._article_deduplicator.deduplicate(
                    articles
                )

                #convert all fetched articles to domain models
                models = [
                    self._article_mapper.to_model(article)
                    for article in unique_articles
                ]

                #persist the converted domain models to the database
                async with self._session_factory() as session:
                    repository = ArticleRepository(session)
                    changed_count += await repository.upsert_articles(
                        models
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
