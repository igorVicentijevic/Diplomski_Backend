from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.Base import Base

if TYPE_CHECKING:
    from app.articles.models.ArticleAnalysisModel import (
        ArticleAnalysisModel,
    )


class ArticleToneAnalysisModel(Base):
    __tablename__ = "article_tone_analyses"

    article_id: Mapped[str] = mapped_column(
        ForeignKey("article_analyses.article_id", ondelete="CASCADE"),
        primary_key=True,
    )
    negative_percentage: Mapped[float] = mapped_column(Float)
    positive_percentage: Mapped[float] = mapped_column(Float)
    neutral_percentage: Mapped[float] = mapped_column(Float)
    input_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    provider: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    prompt_version: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    analysis: Mapped["ArticleAnalysisModel"] = relationship(
        back_populates="tone",
    )
