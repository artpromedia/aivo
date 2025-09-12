"""
Add org_settings and tenant_settings tables

Revision ID: add_settings_tables
Revises:
Create Date: 2025-09-12 15:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_settings_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create org_settings table
    op.create_table(
        'org_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id')
    )
    op.create_index(op.f('ix_org_settings_org_id'), 'org_settings', ['org_id'], unique=False)

    # Create tenant_settings table
    op.create_table(
        'tenant_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('setting_type', sa.String(), nullable=False),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'setting_type', name='uq_tenant_setting_type')
    )
    op.create_index(op.f('ix_tenant_settings_tenant_id'), 'tenant_settings', ['tenant_id'], unique=False)

    # Insert default organization settings
    op.execute("""
        INSERT INTO org_settings (id, org_id, settings, updated_by) VALUES
        (gen_random_uuid(), 'default_org',
         '{"brand_name": "AIVO Education", "logo_url": "", "primary_color": "#3B82F6", "support_email": "support@aivo.education", "website_url": "https://aivo.education", "privacy_policy_url": "", "terms_of_service_url": ""}',
         'system')
        ON CONFLICT (org_id) DO NOTHING;
    """)

    # Insert default tenant settings
    op.execute("""
        INSERT INTO tenant_settings (id, tenant_id, setting_type, settings, updated_by) VALUES
        (gen_random_uuid(), 'default_tenant', 'locale',
         '{"default_locale": "en-US", "time_zone": "UTC", "date_format": "MM/DD/YYYY", "currency": "USD", "grade_scheme": "letter", "first_day_of_week": 0}',
         'system'),
        (gen_random_uuid(), 'default_tenant', 'residency',
         '{"region": "us-east", "processing_purposes": ["educational", "analytics"], "data_retention_days": 2555, "cross_border_transfer": false, "compliance_framework": "FERPA"}',
         'system'),
        (gen_random_uuid(), 'default_tenant', 'consent',
         '{"media_default": false, "analytics_opt_in": true, "retention_days": 2555, "parental_consent_required": true, "consent_expiry_days": 365, "withdrawal_process": "contact_support"}',
         'system')
        ON CONFLICT (tenant_id, setting_type) DO NOTHING;
    """)


def downgrade():
    op.drop_index(op.f('ix_tenant_settings_tenant_id'), table_name='tenant_settings')
    op.drop_table('tenant_settings')
    op.drop_index(op.f('ix_org_settings_org_id'), table_name='org_settings')
    op.drop_table('org_settings')
