"""phase 7 column backfill for users/projects/simulation

Revision ID: 20260316_02
Revises: 20260315_01
Create Date: 2026-03-16 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_02"
down_revision = "20260315_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add auth method for existing and future users.
    op.add_column(
        "users",
        sa.Column("auth_method", sa.String(length=30), nullable=False, server_default=sa.text("'local'")),
    )

    # Add project metadata storage with a safe default payload.
    op.add_column(
        "projects",
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
    )

    # Add optional simulation accuracy score and enforce [0, 1] when provided.
    op.add_column(
        "simulation",
        sa.Column("accuracy_score", sa.Float(), nullable=True),
    )
    op.create_check_constraint(
        "ck_simulation_accuracy_score_range",
        "simulation",
        "accuracy_score IS NULL OR (accuracy_score >= 0 AND accuracy_score <= 1)",
    )

    # Drop server defaults after backfill so application controls values explicitly.
    op.alter_column("users", "auth_method", server_default=None)
    op.alter_column("projects", "metadata_json", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_simulation_accuracy_score_range", "simulation", type_="check")
    op.drop_column("simulation", "accuracy_score")
    op.drop_column("projects", "metadata_json")
    op.drop_column("users", "auth_method")
