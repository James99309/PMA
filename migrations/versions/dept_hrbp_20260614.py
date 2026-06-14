"""部门增加 HRBP 负责人字段(2026-06-14)

Department.hrbp_user_id:该部门的 HRBP 负责人(人,非角色)。用于"绩效合格率"按
HRBP 负责的部门聚合(HRBP→部门 一对多映射)。在部门管理页配置。

幂等:列已存在则跳过。

Revision ID: dept_hrbp_20260614
Revises: approval_admin_to_ceo_20260613
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = 'dept_hrbp_20260614'
down_revision = 'approval_admin_to_ceo_20260613'
branch_labels = None
depends_on = None


def _has_col(conn, table, col):
    return col in [c['name'] for c in sa.inspect(conn).get_columns(table)]


def upgrade():
    conn = op.get_bind()
    if not _has_col(conn, 'departments', 'hrbp_user_id'):
        op.add_column('departments', sa.Column('hrbp_user_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_departments_hrbp_user', 'departments', 'users',
                              ['hrbp_user_id'], ['id'])


def downgrade():
    conn = op.get_bind()
    if _has_col(conn, 'departments', 'hrbp_user_id'):
        try:
            op.drop_constraint('fk_departments_hrbp_user', 'departments', type_='foreignkey')
        except Exception:
            pass
        op.drop_column('departments', 'hrbp_user_id')
