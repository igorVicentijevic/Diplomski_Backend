from dataclasses import dataclass

from experiments.tone_eval.models.ToneLabel import ToneLabel


@dataclass(frozen=True, slots=True)
class ConsensusResult:
    """Gold labels agreed upon by both annotators, plus the disputed items."""

    gold: dict[str, ToneLabel]
    disputed: dict[str, tuple[ToneLabel, ToneLabel]]

    @property
    def total(self) -> int:
        return len(self.gold) + len(self.disputed)
