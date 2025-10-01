#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查"申请备案"模板和报销单审批模板的关系"""
import sys, os
sys.path.insert(0, '/Users/nijie/Documents/PMA')
os.environ['DATABASE_URL'] = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    print('\n' + '=' * 100)
    print('审批模板详细信息')
    print('=' * 100)

    # 1. 查询所有审批模板
    templates = db.session.execute(text("""
        SELECT id, template_name, business_type, status, created_by, created_at
        FROM approval_process_template
        ORDER BY id
    """))

    print('\n所有审批模板:')
    for t in templates:
        print(f'  - ID={t[0]}: {t[1]} (业务类型={t[2]}, 状态={t[3]}, 创建者={t[4]}, 创建时间={t[5]})')

    # 2. 查询ID=1的"申请备案"模板的步骤
    print('\n' + '=' * 100)
    print('模板ID=1 ("申请备案"?) 的步骤:')
    print('=' * 100)

    steps_1 = db.session.execute(text("""
        SELECT id, step_name, step_order, approver_user_id, approver_type, action_type
        FROM approval_step
        WHERE process_id = 1
        ORDER BY step_order
    """))

    steps_1_list = steps_1.fetchall()
    if steps_1_list:
        for step in steps_1_list:
            print(f'  步骤 {step[2]}: ID={step[0]}, 名称={step[1]}, 审批人={step[3]}, 类型={step[4]}, 动作={step[5]}')
    else:
        print('  ❌ 没有步骤')

    # 3. 查询ID=5的报销单审批模板的步骤
    print('\n' + '=' * 100)
    print('模板ID=5 (报销单审批) 的步骤:')
    print('=' * 100)

    steps_5 = db.session.execute(text("""
        SELECT id, step_name, step_order, approver_user_id, approver_type, action_type
        FROM approval_step
        WHERE process_id = 5
        ORDER BY step_order
    """))

    for step in steps_5:
        print(f'  步骤 {step[2]}: ID={step[0]}, 名称={step[1]}, 审批人={step[3]}, 类型={step[4]}, 动作={step[5]}')

    # 4. 检查approval_step表中所有step_order=1的记录
    print('\n' + '=' * 100)
    print('所有step_order=1的步骤 (可能造成混淆):')
    print('=' * 100)

    order_1_steps = db.session.execute(text("""
        SELECT id, step_name, step_order, process_id, approver_user_id
        FROM approval_step
        WHERE step_order = 1
        ORDER BY process_id, id
    """))

    for step in order_1_steps:
        print(f'  - ID={step[0]}, 名称={step[1]}, 顺序={step[2]}, 流程={step[3]}, 审批人={step[4]}')

    # 5. 检查问题实例8使用的模板
    print('\n' + '=' * 100)
    print('问题实例8的审批流程信息:')
    print('=' * 100)

    instance_8 = db.session.execute(text("""
        SELECT ai.id, ai.process_id, ai.current_step, apt.template_name, apt.business_type
        FROM approval_instance ai
        JOIN approval_process_template apt ON ai.process_id = apt.id
        WHERE ai.id = 8
    """))

    i8 = instance_8.fetchone()
    if i8:
        print(f'  实例ID: {i8[0]}')
        print(f'  流程ID: {i8[1]}')
        print(f'  current_step: {i8[2]}')
        print(f'  模板名称: {i8[3]}')
        print(f'  业务类型: {i8[4]}')

        # 查询current_step指向的步骤
        print(f'\n  current_step={i8[2]}指向的步骤:')
        cs = db.session.execute(text("""
            SELECT id, step_name, step_order, process_id
            FROM approval_step
            WHERE id = :sid
        """), {'sid': i8[2]})

        cs_row = cs.fetchone()
        if cs_row:
            print(f'    - ID={cs_row[0]}, 名称={cs_row[1]}, 顺序={cs_row[2]}, 流程={cs_row[3]}')
            if cs_row[3] != i8[1]:
                print(f'    ⚠️  警告: 步骤的流程ID({cs_row[3]})与实例的流程ID({i8[1]})不匹配！')
        else:
            print(f'    ❌ 找不到ID={i8[2]}的步骤')

    print('\n' + '=' * 100)
