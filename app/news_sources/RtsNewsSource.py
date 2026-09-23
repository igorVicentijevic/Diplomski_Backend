import re

import httpx

from app.news_sources.NewsSource import NewsSource
from app.news_sources.RssFeedParser import RssFeedParser
from app.news_sources.models.NewsArticle import NewsArticle


class RtsNewsSource(NewsSource):
    _FEED_URL = "https://www.rts.rs/vesti/rss.html"

    def __init__(self, parser: RssFeedParser) -> None:
        self._parser = parser

    @property
    def id(self) -> str:
        return "rts"

    @property
    def display_name(self) -> str:
        return "RTS"

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
        secure_url = re.sub(
            r"^http://(?:www\.)?rts\.rs/",
            "https://www.rts.rs/",
            url,
            flags=re.IGNORECASE,
        )
        normalized_path = secure_url.replace(
            "/upload/thumbnail//",
            "/upload//",
        )
        parent_path, separator, file_name = normalized_path.rpartition("/")
        if separator and parent_path.endswith(f"/{file_name}"):
            return parent_path
        return normalized_path
