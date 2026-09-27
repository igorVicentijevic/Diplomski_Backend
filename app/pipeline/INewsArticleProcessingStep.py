from typing import Protocol

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)


class INewsArticleProcessingStep(Protocol):
    async def process(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        ...
