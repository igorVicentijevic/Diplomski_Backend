import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .LabelledPairLoader import LabelledPairLoader
from .embedding_engine.SentenceTransformerEmbeddingEngine import (
    SentenceTransformerEmbeddingEngine,
)
from .services.ModelBenchmarkService import ModelBenchmarkService

MODULE_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = (
    MODULE_DIRECTORY
    / "datasets"
    / "article_pairs_v1.jsonl"
)
DEFAULT_OUTPUT_PATH = (
    MODULE_DIRECTORY
    / "results"
    / "model_comparison_v1.json"
)
DEFAULT_MODELS = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/distiluse-base-multilingual-cased-v2",
]
MINIMUM_POSITIVE_PAIRS = 50
MINIMUM_POSITIVE_EVENTS = 2


def evaluate_calibration_readiness(
    positive_count: int,
    positive_event_count: int,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if positive_count < MINIMUM_POSITIVE_PAIRS:
        reasons.append(
            f"only {positive_count} positive pairs are available; "
            f"at least {MINIMUM_POSITIVE_PAIRS} are required"
        )
    if positive_event_count < MINIMUM_POSITIVE_EVENTS:
        reasons.append(
            "positive pairs cover fewer than two explicitly labelled "
            "independent events"
        )
    return not reasons, reasons


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare embedding models with grouped stratified "
            "cross-validation."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help=(
            "Sentence Transformers model name. Repeat for each model; "
            "at least two are required."
        ),
    )
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--threshold-start", type=float, default=0.50)
    parser.add_argument("--threshold-end", type=float, default=0.95)
    parser.add_argument("--threshold-step", type=float, default=0.01)
    return parser.parse_args()


def build_report(arguments: argparse.Namespace) -> dict[str, Any]:
    pairs = LabelledPairLoader().load(arguments.dataset)
    service = ModelBenchmarkService(
        pairs=pairs,
        fold_count=arguments.folds,
        threshold_start=arguments.threshold_start,
        threshold_end=arguments.threshold_end,
        threshold_step=arguments.threshold_step,
    )
    model_names = arguments.models or DEFAULT_MODELS
    model_reports = service.benchmark(
        model_names,
        SentenceTransformerEmbeddingEngine,
    )
    positive_count = sum(pair.same_event is True for pair in pairs)
    negative_count = sum(pair.same_event is False for pair in pairs)
    hard_negative_count = sum(
        pair.same_event is False
        and pair.candidate_type == "hard_negative"
        for pair in pairs
    )
    positive_component_count = service.positive_component_count
    positive_event_count = len(
        {
            pair.event_id
            for pair in pairs
            if pair.same_event is True and pair.event_id is not None
        }
    )
    calibration_ready, preliminary_reasons = (
        evaluate_calibration_readiness(
            positive_count,
            positive_event_count,
        )
    )
    try:
        dataset_path = str(
            arguments.dataset.resolve().relative_to(
                MODULE_DIRECTORY
            )
        )
    except ValueError:
        dataset_path = str(arguments.dataset)

    return {
        "version": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "preliminary": not calibration_ready,
        "preliminaryReason": (
            "; ".join(preliminary_reasons)
            if preliminary_reasons
            else None
        ),
        "dataset": {
            "path": dataset_path,
            "pairCount": len(pairs),
            "positive": positive_count,
            "negative": negative_count,
            "hardNegative": hard_negative_count,
            "positiveArticleComponents": positive_component_count,
            "positiveEventCount": positive_event_count,
            "minimumPositivePairs": MINIMUM_POSITIVE_PAIRS,
            "minimumPositiveEvents": MINIMUM_POSITIVE_EVENTS,
            "readyForThresholdCalibration": (
                calibration_ready
            ),
        },
        "crossValidation": {
            "foldCount": arguments.folds,
            "strategy": "grouped_stratified_best_effort",
            "groupingRule": (
                "All pairs connected through a shared article are "
                "assigned to the same fold."
            ),
            "positiveArticleComponents": (
                positive_component_count
            ),
            "allTestFoldsCanContainPositives": (
                positive_component_count >= arguments.folds
            ),
            "limitation": (
                None
                if positive_component_count >= arguments.folds
                else (
                    "Leakage-safe five-fold stratification cannot place "
                    "positives in every test fold because only "
                    f"{positive_component_count} connected article "
                    "components contain positive pairs."
                )
            ),
            "foldPairIds": service.fold_pair_ids,
        },
        "thresholdSearch": {
            "start": arguments.threshold_start,
            "end": arguments.threshold_end,
            "step": arguments.threshold_step,
            "selectionMetric": "f1",
        },
        "models": [
            report.to_dict()
            for report in model_reports
        ],
    }


def main() -> None:
    arguments = parse_arguments()
    report = build_report(arguments)
    serialized_report = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        serialized_report,
        encoding="utf-8",
    )
    print(f"Report written to: {arguments.output}")
    for model in report["models"]:
        metrics = model["aggregateMetrics"]
        threshold = model["thresholdSummary"]
        print(
            f"{model['model']}: "
            f"F1={metrics['f1']:.4f}, "
            f"PR-AUC={metrics['prAuc']:.4f}, "
            f"threshold={threshold['average']:.4f}"
        )


if __name__ == "__main__":
    main()
