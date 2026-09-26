"""Add persistent article groups.

Revision ID: 20260926_02
Revises: 20260926_01
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260926_02"
down_revision: str | Sequence[str] | None = "20260926_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "article_groups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "latest_article_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_article_groups_active"),
        "article_groups",
        ["active"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_groups_latest_article_at"),
        "article_groups",
        ["latest_article_at"],
        unique=False,
    )
    op.create_table(
        "article_group_memberships",
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("article_id", sa.String(length=255), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["article_groups.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "group_id",
            "article_id",
            name="pk_article_group_memberships",
        ),
    )
    op.create_index(
        op.f("ix_article_group_memberships_article_id"),
        "article_group_memberships",
        ["article_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_article_group_memberships_article_id"),
        table_name="article_group_memberships",
    )
    op.drop_table("article_group_memberships")
    op.drop_index(
        op.f("ix_article_groups_latest_article_at"),
        table_name="article_groups",
    )
    op.drop_index(
        op.f("ix_article_groups_active"),
        table_name="article_groups",
    )
    op.drop_table("article_groups")
