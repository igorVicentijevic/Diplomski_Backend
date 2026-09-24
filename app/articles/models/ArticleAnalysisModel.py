from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.Base import Base

if TYPE_CHECKING:
    from app.articles.models.ArticleModel import ArticleModel
    from app.articles.models.ArticleToneAnalysisModel import (
        ArticleToneAnalysisModel,
    )


def utc_now() -> datetime:
    return datetime.now(UTC)


class ArticleAnalysisModel(Base):
    __tablename__ = "article_analyses"

    article_id: Mapped[str] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    article: Mapped["ArticleModel"] = relationship(
        back_populates="analysis",
    )
    tone: Mapped["ArticleToneAnalysisModel | None"] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        uselist=False,
    )
