import hashlib

from app.articles.models.ArticleModel import ArticleModel
from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)


class NewsArticleMapper:
    def to_model(
        self,
        context: ArticleProcessingContext,
    ) -> ArticleModel:
        if context.normalized_url is None:
            raise ValueError(
                "Article URL must be normalized before mapping."
            )

        article_hash = hashlib.sha256(
            (
                f"{context.article.source_id}:"
                f"{context.normalized_url}"
            ).encode("utf-8")
        ).hexdigest()

        return ArticleModel(
            id=f"{context.article.source_id}-{article_hash}",
            title=context.article.title,
            summary=context.article.summary,
            source=context.article.source_name,
            category=context.article.category,
            published_at=context.article.published_at,
            image_url=context.article.image_url,
            article_url=context.article.article_url,
            normalized_url=context.normalized_url,
            related_city_ids=[],
        )
