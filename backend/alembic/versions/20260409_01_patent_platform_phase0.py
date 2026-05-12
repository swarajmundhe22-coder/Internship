"""Patent Platform Phase 0 MVP - Database schema migration.

Creates tables for:
- patents (core patent applications)
- inventors (applicants for each patent)
- materials (5K hand-curated materials database)
- patent_audit_logs (audit trail for compliance)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Create patent platform tables."""

    # Patents table
    op.create_table(
        'patents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=False),
        sa.Column('technical_field', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('patent_type', sa.String(50), nullable=False, server_default='UTILITY'),
        sa.Column('embodiments', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('claims_summary', sa.Text(), nullable=True),
        sa.Column('detailed_description', sa.Text(), nullable=True),
        sa.Column('jurisdictions', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('fea_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('fea_file_name', sa.String(255), nullable=True),
        sa.Column('uspto_application_number', sa.String(50), nullable=True),
        sa.Column('indian_ipo_application_number', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('filed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uspto_application_number'),
        sa.UniqueConstraint('indian_ipo_application_number'),
    )
    op.create_index('ix_patents_tenant_id', 'patents', ['tenant_id'])
    op.create_index('ix_patents_status', 'patents', ['status'])
    op.create_index('ix_patents_created_at', 'patents', ['created_at'])

    # Inventors table
    op.create_table(
        'inventors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('country', sa.String(2), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='PRIMARY'),
        sa.ForeignKeyConstraint(['patent_id'], ['patents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_inventors_patent_id', 'inventors', ['patent_id'])
    op.create_index('ix_inventors_email', 'inventors', ['email'])

    # Materials table
    op.create_table(
        'materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('material_type', sa.String(50), nullable=False),
        sa.Column('density', sa.Float(), nullable=False),
        sa.Column('youngs_modulus', sa.Float(), nullable=False),
        sa.Column('tensile_strength', sa.Float(), nullable=False),
        sa.Column('yield_strength', sa.Float(), nullable=True),
        sa.Column('elongation_at_break', sa.Float(), nullable=True),
        sa.Column('corrosion_resistance', sa.String(50), nullable=False),
        sa.Column('temperature_range_min', sa.Float(), nullable=True),
        sa.Column('temperature_range_max', sa.Float(), nullable=True),
        sa.Column('corrosion_potential', sa.Float(), nullable=True),
        sa.Column('corrosion_current_density', sa.Float(), nullable=True),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(1024), nullable=True),
        sa.Column('datasheet_url', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_materials_type', 'materials', ['material_type'])
    op.create_index('ix_materials_corrosion_resistance', 'materials', ['corrosion_resistance'])

    # Patent audit logs table
    op.create_table(
        'patent_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('actor', sa.String(255), nullable=False),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['patent_id'], ['patents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_patent_audit_logs_patent_id', 'patent_audit_logs', ['patent_id'])
    op.create_index('ix_patent_audit_logs_timestamp', 'patent_audit_logs', ['timestamp'])
    op.create_index('ix_patent_audit_logs_action', 'patent_audit_logs', ['action'])


def downgrade() -> None:
    """Drop patent platform tables."""
    op.drop_table('patent_audit_logs')
    op.drop_table('materials')
    op.drop_table('inventors')
    op.drop_table('patents')
