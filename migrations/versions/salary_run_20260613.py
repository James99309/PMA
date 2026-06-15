"""月度薪资审批批次表 salary_runs(2026-06-13)

HR 生成当月全员薪资表 → 提交审批(财务主管→财务总监→总经理)→ 提交即锁定该公司该月
个人薪资;召回解锁,通过永久锁。snapshot 固化提交时各人各项当月应发。

幂等:表已存在则跳过(本地 create_all 可能已建)。

Revision ID: salary_run_20260613
Revises: dept_seed_companies_20260613
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa

revision = 'salary_run_20260613'
down_revision = 'dept_seed_companies_20260613'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if 'salary_runs' in insp.get_table_names():
        return
    op.create_table(
        'salary_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_name', sa.String(length=200), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending'),
        sa.Column('is_locked', sa.Boolean(), server_default=sa.false()),
        sa.Column('snapshot', sa.JSON()),
        sa.Column('total_amount', sa.Numeric(15, 2)),
        sa.Column('headcount', sa.Integer()),
        sa.Column('initiated_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('approval_instance_id', sa.Integer()),
        sa.Column('settled_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.UniqueConstraint('company_name', 'year', 'month', name='uq_salary_run'),
    )
    op.create_index('ix_salary_runs_company_name', 'salary_runs', ['company_name'])


def downgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if 'salary_runs' in insp.get_table_names():
        op.drop_table('salary_runs')
