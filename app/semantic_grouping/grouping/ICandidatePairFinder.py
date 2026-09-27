from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.models.ArticlePairSimilarity import (
    ArticlePairSimilarity,
)


class ICandidatePairFinder(ABC):
    """Finds candidate article pairs and their cosine similarity.

    Implementations decide both which articles are compared (e.g. a
    time-window filter) and how the similarity is computed (e.g. in
    Python or pushed down to the database).
    """

    @abstractmethod
    async def find(
        self,
        articles: Sequence[ArticleModel],
        embedding_by_article_id: dict[str, list[float]],
    ) -> list[ArticlePairSimilarity]:
        ...
