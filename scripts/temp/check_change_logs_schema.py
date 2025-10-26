#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 change_logs 表结构"""
import sys, os

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

from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, '.env.sp8d.backup')
load_dotenv(dotenv_path, override=True)

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 80)
    print("查看 change_logs 表结构")
    print("=" * 80)

    result = db.session.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'change_logs'
        ORDER BY ordinal_position
    """))

    print("\n字段列表:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    print("\n查看表中的数据示例:")
    sample = db.session.execute(text("""
        SELECT * FROM change_logs
        WHERE table_name = 'quotations'
        LIMIT 1
    """))

    columns = sample.keys()
    print(f"\n实际字段: {list(columns)}")

    for row in sample:
        print("\n示例数据:")
        for i, col in enumerate(columns):
            print(f"  {col}: {row[i]}")
