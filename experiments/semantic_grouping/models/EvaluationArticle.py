from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EvaluationArticle:
    article_id: str
    title: str
    summary: str
    source: str
    published_at: datetime
