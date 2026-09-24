import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

from sqlalchemy import func, select
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.articles.models.ArticleModel import ArticleModel
from app.database.Base import Base
from app.news_sources.NewsSource import NewsSource
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.models.NewsArticle import NewsArticle
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


def test_news_article_deduplicator_uses_normalized_url() -> None:
    deduplicator = NewsArticleDeduplicator(ArticleUrlNormalizer())
    original = create_news_article(
        "https://example.com/article?utm_source=first",
        title="Original",
    )
    updated = create_news_article(
        "https://example.com/article/?fbclid=value",
        title="Updated",
    )

    unique_articles = deduplicator.deduplicate([original, updated])

    assert unique_articles == [updated]


def test_news_article_mapper_creates_stable_model() -> None:
    mapper = NewsArticleMapper(ArticleUrlNormalizer())
    article = create_news_article(
        "https://example.com/article/?utm_source=test"
    )

    first_model = mapper.to_model(article)
    second_model = mapper.to_model(article)

    assert first_model.id == second_model.id
    assert first_model.id.startswith("test-")
    assert first_model.normalized_url == "https://example.com/article"
    assert first_model.article_url == article.article_url


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
        service = NewsSourcePollingService(
            sources=[source],
            session_factory=session_factory,
            article_mapper=NewsArticleMapper(article_url_normalizer),
            article_deduplicator=NewsArticleDeduplicator(
                article_url_normalizer
            ),
        )

        assert await service.refresh_once() == 1
        assert await service.refresh_once() == 0

        async with session_factory() as session:
            article_count = await session.scalar(
                select(func.count()).select_from(ArticleModel)
            )
            article = await session.scalar(select(ArticleModel))

        assert article_count == 1
        assert article is not None
        assert article.normalized_url == "https://example.com/article"

        await engine.dispose()

    asyncio.run(run_test())
