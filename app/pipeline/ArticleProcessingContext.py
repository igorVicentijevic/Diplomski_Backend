from dataclasses import dataclass

from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)


@dataclass(frozen=True, slots=True)
class ArticleProcessingContext:
    article: NewsArticle
    normalized_url: str | None = None
    tone_analysis: ToneAnalysisResult | None = None
