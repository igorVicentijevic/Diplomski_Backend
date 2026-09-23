from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.models.ArticleModel import ArticleModel


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_articles(self) -> list[ArticleModel]:
        result = await self._session.scalars(
            select(ArticleModel).order_by(
                ArticleModel.published_at.desc()
            )
        )
        return list(result)

    async def get_article(
        self,
        article_id: str,
    ) -> ArticleModel | None:
        return await self._session.get(ArticleModel, article_id)
