from fastapi import APIRouter

from app.semantic_grouping.dependencies import ArticleGroupServiceDependency
from app.semantic_grouping.schemas.ArticleGroupListResponse import (
    ArticleGroupListResponse,
)

router = APIRouter(prefix="/article-groups", tags=["article groups"])


@router.get("", response_model=ArticleGroupListResponse)
async def get_article_groups(
    service: ArticleGroupServiceDependency,
) -> ArticleGroupListResponse:
    return ArticleGroupListResponse(
        groups=await service.list_groups(),
    )
