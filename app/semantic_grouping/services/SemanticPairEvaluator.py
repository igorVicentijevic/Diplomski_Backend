import logging
import math

from app.semantic_grouping.models.CandidateArticlePair import (
    CandidateArticlePair,
)
from app.semantic_grouping.models.SemanticGroupingConfiguration import (
    SemanticGroupingConfiguration,
)
from app.semantic_grouping.models.SemanticGroupingDecision import (
    SemanticGroupingDecision,
)

logger = logging.getLogger(__name__)


class SemanticPairEvaluator:
    def __init__(
        self,
        configuration: SemanticGroupingConfiguration,
    ) -> None:
        self._configuration = configuration

    def evaluate(
        self,
        pairs: list[CandidateArticlePair],
        embedding_by_article_id: dict[str, list[float]],
    ) -> list[SemanticGroupingDecision]:
        return [
            self._evaluate_pair(pair, embedding_by_article_id)
            for pair in pairs
        ]

    def _evaluate_pair(
        self,
        pair: CandidateArticlePair,
        embedding_by_article_id: dict[str, list[float]],
    ) -> SemanticGroupingDecision:
        similarity = self._cosine_similarity(
            embedding_by_article_id[pair.left.id],
            embedding_by_article_id[pair.right.id],
        )
        decision = SemanticGroupingDecision(
            left_article_id=pair.left.id,
            right_article_id=pair.right.id,
            similarity=similarity,
            predicted_same_event=(
                similarity >= self._configuration.threshold
            ),
            is_boundary_candidate=self._is_boundary_similarity(
                similarity
            ),
        )
        self._log_boundary_decision(decision)
        return decision

    def _is_boundary_similarity(self, similarity: float) -> bool:
        return (
            self._configuration.boundary_min
            <= similarity
            <= self._configuration.boundary_max
        )

    def _log_boundary_decision(
        self,
        decision: SemanticGroupingDecision,
    ) -> None:
        if not decision.is_boundary_candidate:
            return

        logger.info(
            "Semantic grouping boundary pair "
            "left=%s right=%s similarity=%.4f threshold=%.4f",
            decision.left_article_id,
            decision.right_article_id,
            decision.similarity,
            self._configuration.threshold,
        )

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
