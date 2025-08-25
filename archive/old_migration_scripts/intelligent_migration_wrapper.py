#!/usr/bin/env python3
"""
智能迁移包装器
自动检查数据库状态，只执行必要的迁移操作
"""

def safe_add_column(batch_op, table_name, column_name, column_type, **kwargs):
    """安全添加列：只在列不存在时添加"""
    if not column_exists(table_name, column_name):
        batch_op.add_column(sa.Column(column_name, column_type, **kwargs))
        print(f"✅ 添加列: {table_name}.{column_name}")
    else:
        print(f"⏭️ 跳过: {table_name}.{column_name} 已存在")

def safe_drop_column(batch_op, table_name, column_name):
    """安全删除列：只在列存在时删除"""
    if column_exists(table_name, column_name):
        batch_op.drop_column(column_name)
        print(f"✅ 删除列: {table_name}.{column_name}")
    else:
        print(f"⏭️ 跳过: {table_name}.{column_name} 不存在")

def safe_add_constraint(batch_op, table_name, constraint_name, constraint_type, **kwargs):
    """安全添加约束：只在约束不存在时添加"""
    if not constraint_exists(table_name, constraint_name):
        if constraint_type == 'foreignkey':
            batch_op.create_foreign_key(constraint_name, **kwargs)
        elif constraint_type == 'unique':
            batch_op.create_unique_constraint(constraint_name, **kwargs)
        print(f"✅ 添加约束: {table_name}.{constraint_name}")
    else:
        print(f"⏭️ 跳过: {table_name}.{constraint_name} 已存在")

def safe_drop_constraint(batch_op, table_name, constraint_name, constraint_type):
    """安全删除约束：只在约束存在时删除"""
    if constraint_exists(table_name, constraint_name):
        batch_op.drop_constraint(constraint_name, type_=constraint_type)
        print(f"✅ 删除约束: {table_name}.{constraint_name}")
    else:
        print(f"⏭️ 跳过: {table_name}.{constraint_name} 不存在")

def safe_create_table(table_name, *columns, **kwargs):
    """安全创建表：只在表不存在时创建"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
        print(f"✅ 创建表: {table_name}")
    else:
        print(f"⏭️ 跳过: 表 {table_name} 已存在")

def safe_drop_table(table_name):
    """安全删除表：只在表存在时删除"""
    if table_exists(table_name):
        op.drop_table(table_name)
        print(f"✅ 删除表: {table_name}")
    else:
        print(f"⏭️ 跳过: 表 {table_name} 不存在")

def safe_create_index(index_name, table_name, columns, **kwargs):
    """安全创建索引：只在索引不存在时创建"""
    if not index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns, **kwargs)
        print(f"✅ 创建索引: {index_name}")
    else:
        print(f"⏭️ 跳过: 索引 {index_name} 已存在")

# 检查函数
def table_exists(table_name):
    """检查表是否存在"""
    connection = op.get_bind()
    try:
        result = connection.execute(sa.text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = :table_name AND table_schema = 'public'
        """), {"table_name": table_name})
        return result.fetchone()[0] > 0
    except Exception:
        return False

def column_exists(table_name, column_name):
    """检查列是否存在"""
    connection = op.get_bind()
    try:
        result = connection.execute(sa.text("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = :table_name AND column_name = :column_name
        """), {"table_name": table_name, "column_name": column_name})
        return result.fetchone()[0] > 0
    except Exception:
        return False

def constraint_exists(table_name, constraint_name):
    """检查约束是否存在"""
    connection = op.get_bind()
    try:
        result = connection.execute(sa.text("""
            SELECT COUNT(*) FROM information_schema.table_constraints 
            WHERE table_name = :table_name AND constraint_name = :constraint_name
        """), {"table_name": table_name, "constraint_name": constraint_name})
        return result.fetchone()[0] > 0
    except Exception:
        return False

def index_exists(table_name, index_name):
    """检查索引是否存在"""
    connection = op.get_bind()
    try:
        result = connection.execute(sa.text("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE tablename = :table_name AND indexname = :index_name
        """), {"table_name": table_name, "index_name": index_name})
        return result.fetchone()[0] > 0
    except Exception:
        return False

# 使用示例：
"""
# 在迁移文件中使用：
from intelligent_migration_wrapper import *

def upgrade():
    # 安全添加列
    with op.batch_alter_table('projects', schema=None) as batch_op:
        safe_add_column(batch_op, 'projects', 'vendor_sales_manager_id', sa.Integer(), nullable=True)
    
    # 安全创建表
    safe_create_table('temp_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 安全创建索引
    safe_create_index('idx_projects_vendor_manager', 'projects', ['vendor_sales_manager_id'])
"""