from collections.abc import Sequence
from importlib.util import find_spec
from typing import Any

if find_spec("sentence_transformers") is not None:
    from sentence_transformers import SentenceTransformer
else:
    SentenceTransformer = None

from app.semantic_grouping.embedding_engine.EmbeddingEngine import (
    EmbeddingEngine,
)


class SentenceTransformerEmbeddingEngine(EmbeddingEngine):
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: Any | None = None

    def encode(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def _get_model(self) -> Any:
        if SentenceTransformer is None:
            raise ModuleNotFoundError(
                "Install the application dependencies with "
                'python -m pip install -e ".".'
            )
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model
