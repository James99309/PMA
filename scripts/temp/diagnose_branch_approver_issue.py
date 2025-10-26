#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断云端PO202510-004分支步骤审批人获取失败的问题"""
import sys, os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

import psycopg2
from psycopg2.extras import RealDictCursor
import json

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("诊断: 批价单PO202510-004分支步骤审批人获取失败问题".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. 获取批价单基本信息
        print("1. 批价单基本信息:")
        cursor.execute("""
            SELECT id, order_number, project_id, approval_flow_type, status
            FROM pricing_orders
            WHERE order_number = 'PO202510-004'
        """)
        po = cursor.fetchone()

        if not po:
            print("   ❌ 未找到批价单")
            return

        print(f"   批价单ID: {po['id']}")
        print(f"   订单号: {po['order_number']}")
        print(f"   关联项目ID: {po['project_id']}")
        print(f"   审批流程类型: {po['approval_flow_type']}")
        print(f"   状态: {po['status']}")

        # 2. 获取关联项目信息
        print(f"\n2. 关联项目信息:")
        cursor.execute("""
            SELECT id, project_name, project_type
            FROM projects
            WHERE id = %s
        """, (po['project_id'],))
        project = cursor.fetchone()

        if project:
            print(f"   项目ID: {project['id']}")
            print(f"   项目名称: {project['project_name']}")
            print(f"   项目类型: {project['project_type']} ✓")
        else:
            print(f"   ❌ 未找到关联项目（project_id={po['project_id']}）")
            print(f"   → 这可能是问题根源！分支条件无法获取project_type")

        # 3. 获取审批实例信息
        print(f"\n3. 审批实例信息:")
        cursor.execute("""
            SELECT id, current_step, status, template_snapshot
            FROM approval_instance
            WHERE object_type = 'pricing_order' AND object_id = %s
            ORDER BY started_at DESC
            LIMIT 1
        """, (po['id'],))
        instance = cursor.fetchone()

        if not instance:
            print("   ❌ 未找到待审批实例")
            return

        print(f"   实例ID: {instance['id']}")
        print(f"   当前步骤ID: {instance['current_step']}")
        print(f"   状态: {instance['status']}")

        # 4. 解析当前步骤配置
        print(f"\n4. 当前步骤配置（步骤{instance['current_step']}）:")
        template_snapshot = instance['template_snapshot']
        steps = template_snapshot.get('steps', [])

        current_step = None
        for step in steps:
            if step.get('step_id') == instance['current_step']:
                current_step = step
                break

        if not current_step:
            print(f"   ❌ 在快照中找不到步骤ID {instance['current_step']}")
            return

        print(f"   步骤名称: {current_step.get('step_name')}")
        print(f"   步骤类型: {current_step.get('step_type')}")
        print(f"   审批人类型: {current_step.get('approver_type')}")
        print(f"   动作类型: {current_step.get('action_type')}")

        # 5. 解析分支条件
        if current_step.get('approver_type') == 'branch':
            print(f"\n5. 分支条件配置:")
            branch_condition = current_step.get('branch_condition')

            if branch_condition:
                field_name = branch_condition.get('field')
                conditions = branch_condition.get('conditions', [])

                print(f"   条件字段: {field_name}")
                print(f"   条件数量: {len(conditions)}")
                print(f"\n   条件列表:")

                for i, cond in enumerate(conditions):
                    print(f"     {i+1}. value={cond.get('value')}, approver_id={cond.get('approver_id')}, action={cond.get('action')}")

                # 6. 匹配条件
                if project:
                    print(f"\n6. 条件匹配:")
                    print(f"   项目类型: {project['project_type']}")

                    matched = False
                    for i, cond in enumerate(conditions):
                        if cond.get('value') == project['project_type']:
                            print(f"   ✓ 匹配条件{i+1}: value={cond.get('value')}")
                            print(f"     → 应分配审批人ID: {cond.get('approver_id')}")
                            print(f"     → 执行动作: {cond.get('action')}")

                            # 查询审批人信息
                            cursor.execute("""
                                SELECT id, username, real_name
                                FROM users
                                WHERE id = %s
                            """, (cond.get('approver_id'),))
                            approver = cursor.fetchone()

                            if approver:
                                print(f"     → 审批人: {approver['real_name']} (ID:{approver['id']}, username:{approver['username']})")
                            else:
                                print(f"     ❌ 找不到审批人ID {cond.get('approver_id')}")

                            matched = True
                            break

                    if not matched:
                        print(f"   ❌ 没有匹配的条件！")
                        print(f"   → 项目类型 '{project['project_type']}' 不在条件列表中")
                else:
                    print(f"\n6. 条件匹配:")
                    print(f"   ❌ 无法匹配 - 关联项目不存在")
            else:
                print(f"   ❌ 分支步骤缺少branch_condition配置")
        else:
            print(f"\n5. 非分支步骤，跳过条件分析")

        # 7. 问题诊断总结
        print(f"\n" + "="*80)
        print("问题诊断总结".center(80))
        print("="*80 + "\n")

        if not project:
            print("❌ 根本原因: 批价单的关联项目不存在或已被删除")
            print()
            print("   影响:")
            print("   1. 分支条件无法获取project_type字段")
            print("   2. get_branch_approver() 返回 None")
            print("   3. 权限检查失败: actual_approver is None")
            print("   4. process_approval() 返回 False")
            print("   5. 前端提交的审批被拒绝，不创建approval_record")
            print()
            print("   修复方案:")
            print("   → 检查项目ID是否正确")
            print("   → 如果项目被删除，需要恢复或重新关联")
        elif current_step.get('approver_type') == 'branch' and not current_step.get('branch_condition'):
            print("❌ 根本原因: 分支步骤缺少branch_condition配置")
            print()
            print("   修复方案:")
            print("   → 在审批流程模板中添加分支条件配置")
        elif project:
            # 检查是否能匹配到审批人
            branch_condition = current_step.get('branch_condition')
            if branch_condition:
                matched = False
                for cond in branch_condition.get('conditions', []):
                    if cond.get('value') == project['project_type']:
                        matched = True
                        break

                if matched:
                    print("✓ 配置正确，理论上应该能找到审批人")
                    print()
                    print("   可能的问题:")
                    print("   1. 代码中get_branch_business_object()没有加载project关系")
                    print("      → 需要添加: .options(joinedload(PricingOrder.project))")
                    print("   2. 数据库连接问题导致延迟加载失败")
                    print("   3. 应用日志会显示具体错误信息")
                    print()
                    print("   建议:")
                    print("   → 检查云端应用日志（实例ID: {})".format(instance['id']))
                    print("   → 搜索关键字: 'get_branch_approver', '分支条件', 'project_type'")
                else:
                    print(f"❌ 根本原因: 项目类型 '{project['project_type']}' 没有匹配的分支条件")
                    print()
                    print("   修复方案:")
                    print("   → 在审批流程模板中添加该项目类型的分支条件")

    except Exception as e:
        print(f"\n❌ 诊断失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

    print("\n" + "="*80)
    print("诊断完成".center(80))
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
