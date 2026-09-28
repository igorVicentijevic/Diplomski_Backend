import asyncio
import random
from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import httpx
from groq import RateLimitError
from sqlalchemy import func, select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel
from app.articles.models.ArticleModel import ArticleModel
from app.articles.repositories.ArticleRepository import ArticleRepository
from app.articles.models.ArticleToneAnalysisModel import (
    ArticleToneAnalysisModel,
)
from app.database.Base import Base
from app.news_sources.B92NewsSource import B92NewsSource
from app.news_sources.BetaNewsSource import BetaNewsSource
from app.news_sources.DanasNewsSource import DanasNewsSource
from app.news_sources.JuzneVestiNewsSource import JuzneVestiNewsSource
from app.news_sources.N1NewsSource import N1NewsSource
from app.news_sources.INewsSource import INewsSource
from app.news_sources.NovaNewsSource import NovaNewsSource
from app.news_sources.PolitikaNewsSource import PolitikaNewsSource
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.RtsNewsSource import RtsNewsSource
from app.news_sources.VremeNewsSource import VremeNewsSource
from app.news_sources.models.NewsArticle import NewsArticle
from app.pipeline.ArticleProcessingContext import ArticleProcessingContext
from app.pipeline.NewsArticleProcessingPipeline import (
    NewsArticleProcessingPipeline,
)
from app.pipeline.steps.ArticleDeduplicationStep import (
    ArticleDeduplicationStep,
)
from app.pipeline.steps.ExistingToneAnalysisStep import (
    ExistingToneAnalysisStep,
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
from app.tone_analysis.clients.GroqToneAnalysisLlmClient import (
    GroqToneAnalysisLlmClient,
)
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)
from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)
from app.tone_analysis.models.ToneAnalysisMetadata import (
    ToneAnalysisMetadata,
)
from app.tone_analysis.strategies.LlmToneAnalysisStrategy import (
    LlmToneAnalysisStrategy,
)
from app.tone_analysis.strategies.RandomToneAnalysisStrategy import (
    RandomToneAnalysisStrategy,
)
from app.tone_analysis.services.ExistingToneAnalysisLoader import (
    ExistingToneAnalysisLoader,
)
from app.tone_analysis.services.ToneAnalysisInputHasher import (
    ToneAnalysisInputHasher,
)
from app.tone_analysis.exceptions.ToneAnalysisUnavailableError import (
    ToneAnalysisUnavailableError,
)
from app.tone_analysis.models.ToneAnalysisAvailability import (
    ToneAnalysisAvailability,
)


def create_tone_strategy(
    analyze: AsyncMock,
    availability: ToneAnalysisAvailability | None = None,
) -> Mock:
    strategy = Mock()
    strategy.analyze = analyze
    strategy.check_availability = AsyncMock(
        return_value=(
            availability or ToneAnalysisAvailability.available()
        )
    )
    return strategy


def create_groq_client(groq_client: Mock) -> GroqToneAnalysisLlmClient:
    return GroqToneAnalysisLlmClient(
        api_key="test-key",
        model="openai/gpt-oss-20b",
        timeout_seconds=30,
        max_retries=2,
        groq_client=groq_client,
    )


def create_rate_limit_error() -> RateLimitError:
    return RateLimitError(
        "rate limit reached",
        response=httpx.Response(
            status_code=429,
            request=httpx.Request("POST", "https://api.groq.com"),
        ),
        body=None,
    )


def create_news_article(
    article_url: str,
    title: str = "Test article",
) -> NewsArticle:
    return NewsArticle(
        source_id="test",
        source_name="Test source",
        title=title,
        summary="Summary",
        category="SERBIA",
        published_at=datetime(
            2026,
            9,
            23,
            20,
            0,
            tzinfo=UTC,
        ),
        image_url=None,
        article_url=article_url,
    )


