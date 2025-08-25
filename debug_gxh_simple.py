#!/usr/bin/env python3
"""简化版gxh审批列表调试脚本 - 绕过WeasyPrint依赖"""

import os
import sys
import json
import psycopg2
from datetime import datetime

def debug_with_direct_db():
    """直接通过数据库调试，不依赖Flask应用"""
    
    print("🔍 直接数据库调试gxh审批列表问题")
    print("=" * 60)
    
    # 数据库连接
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='nijie',
        dbname='pma_local'
    )
    
    try:
        cursor = conn.cursor()
        
        print("🔍 步骤1: 检查审批实例222的快照数据")
        cursor.execute("""
            SELECT 
                id,
                current_step,
                status,
                object_type,
                object_id,
                template_snapshot::text
            FROM approval_instance 
            WHERE id = 222;
        """)
        
        instance_data = cursor.fetchone()
        if instance_data:
            print(f"   ✅ 找到审批实例222")
            print(f"   - ID: {instance_data[0]}")
            print(f"   - 当前步骤: {instance_data[1]}")
            print(f"   - 状态: {instance_data[2]}")
            print(f"   - 对象类型: {instance_data[3]}")
            print(f"   - 对象ID: {instance_data[4]}")
            
            # 解析快照数据
            snapshot_json = json.loads(instance_data[5])
            steps = snapshot_json.get('steps', [])
            print(f"   - 快照步骤数量: {len(steps)}")
            
            # 找到当前步骤（步骤53）
            current_step_data = None
            for step in steps:
                if step.get('step_id') == instance_data[1]:  # current_step = 53
                    current_step_data = step
                    break
            
            if current_step_data:
                print(f"\n🔍 步骤2: 分析当前步骤53的数据")
                print(f"   ✅ 找到步骤53的快照数据")
                print(f"   - 步骤名称: {current_step_data.get('step_name')}")
                print(f"   - 审批人类型: {current_step_data.get('approver_type')}")
                print(f"   - 分支条件: {bool(current_step_data.get('branch_condition'))}")
                
                if current_step_data.get('branch_condition'):
                    branch_condition = current_step_data['branch_condition']
                    print(f"\n🔍 步骤3: 分析分支条件")
                    print(f"   - 分支字段: {branch_condition.get('field')}")
                    conditions = branch_condition.get('conditions', [])
                    print(f"   - 条件数量: {len(conditions)}")
                    
                    for i, condition in enumerate(conditions):
                        print(f"   - 条件{i+1}:")
                        print(f"     操作符: {condition.get('operator')}")
                        print(f"     期望值: {condition.get('value')}")
                        print(f"     审批人ID: {condition.get('approver_id')}")
                    
                    # 检查项目类型
                    print(f"\n🔍 步骤4: 检查项目类型匹配")
                    cursor.execute("""
                        SELECT p.project_type
                        FROM pricing_orders po
                        JOIN projects p ON po.project_id = p.id
                        WHERE po.id = %s;
                    """, (instance_data[4],))
                    
                    project_data = cursor.fetchone()
                    if project_data:
                        project_type = project_data[0]
                        print(f"   ✅ 项目类型: {project_type}")
                        
                        # 检查条件匹配
                        matching_condition = None
                        for condition in conditions:
                            operator = condition.get('operator')
                            value = condition.get('value')
                            
                            if operator == 'in' and project_type in value.split(','):
                                matching_condition = condition
                                print(f"   ✅ 匹配条件: {project_type} in {value}")
                                break
                            elif operator == 'equals' and project_type == value:
                                matching_condition = condition
                                print(f"   ✅ 匹配条件: {project_type} == {value}")
                                break
                        
                        if matching_condition:
                            approver_id = matching_condition.get('approver_id')
                            print(f"\n🔍 步骤5: 检查审批人")
                            print(f"   ✅ 匹配的审批人ID: {approver_id}")
                            
                            # 检查是否为gxh
                            cursor.execute("""
                                SELECT id, username, real_name
                                FROM users 
                                WHERE id = %s;
                            """, (approver_id,))
                            
                            approver_data = cursor.fetchone()
                            if approver_data:
                                print(f"   ✅ 审批人: {approver_data[2]} ({approver_data[1]})")
                                print(f"   🎯 是否为gxh: {approver_data[1] == 'gxh'}")
                                
                                if approver_data[1] == 'gxh':
                                    print(f"\n🎉 结论: 审批实例222应该出现在gxh的审批列表中")
                                    print(f"     问题不在分支条件匹配逻辑")
                                    print(f"     需要检查get_user_pending_approvals函数的其他部分")
                                else:
                                    print(f"\n❌ 结论: 审批实例222不属于gxh")
                            else:
                                print(f"   ❌ 找不到审批人ID {approver_id}")
                        else:
                            print(f"   ❌ 项目类型{project_type}不匹配任何分支条件")
                    else:
                        print(f"   ❌ 找不到关联的项目数据")
                else:
                    print(f"   ❌ 步骤53没有分支条件")
            else:
                print(f"   ❌ 在快照中找不到步骤53的数据")
        else:
            print(f"   ❌ 找不到审批实例222")
            
    except Exception as e:
        print(f"❌ 调试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    debug_with_direct_db()