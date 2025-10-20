#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端projects表结构"""
import sys
import os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from sqlalchemy import create_engine, text, inspect

# 云端数据库配置
CLOUD_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': '6543',
    'database': 'postgres',
    'user': 'postgres.iqcyimnjtnmomvfuwjzw',
    'password': 'towsys-coGdoq-6gofdi'
}

db_url = f"postgresql://{CLOUD_DB_CONFIG['user']}:{CLOUD_DB_CONFIG['password']}@" \
         f"{CLOUD_DB_CONFIG['host']}:{CLOUD_DB_CONFIG['port']}/{CLOUD_DB_CONFIG['database']}"
engine = create_engine(db_url)

inspector = inspect(engine)

print("云端 projects 表的字段:")
print("=" * 60)
for col in inspector.get_columns('projects'):
    print(f"{col['name']:30} {str(col['type']):20} nullable={col['nullable']}")

print("\n云端 quotations 表的字段:")
print("=" * 60)
for col in inspector.get_columns('quotations'):
    print(f"{col['name']:30} {str(col['type']):20} nullable={col['nullable']}")
