"""添加审批步骤分支功能支持

Revision ID: add_approval_branch_support
Revises: 26d24eb66d82
Create Date: 2025-08-17 09:59:30.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_approval_branch_support'
down_revision = '26d24eb66d82'
branch_labels = None
depends_on = None


def upgrade():
    """添加审批步骤分支功能字段"""
    
    # 添加新字段到 approval_step 表
    op.add_column('approval_step', sa.Column('step_type', sa.String(length=20), nullable=False, server_default='normal', comment='步骤类型：normal(常规) 或 branch(分支)'))
    op.add_column('approval_step', sa.Column('branch_condition', sa.JSON(), nullable=True, comment='分支条件配置'))
    op.add_column('approval_step', sa.Column('parent_step_id', sa.Integer(), nullable=True, comment='上级步骤ID，用于并行分支'))
    op.add_column('approval_step', sa.Column('is_parallel', sa.Boolean(), nullable=False, server_default='false', comment='是否为并行分支'))
    
    # 创建外键约束
    op.create_foreign_key(
        'fk_approval_step_parent_step',
        'approval_step', 'approval_step',
        ['parent_step_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 更新现有记录的默认值
    op.execute("UPDATE approval_step SET step_type = 'normal' WHERE step_type IS NULL")
    op.execute("UPDATE approval_step SET is_parallel = false WHERE is_parallel IS NULL")


def downgrade():
    """移除审批步骤分支功能字段"""
    
    # 删除外键约束
    op.drop_constraint('fk_approval_step_parent_step', 'approval_step', type_='foreignkey')
    
    # 删除新增字段
    op.drop_column('approval_step', 'is_parallel')
    op.drop_column('approval_step', 'parent_step_id')
    op.drop_column('approval_step', 'branch_condition')
    op.drop_column('approval_step', 'step_type')