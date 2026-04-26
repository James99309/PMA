"""add prospect_projects and prospect_stakeholders tables

Revision ID: prospect_tables_20260426
Revises: xlsx_skill_system_20260420
Create Date: 2026-04-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'prospect_tables_20260426'
down_revision = '281843a6c6fb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'prospect_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(200), nullable=False),
        sa.Column('industry', sa.String(50), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('stage', sa.String(20), nullable=False, server_default='planning'),
        sa.Column('total_investment', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source', sa.String(20), nullable=True),
        sa.Column('claimed_by_id', sa.Integer(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('converted_project_id', sa.Integer(), nullable=True),
        sa.Column('info_updated_at', sa.DateTime(), nullable=True),
        sa.Column('info_updated_by', sa.String(50), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['claimed_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['converted_project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_prospect_projects_project_name', 'prospect_projects', ['project_name'])

    op.create_table(
        'prospect_stakeholders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prospect_id', sa.Integer(), nullable=False),
        sa.Column('stakeholder_type', sa.String(20), nullable=False),
        sa.Column('company_name', sa.String(200), nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('address', sa.String(300), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('contact_person', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['prospect_id'], ['prospect_projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_prospect_stakeholders_prospect_id', 'prospect_stakeholders', ['prospect_id'])


def downgrade():
    op.drop_index('ix_prospect_stakeholders_prospect_id', table_name='prospect_stakeholders')
    op.drop_table('prospect_stakeholders')
    op.drop_index('ix_prospect_projects_project_name', table_name='prospect_projects')
    op.drop_table('prospect_projects')
