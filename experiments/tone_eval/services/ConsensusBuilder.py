from experiments.tone_eval.models.ConsensusResult import ConsensusResult
from experiments.tone_eval.models.ToneLabel import ToneLabel


class ConsensusBuilder:
    """Forms the reference set from two independent annotations.

    Items on which the annotators disagree are excluded instead of being
    resolved by a third opinion, so the reference set contains only labels
    that both annotators independently confirmed.
    """

    def build(
        self,
        first: dict[str, ToneLabel],
        second: dict[str, ToneLabel],
        adjudicated: dict[str, ToneLabel] | None = None,
    ) -> ConsensusResult:
        resolved = adjudicated or {}
        gold: dict[str, ToneLabel] = {}
        disputed: dict[str, tuple[ToneLabel, ToneLabel]] = {}
        for item_id in sorted(set(first) & set(second)):
            if first[item_id] == second[item_id]:
                gold[item_id] = first[item_id]
            elif item_id in resolved:
                gold[item_id] = resolved[item_id]
            else:
                disputed[item_id] = (first[item_id], second[item_id])
        return ConsensusResult(gold=gold, disputed=disputed)
