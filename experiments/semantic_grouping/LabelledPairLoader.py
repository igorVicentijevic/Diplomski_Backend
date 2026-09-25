import json
from pathlib import Path

from .ArticlePairJsonCodec import (
    ArticlePairJsonCodec,
)
from .models.ArticlePair import ArticlePair


class LabelledPairLoader:
    def __init__(
        self,
        codec: ArticlePairJsonCodec | None = None,
    ) -> None:
        self._codec = codec or ArticlePairJsonCodec()

    def load(self, path: Path) -> list[ArticlePair]:
        pairs: list[ArticlePair] = []

        with path.open(encoding="utf-8") as dataset:
            for line_number, line in enumerate(dataset, start=1):
                if not line.strip():
                    continue

                try:
                    payload = json.loads(line)
                    pair = self._codec.decode(payload)
                    if pair.same_event is None:
                        raise ValueError(
                            "sameEvent must be labelled before evaluation."
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
