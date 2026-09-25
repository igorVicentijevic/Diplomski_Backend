from collections.abc import Sequence
from importlib.util import find_spec

if find_spec("sentence_transformers") is not None:
    from sentence_transformers import SentenceTransformer
else:
    SentenceTransformer = None

from .EmbeddingEngine import (
    EmbeddingEngine,
)


class SentenceTransformerEmbeddingEngine(EmbeddingEngine):
    def __init__(self, model_name: str) -> None:
        if SentenceTransformer is None:
            raise ModuleNotFoundError(
                "Install the semantic experiment dependencies with "
                'python -m pip install -e ".[semantic-experiments]".'
            )
        self._model = SentenceTransformer(model_name)

    def encode(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        
        embeddings = self._model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        
        return embeddings.tolist()