def test_rss_feed_parser() -> None:
    feed_xml = """
        <rss xmlns:media="http://search.yahoo.com/mrss/">
          <channel>
            <item>
              <title>Test &amp; vest</title>
              <link>https://example.com/vest/1</link>
              <description><![CDATA[
                <p>Opis <strong>vesti</strong>.</p>
              ]]></description>
              <pubDate>Wed, 23 Sep 2026 20:00:00 +0000</pubDate>
              <category>Sport</category>
              <media:content url="https://example.com/image.jpg" />
            </item>
          </channel>
        </rss>
    """

    articles = RssFeedParser().parse(
        feed_xml=feed_xml,
        feed_url="https://example.com/feed.xml",
        source_id="test",
        source_name="Test source",
        image_url_normalizer=lambda url: url,
    )

    assert len(articles) == 1
    assert articles[0].title == "Test & vest"
    assert articles[0].summary == "Opis vesti."
    assert articles[0].category == "SPORT"
    assert articles[0].image_url == "https://example.com/image.jpg"
    assert articles[0].published_at == datetime(
        2026,
        9,
        23,
        20,
        0,
        tzinfo=UTC,
    )


def test_rss_news_sources_have_unique_metadata() -> None:
    parser = RssFeedParser()
    sources = [
        RtsNewsSource(parser),
        DanasNewsSource(parser),
        N1NewsSource(parser),
        PolitikaNewsSource(parser),
        B92NewsSource(parser),
        BetaNewsSource(parser),
        JuzneVestiNewsSource(parser),
        NovaNewsSource(parser),
        VremeNewsSource(parser),
    ]

    assert len({source.id for source in sources}) == len(sources)
    assert all(source.id for source in sources)
    assert all(source.display_name for source in sources)


def test_article_url_normalizer_removes_tracking_data() -> None:
    normalizer = ArticleUrlNormalizer()

    normalized_url = normalizer.normalize(
        "HTTPS://Example.COM/article/"
        "?utm_source=test&category=tech&fbclid=value#section"
    )

    assert normalized_url == "https://example.com/article?category=tech"


def test_random_tone_analysis_strategy_returns_percentages() -> None:
    async def run_test() -> None:
        strategy = RandomToneAnalysisStrategy(random.Random(42))

        result = await strategy.analyze(
            create_news_article("https://example.com/article")
        )
        percentages = (
            result.negative_percentage,
            result.positive_percentage,
            result.neutral_percentage,
        )

        assert all(0 <= value <= 100 for value in percentages)
        assert abs(sum(percentages) - 100) < 0.01

    asyncio.run(run_test())


def test_groq_tone_analysis_client_uses_structured_output() -> None:
    async def run_test() -> None:
        completion = Mock()
        completion.choices = [
            Mock(
                message=Mock(
                    content=(
                        '{"negative": 20, "positive": 30, '
                        '"neutral": 50}'
                    )
                )
            )
        ]
        groq_client = Mock()
        groq_client.chat.completions.create = AsyncMock(
            return_value=completion
        )
        client = GroqToneAnalysisLlmClient(
            api_key="test-key",
            model="openai/gpt-oss-20b",
            timeout_seconds=30,
            max_retries=2,
            groq_client=groq_client,
        )

        result = await client.analyze_tone(
            title="Naslov",
            summary="Sazetak vesti",
        )

        assert result.negative == 20
        assert result.positive == 30
        assert result.neutral == 50

        request = groq_client.chat.completions.create.await_args.kwargs
        assert request["model"] == "openai/gpt-oss-20b"
        assert request["response_format"]["type"] == "json_schema"
        assert "zbir mora biti tacno 100" in (
            request["messages"][0]["content"]
        )
        json_schema = request["response_format"]["json_schema"]
        assert json_schema["strict"] is True
        assert json_schema["schema"]["additionalProperties"] is False

    asyncio.run(run_test())


def test_groq_client_reports_unavailability_on_rate_limit() -> None:
    async def run_test() -> None:
        groq_client = Mock()
        groq_client.chat.completions.create = AsyncMock(
            side_effect=create_rate_limit_error()
        )
        client = create_groq_client(groq_client)

        availability = await client.check_availability()

        assert availability.is_available is False
        assert "429" in (availability.reason or "")
        request = groq_client.chat.completions.create.await_args.kwargs
        assert request["max_completion_tokens"] == 1

    asyncio.run(run_test())


def test_groq_client_reports_availability_on_a_successful_probe() -> None:
    async def run_test() -> None:
        groq_client = Mock()
        groq_client.chat.completions.create = AsyncMock(
            return_value=Mock()
        )
        client = create_groq_client(groq_client)

        availability = await client.check_availability()

        assert availability.is_available is True
        assert availability.reason is None

    asyncio.run(run_test())


