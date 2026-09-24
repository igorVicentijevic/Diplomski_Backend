from app.articles.schemas.ApiModel import ApiModel


class ArticleToneAnalysisResponse(ApiModel):
    negative_percentage: float
    positive_percentage: float
    neutral_percentage: float
