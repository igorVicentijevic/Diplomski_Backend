import math
import statistics
from collections.abc import Callable
from time import perf_counter
from typing import Any

from ..ArticlePairJsonCodec import ArticlePairJsonCodec
from ..ArticleTextBuilder import ArticleTextBuilder
from ..EmbeddingEvaluator import EmbeddingEvaluator
from ..embedding_engine.EmbeddingEngine import EmbeddingEngine
from ..models.ArticlePair import ArticlePair
from ..models.CrossValidationResult import CrossValidationResult
from ..models.EvaluationMetrics import EvaluationMetrics
from ..models.ModelEvaluationReport import ModelEvaluationReport
from ..models.SimilarityResult import SimilarityResult

HARD_NEGATIVE = "hard_negative"


class ModelBenchmarkService:
    def __init__(
        self,
        pairs: list[ArticlePair],
        fold_count: int = 5,
        threshold_start: float = 0.50,
        threshold_end: float = 0.95,
        threshold_step: float = 0.01,
    ) -> None:
        if fold_count < 2:
            raise ValueError("At least two folds are required.")
        if len(pairs) < fold_count:
            raise ValueError(
                "The dataset must contain at least one pair per fold."
            )

        self._pairs = pairs
        self._fold_count = fold_count
        self._threshold_start = threshold_start
        self._threshold_end = threshold_end
        self._threshold_step = threshold_step
        self._fold_pair_ids = self._create_grouped_stratified_folds()
        self._pair_by_id = {
            pair.pair_id: pair
            for pair in pairs
        }
        self._codec = ArticlePairJsonCodec()

    @property
    def fold_pair_ids(self) -> list[list[str]]:
        return [
            list(pair_ids)
            for pair_ids in self._fold_pair_ids
        ]

    @property
    def positive_component_count(self) -> int:
        return sum(
            any(pair.same_event is True for pair in component)
            for component in self._build_article_components()
        )

    def benchmark(
        self,
        model_names: list[str],
        engine_factory: Callable[[str], EmbeddingEngine],
    ) -> list[ModelEvaluationReport]:
        if len(model_names) < 2:
            raise ValueError(
                "At least two embedding models must be compared."
            )
        if len(set(model_names)) != len(model_names):
            raise ValueError("Embedding model names must be unique.")

        return [
            self._benchmark_model(
                model_name,
                engine_factory(model_name),
            )
            for model_name in model_names
        ]

    def _benchmark_model(
        self,
        model_name: str,
        embedding_engine: EmbeddingEngine,
    ) -> ModelEvaluationReport:
        evaluator = EmbeddingEvaluator(
            embedding_engine=embedding_engine,
            text_builder=ArticleTextBuilder(),
        )
        embedding_started_at = perf_counter()
        similarity_results = evaluator.calculate_similarities(
            self._pairs
        )
        embedding_generation_seconds = (
            perf_counter() - embedding_started_at
        )
        result_by_id = {
            result.pair_id: result
            for result in similarity_results
        }

        fold_results: list[CrossValidationResult] = []
        pair_results: list[dict[str, Any]] = []
        false_positive_pairs: list[dict[str, Any]] = []
        false_negative_pairs: list[dict[str, Any]] = []

        for fold_index, test_pair_ids in enumerate(
            self._fold_pair_ids,
            start=1,
        ):
            test_pair_id_set = set(test_pair_ids)
            training_results = [
                result
                for result in similarity_results
                if result.pair_id not in test_pair_id_set
            ]
            test_results = [
                result_by_id[pair_id]
                for pair_id in test_pair_ids
            ]
            training_metrics = evaluator.find_best_threshold(
                training_results,
                threshold_start=self._threshold_start,
                threshold_end=self._threshold_end,
                threshold_step=self._threshold_step,
            )
            test_metrics = evaluator.evaluate_threshold(
                test_results,
                training_metrics.threshold,
            )
            fold_results.append(
                self._create_fold_result(
                    fold_index,
                    training_metrics.threshold,
                    test_results,
                    test_metrics,
                )
            )

            for result in test_results:
                pair_result = self._create_pair_result(
                    result,
                    fold_index,
                    training_metrics.threshold,
                )
                pair_results.append(pair_result)
                if (
                    pair_result["predictedSameEvent"]
                    and not result.same_event
                ):
                    false_positive_pairs.append(pair_result)
                elif (
                    not pair_result["predictedSameEvent"]
                    and result.same_event
                ):
                    false_negative_pairs.append(pair_result)

        pair_results.sort(key=lambda item: item["pairId"])
        false_positive_pairs.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )
        false_negative_pairs.sort(
            key=lambda item: item["similarity"],
        )

        return ModelEvaluationReport(
            model=model_name,
            embedding_generation_seconds=(
                embedding_generation_seconds
            ),
            aggregate_metrics=self._aggregate_metrics(
                fold_results,
                similarity_results,
            ),
            threshold_summary=self._threshold_summary(fold_results),
            hard_negative_metrics=self._hard_negative_metrics(
                fold_results
            ),
            fold_results=fold_results,
            pair_results=pair_results,
            false_positive_pairs=false_positive_pairs,
            false_negative_pairs=false_negative_pairs,
        )

    def _create_fold_result(
        self,
        fold_index: int,
        threshold: float,
        test_results: list[SimilarityResult],
        test_metrics: EvaluationMetrics,
    ) -> CrossValidationResult:
        hard_negative_results = [
            result
            for result in test_results
            if (
                not result.same_event
                and result.candidate_type == HARD_NEGATIVE
            )
        ]
        hard_negative_false_positive = sum(
            result.similarity >= threshold
            for result in hard_negative_results
        )

        return CrossValidationResult(
            fold=fold_index,
            threshold=threshold,
            pair_count=len(test_results),
            positive_count=sum(
                result.same_event
                for result in test_results
            ),
            negative_count=sum(
                not result.same_event
                for result in test_results
            ),
            precision=test_metrics.precision,
            recall=test_metrics.recall,
            f1=test_metrics.f1,
            pr_auc=self._calculate_pr_auc(test_results),
            true_positive=test_metrics.true_positive,
            false_positive=test_metrics.false_positive,
            true_negative=test_metrics.true_negative,
            false_negative=test_metrics.false_negative,
            hard_negative_count=len(hard_negative_results),
            hard_negative_false_positive=(
                hard_negative_false_positive
            ),
            hard_negative_true_negative=(
                len(hard_negative_results)
                - hard_negative_false_positive
            ),
        )

    def _create_pair_result(
        self,
        result: SimilarityResult,
        fold_index: int,
        threshold: float,
    ) -> dict[str, Any]:
        pair = self._pair_by_id[result.pair_id]
        return {
            "pairId": result.pair_id,
            "fold": fold_index,
            "similarity": round(result.similarity, 6),
            "threshold": round(threshold, 4),
            "sameEvent": result.same_event,
            "predictedSameEvent": result.similarity >= threshold,
            "candidateType": result.candidate_type,
            "left": self._codec.encode(pair)["left"],
            "right": self._codec.encode(pair)["right"],
        }

    def _aggregate_metrics(
        self,
        folds: list[CrossValidationResult],
        similarity_results: list[SimilarityResult],
    ) -> dict[str, Any]:
        true_positive = sum(fold.true_positive for fold in folds)
        false_positive = sum(fold.false_positive for fold in folds)
        true_negative = sum(fold.true_negative for fold in folds)
        false_negative = sum(fold.false_negative for fold in folds)
        precision = self._safe_divide(
            true_positive,
            true_positive + false_positive,
        )
        recall = self._safe_divide(
            true_positive,
            true_positive + false_negative,
        )
        f1 = self._safe_divide(
            2 * precision * recall,
            precision + recall,
        )

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "prAuc": round(
                self._calculate_pr_auc(similarity_results),
                4,
            ),
            "truePositive": true_positive,
            "falsePositive": false_positive,
            "trueNegative": true_negative,
            "falseNegative": false_negative,
            "foldMean": self._metric_statistics(
                folds,
                statistics.mean,
            ),
            "foldStandardDeviation": self._metric_statistics(
                folds,
                statistics.pstdev,
            ),
        }

    @staticmethod
    def _metric_statistics(
        folds: list[CrossValidationResult],
        operation: Callable[[list[float]], float],
    ) -> dict[str, float]:
        return {
            metric: round(
                operation(
                    [
                        float(getattr(fold, attribute))
                        for fold in folds
                    ]
                ),
                4,
            )
            for metric, attribute in (
                ("precision", "precision"),
                ("recall", "recall"),
                ("f1", "f1"),
                ("prAuc", "pr_auc"),
            )
        }

    @staticmethod
    def _threshold_summary(
        folds: list[CrossValidationResult],
    ) -> dict[str, float]:
        thresholds = [fold.threshold for fold in folds]
        return {
            "average": round(statistics.mean(thresholds), 4),
            "minimum": round(min(thresholds), 4),
            "maximum": round(max(thresholds), 4),
            "range": round(max(thresholds) - min(thresholds), 4),
            "standardDeviation": round(
                statistics.pstdev(thresholds),
                4,
            ),
        }

    @staticmethod
    def _hard_negative_metrics(
        folds: list[CrossValidationResult],
    ) -> dict[str, float | int]:
        pair_count = sum(
            fold.hard_negative_count
            for fold in folds
        )
        false_positive = sum(
            fold.hard_negative_false_positive
            for fold in folds
        )
        true_negative = sum(
            fold.hard_negative_true_negative
            for fold in folds
        )
        return {
            "pairCount": pair_count,
            "falsePositive": false_positive,
            "trueNegative": true_negative,
            "falsePositiveRate": round(
                ModelBenchmarkService._safe_divide(
                    false_positive,
                    pair_count,
                ),
                4,
            ),
        }

    def _create_grouped_stratified_folds(self) -> list[list[str]]:
        components = self._build_article_components()
        components.sort(
            key=lambda component: (
                sum(pair.same_event is True for pair in component),
                len(component),
                component[0].pair_id,
            ),
            reverse=True,
        )
        folds: list[list[ArticlePair]] = [
            []
            for _ in range(self._fold_count)
        ]
        target_positive = (
            sum(pair.same_event is True for pair in self._pairs)
            / self._fold_count
        )
        target_negative = (
            sum(pair.same_event is False for pair in self._pairs)
            / self._fold_count
        )
        target_size = len(self._pairs) / self._fold_count

        for component_index, component in enumerate(components):
            if component_index < self._fold_count:
                selected_fold = component_index
            else:
                selected_fold = min(
                    range(self._fold_count),
                    key=lambda fold_index: self._fold_score(
                        folds[fold_index],
                        component,
                        target_positive,
                        target_negative,
                        target_size,
                        fold_index,
                    ),
                )
            folds[selected_fold].extend(component)

        self._validate_folds(folds)
        return [
            sorted(pair.pair_id for pair in fold)
            for fold in folds
        ]

    @staticmethod
    def _fold_score(
        fold: list[ArticlePair],
        component: list[ArticlePair],
        target_positive: float,
        target_negative: float,
        target_size: float,
        fold_index: int,
    ) -> tuple[float, int, int]:
        combined = fold + component
        positive_count = sum(
            pair.same_event is True
            for pair in combined
        )
        negative_count = sum(
            pair.same_event is False
            for pair in combined
        )
        current_positive_count = sum(
            pair.same_event is True
            for pair in fold
        )
        current_negative_count = sum(
            pair.same_event is False
            for pair in fold
        )
        combined_score = (
            ModelBenchmarkService._normalized_square_error(
                positive_count,
                target_positive,
            )
            + ModelBenchmarkService._normalized_square_error(
                negative_count,
                target_negative,
            )
            + ModelBenchmarkService._normalized_square_error(
                len(combined),
                target_size,
            )
        )
        current_score = (
            ModelBenchmarkService._normalized_square_error(
                current_positive_count,
                target_positive,
            )
            + ModelBenchmarkService._normalized_square_error(
                current_negative_count,
                target_negative,
            )
            + ModelBenchmarkService._normalized_square_error(
                len(fold),
                target_size,
            )
        )
        return combined_score - current_score, len(fold), fold_index

    def _build_article_components(self) -> list[list[ArticlePair]]:
        parent: dict[str, str] = {}

        def find(article_id: str) -> str:
            parent.setdefault(article_id, article_id)
            if parent[article_id] != article_id:
                parent[article_id] = find(parent[article_id])
            return parent[article_id]

        def union(left_id: str, right_id: str) -> None:
            left_root = find(left_id)
            right_root = find(right_id)
            if left_root != right_root:
                parent[right_root] = left_root

        for pair in self._pairs:
            union(pair.left.article_id, pair.right.article_id)

        components: dict[str, list[ArticlePair]] = {}
        for pair in self._pairs:
            root = find(pair.left.article_id)
            components.setdefault(root, []).append(pair)
        return list(components.values())

    def _validate_folds(
        self,
        folds: list[list[ArticlePair]],
    ) -> None:
        if any(not fold for fold in folds):
            raise ValueError(
                "Grouped stratification produced an empty fold."
            )

        pair_ids = [
            pair.pair_id
            for fold in folds
            for pair in fold
        ]
        if len(pair_ids) != len(set(pair_ids)):
            raise ValueError("A pair was assigned to multiple folds.")
        if set(pair_ids) != {
            pair.pair_id
            for pair in self._pairs
        }:
            raise ValueError("Not every pair was assigned to a fold.")

        article_fold: dict[str, int] = {}
        for fold_index, fold in enumerate(folds):
            for pair in fold:
                for article_id in (
                    pair.left.article_id,
                    pair.right.article_id,
                ):
                    previous_fold = article_fold.setdefault(
                        article_id,
                        fold_index,
                    )
                    if previous_fold != fold_index:
                        raise ValueError(
                            "An article was assigned to multiple folds."
                        )

    @staticmethod
    def _calculate_pr_auc(
        results: list[SimilarityResult],
    ) -> float:
        positive_count = sum(
            result.same_event
            for result in results
        )
        if positive_count == 0:
            return 0.0

        sorted_results = sorted(
            results,
            key=lambda result: result.similarity,
            reverse=True,
        )
        true_positive = 0
        false_positive = 0
        previous_recall = 0.0
        previous_precision = 1.0
        area = 0.0
        index = 0

        while index < len(sorted_results):
            similarity = sorted_results[index].similarity
            while (
                index < len(sorted_results)
                and math.isclose(
                    sorted_results[index].similarity,
                    similarity,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
            ):
                if sorted_results[index].same_event:
                    true_positive += 1
                else:
                    false_positive += 1
                index += 1

            recall = true_positive / positive_count
            precision = true_positive / (
                true_positive + false_positive
            )
            area += (
                recall - previous_recall
            ) * (
                precision + previous_precision
            ) / 2
            previous_recall = recall
            previous_precision = precision

        return area

    @staticmethod
    def _normalized_square_error(
        value: float,
        target: float,
    ) -> float:
        if target == 0:
            return value * value
        return ((value - target) / target) ** 2

    @staticmethod
    def _safe_divide(
        numerator: float,
        denominator: float,
    ) -> float:
        if denominator == 0:
            return 0.0
        return numerator / denominator
