import httpx

from app.news_sources.NewsSource import NewsSource
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.models.NewsArticle import NewsArticle


class RssNewsSource(NewsSource):
    _SOURCE_ID = ""
    _DISPLAY_NAME = ""
    _FEED_URL = ""

    def __init__(self, parser: RssFeedParser) -> None:
        self._parser = parser

    @property
    def id(self) -> str:
        return self._SOURCE_ID

    @property
    def display_name(self) -> str:
        return self._DISPLAY_NAME

    async def fetch_articles(self) -> list[NewsArticle]:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=20,
            headers={"User-Agent": "Tok News Aggregator"},
        ) as client:
            response = await client.get(self._FEED_URL)
            response.raise_for_status()

        return self._parser.parse(
            feed_xml=response.content,
            feed_url=self._FEED_URL,
            source_id=self.id,
            source_name=self.display_name,
            image_url_normalizer=self._normalize_image_url,
        )

    @staticmethod
    def _normalize_image_url(url: str) -> str:
        return url
