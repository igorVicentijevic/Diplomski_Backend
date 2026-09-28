from dataclasses import dataclass

from app.articles.models.ArticleAnalysisModel import ArticleAnalysisModel
from app.articles.models.ArticleModel import ArticleModel


@dataclass(frozen=True, slots=True)
class ProcessedArticleModels:
    article: ArticleModel
    #missing while the tone analysis has not landed yet
    analysis: ArticleAnalysisModel | None
