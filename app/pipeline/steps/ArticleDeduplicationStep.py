from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)


class ArticleDeduplicationStep:
    async def process(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        contexts_by_url: dict[str, ArticleProcessingContext] = {}

        for context in contexts:
            if context.normalized_url is None:
                raise ValueError(
                    "Article URL must be normalized before deduplication."
                )

            contexts_by_url[context.normalized_url] = context

        return list(contexts_by_url.values())
