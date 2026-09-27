import math
from collections.abc import Sequence

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.grouping.CandidateArticlePairGenerator import (
    CandidateArticlePairGenerator,
)
from app.semantic_grouping.grouping.ICandidatePairFinder import (
    ICandidatePairFinder,
)
from app.semantic_grouping.models.ArticlePairSimilarity import (
    ArticlePairSimilarity,
)


class PythonCandidatePairFinder(ICandidatePairFinder):
    """Portable candidate pair finder that works on any SQL dialect.

    Pairs are generated with a Python sliding-window scan and their
    cosine similarity is computed in Python. This is the fallback used
    where the database does not support pgvector (e.g. SQLite tests).
    """

    def __init__(
        self,
        pair_generator: CandidateArticlePairGenerator,
    ) -> None:
        self._pair_generator = pair_generator

    async def find(
        self,
        articles: Sequence[ArticleModel],
        embedding_by_article_id: dict[str, list[float]],
    ) -> list[ArticlePairSimilarity]:
        pairs = self._pair_generator.generate(list(articles))

        return [
            ArticlePairSimilarity(
                left_article_id=pair.left.id,
                right_article_id=pair.right.id,
                similarity=self._cosine_similarity(
                    embedding_by_article_id[pair.left.id],
                    embedding_by_article_id[pair.right.id],
                ),
            )
            for pair in pairs
        ]

    @staticmethod
    def _cosine_similarity(
        left: list[float],
        right: list[float],
    ) -> float:
        if len(left) != len(right):
            raise ValueError(
                "Embedding vectors must have the same dimension."
            )
        if not left:
            raise ValueError("Embedding vectors must not be empty.")

        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            raise ValueError(
                "Embedding vectors must have a non-zero norm."
            )

        return sum(
            left_value * right_value
            for left_value, right_value in zip(
                left,
                right,
                strict=True,
            )
        ) / (left_norm * right_norm)
