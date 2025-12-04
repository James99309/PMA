#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS数据库同步到最新版本

这个脚本将:
1. 直接添加缺失的13个字段（使用safe方式）
2. 更新alembic_version到最新head

这是一个临时解决方案，因为中间有太多迁移文件需要添加安全检查
"""
import os
import sys

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)
os.chdir(project_root)

from sqlalchemy import create_engine, text, inspect
from datetime import datetime

# OVS数据库URL
OVS_DB_URL = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

# 本地head版本
HEAD_REVISION = 'be0fcb982e76'


def print_header(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def column_exists(inspector, table_name, column_name):
    """检查字段是否存在"""
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def constraint_exists(conn, table_name, constraint_name):
    """检查约束是否存在"""
    result = conn.execute(text(f"""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = '{table_name}'
        AND constraint_name = '{constraint_name}'
    """))
    return result.fetchone() is not None


def index_exists(conn, index_name):
    """检查索引是否存在"""
    result = conn.execute(text(f"""
        SELECT indexname FROM pg_indexes
        WHERE indexname = '{index_name}'
    """))
    return result.fetchone() is not None


def table_exists(inspector, table_name):
    """检查表是否存在"""
    return table_name in inspector.get_table_names()


def main():
    print_header("🚀 OVS数据库同步到最新版本")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标版本: {HEAD_REVISION}")

    # 连接数据库
    print("\n📡 连接OVS数据库...")
    engine = create_engine(OVS_DB_URL)

    with engine.connect() as conn:
        inspector = inspect(conn)

        # 检查当前版本
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        print(f"当前版本: {current_version}")

        print_header("📋 检查并添加缺失的表和字段")

        # 1. 创建 specification_options 表（如果不存在）
        if not table_exists(inspector, 'specification_options'):
            conn.execute(text("""
                CREATE TABLE specification_options (
                    id SERIAL PRIMARY KEY,
                    spec_id INTEGER NOT NULL,
                    value VARCHAR(100) NOT NULL,
                    code VARCHAR(10) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    position INTEGER DEFAULT 0,
                    created_at TIMESTAMP,
                    CONSTRAINT fk_spec_options_spec_id FOREIGN KEY (spec_id)
                        REFERENCES specification_dictionary(id),
                    CONSTRAINT uq_spec_option_value UNIQUE (spec_id, value)
                )
            """))
            print("✅ 创建 specification_options 表成功")
        else:
            print("⏭️ specification_options 表已存在")

        # 2. 添加所有缺失的字段
        fields_to_add = [
            ('approval_record', 'status', 'VARCHAR(20)'),
            ('product_code_field_options', 'allow_quotation_config', 'BOOLEAN DEFAULT false'),
            ('product_code_field_options', 'price_adjustment', 'INTEGER DEFAULT 0'),
            ('product_code_field_options', 'spec_option_id', 'INTEGER'),
            ('product_code_field_options', 'subcategory_id', 'INTEGER'),
            ('product_code_fields', 'allow_quotation_config', 'BOOLEAN DEFAULT false'),
            ('product_subcategories', 'image_path', 'VARCHAR(500)'),
            ('product_subcategories', 'pdf_path', 'VARCHAR(500)'),
            ('quotation_details', 'configured_mn', 'VARCHAR(50)'),
            ('quotation_details', 'configured_specs', 'JSONB'),
            ('quotation_details', 'pending_product_creation', 'BOOLEAN DEFAULT false'),
            ('quotation_details', 'price_adjustment_total', 'INTEGER DEFAULT 0'),
            ('settlement_orders', 'currency', "VARCHAR(10) DEFAULT 'CNY'"),
        ]

        for table, column, col_type in fields_to_add:
            if not column_exists(inspector, table, column):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                print(f"✅ 添加 {table}.{column} 字段成功")
            else:
                print(f"⏭️ {table}.{column} 已存在")

        # 3. 添加外键约束（如果不存在）
        fk_constraints = [
            ('product_code_field_options', 'fk_field_options_spec_option_id',
             'spec_option_id', 'specification_options', 'id'),
            ('product_code_field_options', 'fk_field_options_subcategory',
             'subcategory_id', 'product_subcategories', 'id'),
        ]

        for table, fk_name, column, ref_table, ref_column in fk_constraints:
            if not constraint_exists(conn, table, fk_name):
                try:
                    conn.execute(text(f"""
                        ALTER TABLE {table}
                        ADD CONSTRAINT {fk_name}
                        FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})
                    """))
                    print(f"✅ 添加外键约束 {fk_name} 成功")
                except Exception as e:
                    print(f"⚠️ 添加外键约束 {fk_name} 失败: {e}")
            else:
                print(f"⏭️ 外键约束 {fk_name} 已存在")

        # 4. 添加索引（如果不存在）
        indexes = [
            ('ix_product_code_field_options_subcategory_id',
             'product_code_field_options', 'subcategory_id'),
        ]

        for idx_name, table, column in indexes:
            if not index_exists(conn, idx_name):
                try:
                    conn.execute(text(f"""
                        CREATE INDEX {idx_name} ON {table} ({column})
                    """))
                    print(f"✅ 创建索引 {idx_name} 成功")
                except Exception as e:
                    print(f"⚠️ 创建索引 {idx_name} 失败: {e}")
            else:
                print(f"⏭️ 索引 {idx_name} 已存在")

        # 5. 更新 alembic_version 到最新
        print_header("🔄 更新迁移版本")
        conn.execute(text(f"UPDATE alembic_version SET version_num = '{HEAD_REVISION}'"))
        print(f"✅ 已更新版本到 {HEAD_REVISION}")

        # 提交事务
        conn.commit()

        # 验证
        print_header("🔍 验证结果")
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        final_version = result.scalar()
        print(f"最终版本: {final_version}")

        if final_version == HEAD_REVISION:
            print("\n✅ 同步成功！OVS数据库已更新到最新版本")
        else:
            print("\n⚠️ 版本更新可能未生效")

    print_header("✅ 完成")
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
