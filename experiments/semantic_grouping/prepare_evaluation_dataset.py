import argparse
import json
from pathlib import Path
from typing import Any

MODULE_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_INPUT_PATH = MODULE_DIRECTORY / "datasets" / "candidates.jsonl"
DEFAULT_OUTPUT_PATH = (
    MODULE_DIRECTORY
    / "datasets"
    / "article_pairs_v1.jsonl"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze the currently labelled article pairs for evaluation."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Explicitly replace an existing frozen dataset.",
    )
    return parser.parse_args()


def prepare_dataset(
    input_path: Path,
    output_path: Path,
    force: bool = False,
) -> dict[str, int]:
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Frozen dataset already exists: {output_path}"
        )

    labelled_payloads: list[dict[str, Any]] = []
    positive_count = 0
    negative_count = 0
    hard_negative_count = 0
    excluded_count = 0

    with input_path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise TypeError("Dataset entry must be an object.")
                same_event = payload["sameEvent"]
                if same_event is not None and not isinstance(
                    same_event,
                    bool,
                ):
                    raise TypeError(
                        "sameEvent must be a boolean or null."
                    )
            except (
                KeyError,
                TypeError,
                json.JSONDecodeError,
            ) as error:
                raise ValueError(
                    f"Invalid dataset entry at line {line_number}."
                ) from error

            if same_event is None:
                excluded_count += 1
                continue

            labelled_payloads.append(payload)
            if same_event:
                positive_count += 1
            else:
                negative_count += 1
                if payload.get("candidateType") == "hard_negative":
                    hard_negative_count += 1

    if not labelled_payloads:
        raise ValueError("No labelled article pairs were found.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(
        f"{output_path.suffix}.tmp"
    )
    serialized = "\n".join(
        json.dumps(payload, ensure_ascii=False)
        for payload in labelled_payloads
    )
    temporary_path.write_text(
        f"{serialized}\n",
        encoding="utf-8",
    )
    temporary_path.replace(output_path)

    return {
        "positive": positive_count,
        "negative": negative_count,
        "hardNegative": hard_negative_count,
        "excluded": excluded_count,
    }


def main() -> None:
    arguments = parse_arguments()
    statistics = prepare_dataset(
        arguments.input,
        arguments.output,
        arguments.force,
    )
    print(f"Positive:       {statistics['positive']}")
    print(f"Negative:       {statistics['negative']}")
    print(f"Hard negative:  {statistics['hardNegative']}")
    print(f"Excluded:       {statistics['excluded']}")


if __name__ == "__main__":
    main()
