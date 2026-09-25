from dataclasses import dataclass
from typing import Any

from .CrossValidationResult import CrossValidationResult


@dataclass(frozen=True, slots=True)
class ModelEvaluationReport:
    model: str
    embedding_generation_seconds: float
    aggregate_metrics: dict[str, Any]
    threshold_summary: dict[str, float]
    hard_negative_metrics: dict[str, float | int]
    fold_results: list[CrossValidationResult]
    pair_results: list[dict[str, Any]]
    false_positive_pairs: list[dict[str, Any]]
    false_negative_pairs: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "embeddingGenerationSeconds": round(
                self.embedding_generation_seconds,
                4,
            ),
            "aggregateMetrics": self.aggregate_metrics,
            "thresholdSummary": self.threshold_summary,
            "hardNegativeMetrics": self.hard_negative_metrics,
            "folds": [
                result.to_dict()
                for result in self.fold_results
            ],
            "falsePositivePairs": self.false_positive_pairs,
            "falseNegativePairs": self.false_negative_pairs,
            "pairs": self.pair_results,
        }
