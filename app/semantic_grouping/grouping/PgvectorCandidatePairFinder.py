from collections.abc import Sequence
from datetime import timedelta

from sqlalchemy import Interval, and_, literal, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import aliased

from app.articles.models.ArticleModel import ArticleModel
from app.semantic_grouping.grouping.ICandidatePairFinder import (
    ICandidatePairFinder,
)
from app.semantic_grouping.models.ArticlePairSimilarity import (
    ArticlePairSimilarity,
)
from app.vectordb.models.ArticleEmbeddingModel import (
    ArticleEmbeddingModel,
)


class PgvectorCandidatePairFinder(ICandidatePairFinder):
    """Postgres/pgvector candidate pair finder.

    Finds candidate pairs and computes their cosine similarity in a
    single SQL self-join, delegating both the pairing (time window,
    different source) and the vector math to PostgreSQL/pgvector's
    ``<=>`` cosine distance operator instead of looping over pairs in
    Python. Requires a PostgreSQL database with the pgvector
    extension; ``embedding_by_article_id`` is accepted only to satisfy
    :class:`ICandidatePairFinder` and is not used, since embeddings are
    read directly from the database.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        model_name: str,
        candidate_window: timedelta,
    ) -> None:
        if not model_name.strip():
            raise ValueError("Model name must not be empty.")
        if candidate_window <= timedelta(0):
            raise ValueError(
                "Candidate window must be greater than zero."
            )
        self._session_factory = session_factory
        self._model_name = model_name
        self._candidate_window = candidate_window

    async def find(
        self,
        articles: Sequence[ArticleModel],
        embedding_by_article_id: dict[str, list[float]],
    ) -> list[ArticlePairSimilarity]:
        article_ids = [article.id for article in articles]
        if len(article_ids) < 2:
            return []

        left_article = aliased(ArticleModel)
        right_article = aliased(ArticleModel)
        left_embedding = aliased(ArticleEmbeddingModel)
        right_embedding = aliased(ArticleEmbeddingModel)
        window = literal(self._candidate_window, type_=Interval())

        statement = (
            select(
                left_article.id.label("left_article_id"),
                right_article.id.label("right_article_id"),
                (
                    1
                    - left_embedding.embedding.cosine_distance(
                        right_embedding.embedding
                    )
                ).label("similarity"),
            )
            .select_from(left_article)
            .join(
                right_article,
                and_(
                    right_article.id > left_article.id,
                    right_article.source_id
                    != left_article.source_id,
                    right_article.published_at
                    >= left_article.published_at - window,
                    right_article.published_at
                    <= left_article.published_at + window,
                ),
            )
            .join(
                left_embedding,
                and_(
                    left_embedding.article_id == left_article.id,
                    left_embedding.model_name == self._model_name,
                ),
            )
            .join(
                right_embedding,
                and_(
                    right_embedding.article_id == right_article.id,
                    right_embedding.model_name == self._model_name,
                ),
            )
            .where(
                left_article.id.in_(article_ids),
                right_article.id.in_(article_ids),
            )
        )

        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()

        return [
            ArticlePairSimilarity(
                left_article_id=row.left_article_id,
                right_article_id=row.right_article_id,
                similarity=row.similarity,
            )
            for row in rows
        ]
