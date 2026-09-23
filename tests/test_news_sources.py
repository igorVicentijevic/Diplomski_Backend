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
from app.news_sources.NewsSourcePollingService import (
    NewsSourcePollingService,
)
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.models.NewsArticle import NewsArticle


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
                NewsArticle(
                    source_id="test",
                    source_name="Test source",
                    title="Test article",
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
                    article_url=(
                        "https://example.com/article/?utm_source=test"
                    ),
                )
            ]
        )
        service = NewsSourcePollingService(
            sources=[source],
            session_factory=session_factory,
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
