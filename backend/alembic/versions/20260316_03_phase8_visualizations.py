"""phase 8 visualization and export tables

Revision ID: 20260316_03
Revises: 20260316_02
Create Date: 2026-03-16 00:00:01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_03"
down_revision = "20260316_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visualizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("simulation_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="twin"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="generated"),
        sa.Column("overlay_accuracy", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("overlay_accuracy >= 0 AND overlay_accuracy <= 1", name="ck_visualizations_overlay_accuracy"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulation.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_visualizations_simulation_id", "visualizations", ["simulation_id"])
    op.create_index("ix_visualizations_tenant_id", "visualizations", ["tenant_id"])
    op.create_index("ix_visualizations_mode", "visualizations", ["mode"])
    op.create_index("ix_visualizations_created_at", "visualizations", ["created_at"])

    op.create_table(
        "visualization_exports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("visualization_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("file_uri", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["visualization_id"], ["visualizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_visualization_exports_visualization_id", "visualization_exports", ["visualization_id"])
    op.create_index("ix_visualization_exports_tenant_id", "visualization_exports", ["tenant_id"])
    op.create_index("ix_visualization_exports_file_type", "visualization_exports", ["file_type"])
    op.create_index("ix_visualization_exports_created_at", "visualization_exports", ["created_at"])

    op.alter_column("visualizations", "mode", server_default=None)
    op.alter_column("visualizations", "metadata_json", server_default=None)
    op.alter_column("visualizations", "status", server_default=None)
    op.alter_column("visualizations", "overlay_accuracy", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_visualization_exports_created_at", table_name="visualization_exports")
    op.drop_index("ix_visualization_exports_file_type", table_name="visualization_exports")
    op.drop_index("ix_visualization_exports_tenant_id", table_name="visualization_exports")
    op.drop_index("ix_visualization_exports_visualization_id", table_name="visualization_exports")
    op.drop_table("visualization_exports")

    op.drop_index("ix_visualizations_created_at", table_name="visualizations")
    op.drop_index("ix_visualizations_mode", table_name="visualizations")
    op.drop_index("ix_visualizations_tenant_id", table_name="visualizations")
    op.drop_index("ix_visualizations_simulation_id", table_name="visualizations")
    op.drop_table("visualizations")
