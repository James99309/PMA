#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证规格字典功能"""
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

project_root = get_project_root()
sys.path.insert(0, project_root)

from config import Config
from sqlalchemy import create_engine, text

# 创建数据库引擎
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

print("📊 规格字典表验证报告")
print("=" * 60)

with engine.connect() as conn:
    # 查询所有记录
    result = conn.execute(text("""
        SELECT id, name, unit, is_active, created_at
        FROM specification_dictionary
        ORDER BY id
    """))

    rows = result.fetchall()

    print(f"\n总记录数: {len(rows)}")
    print("\n所有规格记录：")
    print(f"{'ID':<5} {'规格名称':<15} {'单位':<10} {'状态':<8} {'创建时间'}")
    print("-" * 60)

    for row in rows:
        status = "启用" if row[3] else "停用"
        unit = row[2] if row[2] else "-"
        created = row[4].strftime('%Y-%m-%d %H:%M') if row[4] else "-"
        print(f"{row[0]:<5} {row[1]:<15} {unit:<10} {status:<8} {created}")

    # 验证索引
    print("\n" + "=" * 60)
    print("📋 索引验证：")

    result = conn.execute(text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'specification_dictionary'
    """))

    indexes = result.fetchall()
    for idx in indexes:
        print(f"  ✅ {idx[0]}")

    # 测试唯一约束
    print("\n" + "=" * 60)
    print("🔍 约束验证：")

    result = conn.execute(text("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'specification_dictionary'
    """))

    constraints = result.fetchall()
    for const in constraints:
        const_type_map = {
            'PRIMARY KEY': '主键',
            'UNIQUE': '唯一约束',
            'FOREIGN KEY': '外键',
            'CHECK': '检查约束'
        }
        const_type = const_type_map.get(const[1], const[1])
        print(f"  ✅ {const[0]}: {const_type}")

    print("\n" + "=" * 60)
    print("✅ 规格字典表验证完成！")
