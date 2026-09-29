from dataclasses import dataclass

from experiments.tone_eval.models.ToneLabel import ToneLabel


@dataclass(frozen=True, slots=True)
class ClassMetrics:
    label: ToneLabel
    support: int
    precision: float
    recall: float
    f1: float
