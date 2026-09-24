from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.Base import Base

if TYPE_CHECKING:
    from app.articles.models.ArticleAnalysisModel import (
        ArticleAnalysisModel,
    )


def utc_now() -> datetime:
    return datetime.now(UTC)


class ArticleModel(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(32))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    article_url: Mapped[str] = mapped_column(Text)
    normalized_url: Mapped[str] = mapped_column(
        String(2048),
        unique=True,
        index=True,
    )
    related_city_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    analysis: Mapped["ArticleAnalysisModel | None"] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
        uselist=False,
    )