def test_groq_client_raises_unavailable_error_on_rate_limit() -> None:
    async def run_test() -> None:
        groq_client = Mock()
        groq_client.chat.completions.create = AsyncMock(
            side_effect=create_rate_limit_error()
        )
        client = create_groq_client(groq_client)

        try:
            await client.analyze_tone(
                title="Naslov",
                summary="Sazetak vesti",
            )
        except ToneAnalysisUnavailableError:
            return

        raise AssertionError(
            "Expected a ToneAnalysisUnavailableError."
        )

    asyncio.run(run_test())


def test_llm_tone_analysis_strategy_normalizes_response() -> None:
    async def run_test() -> None:
        article = create_news_article("https://example.com/article")
        client = Mock()
        client.analyze_tone = AsyncMock(
            return_value=LlmToneAnalysisResponse(
                negative=7,
                positive=1,
                neutral=2,
            )
        )
        strategy = LlmToneAnalysisStrategy(client)

        result = await strategy.analyze(article)

        assert result == ToneAnalysisResult(
            negative_percentage=70,
            positive_percentage=10,
            neutral_percentage=20,
        )
        client.analyze_tone.assert_awaited_once_with(
            title=article.title,
            summary=article.summary,
        )

    asyncio.run(run_test())


def test_llm_tone_analysis_strategy_rejects_zero_total() -> None:
    async def run_test() -> None:
        client = Mock()
        client.analyze_tone = AsyncMock(
            return_value=LlmToneAnalysisResponse(
                negative=0,
                positive=0,
                neutral=0,
            )
        )
        strategy = LlmToneAnalysisStrategy(client)

        try:
            await strategy.analyze(
                create_news_article("https://example.com/article")
            )
        except ValueError as error:
            assert str(error) == (
                "LLM tone analysis values must not all be zero."
            )
        else:
            raise AssertionError("Expected zero tone total to fail.")

    asyncio.run(run_test())


def test_tone_analysis_step_updates_context() -> None:
    async def run_test() -> None:
        article = create_news_article("https://example.com/article")
        context = ArticleProcessingContext(article=article)
        expected_result = ToneAnalysisResult(
            negative_percentage=20,
            positive_percentage=30,
            neutral_percentage=50,
        )
        strategy = Mock()
        strategy.analyze = AsyncMock(return_value=expected_result)

        transformed_context = await ToneAnalysisStep(
            strategy
        ).transform(context)

        assert transformed_context.article == article
        assert transformed_context.tone_analysis == expected_result
        strategy.analyze.assert_awaited_once_with(article)

    asyncio.run(run_test())


def test_tone_analysis_step_reuses_existing_result() -> None:
    async def run_test() -> None:
        existing_result = ToneAnalysisResult(
            negative_percentage=20,
            positive_percentage=30,
            neutral_percentage=50,
        )
        context = ArticleProcessingContext(
            article=create_news_article(
                "https://example.com/article"
            ),
            tone_analysis=existing_result,
        )
        strategy = Mock()
        strategy.analyze = AsyncMock()

        transformed_context = await ToneAnalysisStep(
            strategy
        ).transform(context)

        assert transformed_context is context
        strategy.analyze.assert_not_awaited()

    asyncio.run(run_test())


def test_news_article_processing_pipeline() -> None:
    async def run_test() -> None:
        pipeline = NewsArticleProcessingPipeline(
            steps=[
                UrlNormalizationStep(ArticleUrlNormalizer()),
                ArticleDeduplicationStep(),
            ]
        )
        original = create_news_article(
            "https://example.com/article?utm_source=first",
            title="Original",
        )
        updated = create_news_article(
            "https://example.com/article/?fbclid=value",
            title="Updated",
        )

        processed_articles = await pipeline.process([original, updated])

        assert len(processed_articles) == 1
        assert processed_articles[0].article == updated
        assert (
            processed_articles[0].normalized_url
            == "https://example.com/article"
        )

    asyncio.run(run_test())


