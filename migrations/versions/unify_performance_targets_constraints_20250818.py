"""统一performance_targets表的约束和默认值

Revision ID: unify_performance_targets_constraints
Revises: unify_performance_amount_types
Create Date: 2025-08-18 22:10:00.000000

根据CLAUDE.md规范统一performance_targets表的约束和默认值
确保SP8D与本地数据库完全一致，避免数据插入失败
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'unify_performance_targets_constraints'
down_revision = 'unify_performance_amount_types'
branch_labels = None
depends_on = None


def upgrade():
    """统一performance_targets表的约束和默认值"""
    
    # 获取数据库连接以检查当前约束状态
    conn = op.get_bind()
    
    # 检查created_by字段的约束状态
    result = conn.execute(sa.text("""
        SELECT column_name, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'performance_targets' 
        AND column_name IN ('created_by', 'customers_rate', 'implant_rate', 
                           'projects_rate', 'sales_rate')
    """))
    
    column_info = {row[0]: {'nullable': row[1] == 'YES', 'default': row[2]} 
                   for row in result.fetchall()}
    
    with op.batch_alter_table('performance_targets', schema=None) as batch_op:
        
        # 1. 修改created_by字段为NOT NULL（如果当前是nullable）
        if column_info.get('created_by', {}).get('nullable', True):
            # 首先为现有NULL值设置默认值（如果有的话）
            conn.execute(sa.text("""
                UPDATE performance_targets 
                SET created_by = 1 
                WHERE created_by IS NULL
            """))
            
            batch_op.alter_column('created_by',
                   existing_type=sa.INTEGER(),
                   nullable=False,
                   comment='创建人ID',
                   existing_nullable=True)
        
        # 2. 设置各个rate字段的默认值为0（如果当前没有默认值）
        rate_fields = ['customers_rate', 'implant_rate', 'projects_rate', 'sales_rate']
        
        for field in rate_fields:
            current_default = column_info.get(field, {}).get('default')
            if current_default is None or current_default == 'NULL':
                # 首先为现有NULL值设置默认值
                conn.execute(sa.text(f"""
                    UPDATE performance_targets 
                    SET {field} = 0 
                    WHERE {field} IS NULL
                """))
                
                batch_op.alter_column(field,
                       existing_type=sa.Numeric(precision=5, scale=2),
                       server_default=sa.text('0'),
                       comment=f'{field.replace("_", "").replace("rate", "")}完成率',
                       existing_nullable=True)


def downgrade():
    """回滚约束和默认值修改（谨慎使用）"""
    
    with op.batch_alter_table('performance_targets', schema=None) as batch_op:
        
        # 移除rate字段的默认值
        rate_fields = ['customers_rate', 'implant_rate', 'projects_rate', 'sales_rate']
        
        for field in rate_fields:
            batch_op.alter_column(field,
                   existing_type=sa.Numeric(precision=5, scale=2),
                   server_default=None,
                   existing_nullable=True)
        
        # 将created_by字段改为可空
        batch_op.alter_column('created_by',
               existing_type=sa.INTEGER(),
               nullable=True,
               existing_nullable=False)