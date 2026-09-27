from abc import ABC, abstractmethod
from collections.abc import Sequence


class IEmbeddingEngine(ABC):
    @abstractmethod
    def encode(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        ...