def test_news_article_mapper_creates_stable_model() -> None:
    article = create_news_article(
        "https://example.com/article/?utm_source=test"
    )
    context = ArticleProcessingContext(
        article=article,
        normalized_url="https://example.com/article",
        tone_analysis=ToneAnalysisResult(
            negative_percentage=20,
            positive_percentage=30,
            neutral_percentage=50,
        ),
        tone_analysis_metadata=ToneAnalysisMetadata(
            input_hash="input-hash",
            provider="random",
            model_name="random",
            prompt_version="v1",
        ),
    )
    mapper = ProcessedArticleMapper()

    first_models = mapper.to_models(context)
    second_models = mapper.to_models(context)

    assert first_models.article.id == second_models.article.id
    assert first_models.article.id.startswith("test-")
    assert first_models.article.source_id == "test"
    assert (
        first_models.article.normalized_url
        == "https://example.com/article"
    )
    assert first_models.article.article_url == article.article_url
    assert first_models.analysis.tone is not None
    assert first_models.analysis.tone.negative_percentage == 20
    assert first_models.analysis.tone.positive_percentage == 30
    assert first_models.analysis.tone.neutral_percentage == 50
    assert first_models.analysis.tone.input_hash == "input-hash"
    assert first_models.analysis.tone.provider == "random"
    assert first_models.analysis.tone.model_name == "random"
    assert first_models.analysis.tone.prompt_version == "v1"


def test_polling_service_upserts_articles(tmp_path) -> None:
    async def run_test() -> None:
        database_url = URL.create(
            drivername="sqlite+aiosqlite",
            database=str(tmp_path / "polling.db"),
        )
        engine = create_async_engine(database_url)
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        source = Mock(spec=INewsSource)
        source.id = "test"
        source.display_name = "Test source"
        source.fetch_articles = AsyncMock(
            return_value=[
                create_news_article(
                    "https://example.com/article/?utm_source=test"
                )
            ]
        )
        article_url_normalizer = ArticleUrlNormalizer()
        tone_result = ToneAnalysisResult(
            negative_percentage=20,
            positive_percentage=30,
            neutral_percentage=50,
        )
        strategy = create_tone_strategy(
            AsyncMock(return_value=tone_result)
        )
        pipeline = NewsArticleProcessingPipeline(
            steps=[
                UrlNormalizationStep(article_url_normalizer),
                ArticleDeduplicationStep(),
                ExistingToneAnalysisStep(
                    ExistingToneAnalysisLoader(
                        session_factory=session_factory,
                        input_hasher=ToneAnalysisInputHasher(),
                        provider="random",
                        model_name="random",
                        prompt_version="v1",
                    )
                ),
                ToneAnalysisStep(strategy),
            ]
        )
        service = NewsSourcePollingService(
            sources=[source],
            pipeline=pipeline,
            persistence_service=ArticlePersistenceService(
                session_factory=session_factory,
                article_mapper=ProcessedArticleMapper(),
            ),
        )

        assert await service.refresh_once() == 1
        assert await service.refresh_once() == 0
        assert strategy.analyze.await_count == 1

        source.fetch_articles.return_value = [
            create_news_article(
                "https://example.com/article/?utm_source=test",
                title="Updated article",
            )
        ]
        assert await service.refresh_once() == 1
        assert strategy.analyze.await_count == 2

        source.fetch_articles.return_value = [
            create_news_article(
                "https://example.com/second-article"
            )
        ]
        assert await service.refresh_once() == 1
        assert strategy.analyze.await_count == 3

        source.fetch_articles.return_value = [
            create_news_article(
                "https://example.com/article/?utm_source=test",
                title="Updated article",
            )
        ]
        assert await service.refresh_once() == 0
        assert strategy.analyze.await_count == 3

        async with session_factory() as session:
            article_count = await session.scalar(
                select(func.count()).select_from(ArticleModel)
            )
            articles = await session.scalars(select(ArticleModel))
            analysis = await session.scalar(
                select(ArticleAnalysisModel)
            )
            tone_analysis = await session.scalar(
                select(ArticleToneAnalysisModel)
            )

        articles_by_url = {
            article.normalized_url: article
            for article in articles
        }
        assert article_count == 2
        assert articles_by_url[
            "https://example.com/article"
        ].is_active is True
        assert articles_by_url[
            "https://example.com/second-article"
        ].is_active is False
        assert analysis is not None
        assert tone_analysis is not None
        assert tone_analysis.input_hash is not None
        assert tone_analysis.provider == "random"
        assert tone_analysis.model_name == "random"
        assert tone_analysis.prompt_version == "v1"
        assert abs(
            tone_analysis.negative_percentage
            + tone_analysis.positive_percentage
            + tone_analysis.neutral_percentage
            - 100
        ) < 0.01

        await engine.dispose()

    asyncio.run(run_test())


