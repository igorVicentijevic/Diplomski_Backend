from dataclasses import replace

from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.pipeline.ArticleTransformationStep import (
    ArticleTransformationStep,
)
from app.services.news_sources.ArticleUrlNormalizer import (
    ArticleUrlNormalizer,
)


class UrlNormalizationStep(ArticleTransformationStep):
    def __init__(self, url_normalizer: ArticleUrlNormalizer) -> None:
        self._url_normalizer = url_normalizer

    async def transform(
        self,
        context: ArticleProcessingContext,
    ) -> ArticleProcessingContext:
        return replace(
            context,
            normalized_url=self._url_normalizer.normalize(
                context.article.article_url
            ),
        )
