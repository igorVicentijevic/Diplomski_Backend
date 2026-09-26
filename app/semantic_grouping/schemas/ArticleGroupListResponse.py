from app.articles.schemas.ApiModel import ApiModel
from app.semantic_grouping.schemas.ArticleGroupResponse import (
    ArticleGroupResponse,
)


class ArticleGroupListResponse(ApiModel):
    groups: list[ArticleGroupResponse]
