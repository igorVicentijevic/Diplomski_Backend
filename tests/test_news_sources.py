import asyncio
import random
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

from sqlalchemy import func, select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel
from app.articles.models.ArticleModel import ArticleModel
from app.articles.models.ArticleToneAnalysisModel import (
    ArticleToneAnalysisModel,
)
from app.database.Base import Base
from app.news_sources.NewsSource import NewsSource
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.models.NewsArticle import NewsArticle
from app.pipeline.ArticleProcessingContext import ArticleProcessingContext
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
from app.tone_analysis.clients.GroqToneAnalysisLlmClient import (
    GroqToneAnalysisLlmClient,
)
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)
from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)
from app.tone_analysis.strategies.LlmToneAnalysisStrategy import (
    LlmToneAnalysisStrategy,
)
from app.tone_analysis.strategies.RandomToneAnalysisStrategy import (
    RandomToneAnalysisStrategy,
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
    )
    mapper = ProcessedArticleMapper()

    first_models = mapper.to_models(context)
    second_models = mapper.to_models(context)

    assert first_models.article.id == second_models.article.id
    assert first_models.article.id.startswith("test-")
    assert (
        first_models.article.normalized_url
        == "https://example.com/article"
    )
    assert first_models.article.article_url == article.article_url
    assert first_models.analysis.tone is not None
    assert first_models.analysis.tone.negative_percentage == 20
    assert first_models.analysis.tone.positive_percentage == 30
    assert first_models.analysis.tone.neutral_percentage == 50


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

        source = Mock(spec=NewsSource)
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
        processing_pipeline = NewsArticleProcessingPipeline(
            steps=[
                UrlNormalizationStep(article_url_normalizer),
                ArticleDeduplicationStep(),
                ToneAnalysisStep(
                    RandomToneAnalysisStrategy(random.Random(42))
                ),
            ]
        )
        service = NewsSourcePollingService(
            sources=[source],
            processing_pipeline=processing_pipeline,
            persistence_service=ArticlePersistenceService(
                session_factory=session_factory,
                article_mapper=ProcessedArticleMapper(),
            ),
        )

        assert await service.refresh_once() == 1
        assert await service.refresh_once() == 0

        async with session_factory() as session:
            article_count = await session.scalar(
                select(func.count()).select_from(ArticleModel)
            )
            article = await session.scalar(select(ArticleModel))
            analysis = await session.scalar(
                select(ArticleAnalysisModel)
            )
            tone_analysis = await session.scalar(
                select(ArticleToneAnalysisModel)
            )

        assert article_count == 1
        assert article is not None
        assert article.normalized_url == "https://example.com/article"
        assert analysis is not None
        assert analysis.article_id == article.id
        assert tone_analysis is not None
        assert tone_analysis.article_id == article.id
        assert abs(
            tone_analysis.negative_percentage
            + tone_analysis.positive_percentage
            + tone_analysis.neutral_percentage
            - 100
        ) < 0.01

        await engine.dispose()

    asyncio.run(run_test())
