from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.articles import router as articles_router
from app.config.Settings import get_settings
from app.database.session import AsyncSessionFactory
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.RtsNewsSource import RtsNewsSource
from app.pipeline.NewsArticleProcessingPipeline import (
    NewsArticleProcessingPipeline,
)
from app.pipeline.steps.ArticleDeduplicationStep import (
    ArticleDeduplicationStep,
)
from app.pipeline.steps.ToneAnalysisStep import ToneAnalysisStep
from app.pipeline.steps.UrlNormalizationStep import UrlNormalizationStep
from app.services.news_sources.ArticlePersistenceService import (
    ArticlePersistenceService,
)
from app.services.news_sources.ArticleUrlNormalizer import (
    ArticleUrlNormalizer,
)
from app.services.news_sources.ProcessedArticleMapper import (
    ProcessedArticleMapper,
)
from app.services.news_sources.NewsSourcePollingService import (
    NewsSourcePollingService,
)
from app.tone_analysis.services.ExistingToneAnalysisLoader import (
    ExistingToneAnalysisLoader,
)
from app.tone_analysis.services.ToneAnalysisInputHasher import (
    ToneAnalysisInputHasher,
)
from app.tone_analysis.factories.ToneAnalysisStrategyFactory import (
    ToneAnalysisStrategyFactory,
)

settings = get_settings()
tone_analysis = ToneAnalysisStrategyFactory.create(settings)
article_url_normalizer = ArticleUrlNormalizer()
news_article_preprocessing_pipeline = NewsArticleProcessingPipeline(
    steps=[
        UrlNormalizationStep(article_url_normalizer),
        ArticleDeduplicationStep(),
    ]
)
news_article_analysis_pipeline = NewsArticleProcessingPipeline(
    steps=[
        ToneAnalysisStep(tone_analysis.strategy),
    ]
)
news_source_polling_service = NewsSourcePollingService(
    sources=[
        RtsNewsSource(
            parser=RssFeedParser(),
        )
    ],
    preprocessing_pipeline=news_article_preprocessing_pipeline,
    analysis_pipeline=news_article_analysis_pipeline,
    existing_tone_analysis_loader=ExistingToneAnalysisLoader(
        session_factory=AsyncSessionFactory,
        input_hasher=ToneAnalysisInputHasher(),
        provider=tone_analysis.provider,
        model_name=tone_analysis.model_name,
        prompt_version=tone_analysis.prompt_version,
    ),
    persistence_service=ArticlePersistenceService(
        session_factory=AsyncSessionFactory,
        article_mapper=ProcessedArticleMapper(),
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
