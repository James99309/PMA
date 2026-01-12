#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查已提交日志中关联的未完成行程

问题描述：
用户提交日志后，关联的行程状态应该是 'completed'，
但由于代码问题，部分行程状态仍然是 'planned'
"""
import sys
import os
from datetime import datetime, date

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

# SP8D云端数据库连接
SP8D_DATABASE_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("=" * 70)
    print("🔍 检查已提交日志中关联的未完成行程")
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    engine = create_engine(SP8D_DATABASE_URL)

    with engine.connect() as conn:
        # 1. 查看问题行程的总体情况
        print("\n📊 问题数据统计:")

        # 1.1 已提交日志关联的未完成行程 (今天之前)
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM work_items wi
            JOIN worklogs wl ON wi.worklog_id = wl.id
            WHERE wl.status = 'submitted'
            AND wi.status = 'planned'
            AND wi.is_deleted = false
            AND wi.planned_date < CURRENT_DATE
        """))
        count_submitted_but_not_completed = result.scalar()
        print(f"   已提交日志中未完成的行程（今天之前）: {count_submitted_but_not_completed}")

        # 1.2 按日期分布
        print("\n📅 按日期分布:")
        result = conn.execute(text("""
            SELECT
                wi.planned_date,
                COUNT(*) as count,
                STRING_AGG(DISTINCT u.real_name, ', ') as users
            FROM work_items wi
            JOIN worklogs wl ON wi.worklog_id = wl.id
            JOIN users u ON wi.owner_id = u.id
            WHERE wl.status = 'submitted'
            AND wi.status = 'planned'
            AND wi.is_deleted = false
            AND wi.planned_date < CURRENT_DATE
            GROUP BY wi.planned_date
            ORDER BY wi.planned_date DESC
            LIMIT 20
        """))
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"   {row[0]}: {row[1]} 条 (用户: {row[2]})")
        else:
            print("   无数据")

        # 1.3 按用户分布
        print("\n👤 按用户分布:")
        result = conn.execute(text("""
            SELECT
                u.real_name,
                COUNT(*) as count
            FROM work_items wi
            JOIN worklogs wl ON wi.worklog_id = wl.id
            JOIN users u ON wi.owner_id = u.id
            WHERE wl.status = 'submitted'
            AND wi.status = 'planned'
            AND wi.is_deleted = false
            AND wi.planned_date < CURRENT_DATE
            GROUP BY u.real_name
            ORDER BY count DESC
        """))
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"   {row[0]}: {row[1]} 条")
        else:
            print("   无数据")

        # 2. 显示详细的问题记录（最近10条）
        print("\n📋 问题行程详情（最近10条）:")
        result = conn.execute(text("""
            SELECT
                wi.id,
                wi.title,
                wi.planned_date,
                wi.status as item_status,
                wl.status as log_status,
                wl.submitted_at,
                u.real_name
            FROM work_items wi
            JOIN worklogs wl ON wi.worklog_id = wl.id
            JOIN users u ON wi.owner_id = u.id
            WHERE wl.status = 'submitted'
            AND wi.status = 'planned'
            AND wi.is_deleted = false
            AND wi.planned_date < CURRENT_DATE
            ORDER BY wi.planned_date DESC, wi.id DESC
            LIMIT 10
        """))
        rows = result.fetchall()
        if rows:
            for row in rows:
                print(f"   ID:{row[0]} | {row[6]} | {row[2]} | {row[1][:30]}...")
                print(f"      行程状态: {row[3]} | 日志状态: {row[4]} | 提交于: {row[5]}")
        else:
            print("   无数据")

        # 3. 另外一种情况：行程没有关联日志但日志已提交
        print("\n📊 其他情况 - 行程未关联日志但当天日志已提交:")
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM work_items wi
            WHERE wi.worklog_id IS NULL
            AND wi.status = 'planned'
            AND wi.is_deleted = false
            AND wi.planned_date < CURRENT_DATE
            AND EXISTS (
                SELECT 1 FROM worklogs wl
                WHERE wl.owner_id = wi.owner_id
                AND wl.log_date = wi.planned_date
                AND wl.status = 'submitted'
            )
        """))
        count_not_linked = result.scalar()
        print(f"   未关联但当天日志已提交的行程: {count_not_linked}")

        if count_not_linked > 0:
            print("\n   详情（最近10条）:")
            result = conn.execute(text("""
                SELECT
                    wi.id,
                    wi.title,
                    wi.planned_date,
                    u.real_name
                FROM work_items wi
                JOIN users u ON wi.owner_id = u.id
                WHERE wi.worklog_id IS NULL
                AND wi.status = 'planned'
                AND wi.is_deleted = false
                AND wi.planned_date < CURRENT_DATE
                AND EXISTS (
                    SELECT 1 FROM worklogs wl
                    WHERE wl.owner_id = wi.owner_id
                    AND wl.log_date = wi.planned_date
                    AND wl.status = 'submitted'
                )
                ORDER BY wi.planned_date DESC
                LIMIT 10
            """))
            rows = result.fetchall()
            for row in rows:
                print(f"      ID:{row[0]} | {row[3]} | {row[2]} | {row[1][:30]}...")

        print("\n" + "=" * 70)
        print("📈 汇总:")
        print(f"   需要标记完成的行程总数: {count_submitted_but_not_completed + count_not_linked}")
        print("=" * 70)

if __name__ == '__main__':
    main()
