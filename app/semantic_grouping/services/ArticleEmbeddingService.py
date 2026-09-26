from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.grouping.ArticleEmbeddingGenerator import (
    ArticleEmbeddingGenerator,
)
from app.semantic_grouping.grouping.ArticleEmbeddingProvider import (
    ArticleEmbeddingProvider,
)
from app.semantic_grouping.grouping.ArticleEmbeddingRequestFactory import (
    ArticleEmbeddingRequestFactory,
)
from app.semantic_grouping.models.ArticleEmbeddingRequest import (
    ArticleEmbeddingRequest,
)
from app.vectordb.models.ArticleEmbedding import (
    ArticleEmbedding,
)
from app.vectordb.repositories.ArticleEmbeddingRepository import (
    ArticleEmbeddingRepository,
)


class ArticleEmbeddingService(ArticleEmbeddingProvider):
    """Reuses stored embeddings and generates only the missing ones."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        request_factory: ArticleEmbeddingRequestFactory,
        generator: ArticleEmbeddingGenerator,
        model_name: str,
    ) -> None:
        if not model_name.strip():
            raise ValueError("Model name must not be empty.")
        self._session_factory = session_factory
        self._request_factory = request_factory
        self._generator = generator
        self._model_name = model_name

    async def provide(
        self,
        articles: Sequence[ArticleModel],
    ) -> dict[str, list[float]]:
        requests = self._request_factory.create(articles)
        if not requests:
            return {}

        reusable = await self._load_reusable(requests)
        generated = await self._generator.generate(
            self._select_outdated(requests, reusable)
        )
        await self._save(generated)

        return reusable | {
            embedding.article_id: embedding.vector
            for embedding in generated
        }

    async def _load_reusable(
        self,
        requests: Sequence[ArticleEmbeddingRequest],
    ) -> dict[str, list[float]]:
        hash_by_article_id = {
            request.article_id: request.input_hash
            for request in requests
        }

        async with self._session_factory() as session:
            stored_embeddings = await ArticleEmbeddingRepository(
                session
            ).list_by_article_ids(
                self._model_name,
                list(hash_by_article_id),
            )

        return {
            stored.article_id: list(stored.embedding)
            for stored in stored_embeddings
            if stored.embedding
            and stored.input_hash
            == hash_by_article_id[stored.article_id]
        }

    async def _save(
        self,
        embeddings: Sequence[ArticleEmbedding],
    ) -> None:
        if not embeddings:
            return

        async with self._session_factory() as session:
            async with session.begin():
                await ArticleEmbeddingRepository(session).save_all(
                    self._model_name,
                    embeddings,
                )

    @staticmethod
    def _select_outdated(
        requests: Sequence[ArticleEmbeddingRequest],
        reusable: dict[str, list[float]],
    ) -> list[ArticleEmbeddingRequest]:
        return [
            request
            for request in requests
            if request.article_id not in reusable
        ]
