from abc import ABC, abstractmethod

from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.models.ToneAnalysisAvailability import (
    ToneAnalysisAvailability,
)
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)


class IToneAnalysisStrategy(ABC):
    @abstractmethod
    async def check_availability(self) -> ToneAnalysisAvailability:
        """Tells whether a batch of analyses can be started at all."""
        ...

    @abstractmethod
    async def analyze(
        self,
        article: NewsArticle,
    ) -> ToneAnalysisResult:
        ...
