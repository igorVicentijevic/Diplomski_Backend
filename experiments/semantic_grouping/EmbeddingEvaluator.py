import math

from .ArticleTextBuilder import (
    ArticleTextBuilder,
)
from .embedding_engine.EmbeddingEngine import (
    EmbeddingEngine,
)
from .models.ArticlePair import ArticlePair
from .models.EvaluationMetrics import (
    EvaluationMetrics,
)
from .models.SimilarityResult import (
    SimilarityResult,
)


class EmbeddingEvaluator:
    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        text_builder: ArticleTextBuilder,
    ) -> None:
        self._embedding_engine = embedding_engine
        self._text_builder = text_builder

    def calculate_similarities(
        self,
        pairs: list[ArticlePair],
    ) -> list[SimilarityResult]:
        self._validate_labels(pairs)

        left_embeddings = self._embedding_engine.encode(
            self._build_left_texts(pairs)
        )

        right_embeddings = self._embedding_engine.encode(
            self._build_right_texts(pairs)
        )

        self._validate_embedding_count(
            pairs,
            left_embeddings,
            "left",
        )
        self._validate_embedding_count(
            pairs,
            right_embeddings,
            "right",
        )

        return self._create_similarity_results(
            pairs,
            left_embeddings,
            right_embeddings,
        )

    def _create_similarity_results(
        self,
        pairs: list[ArticlePair],
        left_embeddings: list[list[float]],
        right_embeddings: list[list[float]],
    ) -> list[SimilarityResult]:
        results: list[SimilarityResult] = []

        paired_embeddings = zip(
            pairs,
            left_embeddings,
            right_embeddings,
            strict=True,
        )

        for pair, left_embedding, right_embedding in paired_embeddings:

            result = self._create_similarity_result(
                pair,
                left_embedding,
                right_embedding,
            )
            
            results.append(result)

        return results

    def _create_similarity_result(
        self,
        pair: ArticlePair,
        left_embedding: list[float],
        right_embedding: list[float],
    ) -> SimilarityResult:
        
        return SimilarityResult(
            pair_id=pair.pair_id,
            similarity=self._cosine_similarity(
                left_embedding,
                right_embedding,
            ),
            same_event=self._require_label(pair),
            candidate_type=pair.candidate_type,
        )

    def _build_left_texts(
        self,
        pairs: list[ArticlePair],
    ) -> list[str]:
        return [
            self._text_builder.build(
                pair.left.title,
                pair.left.summary,
            )
            for pair in pairs
        ]

    def _build_right_texts(
        self,
        pairs: list[ArticlePair],
    ) -> list[str]:
        return [
            self._text_builder.build(
                pair.right.title,
                pair.right.summary,
            )
            for pair in pairs
        ]

    @staticmethod
    def _validate_labels(pairs: list[ArticlePair]) -> None:
        unlabelled_ids = [
            pair.pair_id
            for pair in pairs
            if pair.same_event is None
        ]
        if unlabelled_ids:
            raise ValueError(
                "All article pairs must be labelled before evaluation. "
                f"Unlabelled pairs: {', '.join(unlabelled_ids)}"
            )

    @staticmethod
    def _require_label(pair: ArticlePair) -> bool:
        if pair.same_event is None:
            raise ValueError(
                f"Article pair {pair.pair_id} is not labelled."
            )
        return pair.same_event

    @staticmethod
    def _validate_embedding_count(
        pairs: list[ArticlePair],
        embeddings: list[list[float]],
        side: str,
    ) -> None:
        if len(embeddings) != len(pairs):
            raise ValueError(
                f"Embedding engine returned an unexpected number "
                f"of {side} embeddings."
            )

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
