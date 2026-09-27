from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.tone_analysis.services.ExistingToneAnalysisLoader import (
    ExistingToneAnalysisLoader,
)


class ExistingToneAnalysisStep:
    def __init__(
        self,
        loader: ExistingToneAnalysisLoader,
    ) -> None:
        self._loader = loader

    async def process(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        return await self._loader.load_existing(contexts)
