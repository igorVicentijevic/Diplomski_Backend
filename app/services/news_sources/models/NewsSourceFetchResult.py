from dataclasses import dataclass, field

from app.news_sources.INewsSource import INewsSource
from app.news_sources.models.NewsArticle import NewsArticle


@dataclass(frozen=True, slots=True)
class NewsSourceFetchResult:
    source: INewsSource
    articles: list[NewsArticle] = field(default_factory=list)
    failed: bool = False
