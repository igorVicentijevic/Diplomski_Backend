from app.articles.schemas.ApiModel import ApiModel
from app.articles.schemas.ArticleResponse import ArticleResponse


class ArticleGroupResponse(ApiModel):
    id: str
    articles: list[ArticleResponse]
