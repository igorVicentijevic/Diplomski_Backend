from collections.abc import Sequence


class SentenceTransformerEmbeddingModel:
    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "Install the semantic experiment dependencies with "
                'python -m pip install -e ".[semantic-experiments]".'
            ) from error

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
