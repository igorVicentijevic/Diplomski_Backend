from typing import Protocol

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)


class NewsArticleProcessingStep(Protocol):
    async def process(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        ...
