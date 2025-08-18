"""统一绩效模块金额字段数据类型从double precision到numeric(15,2)

Revision ID: unify_performance_amount_types  
Revises: fix_sp8d_approval_branch_fields
Create Date: 2025-08-18 22:05:00.000000

根据CLAUDE.md数据库规范，统一金额字段使用numeric(15,2)类型确保精度
修复SP8D与本地数据库结构差异，避免精度丢失问题
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'unify_performance_amount_types'
down_revision = 'fix_sp8d_approval_branch_fields'
branch_labels = None
depends_on = None


def upgrade():
    """将绩效模块金额字段从double precision统一为numeric(15,2)"""
    
    # 获取数据库连接以检查当前数据类型
    conn = op.get_bind()
    
    # 检查performance_statistics表的金额字段类型
    result = conn.execute(sa.text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'performance_statistics' 
        AND column_name IN ('implant_amount_actual', 'sales_amount_actual')
    """))
    
    perf_stats_columns = {row[0]: row[1] for row in result.fetchall()}
    
    # 检查performance_targets表的金额字段类型
    result = conn.execute(sa.text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'performance_targets' 
        AND column_name IN ('implant_amount_target', 'sales_amount_target')
    """))
    
    perf_targets_columns = {row[0]: row[1] for row in result.fetchall()}
    
    # 修改performance_statistics表的金额字段类型
    with op.batch_alter_table('performance_statistics', schema=None) as batch_op:
        
        # 只有当前是double precision类型时才进行转换
        if perf_stats_columns.get('implant_amount_actual') == 'double precision':
            batch_op.alter_column('implant_amount_actual',
                   existing_type=sa.DOUBLE_PRECISION(precision=53),
                   type_=sa.Numeric(precision=15, scale=2),
                   comment='植入额实际完成（万元）',
                   existing_nullable=True)
        
        if perf_stats_columns.get('sales_amount_actual') == 'double precision':  
            batch_op.alter_column('sales_amount_actual',
                   existing_type=sa.DOUBLE_PRECISION(precision=53),
                   type_=sa.Numeric(precision=15, scale=2),
                   comment='销售额实际完成（万元）',
                   existing_nullable=True)
    
    # 修改performance_targets表的金额字段类型
    with op.batch_alter_table('performance_targets', schema=None) as batch_op:
        
        # 只有当前是double precision类型时才进行转换
        if perf_targets_columns.get('implant_amount_target') == 'double precision':
            batch_op.alter_column('implant_amount_target',
                   existing_type=sa.DOUBLE_PRECISION(precision=53),
                   type_=sa.Numeric(precision=15, scale=2),
                   comment='植入额目标（万元）',
                   existing_nullable=True)
        
        if perf_targets_columns.get('sales_amount_target') == 'double precision':
            batch_op.alter_column('sales_amount_target',
                   existing_type=sa.DOUBLE_PRECISION(precision=53),
                   type_=sa.Numeric(precision=15, scale=2),
                   comment='销售额目标（万元）',
                   existing_nullable=True)


def downgrade():
    """回滚金额字段类型到double precision（不推荐，可能导致精度问题）"""
    
    # 回滚performance_statistics表
    with op.batch_alter_table('performance_statistics', schema=None) as batch_op:
        batch_op.alter_column('sales_amount_actual',
               existing_type=sa.Numeric(precision=15, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
        
        batch_op.alter_column('implant_amount_actual',
               existing_type=sa.Numeric(precision=15, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    
    # 回滚performance_targets表  
    with op.batch_alter_table('performance_targets', schema=None) as batch_op:
        batch_op.alter_column('sales_amount_target',
               existing_type=sa.Numeric(precision=15, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
        
        batch_op.alter_column('implant_amount_target',
               existing_type=sa.Numeric(precision=15, scale=2),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)