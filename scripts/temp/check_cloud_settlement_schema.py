#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端数据库 settlement_orders 表结构和迁移状态"""
import sys
import os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from sqlalchemy import text
import os

# 加载云端配置 - 使用 .env 文件（云端配置）
cloud_env = {}
env_file = os.path.join(get_project_root(), '.env')
print(f"读取配置文件: {env_file}")
with open(env_file, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                key, value = line.split('=', 1)
                # 只保留数据库相关的环境变量
                if key.startswith('DATABASE') or key.startswith('POSTGRES'):
                    os.environ[key] = value

app = create_app()
with app.app_context():
    print("=" * 80)
    print("检查云端数据库状态")
    print("=" * 80)

    # 1. 检查迁移版本表
    print("\n1. 最近的迁移版本:")
    try:
        result = db.session.execute(text('SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 10'))
        versions = result.fetchall()
        for v in versions:
            print(f'  - {v[0]}')
    except Exception as e:
        print(f"  错误: {e}")

    # 2. 检查 settlement_orders 表的字段约束
    print("\n2. settlement_orders 表的关键字段:")
    try:
        result = db.session.execute(text("""
            SELECT
                column_name,
                is_nullable,
                data_type
            FROM information_schema.columns
            WHERE table_name = 'settlement_orders'
            AND column_name IN ('distributor_id', 'dealer_id', 'is_direct_contract', 'is_factory_pickup')
            ORDER BY column_name
        """))
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f'  {row[0]}: nullable={row[1]}, type={row[2]}')
        else:
            print("  未找到相关字段")
    except Exception as e:
        print(f"  错误: {e}")

    # 3. 检查是否存在 add_settlement_business_type_20251014 迁移
    print("\n3. 检查特定迁移版本:")
    try:
        # 检查所有迁移版本
        result = db.session.execute(text("SELECT version_num FROM alembic_version"))
        all_versions = [v[0] for v in result.fetchall()]

        target_migration = 'add_settlement_business_type_20251014'
        if target_migration in all_versions:
            print(f"  ✓ 迁移 {target_migration} 已运行")
        else:
            print(f"  ✗ 迁移 {target_migration} 未运行")
            print(f"\n  当前数据库中的所有迁移版本:")
            for v in all_versions:
                print(f"    - {v}")
    except Exception as e:
        print(f"  错误: {e}")

    print("\n" + "=" * 80)
