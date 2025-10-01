#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询问题报销单的创建时间"""
import sys, os
sys.path.insert(0, '/Users/nijie/Documents/PMA')
os.environ['DATABASE_URL'] = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    result = db.session.execute(text("""
        SELECT ai.id, e.expense_number, ai.started_at, e.created_at as expense_created, ai.current_step
        FROM approval_instance ai
        JOIN expenses e ON ai.object_id = e.id
        WHERE ai.object_type = 'expense'
        AND ai.status = 'PENDING'
        AND ai.id IN (8, 9, 10, 11, 26, 32, 30, 33, 34, 35, 24)
        ORDER BY ai.started_at
    """))

    print('\n问题报销单的创建时间：')
    print('=' * 90)
    print(f"{'实例ID':<8} | {'报销单编号':<15} | {'审批启动时间':<20} | {'报销单创建时间':<20} | {'current_step'}")
    print('-' * 90)
    for row in result:
        print(f"{row[0]:<8} | {row[1]:<15} | {str(row[2]):<20} | {str(row[3]):<20} | {row[4]}")
    print('=' * 90)
    print('\n⏰ 代码修复时间: 2025-08-20 16:39:57')
    print('对比分析: 在此时间之前审批流转的是历史数据问题，之后创建/流转的说明代码仍有bug')
