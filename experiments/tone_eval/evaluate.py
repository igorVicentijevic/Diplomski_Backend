"""Formalna evaluacija analize tona na rucno oznacenom skupu.

Pokretanje (posle oznacavanja oba ocenjivaca):
    python -m experiments.tone_eval.evaluate --first igor --second ana

Ispisuje slaganje ocenjivaca (Koenov kapa), sastav skupa i metrike modela
u odnosu na konsenzusne ljudske oznake, i upisuje results/tone_eval.json.
"""

import argparse
import json
from pathlib import Path

from experiments.tone_eval.models.ToneLabel import ToneLabel
from experiments.tone_eval.services.AgreementCalculator import AgreementCalculator
from experiments.tone_eval.services.ClassificationMetricsCalculator import (
    ClassificationMetricsCalculator,
)
from experiments.tone_eval.services.ConsensusBuilder import ConsensusBuilder

BASE = Path(__file__).parent
DATASETS = BASE / "datasets"
RESULTS = BASE / "results"

SERBIAN = {
    ToneLabel.POSITIVE: "pozitivan",
    ToneLabel.NEUTRAL: "neutralan",
    ToneLabel.NEGATIVE: "negativan",
}


def load_labels(annotator: str) -> dict[str, ToneLabel]:
    path = DATASETS / f"tone_labels_{annotator}.jsonl"
    labels: dict[str, ToneLabel] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            labels[record["item_id"]] = ToneLabel(record["label"])
    return labels


def load_model_labels() -> dict[str, ToneLabel]:
    path = DATASETS / "tone_model_labels.jsonl"
    return {
        json.loads(line)["item_id"]: ToneLabel(json.loads(line)["model_label"])
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def print_confusion(title: str, table: dict, rows: str, cols: str) -> None:
    print(f"\n{title}  (red = {rows}, kolona = {cols})")
    header = "".join(f"{SERBIAN[label]:>12}" for label in ToneLabel)
    print(f"{'':>12}{header}")
    for row in ToneLabel:
        cells = "".join(f"{table[(row, col)]:>12}" for col in ToneLabel)
        print(f"{SERBIAN[row]:>12}{cells}")


def main(first_name: str, second_name: str) -> None:
    first = load_labels(first_name)
    second = load_labels(second_name)
    model = load_model_labels()

    agreement = AgreementCalculator().calculate(first, second)
    print(f"uporedjeno stavki: {agreement.compared_items}")
    print(f"posmatrano slaganje: {agreement.observed_agreement:.3f}")
    print(f"ocekivano slaganje:  {agreement.expected_agreement:.3f}")
    print(f"Koenov kapa:         {agreement.cohen_kappa:.3f}")
    print_confusion(
        "matrica slaganja ocenjivaca", agreement.confusion, first_name, second_name
    )

    consensus = ConsensusBuilder().build(first, second)
    print(
        f"\nkonsenzus: {len(consensus.gold)} saglasnih, "
        f"{len(consensus.disputed)} spornih stavki (iskljucene)"
    )
    distribution = {
        SERBIAN[label]: sum(1 for value in consensus.gold.values() if value == label)
        for label in ToneLabel
    }
    print("sastav referentnog skupa:", distribution)

    calculator = ClassificationMetricsCalculator()
    metrics = calculator.per_class(consensus.gold, model)
    accuracy = calculator.accuracy(consensus.gold, model)
    macro = calculator.macro_f1(metrics)
    model_vs_gold = AgreementCalculator().calculate(consensus.gold, model)

    print(f"\ntacnost modela na referentnom skupu: {accuracy:.3f}")
    print(f"macro-F1: {macro:.3f}")
    print(f"Koenov kapa model-konsenzus: {model_vs_gold.cohen_kappa:.3f}")
    print(f"\n{'klasa':>12}{'nosilaca':>10}{'preciznost':>12}{'odziv':>10}{'F1':>8}")
    for item in metrics:
        print(
            f"{SERBIAN[item.label]:>12}{item.support:>10}"
            f"{item.precision:>12.3f}{item.recall:>10.3f}{item.f1:>8.3f}"
        )
    print_confusion(
        "matrica konfuzije modela",
        calculator.confusion(consensus.gold, model),
        "konsenzus",
        "model",
    )

    RESULTS.mkdir(exist_ok=True)
    payload = {
        "annotators": [first_name, second_name],
        "compared_items": agreement.compared_items,
        "observed_agreement": agreement.observed_agreement,
        "cohen_kappa_annotators": agreement.cohen_kappa,
        "annotator_confusion": {
            f"{SERBIAN[a]}|{SERBIAN[b]}": count
            for (a, b), count in agreement.confusion.items()
        },
        "consensus_size": len(consensus.gold),
        "disputed_size": len(consensus.disputed),
        "consensus_distribution": distribution,
        "model_accuracy": accuracy,
        "model_macro_f1": macro,
        "cohen_kappa_model_consensus": model_vs_gold.cohen_kappa,
        "per_class": [
            {
                "label": SERBIAN[item.label],
                "support": item.support,
                "precision": item.precision,
                "recall": item.recall,
                "f1": item.f1,
            }
            for item in metrics
        ],
        "model_confusion": {
            f"{SERBIAN[a]}|{SERBIAN[b]}": count
            for (a, b), count in calculator.confusion(consensus.gold, model).items()
        },
    }
    output = RESULTS / "tone_eval.json"
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nupisano: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", required=True)
    parser.add_argument("--second", required=True)
    arguments = parser.parse_args()
    main(arguments.first, arguments.second)
