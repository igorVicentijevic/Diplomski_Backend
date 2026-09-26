from collections.abc import Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vectordb.models.ArticleEmbedding import (
    ArticleEmbedding,
)
from app.vectordb.models.ArticleEmbeddingModel import (
    ArticleEmbeddingModel,
)


class ArticleEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_article_ids(
        self,
        model_name: str,
        article_ids: Sequence[str],
    ) -> list[ArticleEmbeddingModel]:
        if not article_ids:
            return []

        result = await self._session.scalars(
            select(ArticleEmbeddingModel).where(
                ArticleEmbeddingModel.model_name == model_name,
                ArticleEmbeddingModel.article_id.in_(set(article_ids)),
            )
        )
        return list(result)

    async def save_all(
        self,
        model_name: str,
        embeddings: Sequence[ArticleEmbedding],
    ) -> None:
        if not embeddings:
            return

        stored_by_article_id = {
            stored.article_id: stored
            for stored in await self.list_by_article_ids(
                model_name,
                [embedding.article_id for embedding in embeddings],
            )
        }

        for embedding in embeddings:
            stored = stored_by_article_id.get(embedding.article_id)
            if stored is None:
                self._session.add(
                    self._create_model(model_name, embedding)
                )
                continue

            stored.input_hash = embedding.input_hash
            stored.embedding = embedding.vector

    @staticmethod
    def _create_model(
        model_name: str,
        embedding: ArticleEmbedding,
    ) -> ArticleEmbeddingModel:
        return ArticleEmbeddingModel(
            id=str(uuid4()),
            article_id=embedding.article_id,
            model_name=model_name,
            input_hash=embedding.input_hash,
            embedding=embedding.vector,
        )
