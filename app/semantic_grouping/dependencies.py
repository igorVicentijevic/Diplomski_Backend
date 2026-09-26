from typing import Annotated

from fastapi import Depends

from app.articles.dependencies import DatabaseSession
from app.semantic_grouping.repositories.SemanticGroupingRepository import (
    SemanticGroupingRepository,
)
from app.semantic_grouping.services.ArticleGroupService import (
    ArticleGroupService,
)


def get_semantic_grouping_repository(
    session: DatabaseSession,
) -> SemanticGroupingRepository:
    return SemanticGroupingRepository(session)


SemanticGroupingRepositoryDependency = Annotated[
    SemanticGroupingRepository,
    Depends(get_semantic_grouping_repository),
]


def get_article_group_service(
    repository: SemanticGroupingRepositoryDependency,
) -> ArticleGroupService:
    return ArticleGroupService(repository)


ArticleGroupServiceDependency = Annotated[
    ArticleGroupService,
    Depends(get_article_group_service),
]
