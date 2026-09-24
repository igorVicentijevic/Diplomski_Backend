from dataclasses import replace

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.pipeline.ArticleTransformationStep import (
    ArticleTransformationStep,
)
from app.tone_analysis.strategies.ToneAnalysisStrategy import (
    ToneAnalysisStrategy,
)


class ToneAnalysisStep(ArticleTransformationStep):
    def __init__(
        self,
        strategy: ToneAnalysisStrategy,
    ) -> None:
        self._strategy = strategy

    async def transform(
        self,
        context: ArticleProcessingContext,
    ) -> ArticleProcessingContext:
        tone_analysis = await self._strategy.analyze(context.article)

        return replace(
            context,
            tone_analysis=tone_analysis,
        )
