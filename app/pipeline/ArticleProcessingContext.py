from dataclasses import dataclass
from datetime import datetime

from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)
from app.tone_analysis.models.ToneAnalysisMetadata import (
    ToneAnalysisMetadata,
)


@dataclass(frozen=True, slots=True)
class ArticleProcessingContext:
    article: NewsArticle
    normalized_url: str | None = None
    tone_analysis: ToneAnalysisResult | None = None
    tone_analysis_metadata: ToneAnalysisMetadata | None = None
    tone_analysis_processed_at: datetime | None = None
