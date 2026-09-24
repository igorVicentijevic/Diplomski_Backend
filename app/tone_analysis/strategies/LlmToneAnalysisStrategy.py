from app.news_sources.models.NewsArticle import NewsArticle
from app.tone_analysis.clients.ToneAnalysisLlmClient import (
    ToneAnalysisLlmClient,
)
from app.tone_analysis.models.LlmToneAnalysisResponse import (
    LlmToneAnalysisResponse,
)
from app.tone_analysis.models.ToneAnalysisResult import (
    ToneAnalysisResult,
)
from app.tone_analysis.strategies.ToneAnalysisStrategy import (
    ToneAnalysisStrategy,
)


class LlmToneAnalysisStrategy(ToneAnalysisStrategy):
    def __init__(
        self,
        client: ToneAnalysisLlmClient,
    ) -> None:
        self._client = client

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
