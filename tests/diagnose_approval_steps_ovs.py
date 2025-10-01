#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查询OVS数据库中的approval_steps表，确认current_step=2是否有效"""
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

# 强制设置为云端OVS数据库
os.environ['DATABASE_URL'] = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

from app import create_app, db
from sqlalchemy import text
import json

app = create_app()

print("=" * 80)
print("  OVS数据库 - 审批步骤详细诊断")
print("=" * 80)

with app.app_context():
    # 1. 查询审批实例的详细信息
    print("\n【1】审批实例 30 的详细信息:")
    result = db.session.execute(text("""
        SELECT id, object_type, object_id, process_id,
               current_step, current_step_order, status,
               template_snapshot IS NOT NULL as has_snapshot
        FROM approval_instance
        WHERE id = 30
    """))
    instance = result.fetchone()
    if instance:
        print(f"  - ID: {instance[0]}")
        print(f"  - 对象类型: {instance[1]}")
        print(f"  - 对象ID: {instance[2]}")
        print(f"  - 流程模板ID: {instance[3]}")
        print(f"  - current_step: {instance[4]}")
        print(f"  - current_step_order: {instance[5]}")
        print(f"  - 状态: {instance[6]}")
        print(f"  - 是否有快照: {instance[7]}")

        process_id = instance[3]
        current_step_id = instance[4]
        current_step_order = instance[5]
    else:
        print("  ❌ 未找到审批实例")
        sys.exit(1)

    # 2. 查询approval_steps表中流程5的所有步骤
    print(f"\n【2】approval_steps表中流程ID={process_id}的所有步骤:")
    result = db.session.execute(text("""
        SELECT id, step_name, step_order, approver_user_id, approver_type,
               action_type, approval_instance_id
        FROM approval_steps
        WHERE process_id = :process_id OR approval_instance_id = 30
        ORDER BY step_order
    """), {'process_id': process_id})

    steps = result.fetchall()
    if steps:
        for step in steps:
            marker = " 👉 [current_step指向这里]" if step[0] == current_step_id else ""
            print(f"\n  步骤ID={step[0]}: {step[1]}{marker}")
            print(f"    - step_order: {step[2]}")
            print(f"    - approver_user_id: {step[3]}")
            print(f"    - approver_type: {step[4]}")
            print(f"    - action_type: {step[5]}")
            print(f"    - approval_instance_id: {step[6]}")
    else:
        print("  ⚠️  approval_steps表中没有找到任何步骤")
        print("  说明：系统完全依赖template_snapshot，不使用approval_steps表")

    # 3. 检查ID=2的步骤记录
    print(f"\n【3】检查approval_steps表中ID=2的记录:")
    result = db.session.execute(text("""
        SELECT id, step_name, step_order, process_id, approval_instance_id,
               approver_user_id, approver_type
        FROM approval_steps
        WHERE id = 2
    """))
    step_2 = result.fetchone()
    if step_2:
        print(f"  ✅ 找到ID=2的步骤:")
        print(f"    - 步骤名称: {step_2[1]}")
        print(f"    - 步骤顺序: {step_2[2]}")
        print(f"    - 流程ID: {step_2[3]}")
        print(f"    - 审批实例ID: {step_2[4]}")
        print(f"    - 审批人用户ID: {step_2[5]}")
        print(f"    - 审批人类型: {step_2[6]}")

        if step_2[3] != process_id and step_2[4] != 30:
            print(f"\n  ⚠️  警告: ID=2的步骤不属于流程{process_id}或实例30")
            print(f"     实际所属流程ID: {step_2[3]}")
            print(f"     实际所属实例ID: {step_2[4]}")
    else:
        print("  ❌ approval_steps表中不存在ID=2的记录")

    # 4. 查询审批记录
    print(f"\n【4】审批实例30的审批记录:")
    result = db.session.execute(text("""
        SELECT id, instance_id, action, approver_id, step_id,
               comment, created_at
        FROM approval_record
        WHERE instance_id = 30
        ORDER BY id
    """))
    records = result.fetchall()
    if records:
        for record in records:
            # 查询审批人信息
            user_result = db.session.execute(text("""
                SELECT username, real_name FROM users WHERE id = :user_id
            """), {'user_id': record[3]})
            user = user_result.fetchone()
            user_name = f"{user[0]} ({user[1]})" if user else f"ID:{record[3]}"

            print(f"\n  记录ID={record[0]}:")
            print(f"    - 动作: {record[2]}")
            print(f"    - 审批人: {user_name}")
            print(f"    - step_id: {record[4]}")
            print(f"    - 时间: {record[6]}")
            if record[5]:
                print(f"    - 备注: {record[5]}")
    else:
        print("  无审批记录")

    # 5. 查询模板快照内容
    print(f"\n【5】审批实例30的模板快照内容:")
    result = db.session.execute(text("""
        SELECT template_snapshot FROM approval_instance WHERE id = 30
    """))
    snapshot_row = result.fetchone()
    if snapshot_row and snapshot_row[0]:
        try:
            snapshot = json.loads(snapshot_row[0]) if isinstance(snapshot_row[0], str) else snapshot_row[0]
            steps = snapshot.get('steps', [])
            print(f"  快照包含 {len(steps)} 个步骤:")
            for i, step in enumerate(steps, 1):
                marker = " 👉 [current_step_order指向这里]" if i == current_step_order else ""
                print(f"\n  快照步骤{i}: {step.get('step_name')}{marker}")
                print(f"    - step_id (快照): {step.get('id')}")
                print(f"    - step_order: {step.get('step_order')}")
                print(f"    - approver_user_id: {step.get('approver_user_id')}")
                print(f"    - approver_username: {step.get('approver_username')}")
                print(f"    - approver_real_name: {step.get('approver_real_name')}")
        except Exception as e:
            print(f"  ⚠️  解析快照失败: {e}")
    else:
        print("  ⚠️  没有模板快照")

    # 6. 测试get_current_step_info函数
    print(f"\n【6】测试ApprovalInstance.get_current_step_info()方法:")
    from app.models.approval import ApprovalInstance
    instance_obj = ApprovalInstance.query.get(30)
    if instance_obj:
        current_step_info = instance_obj.get_current_step_info()
        if current_step_info:
            print("  ✅ get_current_step_info()成功返回:")
            if isinstance(current_step_info, dict):
                print(f"    - 类型: 字典(快照)")
                print(f"    - step_name: {current_step_info.get('step_name')}")
                print(f"    - step_order: {current_step_info.get('step_order')}")
                print(f"    - approver_user_id: {current_step_info.get('approver_user_id')}")
                print(f"    - approver_type: {current_step_info.get('approver_type')}")
            else:
                print(f"    - 类型: 对象(数据库)")
                print(f"    - step_name: {getattr(current_step_info, 'step_name', 'N/A')}")
                print(f"    - step_order: {getattr(current_step_info, 'step_order', 'N/A')}")
                print(f"    - approver_user_id: {getattr(current_step_info, 'approver_user_id', 'N/A')}")
        else:
            print("  ❌ get_current_step_info()返回None")
            print("  这就是问题所在！")

    # 7. 测试get_step_actual_approver
    print(f"\n【7】测试get_step_actual_approver函数:")
    if instance_obj and current_step_info:
        from app.helpers.approval_helpers import get_step_actual_approver
        actual_approver = get_step_actual_approver(current_step_info, instance_obj)
        if actual_approver:
            print(f"  ✅ 实际审批人: {actual_approver.username} (ID:{actual_approver.id}, 真实姓名:{actual_approver.real_name})")
        else:
            print(f"  ❌ 无法确定实际审批人")
    else:
        print("  ⚠️  跳过测试（缺少必要信息）")

    # 8. 测试can_user_approve
    print(f"\n【8】测试admin用户(ID=1)的审批权限:")
    from app.helpers.approval_helpers import can_user_approve
    can_approve = can_user_approve(30, 1)
    print(f"  can_user_approve(instance_id=30, user_id=1) = {can_approve}")

    if not can_approve:
        print("\n  ❌ 这就是为什么admin看不到待审批提醒和无法审批的原因！")

print("\n" + "=" * 80)
print("  诊断完成")
print("=" * 80)