def create_polling_service(
    sources: list[INewsSource],
    fetch_timeout_seconds: float = 60.0,
) -> NewsSourcePollingService:
    pipeline = Mock()
    pipeline.process = AsyncMock(side_effect=lambda articles: articles)
    persistence_service = Mock()
    persistence_service.persist = AsyncMock(
        side_effect=lambda contexts, source_id: len(contexts)
    )

    return NewsSourcePollingService(
        sources=sources,
        pipeline=pipeline,
        persistence_service=persistence_service,
        fetch_timeout_seconds=fetch_timeout_seconds,
    )


def create_source(source_id: str, fetch_articles) -> INewsSource:
    source = Mock(spec=INewsSource)
    source.id = source_id
    source.display_name = f"Source {source_id}"
    source.fetch_articles = fetch_articles
    return source


def test_polling_service_fetches_sources_concurrently() -> None:
    async def run_test() -> None:
        async def slow_fetch() -> list[NewsArticle]:
            await asyncio.sleep(0.1)
            return [
                create_news_article(
                    f"https://example.com/{random.random()}"
                )
            ]

        sources = [
            create_source(f"source-{index}", slow_fetch)
            for index in range(5)
        ]
        service = create_polling_service(sources)

        loop = asyncio.get_running_loop()
        started = loop.time()
        assert await service.refresh_once() == 5
        elapsed = loop.time() - started

        #sequential fetching would need at least 0.5 seconds
        assert elapsed < 0.4

    asyncio.run(run_test())


def test_polling_service_skips_a_source_that_times_out() -> None:
    async def run_test() -> None:
        async def hanging_fetch() -> list[NewsArticle]:
            await asyncio.sleep(10)
            return []

        async def working_fetch() -> list[NewsArticle]:
            return [
                create_news_article("https://example.com/working")
            ]

        service = create_polling_service(
            [
                create_source("hanging", hanging_fetch),
                create_source("working", working_fetch),
            ],
            fetch_timeout_seconds=0.05,
        )

        loop = asyncio.get_running_loop()
        started = loop.time()
        assert await service.refresh_once() == 1
        assert loop.time() - started < 1

    asyncio.run(run_test())


def test_polling_service_isolates_a_failing_source() -> None:
    async def run_test() -> None:
        async def failing_fetch() -> list[NewsArticle]:
            raise RuntimeError("feed is down")

        async def working_fetch() -> list[NewsArticle]:
            return [
                create_news_article("https://example.com/working")
            ]

        service = create_polling_service(
            [
                create_source("failing", failing_fetch),
                create_source("working", working_fetch),
            ]
        )

        assert await service.refresh_once() == 1

    asyncio.run(run_test())


def test_tone_analysis_step_limits_concurrency() -> None:
    async def run_test() -> None:
        active = 0
        peak = 0

        async def analyze(article: NewsArticle) -> ToneAnalysisResult:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.01)
            active -= 1
            return ToneAnalysisResult(
                negative_percentage=20,
                positive_percentage=30,
                neutral_percentage=50,
            )

        strategy = create_tone_strategy(AsyncMock(side_effect=analyze))
        step = ToneAnalysisStep(strategy, max_concurrency=3)
        contexts = [
            ArticleProcessingContext(
                article=create_news_article(
                    f"https://example.com/{index}"
                ),
                normalized_url=f"https://example.com/{index}",
            )
            for index in range(10)
        ]

        results = await step.process(contexts)

        assert len(results) == 10
        assert peak <= 3
        assert strategy.analyze.await_count == 10
        assert all(
            result.tone_analysis is not None for result in results
        )

    asyncio.run(run_test())


