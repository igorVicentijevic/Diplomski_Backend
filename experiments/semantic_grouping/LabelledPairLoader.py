import json
from pathlib import Path

from experiments.semantic_grouping.models.ArticlePair import ArticlePair


class LabelledPairLoader:
    def load(self, path: Path) -> list[ArticlePair]:
        pairs: list[ArticlePair] = []

        with path.open(encoding="utf-8") as dataset:
            for line_number, line in enumerate(dataset, start=1):
                if not line.strip():
                    continue

                try:
                    payload = json.loads(line)
                    left = payload["left"]
                    right = payload["right"]
                    pair = ArticlePair(
                        pair_id=str(payload["id"]),
                        left_title=str(left["title"]),
                        left_summary=str(left["summary"]),
                        right_title=str(right["title"]),
                        right_summary=str(right["summary"]),
                        same_event=self._read_label(
                            payload["sameEvent"]
                        ),
                    )
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    json.JSONDecodeError,
                ) as error:
                    raise ValueError(
                        f"Invalid dataset entry at line {line_number}."
                    ) from error

                pairs.append(pair)

        if not pairs:
            raise ValueError("The labelled pair dataset is empty.")

        return pairs

    @staticmethod
    def _read_label(value: object) -> bool:
        if not isinstance(value, bool):
            raise TypeError("sameEvent must be a boolean.")
        return value
