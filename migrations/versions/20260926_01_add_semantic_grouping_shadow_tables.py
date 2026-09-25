"""Add semantic grouping shadow tables.

Revision ID: 20260926_01
Revises: 20260925_01
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260926_01"
down_revision: str | Sequence[str] | None = "20260925_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semantic_grouping_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("boundary_min", sa.Float(), nullable=False),
        sa.Column("boundary_max", sa.Float(), nullable=False),
        sa.Column(
            "candidate_window_hours",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("article_count", sa.Integer(), nullable=False),
        sa.Column("pair_count", sa.Integer(), nullable=False),
        sa.Column(
            "positive_pair_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "boundary_pair_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "semantic_grouping_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column(
            "left_article_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "right_article_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column(
            "predicted_same_event",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "proposed_group_id",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "is_boundary_candidate",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["left_article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["right_article_id"],
            ["articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["semantic_grouping_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "left_article_id",
            "right_article_id",
            name="uq_semantic_grouping_decision_pair",
        ),
    )
    op.create_index(
        "ix_semantic_grouping_decisions_boundary",
        "semantic_grouping_decisions",
        ["is_boundary_candidate", "similarity"],
        unique=False,
    )
    op.create_index(
        op.f("ix_semantic_grouping_decisions_left_article_id"),
        "semantic_grouping_decisions",
        ["left_article_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_semantic_grouping_decisions_proposed_group_id"),
        "semantic_grouping_decisions",
        ["proposed_group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_semantic_grouping_decisions_right_article_id"),
        "semantic_grouping_decisions",
        ["right_article_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_semantic_grouping_decisions_run_id"),
        "semantic_grouping_decisions",
        ["run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_semantic_grouping_decisions_run_id"),
        table_name="semantic_grouping_decisions",
    )
    op.drop_index(
        op.f("ix_semantic_grouping_decisions_right_article_id"),
        table_name="semantic_grouping_decisions",
    )
    op.drop_index(
        op.f("ix_semantic_grouping_decisions_proposed_group_id"),
        table_name="semantic_grouping_decisions",
    )
    op.drop_index(
        op.f("ix_semantic_grouping_decisions_left_article_id"),
        table_name="semantic_grouping_decisions",
    )
    op.drop_index(
        "ix_semantic_grouping_decisions_boundary",
        table_name="semantic_grouping_decisions",
    )
    op.drop_table("semantic_grouping_decisions")
    op.drop_table("semantic_grouping_runs")
