from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

from experiments.semantic_grouping.embedding_engine.EmbeddingEngine import (
    EmbeddingEngine,
)


class SentenceTransformerEmbeddingEngine(EmbeddingEngine):
    def __init__(self, model_name: str) -> None:
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
