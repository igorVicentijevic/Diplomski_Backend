from app.articles.schemas.ApiModel import ApiModel
from app.articles.schemas.ArticleResponse import ArticleResponse


class ArticleListResponse(ApiModel):
    articles: list[ArticleResponse]
