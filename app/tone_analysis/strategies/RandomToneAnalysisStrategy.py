import random

from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)
from app.tone_analysis.strategies.ToneAnalysisStrategy import (
    ToneAnalysisStrategy,
)


class RandomToneAnalysisStrategy(ToneAnalysisStrategy):
    def __init__(
        self,
        random_generator: random.Random | None = None,
    ) -> None:
        self._random_generator = random_generator or random.Random()

    async def analyze(
        self,
        article: NewsArticle,
    ) -> ToneAnalysisResult:
        del article

        weights = [
            self._random_generator.random()
            for _ in range(3)
        ]
        total = sum(weights)

        if total == 0:
            percentages = [33.33, 33.33, 33.34]
        else:
            percentages = [
                round(weight / total * 100, 2)
                for weight in weights
            ]
            adjustment_index = max(
                range(len(weights)),
                key=weights.__getitem__,
            )
            percentages[adjustment_index] = round(
                percentages[adjustment_index]
                + 100
                - sum(percentages),
                2,
            )

        return ToneAnalysisResult(
            negative_percentage=percentages[0],
            positive_percentage=percentages[1],
            neutral_percentage=percentages[2],
        )
