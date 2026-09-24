import hashlib

from app.articles.models.ArticleModel import ArticleModel
from app.news_sources.models.NewsArticle import NewsArticle
from app.services.news_sources.ArticleUrlNormalizer import (
    ArticleUrlNormalizer,
)


class NewsArticleMapper:
    def __init__(self, url_normalizer: ArticleUrlNormalizer) -> None:
        self._url_normalizer = url_normalizer

    def to_model(self, article: NewsArticle) -> ArticleModel:
        
        normalized_url = self._url_normalizer.normalize(
            article.article_url
        )

        article_hash = hashlib.sha256(
            f"{article.source_id}:{normalized_url}".encode("utf-8")
        ).hexdigest()

        return ArticleModel(
            id=f"{article.source_id}-{article_hash}",
            title=article.title,
            summary=article.summary,
            source=article.source_name,
            category=article.category,
            published_at=article.published_at,
            image_url=article.image_url,
            article_url=article.article_url,
            normalized_url=normalized_url,
            related_city_ids=[],
        )
