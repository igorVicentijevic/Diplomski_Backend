from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    threshold: float
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int

    @property
    def precision(self) -> float:
        predicted_positive = (
            self.true_positive + self.false_positive
        )
        if predicted_positive == 0:
            return 0.0
        return self.true_positive / predicted_positive

    @property
    def recall(self) -> float:
        actual_positive = self.true_positive + self.false_negative
        if actual_positive == 0:
            return 0.0
        return self.true_positive / actual_positive

    @property
    def f1(self) -> float:
        total = self.precision + self.recall
        if total == 0:
            return 0.0
        return 2 * self.precision * self.recall / total
