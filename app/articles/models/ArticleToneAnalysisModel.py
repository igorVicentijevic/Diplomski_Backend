from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey
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
    analysis: Mapped["ArticleAnalysisModel"] = relationship(
        back_populates="tone",
    )
