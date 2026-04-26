"""add link_type to prospect_projects and create prospect_claim_requests

Revision ID: da26751ef991
Revises: cf15777f3e83
Create Date: 2026-04-26

Phase 1 of lost-projects tab.

Changes:
1. Add `link_type` column to `prospect_projects` to differentiate
   原始转化记录 ('converted') from AI 反向调研补全记录 ('research').
2. Create `prospect_claim_requests` table for 申请参与流失项目 records,
   with (project_id, applicant_id) uniqueness for permanent dedup.
"""
from alembic import op
from sqlalchemy import inspect
import sqlalchemy as sa


revision = 'da26751ef991'
down_revision = 'cf15777f3e83'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    # 1. prospect_projects.link_type (skip if already present)
    pp_cols = [c['name'] for c in insp.get_columns('prospect_projects')]
    if 'link_type' not in pp_cols:
        with op.batch_alter_table('prospect_projects', schema=None) as batch_op:
            batch_op.add_column(
                sa.Column('link_type', sa.String(length=20),
                          server_default='converted', nullable=False)
            )
            batch_op.create_index(
                'ix_prospect_projects_link_type', ['link_type'], unique=False
            )

    # 2. prospect_claim_requests (skip if already present from db.create_all)
    if insp.has_table('prospect_claim_requests'):
        return

    op.create_table(
        'prospect_claim_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False,
                  server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['applicant_id'], ['users.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'applicant_id',
                            name='uq_claim_project_applicant'),
    )
    op.create_index('ix_claim_project', 'prospect_claim_requests',
                    ['project_id'], unique=False)
    op.create_index('ix_claim_applicant', 'prospect_claim_requests',
                    ['applicant_id'], unique=False)


def downgrade():
    op.drop_index('ix_claim_applicant', table_name='prospect_claim_requests')
    op.drop_index('ix_claim_project', table_name='prospect_claim_requests')
    op.drop_table('prospect_claim_requests')

    with op.batch_alter_table('prospect_projects', schema=None) as batch_op:
        batch_op.drop_index('ix_prospect_projects_link_type')
        batch_op.drop_column('link_type')
