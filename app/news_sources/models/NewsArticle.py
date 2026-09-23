from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NewsArticle:
    source_id: str
    source_name: str
    title: str
    summary: str
    category: str
    published_at: datetime
    image_url: str | None
    article_url: str
