from app.news_sources.models.NewsArticle import NewsArticle
from app.services.news_sources.ArticleUrlNormalizer import (
    ArticleUrlNormalizer,
)


class NewsArticleDeduplicator:
    def __init__(self, url_normalizer: ArticleUrlNormalizer) -> None:
        self._url_normalizer = url_normalizer

    def deduplicate(
        self,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:
        articles_by_url = {
            self._url_normalizer.normalize(article.article_url): article
            for article in articles
        }

        return list(articles_by_url.values())
