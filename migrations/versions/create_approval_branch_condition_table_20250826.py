"""创建approval_branch_condition分支条件表

Revision ID: create_approval_branch_condition_table
Revises: unify_performance_targets_constraints
Create Date: 2025-08-26 00:20:00.000000

修复approval_branch_condition表缺少Alembic迁移文件的问题
将之前通过SQL脚本直接创建的表纳入标准迁移管理
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'create_approval_branch_condition_table'
down_revision = 'unify_performance_targets_constraints'
branch_labels = None
depends_on = None


def upgrade():
    """创建approval_branch_condition表"""
    
    # 获取数据库连接以检查表是否已存在
    conn = op.get_bind()
    
    # 检查表是否已存在
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'approval_branch_condition'
        )
    """))
    
    table_exists = result.fetchone()[0]
    
    if table_exists:
        op.get_context().opts['as_sql'] = True
        print("⚠️  approval_branch_condition表已存在，跳过创建")
        return
    
    print("📝 创建approval_branch_condition表...")
    
    # 创建表
    op.create_table('approval_branch_condition',
        # 主键和关联
        sa.Column('id', sa.String(50), primary_key=True, 
                 comment='条件唯一标识符'),
        sa.Column('step_id', sa.Integer(), nullable=False, 
                 comment='关联的审批步骤ID'),
        sa.Column('condition_order', sa.Integer(), server_default='0', 
                 comment='条件在步骤中的排序位置'),
        
        # 条件配置
        sa.Column('operator', sa.String(50), nullable=False, 
                 comment='条件操作符（等于、包含等）'),
        sa.Column('field_value', sa.String(255), nullable=False, 
                 comment='条件匹配的字段值'),
        
        # 审批人配置
        sa.Column('approver_id', sa.Integer(), nullable=True, 
                 comment='满足条件时的审批人用户ID'),
        sa.Column('approver_type', sa.String(50), server_default='user', 
                 comment='审批人类型（用户/上级/下一分支）'),
        sa.Column('action', sa.String(100), nullable=True, 
                 comment='满足条件时执行的业务动作'),
        
        # 审计字段
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), 
                 comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), 
                 comment='更新时间'),
        
        # 外键约束
        sa.ForeignKeyConstraint(['step_id'], ['approval_step.id'], 
                               name='fk_branch_condition_step', 
                               ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], 
                               name='fk_branch_condition_approver', 
                               ondelete='SET NULL'),
        
        # 检查约束
        sa.CheckConstraint(
            sa.text("operator IN ('equals', 'not_equals', 'contains', 'not_contains', 'greater_than', 'less_than', 'in', 'not_in', 'starts_with', 'ends_with', 'is_null', 'is_not_null')"),
            name='chk_operator_valid'
        ),
        sa.CheckConstraint(
            sa.text("approver_type IN ('user', 'next_level', 'next_branch')"),
            name='chk_approver_type_valid'
        ),
        sa.CheckConstraint(
            sa.text('condition_order >= 0'),
            name='chk_condition_order_positive'
        ),
        
        # 唯一性约束
        sa.UniqueConstraint('step_id', 'operator', 'field_value', 
                           name='uk_step_operator_value'),
        
        comment='审批分支条件表 - 存储审批步骤的分支决策条件'
    )
    
    # 创建索引
    op.create_index('idx_branch_condition_step_id', 'approval_branch_condition', ['step_id'])
    op.create_index('idx_branch_condition_order', 'approval_branch_condition', ['step_id', 'condition_order'])
    op.create_index('idx_branch_condition_approver', 'approval_branch_condition', ['approver_id'])
    op.create_index('idx_branch_condition_value', 'approval_branch_condition', ['field_value', 'operator'])
    
    # 创建触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION update_branch_condition_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # 创建触发器
    op.execute("""
        CREATE TRIGGER trigger_branch_condition_updated_at
            BEFORE UPDATE ON approval_branch_condition
            FOR EACH ROW
            EXECUTE FUNCTION update_branch_condition_updated_at();
    """)
    
    print("✅ approval_branch_condition表创建完成")


def downgrade():
    """删除approval_branch_condition表"""
    
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS trigger_branch_condition_updated_at ON approval_branch_condition")
    
    # 删除触发器函数
    op.execute("DROP FUNCTION IF EXISTS update_branch_condition_updated_at()")
    
    # 删除表（会自动删除索引和约束）
    op.drop_table('approval_branch_condition')
    
    print("🗑️  approval_branch_condition表已删除")