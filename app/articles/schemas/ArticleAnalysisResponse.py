from datetime import datetime

from app.articles.schemas.ApiModel import ApiModel
from app.articles.schemas.ArticleToneAnalysisResponse import (
    ArticleToneAnalysisResponse,
)


class ArticleAnalysisResponse(ApiModel):
    processed_at: datetime
    tone: ArticleToneAnalysisResponse
