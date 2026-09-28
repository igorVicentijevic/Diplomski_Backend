from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.clients.IToneAnalysisLlmClient import (
    IToneAnalysisLlmClient,
)
from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)
from app.tone_analysis.models.ToneAnalysisAvailability import (
    ToneAnalysisAvailability,
)
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)
from app.tone_analysis.strategies.IToneAnalysisStrategy import (
    IToneAnalysisStrategy,
)


class LlmToneAnalysisStrategy(IToneAnalysisStrategy):
    def __init__(
        self,
        client: IToneAnalysisLlmClient,
    ) -> None:
        self._client = client

    async def check_availability(self) -> ToneAnalysisAvailability:
        return await self._client.check_availability()

    async def analyze(
        self,
        article: NewsArticle,
    ) -> ToneAnalysisResult:
        response = await self._client.analyze_tone(
            title=article.title,
            summary=article.summary,
        )

        return self._normalize(response)

    @staticmethod
    def _normalize(
        response: LlmToneAnalysisResponse,
    ) -> ToneAnalysisResult:
        values = [
            response.negative,
            response.positive,
            response.neutral,
        ]
        total = sum(values)
        if total == 0:
            raise ValueError(
                "LLM tone analysis values must not all be zero."
            )

        percentages = [
            round(value / total * 100, 2)
            for value in values
        ]
        adjustment_index = max(
            range(len(values)),
            key=values.__getitem__,
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
