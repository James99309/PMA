"""添加projects表的created_by字段

Revision ID: add_project_created_by_field
Revises: unify_performance_targets_constraints
Create Date: 2025-10-01 11:26:28.000000

添加不可变的创建人字段，永久记录项目发起人
- 字段名: created_by (与系统13个模型保持命名一致)
- 语义: 项目发起人/报备人（不可变）
- 与owner_id区分: owner_id表示当前负责人（可变更）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_project_created_by_field'
down_revision = 'd43fb253b20c'
branch_labels = None
depends_on = None


def upgrade():
    """添加created_by字段并填充历史数据"""

    # 获取数据库连接
    conn = op.get_bind()

    # 1. 添加字段（初始允许NULL）
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('created_by', sa.Integer(),
                     sa.ForeignKey('users.id'), nullable=True,
                     comment='项目发起人/报备人（不可变）')
        )

    # 2. 使用现有owner_id填充历史数据
    # 原因：目前没有任何项目修改过owner_id（ChangeLog记录为0）
    # 因此owner_id就是原始发起人，可以安全地用于填充
    conn.execute(sa.text("""
        UPDATE projects
        SET created_by = owner_id
        WHERE created_by IS NULL
    """))

    # 3. 设置为NOT NULL（确保未来数据完整性）
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column('created_by',
                            existing_type=sa.Integer(),
                            nullable=False)


def downgrade():
    """移除created_by字段"""
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('created_by')
