import argparse
import json
import os
from pathlib import Path
from typing import Any

from .ArticlePairJsonCodec import (
    ArticlePairJsonCodec,
)

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent
    / "datasets"
    / "article_pairs.jsonl"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactively label generated article pairs."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )
    return parser.parse_args()


def load_entries(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    codec = ArticlePairJsonCodec()
    with path.open(encoding="utf-8") as dataset:
        for line_number, line in enumerate(dataset, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                codec.decode(payload)
            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    f"Invalid dataset entry at line {line_number}."
                ) from error
            entries.append(payload)
    return entries


def save_entries(
    path: Path,
    entries: list[dict[str, Any]],
) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as dataset:
        for entry in entries:
            dataset.write(
                json.dumps(entry, ensure_ascii=False) + "\n"
            )
        dataset.flush()
        os.fsync(dataset.fileno())
    temporary_path.replace(path)


def display_entry(
    entry: dict[str, Any],
    current: int,
    total: int,
) -> None:
    left = entry["left"]
    right = entry["right"]
    candidate_type = entry.get("candidateType", "unknown")
    event_id = entry.get("eventId")
    print()
    print(f"PAIR {current}/{total} [{candidate_type}]")
    print()
    print(f"LEFT [{left['source']}]")
    print(left["title"])
    print(left["summary"])
    print()
    print(f"RIGHT [{right['source']}]")
    print(right["title"])
    print(right["summary"])
    print()
    print("[s] isti događaj")
    print("[d] različit događaj")
    print("[p] preskoči")
    print("[q] sačuvaj i izađi")
    if event_id is not None:
        print(f"Trenutni event ID: {event_id}")


def main() -> None:
    arguments = parse_arguments()
    entries = load_entries(arguments.dataset)
    unlabelled_indexes = [
        index
        for index, entry in enumerate(entries)
        if entry["sameEvent"] is None
    ]
    if not unlabelled_indexes:
        print("Nema neoznačenih parova.")
        return

    for position, entry_index in enumerate(
        unlabelled_indexes,
        start=1,
    ):
        entry = entries[entry_index]
        display_entry(
            entry,
            current=position,
            total=len(unlabelled_indexes),
        )
        while True:
            action = input("> ").strip().casefold()
            if action == "q":
                return
            if action == "p":
                break
            if action not in {"s", "d"}:
                print("Unesite s, d, p ili q.")
                continue

            entry["sameEvent"] = action == "s"
            if action == "s":
                while True:
                    event_id = input("Event ID: ").strip()
                    if event_id:
                        entry["eventId"] = event_id
                        break
                    print(
                        "Pozitivan par mora imati neprazan event ID."
                    )
            else:
                entry.pop("eventId", None)
            save_entries(arguments.dataset, entries)
            break

    print("Svi parovi su označeni.")


if __name__ == "__main__":
    main()
