import asyncio
import hashlib
import logging
from contextlib import suppress
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.models.ArticleModel import ArticleModel
from app.articles.repositories.ArticleRepository import ArticleRepository
from app.news_sources.NewsSource import NewsSource
from app.news_sources.models.NewsArticle import NewsArticle

logger = logging.getLogger(__name__)


class NewsSourcePollingService:
    REFRESH_INTERVAL_SECONDS = 15 * 60

    def __init__(
        self,
        sources: list[NewsSource],
        session_factory: async_sessionmaker[AsyncSession],
        refresh_interval_seconds: int = REFRESH_INTERVAL_SECONDS,
    ) -> None:
        self._sources = sources
        self._session_factory = session_factory
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
        for source in self._sources:
            try:
                articles = await source.fetch_articles()
                models = [
                    self._to_model(article)
                    for article in self._deduplicate(articles)
                ]
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

    def _to_model(self, article: NewsArticle) -> ArticleModel:
        normalized_url = self._normalize_url(article.article_url)
        article_id = hashlib.sha256(
            f"{article.source_id}:{normalized_url}".encode("utf-8")
        ).hexdigest()
        return ArticleModel(
            id=f"{article.source_id}-{article_id}",
            title=article.title,
            summary=article.summary,
            source=article.source_name,
            category=article.category,
            published_at=article.published_at,
            image_url=article.image_url,
            article_url=article.article_url,
            normalized_url=normalized_url,
            related_city_ids=[],
        )

    def _deduplicate(
        self,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:
        by_url = {
            self._normalize_url(article.article_url): article
            for article in articles
        }
        return list(by_url.values())

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlsplit(url)
        query = [
            (key, value)
            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
            if not key.casefold().startswith("utm_")
            and key.casefold() not in {"fbclid", "gclid"}
        ]
        path = parsed.path.rstrip("/") or "/"
        return urlunsplit(
            (
                parsed.scheme.casefold(),
                parsed.netloc.casefold(),
                path,
                urlencode(query),
                "",
            )
        )
