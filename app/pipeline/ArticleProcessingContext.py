from dataclasses import dataclass

from app.news_sources.models.NewsArticle import NewsArticle


@dataclass(frozen=True, slots=True)
class ArticleProcessingContext:
    article: NewsArticle
    normalized_url: str | None = None
