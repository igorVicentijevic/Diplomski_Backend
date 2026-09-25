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

# Mapper class to convert processed article data into database models.
class ProcessedArticleMapper:

    def __generate_article_hash(
        self,
        source_id: str,
        normalized_url: str,
    ) -> str:
        return hashlib.sha256(
            (
                f"{source_id}:"
                f"{normalized_url}"
            ).encode("utf-8")
        ).hexdigest()

    def __generate_ArticleModel(self, article, article_id, context): 
        return ArticleModel(
            id=article_id,
            source_id=article.source_id,
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

    def __generate_ToneModel(self, article_id, context):
        return ArticleToneAnalysisModel(
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
            input_hash=context.tone_analysis_metadata.input_hash,
            provider=context.tone_analysis_metadata.provider,
            model_name=context.tone_analysis_metadata.model_name,
            prompt_version=(
                context.tone_analysis_metadata.prompt_version
            ),
        )

    

    def __generate_AnalysisModel(self, article_id, tone_model, context):
        return ArticleAnalysisModel(
            article_id=article_id,
            processed_at=(
                context.tone_analysis_processed_at
                or datetime.now(UTC)
            ),
            tone=tone_model,
        )

    def __generate_agent_id(self, article, normalized_url: str) -> str:
        return f"{article.source_id}-{self.__generate_article_hash(article.source_id, normalized_url)}"

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

        if context.tone_analysis_metadata is None:
            raise ValueError(
                "Article tone metadata must exist before mapping."
            )

        article = context.article

       

        article_id = self.__generate_agent_id(article, normalized_url=context.normalized_url)

        article_model = self.__generate_ArticleModel(article, article_id, context)

        tone_model = self.__generate_ToneModel(article_id, context)
        
        analysis_model = self.__generate_AnalysisModel(article_id, tone_model, context)
        
        return ProcessedArticleModels(
            article=article_model,
            analysis=analysis_model,
        )
