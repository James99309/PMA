#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证问题报销单的步骤ID是否在approval_step表中"""
import sys, os
sys.path.insert(0, '/Users/nijie/Documents/PMA')
os.environ['DATABASE_URL'] = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

from app import create_app, db
from sqlalchemy import text
import json

app = create_app()
with app.app_context():
    # 查询所有问题实例的快照步骤ID
    result = db.session.execute(text("""
        SELECT ai.id, e.expense_number, ai.current_step, ai.process_id, ai.template_snapshot
        FROM approval_instance ai
        JOIN expenses e ON ai.object_id = e.id
        WHERE ai.object_type = 'expense'
        AND ai.status = 'PENDING'
        AND ai.id IN (8, 9, 10, 11, 26, 32, 30, 33, 34, 35, 24)
        ORDER BY ai.id
    """))

    print('\n' + '=' * 100)
    print('验证快照步骤ID是否在approval_step表中')
    print('=' * 100)

    for row in result:
        instance_id = row[0]
        expense_number = row[1]
        current_step = row[2]
        process_id = row[3]
        snapshot_json = row[4]

        print(f'\n审批实例 {instance_id} (报销单: {expense_number}):')
        print(f'  - current_step: {current_step}')
        print(f'  - process_id: {process_id}')

        # 检查current_step是否在approval_step表中
        step_check = db.session.execute(text("""
            SELECT id, step_name, step_order, process_id
            FROM approval_step
            WHERE id = :step_id
        """), {'step_id': current_step})

        step_row = step_check.fetchone()
        if step_row:
            print(f'  ✅ current_step在数据库中: ID={step_row[0]}, 名称={step_row[1]}, 顺序={step_row[2]}, 流程={step_row[3]}')
        else:
            print(f'  ❌ current_step={current_step} 不在approval_step表中')

        # 解析快照并检查所有步骤ID
        if snapshot_json:
            try:
                snapshot = json.loads(snapshot_json) if isinstance(snapshot_json, str) else snapshot_json
                steps = snapshot.get('steps', [])
                print(f'  📋 快照包含 {len(steps)} 个步骤:')

                for i, step in enumerate(steps, 1):
                    step_id = step.get('step_id')
                    step_order = step.get('step_order')
                    step_name = step.get('step_name')

                    # 检查每个快照步骤ID是否在数据库中
                    db_check = db.session.execute(text("""
                        SELECT id FROM approval_step WHERE id = :step_id
                    """), {'step_id': step_id})

                    exists = db_check.fetchone() is not None
                    status = '✅' if exists else '❌'
                    marker = ' 👉 [当前步骤]' if step_id == current_step or step_order == current_step else ''

                    print(f'     {status} 步骤{i}: step_id={step_id}, step_order={step_order}, 名称={step_name}{marker}')

            except Exception as e:
                print(f'  ⚠️  快照解析失败: {e}')

    # 额外检查：列出所有process_id对应的approval_step记录
    print('\n' + '=' * 100)
    print('检查流程模板的approval_step表记录')
    print('=' * 100)

    process_ids = db.session.execute(text("""
        SELECT DISTINCT process_id FROM approval_instance
        WHERE id IN (8, 9, 10, 11, 26, 32, 30, 33, 34, 35, 24)
    """))

    for pid_row in process_ids:
        pid = pid_row[0]
        print(f'\n流程 {pid} 在approval_step表中的记录:')

        steps_result = db.session.execute(text("""
            SELECT id, step_name, step_order, approver_user_id
            FROM approval_step
            WHERE process_id = :pid
            ORDER BY step_order
        """), {'pid': pid})

        steps = steps_result.fetchall()
        if steps:
            for step in steps:
                print(f'  - ID={step[0]}, 名称={step[1]}, 顺序={step[2]}, 审批人={step[3]}')
        else:
            print(f'  ❌ 没有记录！')

    print('\n' + '=' * 100)
