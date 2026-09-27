import logging

from app.semantic_grouping.models.ArticlePairSimilarity import (
    ArticlePairSimilarity,
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
        pair_similarities: list[ArticlePairSimilarity],
    ) -> list[SemanticGroupingDecision]:

        return [
            self._evaluate_pair(pair_similarity)
            for pair_similarity in pair_similarities
        ]

    def _evaluate_pair(
        self,
        pair_similarity: ArticlePairSimilarity,
    ) -> SemanticGroupingDecision:

        similarity = pair_similarity.similarity
        # Determine if the similarity is within the boundary range before making a decision
        decision = SemanticGroupingDecision(
            left_article_id=pair_similarity.left_article_id,
            right_article_id=pair_similarity.right_article_id,
            similarity=similarity,

            predicted_same_event=(
                similarity >= self._configuration.threshold
            ),

            is_boundary_candidate=self._is_boundary_similarity(
                similarity
            ),
        )
        # Log the decision if it is a boundary candidate
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
