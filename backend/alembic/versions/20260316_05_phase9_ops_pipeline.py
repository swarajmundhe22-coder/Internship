"""phase 9 ops pipeline and export orchestration

Revision ID: 20260316_05
Revises: 20260316_04
Create Date: 2026-03-16 00:00:03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_05"
down_revision = "20260316_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "atlas_export_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("region", sa.String(length=160), nullable=False),
        sa.Column("export_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("output_uri", sa.Text(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("attempt_count >= 0", name="ck_atlas_export_jobs_attempt_count_nonnegative"),
        sa.CheckConstraint("max_attempts > 0", name="ck_atlas_export_jobs_max_attempts_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_atlas_export_jobs_tenant_id", "atlas_export_jobs", ["tenant_id"])
    op.create_index("ix_atlas_export_jobs_region", "atlas_export_jobs", ["region"])
    op.create_index("ix_atlas_export_jobs_status", "atlas_export_jobs", ["status"])
    op.create_index("ix_atlas_export_jobs_created_at", "atlas_export_jobs", ["created_at"])

    op.create_table(
        "dead_letter_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("event_source", sa.String(length=80), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("retry_count >= 0", name="ck_dead_letter_events_retry_nonnegative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dead_letter_events_tenant_id", "dead_letter_events", ["tenant_id"])
    op.create_index("ix_dead_letter_events_event_source", "dead_letter_events", ["event_source"])
    op.create_index("ix_dead_letter_events_created_at", "dead_letter_events", ["created_at"])

    op.alter_column("atlas_export_jobs", "attempt_count", server_default=None)
    op.alter_column("atlas_export_jobs", "max_attempts", server_default=None)
    op.alter_column("atlas_export_jobs", "metadata_json", server_default=None)
    op.alter_column("dead_letter_events", "retry_count", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_dead_letter_events_created_at", table_name="dead_letter_events")
    op.drop_index("ix_dead_letter_events_event_source", table_name="dead_letter_events")
    op.drop_index("ix_dead_letter_events_tenant_id", table_name="dead_letter_events")
    op.drop_table("dead_letter_events")

    op.drop_index("ix_atlas_export_jobs_created_at", table_name="atlas_export_jobs")
    op.drop_index("ix_atlas_export_jobs_status", table_name="atlas_export_jobs")
    op.drop_index("ix_atlas_export_jobs_region", table_name="atlas_export_jobs")
    op.drop_index("ix_atlas_export_jobs_tenant_id", table_name="atlas_export_jobs")
    op.drop_table("atlas_export_jobs")
