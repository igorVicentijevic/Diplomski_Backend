from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.repositories.ArticleRepository import ArticleRepository
from app.articles.services.ArticleService import ArticleService
from app.database.session import get_session

DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


def get_article_repository(
    session: DatabaseSession,
) -> ArticleRepository:
    return ArticleRepository(session)


ArticleRepositoryDependency = Annotated[
    ArticleRepository,
    Depends(get_article_repository),
]


def get_article_service(
    article_repository: ArticleRepositoryDependency,
) -> ArticleService:
    return ArticleService(article_repository)


ArticleServiceDependency = Annotated[
    ArticleService,
    Depends(get_article_service),
]
