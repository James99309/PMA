"""Add attributed_to_id field to expenses table

Revision ID: add_expense_attributed_to_id_20260117
Revises: merge_all_heads_20260111
Create Date: 2026-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_expense_attributed_to_id_20260117'
down_revision = 'baseline_sync_20260112'
branch_labels = None
depends_on = None


def upgrade():
    """添加费用归属人字段（用于技术支持费用统计）"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)

    # 检查字段是否已存在
    existing_columns = [col['name'] for col in inspector.get_columns('expenses')]

    if 'attributed_to_id' not in existing_columns:
        op.add_column('expenses',
            sa.Column('attributed_to_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True,
                      comment='费用归属人ID（用于技术支持费用统计）'))
        print("✅ 添加 attributed_to_id 字段成功")
    else:
        print("⏭️ attributed_to_id 字段已存在，跳过")


def downgrade():
    """删除费用归属人字段"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)

    # 检查字段是否存在
    existing_columns = [col['name'] for col in inspector.get_columns('expenses')]

    if 'attributed_to_id' in existing_columns:
        op.drop_column('expenses', 'attributed_to_id')
        print("✅ 删除 attributed_to_id 字段成功")
    else:
        print("⏭️ attributed_to_id 字段不存在，跳过")
