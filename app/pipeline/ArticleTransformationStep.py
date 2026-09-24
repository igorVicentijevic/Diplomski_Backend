from abc import ABC, abstractmethod

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)


class ArticleTransformationStep(ABC):
    async def process(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        return [
            await self.transform(context)
            for context in contexts
        ]

    @abstractmethod
    async def transform(
        self,
        context: ArticleProcessingContext,
    ) -> ArticleProcessingContext:
        ...
