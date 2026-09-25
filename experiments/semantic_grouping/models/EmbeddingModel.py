from collections.abc import Sequence
from typing import Protocol


class EmbeddingModel(Protocol):
    def encode(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        ...
