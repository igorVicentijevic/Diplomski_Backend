from datetime import UTC

from app.articles.models.ArticleModel import ArticleModel
from app.articles.repositories.ArticleRepository import ArticleRepository
from app.articles.schemas.ArticleResponse import ArticleResponse


class ArticleService:
    def __init__(self, article_repository: ArticleRepository) -> None:
        self._article_repository = article_repository

    async def list_articles(self) -> list[ArticleResponse]:

        articles = await self._article_repository.list_articles()

        return [self.to_response(article) for article in articles]

    async def get_article(
        self,
        article_id: str,
    ) -> ArticleResponse | None:
        
        article = await self._article_repository.get_article(article_id)

        return self.to_response(article) if article is not None else None

    @staticmethod
    def to_response(article: ArticleModel) -> ArticleResponse:
        if article.analysis is None or article.analysis.tone is None:
            raise ValueError("Article analysis is incomplete.")

        response = ArticleResponse.model_validate(article)
        published_at = article.published_at
        processed_at = article.analysis.processed_at

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=UTC)

        if processed_at.tzinfo is None:
            processed_at = processed_at.replace(tzinfo=UTC)

        analysis = response.analysis.model_copy(
            update={"processed_at": processed_at}
        )
        return response.model_copy(
            update={
                "published_at": published_at,
                "analysis": analysis,
            }
        )
