from dataclasses import dataclass

from experiments.tone_eval.models.ToneLabel import ToneLabel


@dataclass(frozen=True, slots=True)
class EvaluationItem:
    """One article presented to the annotators, with the hidden model label."""

    item_id: str
    article_id: str
    title: str
    summary: str
    source: str
    category: str
    model_negative: float
    model_positive: float
    model_neutral: float

    @property
    def model_label(self) -> ToneLabel:
        return ToneLabel.from_percentages(
            negative=self.model_negative,
            positive=self.model_positive,
            neutral=self.model_neutral,
        )
