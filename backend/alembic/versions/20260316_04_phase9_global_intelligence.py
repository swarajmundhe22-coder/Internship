"""phase 9 global intelligence network

Revision ID: 20260316_04
Revises: 20260316_03
Create Date: 2026-03-16 00:00:02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_04"
down_revision = "20260316_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("tenant_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_audit_logs_tenant_id_tenants",
        "audit_logs",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])

    op.create_table(
        "iot_data",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("sensor_id", sa.String(length=120), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_iot_data_tenant_id", "iot_data", ["tenant_id"])
    op.create_index("ix_iot_data_sensor_id", "iot_data", ["sensor_id"])
    op.create_index("ix_iot_data_created_at", "iot_data", ["created_at"])

    op.create_table(
        "satellite_data",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("region", sa.String(length=160), nullable=False),
        sa.Column("imagery_source", sa.String(length=120), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_satellite_data_tenant_id", "satellite_data", ["tenant_id"])
    op.create_index("ix_satellite_data_region", "satellite_data", ["region"])
    op.create_index("ix_satellite_data_source", "satellite_data", ["imagery_source"])
    op.create_index("ix_satellite_data_created_at", "satellite_data", ["created_at"])

    op.create_table(
        "atlas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("region", sa.String(length=160), nullable=False),
        sa.Column("atlas_key", sa.String(length=80), nullable=False, server_default="risk_overlay"),
        sa.Column("export_type", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_atlas_tenant_id", "atlas", ["tenant_id"])
    op.create_index("ix_atlas_region", "atlas", ["region"])
    op.create_index("ix_atlas_export_type", "atlas", ["export_type"])
    op.create_index("ix_atlas_created_at", "atlas", ["created_at"])

    op.create_table(
        "maintenance_schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.String(length=120), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=160), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="ck_maintenance_schedules_risk_score"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_schedules_tenant_id", "maintenance_schedules", ["tenant_id"])
    op.create_index("ix_maintenance_schedules_asset_id", "maintenance_schedules", ["asset_id"])
    op.create_index("ix_maintenance_schedules_created_at", "maintenance_schedules", ["created_at"])

    op.alter_column("satellite_data", "metadata_json", server_default=None)
    op.alter_column("atlas", "atlas_key", server_default=None)
    op.alter_column("atlas", "metadata_json", server_default=None)
    op.alter_column("maintenance_schedules", "metadata_json", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_maintenance_schedules_created_at", table_name="maintenance_schedules")
    op.drop_index("ix_maintenance_schedules_asset_id", table_name="maintenance_schedules")
    op.drop_index("ix_maintenance_schedules_tenant_id", table_name="maintenance_schedules")
    op.drop_table("maintenance_schedules")

    op.drop_index("ix_atlas_created_at", table_name="atlas")
    op.drop_index("ix_atlas_export_type", table_name="atlas")
    op.drop_index("ix_atlas_region", table_name="atlas")
    op.drop_index("ix_atlas_tenant_id", table_name="atlas")
    op.drop_table("atlas")

    op.drop_index("ix_satellite_data_created_at", table_name="satellite_data")
    op.drop_index("ix_satellite_data_source", table_name="satellite_data")
    op.drop_index("ix_satellite_data_region", table_name="satellite_data")
    op.drop_index("ix_satellite_data_tenant_id", table_name="satellite_data")
    op.drop_table("satellite_data")

    op.drop_index("ix_iot_data_created_at", table_name="iot_data")
    op.drop_index("ix_iot_data_sensor_id", table_name="iot_data")
    op.drop_index("ix_iot_data_tenant_id", table_name="iot_data")
    op.drop_table("iot_data")

    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_constraint("fk_audit_logs_tenant_id_tenants", "audit_logs", type_="foreignkey")
    op.drop_column("audit_logs", "tenant_id")
