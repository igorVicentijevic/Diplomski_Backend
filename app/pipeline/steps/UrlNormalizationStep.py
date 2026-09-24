from dataclasses import replace

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.services.news_sources.ArticleUrlNormalizer import (
    ArticleUrlNormalizer,
)


class UrlNormalizationStep:
    def __init__(self, url_normalizer: ArticleUrlNormalizer) -> None:
        self._url_normalizer = url_normalizer

    async def process(
        self,
        contexts: list[ArticleProcessingContext],
    ) -> list[ArticleProcessingContext]:
        return [
            replace(
                context,
                normalized_url=self._url_normalizer.normalize(
                    context.article.article_url
                ),
            )
            for context in contexts
        ]
