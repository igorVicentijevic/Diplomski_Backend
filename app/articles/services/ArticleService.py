from datetime import UTC

from app.articles.models.ArticleModel import ArticleModel
from app.articles.repositories.ArticleRepository import ArticleRepository
from app.articles.schemas.ArticleResponse import ArticleResponse


class ArticleService:
    def __init__(self, article_repository: ArticleRepository) -> None:
        self._article_repository = article_repository

    async def list_articles(self) -> list[ArticleResponse]:

        articles = await self._article_repository.list_articles()

        return [self._to_response(article) for article in articles]

    async def get_article(
        self,
        article_id: str,
    ) -> ArticleResponse | None:
        
        article = await self._article_repository.get_article(article_id)

        return self._to_response(article) if article is not None else None

    @staticmethod
    def _to_response(article: ArticleModel) -> ArticleResponse:
        
        response = ArticleResponse.model_validate(article)
        published_at = article.published_at

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)

        return response.model_copy(update={"published_at": published_at})
