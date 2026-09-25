import math

from experiments.semantic_grouping.ArticleTextBuilder import (
    ArticleTextBuilder,
)
from experiments.semantic_grouping.models.ArticlePair import ArticlePair
from experiments.semantic_grouping.models.EmbeddingModel import (
    EmbeddingModel,
)
from experiments.semantic_grouping.models.EvaluationMetrics import (
    EvaluationMetrics,
)
from experiments.semantic_grouping.models.SimilarityResult import (
    SimilarityResult,
)


class EmbeddingEvaluator:
    def __init__(
        self,
        embedding_model: EmbeddingModel,
        text_builder: ArticleTextBuilder,
    ) -> None:
        self._embedding_model = embedding_model
        self._text_builder = text_builder

    def calculate_similarities(
        self,
        pairs: list[ArticlePair],
    ) -> list[SimilarityResult]:
        texts = [
            text
            for pair in pairs
            for text in (
                self._text_builder.build(
                    pair.left_title,
                    pair.left_summary,
                ),
                self._text_builder.build(
                    pair.right_title,
                    pair.right_summary,
                ),
            )
        ]
        embeddings = self._embedding_model.encode(texts)

        if len(embeddings) != len(texts):
            raise ValueError(
                "Embedding model returned an unexpected number "
                "of embeddings."
            )

        return [
            SimilarityResult(
                pair_id=pair.pair_id,
                similarity=self._cosine_similarity(
                    embeddings[index * 2],
                    embeddings[index * 2 + 1],
                ),
                same_event=pair.same_event,
            )
            for index, pair in enumerate(pairs)
        ]

    def find_best_threshold(
        self,
        results: list[SimilarityResult],
        threshold_start: float,
        threshold_end: float,
        threshold_step: float,
    ) -> EvaluationMetrics:
        if not results:
            raise ValueError(
                "At least one labelled article pair is required."
            )
        if threshold_step <= 0:
            raise ValueError("Threshold step must be greater than zero.")
        if threshold_start > threshold_end:
            raise ValueError(
                "Threshold start must not exceed threshold end."
            )

        step_count = (
            math.floor(
                (threshold_end - threshold_start) / threshold_step
            )
            + 1
        )
        metrics = [
            self.evaluate_threshold(
                results,
                min(
                    threshold_end,
                    threshold_start + index * threshold_step,
                ),
            )
            for index in range(step_count)
        ]

        return max(
            metrics,
            key=lambda item: (
                item.f1,
                item.precision,
                item.recall,
                item.threshold,
            ),
        )

    @staticmethod
    def evaluate_threshold(
        results: list[SimilarityResult],
        threshold: float,
    ) -> EvaluationMetrics:
        true_positive = 0
        false_positive = 0
        true_negative = 0
        false_negative = 0

        for result in results:
            predicted_same_event = result.similarity >= threshold
            if predicted_same_event and result.same_event:
                true_positive += 1
            elif predicted_same_event:
                false_positive += 1
            elif result.same_event:
                false_negative += 1
            else:
                true_negative += 1

        return EvaluationMetrics(
            threshold=threshold,
            true_positive=true_positive,
            false_positive=false_positive,
            true_negative=true_negative,
            false_negative=false_negative,
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

        dot_product = sum(
            left_value * right_value
            for left_value, right_value in zip(
                left,
                right,
                strict=True,
            )
        )
        return dot_product / (left_norm * right_norm)
