from datetime import datetime

from app.articles.schemas.ApiModel import ApiModel
from app.articles.schemas.ArticleAnalysisResponse import (
    ArticleAnalysisResponse,
)
from app.articles.schemas.NewsCategory import NewsCategory


class ArticleResponse(ApiModel):
    id: str
    title: str
    summary: str
    source: str
    category: NewsCategory
    published_at: datetime
    image_url: str | None
    article_url: str
    related_city_ids: list[str]
    analysis: ArticleAnalysisResponse
