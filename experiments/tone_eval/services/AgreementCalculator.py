from experiments.tone_eval.models.AgreementReport import AgreementReport
from experiments.tone_eval.models.ToneLabel import ToneLabel


class AgreementCalculator:
    """Observed agreement and Cohen's kappa for two annotators."""

    def calculate(
        self,
        first: dict[str, ToneLabel],
        second: dict[str, ToneLabel],
    ) -> AgreementReport:
        shared = sorted(set(first) & set(second))
        if not shared:
            raise ValueError("Nema zajednickih stavki za poredjenje.")

        confusion = {
            (a, b): 0 for a in ToneLabel for b in ToneLabel
        }
        for item_id in shared:
            confusion[(first[item_id], second[item_id])] += 1

        total = len(shared)
        observed = sum(confusion[(a, a)] for a in ToneLabel) / total

        expected = 0.0
        for label in ToneLabel:
            first_share = sum(
                1 for item_id in shared if first[item_id] == label
            ) / total
            second_share = sum(
                1 for item_id in shared if second[item_id] == label
            ) / total
            expected += first_share * second_share

        kappa = (
            1.0
            if expected == 1.0
            else (observed - expected) / (1.0 - expected)
        )

        return AgreementReport(
            compared_items=total,
            observed_agreement=observed,
            expected_agreement=expected,
            cohen_kappa=kappa,
            confusion=confusion,
        )
