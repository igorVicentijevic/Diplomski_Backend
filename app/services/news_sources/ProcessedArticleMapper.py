import hashlib
from datetime import UTC, datetime

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel
from app.articles.models.ArticleModel import ArticleModel
from app.articles.models.ArticleToneAnalysisModel import (
    ArticleToneAnalysisModel,
)
from app.pipeline.ArticleProcessingContext import (
    ArticleProcessingContext,
)
from app.services.news_sources.models.ProcessedArticleModels import (
    ProcessedArticleModels,
)


class ProcessedArticleMapper:
    def to_models(
        self,
        context: ArticleProcessingContext,
    ) -> ProcessedArticleModels:
        if context.normalized_url is None:
            raise ValueError(
                "Article URL must be normalized before mapping."
            )

        if context.tone_analysis is None:
            raise ValueError(
                "Article tone must be analyzed before mapping."
            )

        article = context.article
        article_hash = hashlib.sha256(
            (
                f"{article.source_id}:"
                f"{context.normalized_url}"
            ).encode("utf-8")
        ).hexdigest()
        article_id = f"{article.source_id}-{article_hash}"

        article_model = ArticleModel(
            id=article_id,
            title=article.title,
            summary=article.summary,
            source=article.source_name,
            category=article.category,
            published_at=article.published_at,
            image_url=article.image_url,
            article_url=article.article_url,
            normalized_url=context.normalized_url,
            related_city_ids=[],
        )
        tone_model = ArticleToneAnalysisModel(
            article_id=article_id,
            negative_percentage=(
                context.tone_analysis.negative_percentage
            ),
            positive_percentage=(
                context.tone_analysis.positive_percentage
            ),
            neutral_percentage=(
                context.tone_analysis.neutral_percentage
            ),
        )
        analysis_model = ArticleAnalysisModel(
            article_id=article_id,
            processed_at=datetime.now(UTC),
            tone=tone_model,
        )

        return ProcessedArticleModels(
            article=article_model,
            analysis=analysis_model,
        )
