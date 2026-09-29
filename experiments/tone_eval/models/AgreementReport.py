from dataclasses import dataclass

from experiments.tone_eval.models.ToneLabel import ToneLabel


@dataclass(frozen=True, slots=True)
class AgreementReport:
    """Agreement between two independent label assignments."""

    compared_items: int
    observed_agreement: float
    expected_agreement: float
    cohen_kappa: float
    confusion: dict[tuple[ToneLabel, ToneLabel], int]
