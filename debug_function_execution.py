#!/usr/bin/env python3
"""调试get_user_pending_approvals函数执行过程"""

import os
import sys
import json
import psycopg2
from datetime import datetime

# 添加项目路径以导入模块
sys.path.insert(0, '/Users/nijie/Documents/PMA')

def simulate_get_user_pending_approvals():
    """模拟get_user_pending_approvals函数的执行过程"""
    
    print("🔍 模拟get_user_pending_approvals函数执行")
    print("=" * 60)
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='nijie',
        dbname='pma_local'
    )
    
    try:
        cursor = conn.cursor()
        
        print("🔍 步骤1: 模拟获取所有PENDING实例")
        cursor.execute("""
            SELECT id, current_step, status, object_type, object_id
            FROM approval_instance 
            WHERE status = 'PENDING'
            ORDER BY id;
        """)
        
        pending_instances = cursor.fetchall()
        print(f"   ✅ 找到{len(pending_instances)}个PENDING实例")
        
        # 查找实例222
        instance_222 = None
        for instance in pending_instances:
            if instance[0] == 222:
                instance_222 = instance
                break
        
        if not instance_222:
            print("   ❌ 实例222不在PENDING状态列表中")
            return
        else:
            print(f"   ✅ 实例222在PENDING列表中: {instance_222}")
        
        print(f"\n🔍 步骤2: 模拟动态审批人解析逻辑")
        print(f"   处理实例222...")
        
        # 获取快照数据模拟get_current_step_info
        cursor.execute("""
            SELECT template_snapshot::text
            FROM approval_instance 
            WHERE id = 222;
        """)
        
        snapshot_result = cursor.fetchone()
        if snapshot_result:
            snapshot_data = json.loads(snapshot_result[0])
            steps = snapshot_data.get('steps', [])
            
            # 找到当前步骤
            current_step_info = None
            for step in steps:
                if step.get('step_id') == 53:  # current_step
                    current_step_info = step
                    break
            
            if current_step_info:
                print(f"   ✅ 成功获取步骤信息")
                print(f"      - 步骤名称: {current_step_info.get('step_name')}")
                print(f"      - 审批人类型: {current_step_info.get('approver_type')}")
                
                # 模拟分支条件解析
                if current_step_info.get('approver_type') == 'branch':
                    branch_condition = current_step_info.get('branch_condition', {})
                    conditions = branch_condition.get('conditions', [])
                    
                    # 获取项目类型
                    cursor.execute("""
                        SELECT p.project_type
                        FROM pricing_orders po
                        JOIN projects p ON po.project_id = p.id
                        WHERE po.id = 88;
                    """)
                    project_result = cursor.fetchone()
                    
                    if project_result:
                        project_type = project_result[0]
                        print(f"      - 项目类型: {project_type}")
                        
                        # 匹配条件
                        for condition in conditions:
                            operator = condition.get('operator')
                            value = condition.get('value')
                            approver_id = condition.get('approver_id')
                            
                            if operator == 'in' and project_type in value.split(','):
                                print(f"   ✅ 条件匹配成功，审批人ID: {approver_id}")
                                
                                # 检查是否为gxh (ID=13)
                                if approver_id == 13:
                                    print(f"   ✅ 审批人为gxh，实例222应该被包含")
                                    
                                    # 这里模拟valid_instance_ids.append(222)
                                    print(f"\n🔍 步骤3: 模拟后续数据库查询")
                                    
                                    # 模拟pricing_order类型的JOIN查询
                                    cursor.execute("""
                                        SELECT ai.id
                                        FROM approval_instance ai
                                        JOIN pricing_orders po ON ai.object_id = po.id
                                        WHERE ai.id = 222
                                        AND ai.object_type = 'pricing_order';
                                    """)
                                    
                                    join_result = cursor.fetchall()
                                    if join_result:
                                        print(f"   ✅ JOIN查询成功，找到实例: {join_result}")
                                        print(f"\n🎉 确诊: 所有逻辑都正常，实例222应该出现在gxh的审批列表中")
                                        print(f"      问题可能在：")
                                        print(f"      1. Python代码中的异常被静默忽略")
                                        print(f"      2. get_current_step_info()实际执行时返回None")
                                        print(f"      3. get_step_actual_approver()实际执行时返回None")
                                        print(f"      4. 循环中的异常处理导致实例被跳过")
                                    else:
                                        print(f"   ❌ JOIN查询失败，这里可能是问题所在")
                                    break
                    else:
                        print(f"      ❌ 无法获取项目类型")
                else:
                    print(f"      - 非分支步骤，直接使用approver_user_id")
            else:
                print(f"   ❌ 无法找到当前步骤信息")
        else:
            print(f"   ❌ 无法获取快照数据")
            
    except Exception as e:
        print(f"❌ 执行过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    simulate_get_user_pending_approvals()