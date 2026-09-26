"""Add pgvector backed article embeddings.

Revision ID: 20260926_02
Revises: 20260926_01
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "20260926_02"
down_revision: str | Sequence[str] | None = "20260926_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 512


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "article_embeddings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "article_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "embedding",
            Vector(EMBEDDING_DIMENSIONS),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "article_id",
            "model_name",
            name="uq_article_embedding_article_model",
        ),
    )
    op.create_index(
        op.f("ix_article_embeddings_article_id"),
        "article_embeddings",
        ["article_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_article_embeddings_model_name"),
        "article_embeddings",
        ["model_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_article_embeddings_model_name"),
        table_name="article_embeddings",
    )
    op.drop_index(
        op.f("ix_article_embeddings_article_id"),
        table_name="article_embeddings",
    )
    op.drop_table("article_embeddings")
