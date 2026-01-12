#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复SP8D云端数据库缺失的linked_company_id等字段

由于多分支迁移合并问题，6eef2ad2bfd0迁移可能未被执行。
此脚本直接连接云端数据库添加缺失字段。
"""
import sys
import os
from datetime import datetime

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

from sqlalchemy import create_engine, text, inspect

# SP8D云端数据库连接 (从simple_sp8d_migration.py获取)
SP8D_DATABASE_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("=" * 60)
    print("🔧 SP8D云端数据库字段修复脚本")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 创建数据库引擎
    print("\n📡 连接SP8D云端数据库...")
    engine = create_engine(SP8D_DATABASE_URL)

    with engine.connect() as conn:
        inspector = inspect(engine)

        # 获取现有列信息
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        companies_columns = [col['name'] for col in inspector.get_columns('companies')]
        products_columns = [col['name'] for col in inspector.get_columns('products')]

        print(f"\n📋 当前状态:")
        print(f"   users.linked_company_id: {'✅ 已存在' if 'linked_company_id' in users_columns else '❌ 不存在'}")
        print(f"   companies.supplier_code: {'✅ 已存在' if 'supplier_code' in companies_columns else '❌ 不存在'}")
        print(f"   products.serial_code: {'✅ 已存在' if 'serial_code' in products_columns else '❌ 不存在'}")

        # 检查是否需要修复
        needs_fix = (
            'linked_company_id' not in users_columns or
            'supplier_code' not in companies_columns or
            'serial_code' not in products_columns
        )

        if not needs_fix:
            print("\n✅ 所有字段已存在，无需修复！")
            return True

        # 确认执行
        print("\n⚠️  需要添加缺失的字段")
        if '--yes' not in sys.argv and '-y' not in sys.argv:
            confirm = input("确认执行修复？(y/N): ")
            if confirm.lower() != 'y':
                print("❌ 已取消")
                return False
        else:
            print("   (自动确认模式)")


        # 开始事务
        trans = conn.begin()

        try:
            # 1. 添加 users.linked_company_id 字段
            if 'linked_company_id' not in users_columns:
                print("\n🔄 添加 users.linked_company_id 字段...")
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN linked_company_id INTEGER REFERENCES companies(id)
                """))
                print("   ✅ 添加成功")

            # 2. 添加 companies.supplier_code 字段
            if 'supplier_code' not in companies_columns:
                print("\n🔄 添加 companies.supplier_code 字段...")
                conn.execute(text("""
                    ALTER TABLE companies
                    ADD COLUMN supplier_code VARCHAR(10)
                """))
                # 添加唯一约束
                conn.execute(text("""
                    ALTER TABLE companies
                    ADD CONSTRAINT uq_companies_supplier_code UNIQUE (supplier_code)
                """))
                print("   ✅ 添加成功")

            # 3. 添加 products.serial_code 字段
            if 'serial_code' not in products_columns:
                print("\n🔄 添加 products.serial_code 字段...")
                conn.execute(text("""
                    ALTER TABLE products
                    ADD COLUMN serial_code VARCHAR(10)
                """))
                # 添加唯一约束
                conn.execute(text("""
                    ALTER TABLE products
                    ADD CONSTRAINT uq_products_serial_code UNIQUE (serial_code)
                """))
                print("   ✅ 添加成功")

            # 更新 alembic_version
            print("\n🔄 更新迁移版本记录...")
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
            print(f"   当前版本: {current_version}")

            # 更新到新版本
            new_version = 'fix_missing_linked_company_id_20260112'
            conn.execute(text("""
                UPDATE alembic_version SET version_num = :version
            """), {"version": new_version})
            print(f"   新版本: {new_version}")

            # 提交事务
            trans.commit()

            print("\n" + "=" * 60)
            print("🎉 修复完成！")
            print("=" * 60)

            # 验证结果
            inspector2 = inspect(engine)
            users_columns2 = [col['name'] for col in inspector2.get_columns('users')]
            companies_columns2 = [col['name'] for col in inspector2.get_columns('companies')]
            products_columns2 = [col['name'] for col in inspector2.get_columns('products')]

            print(f"\n📋 修复后状态:")
            print(f"   users.linked_company_id: {'✅ 已存在' if 'linked_company_id' in users_columns2 else '❌ 不存在'}")
            print(f"   companies.supplier_code: {'✅ 已存在' if 'supplier_code' in companies_columns2 else '❌ 不存在'}")
            print(f"   products.serial_code: {'✅ 已存在' if 'serial_code' in products_columns2 else '❌ 不存在'}")

            return True

        except Exception as e:
            trans.rollback()
            print(f"\n❌ 修复失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
