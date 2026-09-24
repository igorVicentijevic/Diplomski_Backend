from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.articles import router as articles_router
from app.database.session import AsyncSessionFactory
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.RtsNewsSource import RtsNewsSource
from app.services.news_sources.ArticleUrlNormalizer import (
    ArticleUrlNormalizer,
)
from app.services.news_sources.NewsArticleDeduplicator import (
    NewsArticleDeduplicator,
)
from app.services.news_sources.NewsArticleMapper import NewsArticleMapper
from app.services.news_sources.NewsSourcePollingService import (
    NewsSourcePollingService,
)

article_url_normalizer = ArticleUrlNormalizer()
news_source_polling_service = NewsSourcePollingService(
    sources=[
        RtsNewsSource(
            parser=RssFeedParser(),
        )
    ],
    session_factory=AsyncSessionFactory,
    article_mapper=NewsArticleMapper(article_url_normalizer),
    article_deduplicator=NewsArticleDeduplicator(
        article_url_normalizer
    ),
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    news_source_polling_service.start()
    try:
        yield
    finally:
        await news_source_polling_service.stop()

app = FastAPI(
    title="News Aggregator API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(articles_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, World!"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
