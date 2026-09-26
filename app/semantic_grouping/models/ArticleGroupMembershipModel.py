from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.Base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ArticleGroupMembershipModel(Base):
    __tablename__ = "article_group_memberships"

    group_id: Mapped[str] = mapped_column(
        ForeignKey("article_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    article_id: Mapped[str] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
    )