def test_tone_analysis_step_keeps_order_and_skips_analyzed() -> None:
    async def run_test() -> None:
        async def analyze(article: NewsArticle) -> ToneAnalysisResult:
            await asyncio.sleep(random.random() / 100)
            return ToneAnalysisResult(
                negative_percentage=20,
                positive_percentage=30,
                neutral_percentage=50,
            )

        strategy = create_tone_strategy(AsyncMock(side_effect=analyze))
        step = ToneAnalysisStep(strategy, max_concurrency=4)
        existing_tone = ToneAnalysisResult(
            negative_percentage=1,
            positive_percentage=2,
            neutral_percentage=97,
        )
        contexts = [
            ArticleProcessingContext(
                article=create_news_article(
                    f"https://example.com/{index}"
                ),
                normalized_url=f"https://example.com/{index}",
                tone_analysis=(
                    existing_tone if index % 2 == 0 else None
                ),
            )
            for index in range(10)
        ]

        results = await step.process(contexts)

        assert [
            result.normalized_url for result in results
        ] == [context.normalized_url for context in contexts]
        assert strategy.analyze.await_count == 5
        assert results[0].tone_analysis is existing_tone

    asyncio.run(run_test())


def test_tone_analysis_step_rejects_non_positive_concurrency() -> None:
    try:
        ToneAnalysisStep(Mock(), max_concurrency=0)
    except ValueError:
        return

    raise AssertionError("Expected a ValueError.")


def test_tone_analysis_step_survives_a_failing_provider() -> None:
    """One failing article must not discard the whole feed."""

    async def run_test() -> None:
        async def analyze(article: NewsArticle) -> ToneAnalysisResult:
            if article.article_url.endswith("/1"):
                raise RuntimeError("rate limit reached")

            return ToneAnalysisResult(
                negative_percentage=20,
                positive_percentage=30,
                neutral_percentage=50,
            )

        strategy = create_tone_strategy(AsyncMock(side_effect=analyze))
        step = ToneAnalysisStep(strategy, max_concurrency=2)
        contexts = [
            ArticleProcessingContext(
                article=create_news_article(
                    f"https://example.com/{index}"
                ),
                normalized_url=f"https://example.com/{index}",
            )
            for index in range(3)
        ]

        results = await step.process(contexts)

        assert [
            result.tone_analysis is not None for result in results
        ] == [True, False, True]

    asyncio.run(run_test())


def test_tone_analysis_step_skips_everything_when_unavailable() -> None:
    """An exhausted provider must not be called once per article."""

    async def run_test() -> None:
        analyze = AsyncMock()
        strategy = create_tone_strategy(
            analyze,
            ToneAnalysisAvailability.unavailable("no tokens left"),
        )
        step = ToneAnalysisStep(strategy, max_concurrency=2)
        contexts = [
            ArticleProcessingContext(
                article=create_news_article(
                    f"https://example.com/{index}"
                ),
                normalized_url=f"https://example.com/{index}",
            )
            for index in range(5)
        ]

        results = await step.process(contexts)

        assert results == contexts
        analyze.assert_not_awaited()
        strategy.check_availability.assert_awaited_once()

    asyncio.run(run_test())


def test_tone_analysis_step_skips_check_when_nothing_is_pending() -> None:
    async def run_test() -> None:
        analyze = AsyncMock()
        strategy = create_tone_strategy(analyze)
        step = ToneAnalysisStep(strategy)
        contexts = [
            ArticleProcessingContext(
                article=create_news_article("https://example.com/1"),
                normalized_url="https://example.com/1",
                tone_analysis=ToneAnalysisResult(
                    negative_percentage=20,
                    positive_percentage=30,
                    neutral_percentage=50,
                ),
            )
        ]

        results = await step.process(contexts)

        assert results == contexts
        strategy.check_availability.assert_not_awaited()
        analyze.assert_not_awaited()

    asyncio.run(run_test())


def test_tone_analysis_step_stops_after_the_provider_runs_out() -> None:
    """A spent quota stops the batch instead of failing per article."""

    async def run_test() -> None:
        async def analyze(article: NewsArticle) -> ToneAnalysisResult:
            raise ToneAnalysisUnavailableError("quota exceeded")

        analyze_mock = AsyncMock(side_effect=analyze)
        strategy = create_tone_strategy(analyze_mock)
        step = ToneAnalysisStep(strategy, max_concurrency=1)
        contexts = [
            ArticleProcessingContext(
                article=create_news_article(
                    f"https://example.com/{index}"
                ),
                normalized_url=f"https://example.com/{index}",
            )
            for index in range(5)
        ]

        results = await step.process(contexts)

        assert all(
            result.tone_analysis is None for result in results
        )
        assert analyze_mock.await_count == 1

    asyncio.run(run_test())


