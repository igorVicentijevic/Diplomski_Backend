from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.Base import Base
from app.vectordb.types.EmbeddingVector import EmbeddingVector

EMBEDDING_DIMENSIONS = 512


def utc_now() -> datetime:
    return datetime.now(UTC)


class ArticleEmbeddingModel(Base):
    __tablename__ = "article_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "model_name",
            name="uq_article_embedding_article_model",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    article_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(255), index=True)
    input_hash: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[list[float]] = mapped_column(
        EmbeddingVector(EMBEDDING_DIMENSIONS)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
