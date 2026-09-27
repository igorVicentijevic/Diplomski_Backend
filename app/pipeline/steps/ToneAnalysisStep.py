from dataclasses import replace

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.pipeline.IArticleTransformationStep import (
    IArticleTransformationStep,
)
from app.tone_analysis.strategies.IToneAnalysisStrategy import (
    IToneAnalysisStrategy,
)


class ToneAnalysisStep(IArticleTransformationStep):
    def __init__(
        self,
        strategy: IToneAnalysisStrategy,
    ) -> None:
        self._strategy = strategy

    async def transform(
        self,
        context: ArticleProcessingContext,
    ) -> ArticleProcessingContext:
        if context.tone_analysis is not None:
            return context

        tone_analysis = await self._strategy.analyze(context.article)

        return replace(
            context,
            tone_analysis=tone_analysis,
        )
