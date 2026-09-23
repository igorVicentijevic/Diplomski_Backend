import html
import re
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

from app.articles.schemas.NewsCategory import NewsCategory
from app.news_sources.models.NewsArticle import NewsArticle


class RssFeedParser:
    def parse(
        self,
        feed_xml: str | bytes,
        feed_url: str,
        source_id: str,
        source_name: str,
        image_url_normalizer: Callable[[str], str],
    ) -> list[NewsArticle]:
        root = ElementTree.fromstring(feed_xml)
        articles: list[NewsArticle] = []

        for item in root.iter():
            if self._local_name(item.tag) != "item":
                continue

            article = self._parse_item(
                item=item,
                feed_url=feed_url,
                source_id=source_id,
                source_name=source_name,
                image_url_normalizer=image_url_normalizer,
            )
            if article is not None:
                articles.append(article)

        return list(
            {
                article.article_url: article
                for article in articles
            }.values()
        )

    def _parse_item(
        self,
        item: ElementTree.Element,
        feed_url: str,
        source_id: str,
        source_name: str,
        image_url_normalizer: Callable[[str], str],
    ) -> NewsArticle | None:
        title = self._clean_html(self._text(item, "title"))
        article_url = self._web_url(
            urljoin(feed_url, self._text(item, "link"))
        )
        if not title or article_url is None:
            return None

        description_html = (
            self._text(item, "description")
            or self._text(item, "encoded")
        )
        image_url = self._find_image_url(item, description_html)
        if image_url is not None:
            image_url = self._web_url(
                urljoin(
                    feed_url,
                    image_url_normalizer(image_url),
                )
            )

        categories = " ".join(self._texts(item, "category"))
        return NewsArticle(
            source_id=source_id,
            source_name=source_name,
            title=title,
            summary=self._clean_html(description_html),
            category=self._category(categories).value,
            published_at=self._published_at(
                self._text(item, "pubDate")
            ),
            image_url=image_url,
            article_url=article_url,
        )

    def _find_image_url(
        self,
        item: ElementTree.Element,
        description_html: str,
    ) -> str | None:
        for element in item.iter():
            if self._local_name(element.tag) not in {
                "content",
                "thumbnail",
                "enclosure",
                "img",
            }:
                continue

            image_url = (
                element.attrib.get("url")
                or element.attrib.get("src")
            )
            if image_url:
                return image_url

        match = re.search(
            r"""<img[^>]+src\s*=\s*["']([^"']+)["']""",
            description_html,
            re.IGNORECASE,
        )
        return match.group(1) if match else None

    @staticmethod
    def _clean_html(value: str) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", value)
        normalized = re.sub(
            r"\s+",
            " ",
            html.unescape(without_tags),
        ).strip()
        return re.sub(r"\s+([,.!?;:])", r"\1", normalized)

    @staticmethod
    def _published_at(value: str) -> datetime:
        try:
            published_at = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return datetime.now(UTC)

        if published_at.tzinfo is None:
            return published_at.replace(tzinfo=UTC)
        return published_at.astimezone(UTC)

    @staticmethod
    def _web_url(value: str) -> str | None:
        parsed = urlsplit(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        return value.strip()

    @staticmethod
    def _category(value: str) -> NewsCategory:
        normalized = value.casefold()
        if "спорт" in normalized or "sport" in normalized:
            return NewsCategory.SPORT
        if "култур" in normalized or "kultur" in normalized:
            return NewsCategory.CULTURE
        if any(
            word in normalized
            for word in ("економ", "biznis", "privreda")
        ):
            return NewsCategory.BUSINESS
        if "здрав" in normalized or "health" in normalized:
            return NewsCategory.HEALTH
        if any(
            word in normalized
            for word in ("технолог", "наук", "digital")
        ):
            return NewsCategory.TECHNOLOGY
        if any(
            word in normalized
            for word in (
                "свет",
                "svet",
                "region",
                "evropa",
                "украјин",
            )
        ):
            return NewsCategory.WORLD
        return NewsCategory.SERBIA

    def _text(
        self,
        element: ElementTree.Element,
        name: str,
    ) -> str:
        texts = self._texts(element, name)
        return texts[0] if texts else ""

    def _texts(
        self,
        element: ElementTree.Element,
        name: str,
    ) -> list[str]:
        return [
            "".join(child.itertext()).strip()
            for child in element
            if self._local_name(child.tag) == name
            and "".join(child.itertext()).strip()
        ]

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", maxsplit=1)[-1].split(":")[-1]
