#!/usr/bin/env python3
import psycopg2
import json

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# 1. 查看business_admin对project的content_filters
print("=== 1. business_admin对project的内容过滤器 ===")
cursor.execute("""
    SELECT content_filters FROM role_permissions
    WHERE role = 'business_admin' AND module = 'project'
""")
result = cursor.fetchone()
if result and result[0]:
    filters = result[0]
    print(f"  content_filters: {json.dumps(filters, indent=4, ensure_ascii=False)}")
else:
    print("  无内容过滤器")

# 2. 查看项目277的详细信息
print("\n=== 2. 项目277的详细信息 ===")
cursor.execute("""
    SELECT id, project_name, owner_id, current_stage, project_type, report_source,
           is_active, is_locked
    FROM projects WHERE id = 277
""")
project = cursor.fetchone()
if project:
    print(f"  ID: {project[0]}")
    print(f"  名称: {project[1]}")
    print(f"  owner_id: {project[2]}")
    print(f"  current_stage: {project[3]}")
    print(f"  project_type: {project[4]}")
    print(f"  report_source: {project[5]}")
    print(f"  is_active: {project[6]}")
    print(f"  is_locked: {project[7]}")

# 3. 检查过滤条件是否匹配
print("\n=== 3. 内容过滤匹配检查 ===")
if result and result[0] and project:
    filters = result[0]

    # current_stage过滤
    if 'current_stage' in filters:
        allowed_stages = filters['current_stage']
        project_stage = project[3]
        if project_stage in allowed_stages:
            print(f"  ✓ current_stage '{project_stage}' 在允许列表中")
        else:
            print(f"  ✗ current_stage '{project_stage}' 不在允许列表 {allowed_stages} 中")

    # project_type过滤
    if 'project_type' in filters:
        allowed_types = filters['project_type']
        project_type = project[4]
        if project_type in allowed_types:
            print(f"  ✓ project_type '{project_type}' 在允许列表中")
        else:
            print(f"  ✗ project_type '{project_type}' 不在允许列表 {allowed_types} 中")

    # report_source过滤
    if 'report_source' in filters:
        allowed_sources = filters['report_source']
        report_source = project[5]
        if report_source in allowed_sources:
            print(f"  ✓ report_source '{report_source}' 在允许列表中")
        else:
            print(f"  ✗ report_source '{report_source}' 不在允许列表 {allowed_sources} 中")

cursor.close()
conn.close()
