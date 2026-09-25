from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI

from app.api.routes.articles import router as articles_router
from app.config.Settings import get_settings
from app.database.session import AsyncSessionFactory
from app.news_sources.B92NewsSource import B92NewsSource
from app.news_sources.BetaNewsSource import BetaNewsSource
from app.news_sources.DanasNewsSource import DanasNewsSource
from app.news_sources.JuzneVestiNewsSource import JuzneVestiNewsSource
from app.news_sources.N1NewsSource import N1NewsSource
from app.news_sources.NovaNewsSource import NovaNewsSource
from app.news_sources.PolitikaNewsSource import PolitikaNewsSource
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.RtsNewsSource import RtsNewsSource
from app.news_sources.VremeNewsSource import VremeNewsSource
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
from app.semantic_grouping.embedding_engine.SentenceTransformerEmbeddingEngine import (
    SentenceTransformerEmbeddingEngine,
)
from app.semantic_grouping.ArticleTextBuilder import ArticleTextBuilder
from app.semantic_grouping.models.SemanticGroupingConfiguration import (
    SemanticGroupingConfiguration,
)
from app.semantic_grouping.services.ArticleEmbeddingService import (
    ArticleEmbeddingService,
)
from app.semantic_grouping.services.CandidateArticlePairGenerator import (
    CandidateArticlePairGenerator,
)
from app.semantic_grouping.services.ProposedGroupAssigner import (
    ProposedGroupAssigner,
)
from app.semantic_grouping.services.SemanticGroupingRunFactory import (
    SemanticGroupingRunFactory,
)
from app.semantic_grouping.services.SemanticPairEvaluator import (
    SemanticPairEvaluator,
)
from app.semantic_grouping.services.ShadowSemanticGroupingService import (
    ShadowSemanticGroupingService,
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
rss_feed_parser = RssFeedParser()
semantic_grouping_configuration = SemanticGroupingConfiguration(
    model_name=settings.semantic_grouping_model,
    threshold=settings.semantic_grouping_threshold,
    boundary_min=settings.semantic_grouping_boundary_min,
    boundary_max=settings.semantic_grouping_boundary_max,
    candidate_window=timedelta(
        hours=settings.semantic_grouping_candidate_window_hours
    ),
)
shadow_grouping_service = (
    ShadowSemanticGroupingService(
        session_factory=AsyncSessionFactory,
        configuration=semantic_grouping_configuration,
        embedding_service=ArticleEmbeddingService(
            embedding_engine=SentenceTransformerEmbeddingEngine(
                semantic_grouping_configuration.model_name
            ),
            text_builder=ArticleTextBuilder(),
        ),
        pair_generator=CandidateArticlePairGenerator(
            semantic_grouping_configuration.candidate_window
        ),
        pair_evaluator=SemanticPairEvaluator(
            semantic_grouping_configuration
        ),
        group_assigner=ProposedGroupAssigner(),
        run_factory=SemanticGroupingRunFactory(
            semantic_grouping_configuration
        ),
    )
    if settings.semantic_grouping_shadow_enabled
    else None
)
news_source_polling_service = NewsSourcePollingService(
    sources=[
        RtsNewsSource(parser=rss_feed_parser),
        DanasNewsSource(parser=rss_feed_parser),
        N1NewsSource(parser=rss_feed_parser),
        PolitikaNewsSource(parser=rss_feed_parser),
        B92NewsSource(parser=rss_feed_parser),
        BetaNewsSource(parser=rss_feed_parser),
        JuzneVestiNewsSource(parser=rss_feed_parser),
        NovaNewsSource(parser=rss_feed_parser),
        VremeNewsSource(parser=rss_feed_parser),
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
    shadow_grouping_service=shadow_grouping_service,
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
