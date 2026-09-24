from abc import ABC, abstractmethod

from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)


class ToneAnalysisStrategy(ABC):
    @abstractmethod
    async def analyze(
        self,
        article: NewsArticle,
    ) -> ToneAnalysisResult:
        ...
