"""添加审批流程分支支持

Revision ID: add_approval_branch_support_v2
Revises: head
Create Date: 2025-08-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_approval_branch_support_v2'
down_revision = None  # 这将在实际使用时由Alembic自动设置
branch_labels = None
depends_on = None


def upgrade():
    """添加分支支持字段"""
    
    # 添加新的分支支持字段到approval_step表
    op.add_column('approval_step', sa.Column('branch_group_id', sa.String(50), nullable=True, comment='分支组ID，用于标识同一组并行分支'))
    op.add_column('approval_step', sa.Column('branch_level', sa.Integer(), default=0, comment='分支层级，0为主流程，1为一级分支，以此类推'))
    op.add_column('approval_step', sa.Column('branch_path', sa.String(100), nullable=True, comment='分支路径，如 true.false.true 表示分支选择路径'))
    op.add_column('approval_step', sa.Column('merge_step_id', sa.Integer(), nullable=True, comment='分支合并步骤ID'))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_approval_step_merge_step',
        'approval_step', 'approval_step',
        ['merge_step_id'], ['id']
    )
    
    # 为现有记录设置默认值
    op.execute("UPDATE approval_step SET branch_level = 0 WHERE branch_level IS NULL")


def downgrade():
    """移除分支支持字段"""
    
    # 删除外键约束
    op.drop_constraint('fk_approval_step_merge_step', 'approval_step', type_='foreignkey')
    
    # 删除添加的列
    op.drop_column('approval_step', 'merge_step_id')
    op.drop_column('approval_step', 'branch_path')
    op.drop_column('approval_step', 'branch_level')
    op.drop_column('approval_step', 'branch_group_id')