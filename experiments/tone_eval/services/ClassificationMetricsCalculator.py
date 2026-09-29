from experiments.tone_eval.models.ClassMetrics import ClassMetrics
from experiments.tone_eval.models.ToneLabel import ToneLabel


class ClassificationMetricsCalculator:
    """Per-class precision, recall and F1 plus macro and micro averages."""

    def per_class(
        self,
        gold: dict[str, ToneLabel],
        predicted: dict[str, ToneLabel],
    ) -> list[ClassMetrics]:
        shared = sorted(set(gold) & set(predicted))
        metrics: list[ClassMetrics] = []
        for label in ToneLabel:
            true_positive = sum(
                1
                for item_id in shared
                if gold[item_id] == label and predicted[item_id] == label
            )
            false_positive = sum(
                1
                for item_id in shared
                if gold[item_id] != label and predicted[item_id] == label
            )
            false_negative = sum(
                1
                for item_id in shared
                if gold[item_id] == label and predicted[item_id] != label
            )
            precision = self._ratio(true_positive, true_positive + false_positive)
            recall = self._ratio(true_positive, true_positive + false_negative)
            f1 = (
                0.0
                if precision + recall == 0
                else 2 * precision * recall / (precision + recall)
            )
            metrics.append(
                ClassMetrics(
                    label=label,
                    support=true_positive + false_negative,
                    precision=precision,
                    recall=recall,
                    f1=f1,
                )
            )
        return metrics

    def accuracy(
        self,
        gold: dict[str, ToneLabel],
        predicted: dict[str, ToneLabel],
    ) -> float:
        shared = sorted(set(gold) & set(predicted))
        correct = sum(1 for item_id in shared if gold[item_id] == predicted[item_id])
        return self._ratio(correct, len(shared))

    @staticmethod
    def macro_f1(metrics: list[ClassMetrics]) -> float:
        return sum(item.f1 for item in metrics) / len(metrics)

    @staticmethod
    def confusion(
        gold: dict[str, ToneLabel],
        predicted: dict[str, ToneLabel],
    ) -> dict[tuple[ToneLabel, ToneLabel], int]:
        table = {(a, b): 0 for a in ToneLabel for b in ToneLabel}
        for item_id in sorted(set(gold) & set(predicted)):
            table[(gold[item_id], predicted[item_id])] += 1
        return table

    @staticmethod
    def _ratio(numerator: int, denominator: int) -> float:
        return 0.0 if denominator == 0 else numerator / denominator
