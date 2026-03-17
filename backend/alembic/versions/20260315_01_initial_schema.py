"""initial schema

Revision ID: 20260315_01
Revises:
Create Date: 2026-03-15 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260315_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("alloy_group", sa.String(length=120), nullable=False),
        sa.Column("density_kg_m3", sa.Float(), nullable=False),
        sa.Column("electrochemical_potential_v", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("density_kg_m3 > 0", name="ck_material_density_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_materials_name"),
    )
    op.create_index("ix_materials_name", "materials", ["name"])

    op.create_table(
        "environment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_name", sa.String(length=80), nullable=False),
        sa.Column("temperature_c", sa.Float(), nullable=False),
        sa.Column("relative_humidity_pct", sa.Float(), nullable=False),
        sa.Column("chloride_ppm", sa.Float(), nullable=False),
        sa.Column("ph", sa.Float(), nullable=False),
        sa.Column("dissolved_oxygen_mg_l", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "relative_humidity_pct >= 0 AND relative_humidity_pct <= 100",
            name="ck_environment_rh_range",
        ),
        sa.CheckConstraint("ph >= 0 AND ph <= 14", name="ck_environment_ph_range"),
        sa.CheckConstraint("chloride_ppm >= 0", name="ck_environment_chloride_nonnegative"),
        sa.CheckConstraint("dissolved_oxygen_mg_l >= 0", name="ck_environment_do_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_name", name="uq_environment_profile_name"),
    )
    op.create_index("ix_environment_profile_name", "environment", ["profile_name"])
    op.create_index("ix_environment_created_at", "environment", ["created_at"])

    op.create_table(
        "simulation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("material_id", sa.Uuid(), nullable=False),
        sa.Column("environment_id", sa.Uuid(), nullable=False),
        sa.Column("exposed_area_m2", sa.Float(), nullable=False),
        sa.Column("exposure_time_hours", sa.Float(), nullable=False),
        sa.Column("corrosion_rate_mm_per_year", sa.Float(), nullable=False),
        sa.Column("estimated_lifespan_years", sa.Float(), nullable=False),
        sa.Column("risk_classification", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("exposed_area_m2 > 0", name="ck_simulation_area_positive"),
        sa.CheckConstraint("exposure_time_hours > 0", name="ck_simulation_time_positive"),
        sa.CheckConstraint("corrosion_rate_mm_per_year >= 0", name="ck_simulation_corrosion_nonnegative"),
        sa.CheckConstraint("estimated_lifespan_years >= 0", name="ck_simulation_lifespan_nonnegative"),
        sa.CheckConstraint("version > 0", name="ck_simulation_version_positive"),
        sa.ForeignKeyConstraint(["environment_id"], ["environment.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulation_material_id", "simulation", ["material_id"])
    op.create_index("ix_simulation_environment_id", "simulation", ["environment_id"])
    op.create_index("ix_simulation_risk_classification", "simulation", ["risk_classification"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("simulation_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("report_uri", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("version > 0", name="ck_reports_version_positive"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_simulation_id", "reports", ["simulation_id"])
    op.create_index("ix_reports_generated_at", "reports", ["generated_at"])

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])

    op.create_table(
        "project_simulations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("simulation_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "simulation_id", name="uq_project_simulation"),
    )
    op.create_index("ix_project_simulations_project_id", "project_simulations", ["project_id"])
    op.create_index("ix_project_simulations_simulation_id", "project_simulations", ["simulation_id"])

    op.create_table(
        "comparison_sets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comparison_sets_project_id", "comparison_sets", ["project_id"])

    op.create_table(
        "comparison_set_simulations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("comparison_set_id", sa.Uuid(), nullable=False),
        sa.Column("simulation_id", sa.Uuid(), nullable=False),
        sa.Column("ordering", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("ordering >= 0", name="ck_comparison_set_ordering_nonnegative"),
        sa.ForeignKeyConstraint(["comparison_set_id"], ["comparison_sets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["simulation_id"], ["simulation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("comparison_set_id", "simulation_id", name="uq_comparison_set_simulation"),
        sa.UniqueConstraint("comparison_set_id", "ordering", name="uq_comparison_set_ordering"),
    )
    op.create_index(
        "ix_comparison_set_simulations_set_id", "comparison_set_simulations", ["comparison_set_id"]
    )
    op.create_index(
        "ix_comparison_set_simulations_simulation_id", "comparison_set_simulations", ["simulation_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_comparison_set_simulations_simulation_id", table_name="comparison_set_simulations")
    op.drop_index("ix_comparison_set_simulations_set_id", table_name="comparison_set_simulations")
    op.drop_table("comparison_set_simulations")

    op.drop_index("ix_comparison_sets_project_id", table_name="comparison_sets")
    op.drop_table("comparison_sets")

    op.drop_index("ix_project_simulations_simulation_id", table_name="project_simulations")
    op.drop_index("ix_project_simulations_project_id", table_name="project_simulations")
    op.drop_table("project_simulations")

    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_table("projects")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_reports_generated_at", table_name="reports")
    op.drop_index("ix_reports_simulation_id", table_name="reports")
    op.drop_table("reports")

    op.drop_index("ix_simulation_risk_classification", table_name="simulation")
    op.drop_index("ix_simulation_environment_id", table_name="simulation")
    op.drop_index("ix_simulation_material_id", table_name="simulation")
    op.drop_table("simulation")

    op.drop_index("ix_environment_created_at", table_name="environment")
    op.drop_index("ix_environment_profile_name", table_name="environment")
    op.drop_table("environment")

    op.drop_index("ix_materials_name", table_name="materials")
    op.drop_table("materials")
