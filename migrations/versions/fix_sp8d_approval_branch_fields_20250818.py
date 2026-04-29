"""修复SP8D数据库approval_step表审批分支功能字段缺失

Revision ID: fix_sp8d_approval_branch_fields
Revises: b2d5b2180d45
Create Date: 2025-08-18 22:00:00.000000

这个迁移专门为SP8D数据库添加缺失的审批分支功能字段
根据CLAUDE.md规范创建，确保数据安全
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_sp8d_approval_branch_fields'
down_revision = 'b2d5b2180d45'
branch_labels = None
depends_on = None


def upgrade():
    """为SP8D数据库添加缺失的审批分支功能字段"""
    
    # 检查字段是否已存在，避免重复添加
    conn = op.get_bind()
    
    # 检查approval_step表是否存在各个分支功能字段
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'approval_step' 
        AND column_name IN ('is_parallel', 'branch_condition', 'merge_step_id', 
                           'branch_level', 'parent_step_id', 'step_type', 
                           'branch_group_id', 'branch_path')
    """))
    
    existing_columns = {row[0] for row in result.fetchall()}
    
    with op.batch_alter_table('approval_step', schema=None) as batch_op:
        
        # 1. is_parallel - 是否并行审批
        if 'is_parallel' not in existing_columns:
            batch_op.add_column(sa.Column('is_parallel', sa.Boolean(), 
                                         nullable=True, 
                                         server_default=sa.text('false'),
                                         comment='是否为并行分支'))
        
        # 2. branch_condition - 分支条件配置 (JSON)
        if 'branch_condition' not in existing_columns:
            batch_op.add_column(sa.Column('branch_condition', postgresql.JSON(astext_type=sa.Text()), 
                                         nullable=True,
                                         comment='分支条件配置'))
        
        # 3. merge_step_id - 合并步骤ID
        if 'merge_step_id' not in existing_columns:
            batch_op.add_column(sa.Column('merge_step_id', sa.Integer(), 
                                         nullable=True,
                                         comment='合并步骤ID'))
        
        # 4. branch_level - 分支层级
        if 'branch_level' not in existing_columns:
            batch_op.add_column(sa.Column('branch_level', sa.Integer(), 
                                         nullable=True, 
                                         server_default=sa.text('0'),
                                         comment='分支层级，0为主流程，1为一级分支，以此类推'))
        
        # 5. parent_step_id - 父步骤ID
        if 'parent_step_id' not in existing_columns:
            batch_op.add_column(sa.Column('parent_step_id', sa.Integer(), 
                                         nullable=True,
                                         comment='上级步骤ID，用于并行分支'))
        
        # 6. step_type - 步骤类型
        if 'step_type' not in existing_columns:
            batch_op.add_column(sa.Column('step_type', sa.String(length=20), 
                                         nullable=True, 
                                         server_default=sa.text("'normal'::character varying"),
                                         comment='步骤类型：normal(常规) 或 branch(分支)'))
        
        # 7. branch_group_id - 分支组ID  
        if 'branch_group_id' not in existing_columns:
            batch_op.add_column(sa.Column('branch_group_id', sa.String(length=50), 
                                         nullable=True,
                                         comment='分支组ID，用于标识同一组并行分支'))
        
        # 8. branch_path - 分支路径
        if 'branch_path' not in existing_columns:
            batch_op.add_column(sa.Column('branch_path', sa.String(length=100), 
                                         nullable=True,
                                         comment='分支路径，用于追踪审批分支'))

    op.execute("CREATE INDEX IF NOT EXISTS idx_approval_step_branch_level ON approval_step (branch_level)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_approval_step_parent_id ON approval_step (parent_step_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_approval_step_type ON approval_step (step_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_approval_step_branch_group ON approval_step (branch_group_id)")


def downgrade():
    """回滚审批分支功能字段（谨慎使用）"""
    
    # 先删除索引
    try:
        op.drop_index('idx_approval_step_branch_level', table_name='approval_step')
        op.drop_index('idx_approval_step_parent_id', table_name='approval_step')  
        op.drop_index('idx_approval_step_type', table_name='approval_step')
        op.drop_index('idx_approval_step_branch_group', table_name='approval_step')
    except Exception:
        # 索引可能不存在，忽略错误
        pass
    
    # 删除添加的字段
    with op.batch_alter_table('approval_step', schema=None) as batch_op:
        batch_op.drop_column('branch_path')
        batch_op.drop_column('branch_group_id')
        batch_op.drop_column('step_type')
        batch_op.drop_column('parent_step_id')
        batch_op.drop_column('branch_level')
        batch_op.drop_column('merge_step_id')
        batch_op.drop_column('branch_condition')
        batch_op.drop_column('is_parallel')