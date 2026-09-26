import asyncio
from collections.abc import Sequence

from app.semantic_grouping.embedding_engine.EmbeddingEngine import (
    EmbeddingEngine,
)
from app.semantic_grouping.models.ArticleEmbeddingRequest import (
    ArticleEmbeddingRequest,
)
from app.vectordb.models.ArticleEmbedding import (
    ArticleEmbedding,
)


class ArticleEmbeddingGenerator:
    """Turns embedding requests into vectors, without any persistence."""

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        expected_dimensions: int,
    ) -> None:
        if expected_dimensions <= 0:
            raise ValueError(
                "Expected embedding dimensions must be greater "
                "than zero."
            )
        self._embedding_engine = embedding_engine
        self._expected_dimensions = expected_dimensions

    async def generate(
        self,
        requests: Sequence[ArticleEmbeddingRequest],
    ) -> list[ArticleEmbedding]:
        if not requests:
            return []

        vectors = await asyncio.to_thread(
            self._embedding_engine.encode,
            [request.text for request in requests],
        )
        if len(vectors) != len(requests):
            raise ValueError(
                "Embedding engine returned an unexpected number "
                "of embeddings."
            )

        return [
            self._create_embedding(request, vector)
            for request, vector in zip(requests, vectors, strict=True)
        ]

    def _create_embedding(
        self,
        request: ArticleEmbeddingRequest,
        vector: list[float],
    ) -> ArticleEmbedding:
        if len(vector) != self._expected_dimensions:
            raise ValueError(
                "Embedding engine returned "
                f"{len(vector)} dimensions while "
                f"{self._expected_dimensions} were expected."
            )

        return ArticleEmbedding(
            article_id=request.article_id,
            input_hash=request.input_hash,
            vector=list(vector),
        )
