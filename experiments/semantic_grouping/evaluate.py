import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .ArticleTextBuilder import (
    ArticleTextBuilder,
)
from .EmbeddingEvaluator import (
    EmbeddingEvaluator,
)
from .LabelledPairLoader import (
    LabelledPairLoader,
)
from .embedding_engine.SentenceTransformerEmbeddingEngine import (
    SentenceTransformerEmbeddingEngine,
)

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent
    / "datasets"
    / "article_pairs.jsonl"
)
DEFAULT_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate an embedding model on labelled article pairs."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--threshold-start", type=float, default=0.50)
    parser.add_argument("--threshold-end", type=float, default=0.95)
    parser.add_argument("--threshold-step", type=float, default=0.01)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    pairs = LabelledPairLoader().load(arguments.dataset)
    evaluator = EmbeddingEvaluator(
        embedding_engine=SentenceTransformerEmbeddingEngine(
            arguments.model
        ),
        text_builder=ArticleTextBuilder(),
    )
    similarity_results = evaluator.calculate_similarities(pairs)
    best_metrics = evaluator.find_best_threshold(
        similarity_results,
        threshold_start=arguments.threshold_start,
        threshold_end=arguments.threshold_end,
        threshold_step=arguments.threshold_step,
    )

    report: dict[str, Any] = {
        "model": arguments.model,
        "dataset": str(arguments.dataset),
        "pairCount": len(pairs),
        "bestMetrics": {
            "threshold": round(best_metrics.threshold, 4),
            "precision": round(best_metrics.precision, 4),
            "recall": round(best_metrics.recall, 4),
            "f1": round(best_metrics.f1, 4),
            "truePositive": best_metrics.true_positive,
            "falsePositive": best_metrics.false_positive,
            "trueNegative": best_metrics.true_negative,
            "falseNegative": best_metrics.false_negative,
        },
        "pairs": [
            {
                **asdict(result),
                "similarity": round(result.similarity, 6),
            }
            for result in similarity_results
        ],
    }
    serialized_report = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    )

    if arguments.output is not None:
        arguments.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        arguments.output.write_text(
            serialized_report,
            encoding="utf-8",
        )

    print(serialized_report)


if __name__ == "__main__":
    main()
