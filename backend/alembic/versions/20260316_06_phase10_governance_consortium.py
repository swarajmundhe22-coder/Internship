"""phase 10 governance consortium layer

Revision ID: 20260316_06
Revises: 20260316_05
Create Date: 2026-03-16 00:00:04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_06"
down_revision = "20260316_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dossiers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("simulation_id", sa.Uuid(), nullable=False),
        sa.Column("format", sa.String(length=10), nullable=False),
        sa.Column("industry_module", sa.String(length=80), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dossiers_tenant_id", "dossiers", ["tenant_id"])
    op.create_index("ix_dossiers_simulation_id", "dossiers", ["simulation_id"])
    op.create_index("ix_dossiers_format", "dossiers", ["format"])
    op.create_index("ix_dossiers_created_at", "dossiers", ["created_at"])

    op.create_table(
        "decks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("export_type", sa.String(length=12), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=False),
        sa.Column("narrative_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decks_tenant_id", "decks", ["tenant_id"])
    op.create_index("ix_decks_project_id", "decks", ["project_id"])
    op.create_index("ix_decks_export_type", "decks", ["export_type"])
    op.create_index("ix_decks_created_at", "decks", ["created_at"])

    op.create_table(
        "consortium_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("tier", sa.String(length=40), nullable=False, server_default="global_utility"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_consortium_memberships_tenant_id"),
    )
    op.create_index("ix_consortium_memberships_tenant_id", "consortium_memberships", ["tenant_id"])
    op.create_index("ix_consortium_memberships_tier", "consortium_memberships", ["tier"])
    op.create_index("ix_consortium_memberships_created_at", "consortium_memberships", ["created_at"])

    op.alter_column("dossiers", "metadata_json", server_default=None)
    op.alter_column("decks", "narrative_json", server_default=None)
    op.alter_column("consortium_memberships", "tier", server_default=None)
    op.alter_column("consortium_memberships", "status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_consortium_memberships_created_at", table_name="consortium_memberships")
    op.drop_index("ix_consortium_memberships_tier", table_name="consortium_memberships")
    op.drop_index("ix_consortium_memberships_tenant_id", table_name="consortium_memberships")
    op.drop_table("consortium_memberships")

    op.drop_index("ix_decks_created_at", table_name="decks")
    op.drop_index("ix_decks_export_type", table_name="decks")
    op.drop_index("ix_decks_project_id", table_name="decks")
    op.drop_index("ix_decks_tenant_id", table_name="decks")
    op.drop_table("decks")

    op.drop_index("ix_dossiers_created_at", table_name="dossiers")
    op.drop_index("ix_dossiers_format", table_name="dossiers")
    op.drop_index("ix_dossiers_simulation_id", table_name="dossiers")
    op.drop_index("ix_dossiers_tenant_id", table_name="dossiers")
    op.drop_table("dossiers")
