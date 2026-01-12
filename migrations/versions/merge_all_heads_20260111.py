"""Merge all heads 20260111

Revision ID: merge_all_heads_20260111
Revises: 6eef2ad2bfd0, add_approval_external_token_table_20260111, add_meeting_recording_tables_20260111, add_po_progress_mgmt, add_product_test_tables_20260111, add_project_address_fields_20260111, add_quality_score_to_worklogs_20260111, add_supplier_confirmation_file_20260111
Create Date: 2026-01-11 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_all_heads_20260111'
down_revision = (
    '6eef2ad2bfd0',
    'add_approval_external_token_table_20260111',
    'add_meeting_recording_tables_20260111',
    'add_po_progress_mgmt',
    'add_product_test_tables_20260111',
    'add_project_address_fields_20260111',
    'add_quality_score_to_worklogs_20260111',
    'add_supplier_confirmation_file_20260111'
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
