from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CrossValidationResult:
    fold: int
    threshold: float
    pair_count: int
    positive_count: int
    negative_count: int
    precision: float
    recall: float
    f1: float
    pr_auc: float
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    hard_negative_count: int
    hard_negative_false_positive: int
    hard_negative_true_negative: int

    def to_dict(self) -> dict[str, float | int]:
        hard_negative_false_positive_rate = 0.0
        if self.hard_negative_count:
            hard_negative_false_positive_rate = (
                self.hard_negative_false_positive
                / self.hard_negative_count
            )

        return {
            "fold": self.fold,
            "threshold": round(self.threshold, 4),
            "pairCount": self.pair_count,
            "positiveCount": self.positive_count,
            "negativeCount": self.negative_count,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "prAuc": round(self.pr_auc, 4),
            "truePositive": self.true_positive,
            "falsePositive": self.false_positive,
            "trueNegative": self.true_negative,
            "falseNegative": self.false_negative,
            "hardNegativeCount": self.hard_negative_count,
            "hardNegativeFalsePositive": (
                self.hard_negative_false_positive
            ),
            "hardNegativeTrueNegative": (
                self.hard_negative_true_negative
            ),
            "hardNegativeFalsePositiveRate": round(
                hard_negative_false_positive_rate,
                4,
            ),
        }
