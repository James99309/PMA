#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查项目48的所有者信息"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    # 查找李华伟的用户ID
    print("=== 用户信息 ===")
    cursor.execute("""
        SELECT id, username, real_name FROM users
        WHERE real_name LIKE '%李华伟%' OR username LIKE '%lihuawei%'
    """)
    users = cursor.fetchall()
    for u in users:
        print(f"用户ID: {u[0]}, 用户名: {u[1]}, 真实姓名: {u[2]}")

    # 当前项目48的信息
    print("\n=== 当前项目48信息 ===")
    cursor.execute("""
        SELECT p.id, p.project_name, p.owner_id, p.created_by,
               u1.real_name as owner_name,
               u2.real_name as creator_name,
               p.created_at, p.updated_at
        FROM projects p
        LEFT JOIN users u1 ON p.owner_id = u1.id
        LEFT JOIN users u2 ON p.created_by = u2.id
        WHERE p.id = 48
    """)
    project = cursor.fetchone()
    if project:
        print(f"项目ID: {project[0]}")
        print(f"项目名称: {project[1]}")
        print(f"当前所有者: {project[4]} (owner_id={project[2]})")
        print(f"创建人: {project[5]} (created_by={project[3]})")
        print(f"创建时间: {project[6]}")
        print(f"更新时间: {project[7]}")

    # 查看项目变更日志
    print("\n=== 项目48的变更日志 ===")
    cursor.execute("""
        SELECT id, field_name, old_value, new_value, user_name, created_at
        FROM change_logs
        WHERE record_id = 48 AND table_name = 'projects'
        ORDER BY created_at DESC
        LIMIT 20
    """)
    logs = cursor.fetchall()
    if logs:
        for log in logs:
            print(f"变更ID: {log[0]} | 字段: {log[1]}")
            print(f"  旧值: {log[2]} -> 新值: {log[3]}")
            print(f"  操作人: {log[4]} | 时间: {log[5]}")
    else:
        print("未找到变更日志")

    # 检查备份表中项目48的数据
    print("\n=== 检查是否有项目备份表 ===")
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE '%project%backup%'
    """)
    backup_tables = cursor.fetchall()
    print(f"项目备份表: {backup_tables}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