def test_persistence_stores_articles_without_a_tone(tmp_path) -> None:
    """A pending tone must not cost the article its place in the feed."""

    async def run_test() -> None:
        database_url = URL.create(
            drivername="sqlite+aiosqlite",
            database=str(tmp_path / "pending.db"),
        )
        engine = create_async_engine(database_url)
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        persistence_service = ArticlePersistenceService(
            session_factory=session_factory,
            article_mapper=ProcessedArticleMapper(),
        )
        pending_url = "https://example.com/pending"
        pending_context = ArticleProcessingContext(
            article=create_news_article(pending_url),
            normalized_url=pending_url,
        )

        assert await persistence_service.persist(
            [pending_context],
            source_id="test",
        ) == 1

        async with session_factory() as session:
            article = await session.scalar(select(ArticleModel))
            analysis_count = await session.scalar(
                select(func.count()).select_from(ArticleAnalysisModel)
            )
            visible_articles = await ArticleRepository(
                session
            ).list_articles()

        assert article is not None
        assert article.normalized_url == pending_url
        assert article.is_active is True
        assert analysis_count == 0
        #the inner join hides it until the tone analysis lands
        assert visible_articles == []

        #the retry attaches the analysis and the article shows up
        assert await persistence_service.persist(
            [
                replace(
                    pending_context,
                    tone_analysis=ToneAnalysisResult(
                        negative_percentage=20,
                        positive_percentage=30,
                        neutral_percentage=50,
                    ),
                    tone_analysis_metadata=ToneAnalysisMetadata(
                        input_hash="input-hash",
                        provider="random",
                        model_name="random",
                        prompt_version="v1",
                    ),
                )
            ],
            source_id="test",
        ) == 0

        async with session_factory() as session:
            visible_articles = await ArticleRepository(
                session
            ).list_articles()

        assert [
            article.normalized_url for article in visible_articles
        ] == [pending_url]

        await engine.dispose()

    asyncio.run(run_test())


def test_persistence_keeps_unanalyzed_articles_active(tmp_path) -> None:
    """Articles whose analysis failed must not be deactivated."""

    async def run_test() -> None:
        database_url = URL.create(
            drivername="sqlite+aiosqlite",
            database=str(tmp_path / "unanalyzed.db"),
        )
        engine = create_async_engine(database_url)
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        persistence_service = ArticlePersistenceService(
            session_factory=session_factory,
            article_mapper=ProcessedArticleMapper(),
        )
        tone = ToneAnalysisResult(
            negative_percentage=20,
            positive_percentage=30,
            neutral_percentage=50,
        )
        metadata = ToneAnalysisMetadata(
            input_hash="input-hash",
            provider="random",
            model_name="random",
            prompt_version="v1",
        )

        def build_context(url: str, analyzed: bool):
            return ArticleProcessingContext(
                article=create_news_article(url),
                normalized_url=url,
                tone_analysis=tone if analyzed else None,
                tone_analysis_metadata=metadata if analyzed else None,
            )

        analyzed_url = "https://example.com/analyzed"
        pending_url = "https://example.com/pending"

        assert await persistence_service.persist(
            [
                build_context(analyzed_url, analyzed=True),
                build_context(pending_url, analyzed=True),
            ],
            source_id="test",
        ) == 2

        #the second article fails analysis but is still in the feed
        assert await persistence_service.persist(
            [
                build_context(analyzed_url, analyzed=True),
                build_context(pending_url, analyzed=False),
            ],
            source_id="test",
        ) == 0

        async with session_factory() as session:
            articles = await session.scalars(select(ArticleModel))
            active_by_url = {
                article.normalized_url: article.is_active
                for article in articles
            }

        assert active_by_url[analyzed_url] is True
        assert active_by_url[pending_url] is True

        await engine.dispose()

    asyncio.run(run_test())
