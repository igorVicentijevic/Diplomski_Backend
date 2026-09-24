from typing import Protocol

from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)


class ToneAnalysisStrategy(Protocol):
    async def analyze(
        self,
        article: NewsArticle,
    ) -> ToneAnalysisResult:
        ...
