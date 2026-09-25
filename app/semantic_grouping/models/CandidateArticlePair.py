from dataclasses import dataclass

from app.articles.models.ArticleModel import ArticleModel


@dataclass(frozen=True, slots=True)
class CandidateArticlePair:
    left: ArticleModel
    right: ArticleModel
