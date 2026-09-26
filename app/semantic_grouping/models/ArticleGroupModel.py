from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.Base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ArticleGroupModel(Base):
    __tablename__ = "article_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    latest_article_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )
