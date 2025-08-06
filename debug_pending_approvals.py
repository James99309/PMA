#!/usr/bin/env python3
"""调试待审批列表查询问题"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接连接数据库测试
import psycopg2

def debug_pending_approvals():
    """调试待审批查询"""
    
    # 数据库连接
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="nijie", 
            database="pma_local",
            password=""
        )
        cur = conn.cursor()
        
        print("🔍 调试Vivian(用户ID=4)的待审批列表...")
        
        # 1. 首先查看所有PENDING状态的审批实例
        print("\n1️⃣ 所有PENDING状态的审批实例:")
        cur.execute("""
            SELECT ai.id, ai.object_type, ai.object_id, ai.current_step
            FROM approval_instance ai 
            WHERE ai.status = 'PENDING'
            ORDER BY ai.id;
        """)
        
        pending_instances = cur.fetchall()
        print(f"   发现 {len(pending_instances)} 个PENDING实例:")
        for instance in pending_instances:
            print(f"   - 实例{instance[0]}: {instance[1]} #{instance[2]}, 当前步骤: {instance[3]}")
        
        # 2. 检查每个实例的当前步骤审批人
        print("\n2️⃣ 检查每个实例的当前步骤审批人:")
        for instance_id, object_type, object_id, current_step in pending_instances:
            cur.execute("""
                SELECT ast.id, ast.step_name, ast.approver_user_id, ast.approver_type, u.username
                FROM approval_step ast
                LEFT JOIN users u ON ast.approver_user_id = u.id
                WHERE ast.id = %s;
            """, (current_step,))
            
            step_info = cur.fetchone()
            if step_info:
                step_id, step_name, approver_id, approver_type, username = step_info
                print(f"   实例{instance_id}: 步骤'{step_name}', 审批人ID={approver_id}({username}), 类型={approver_type}")
                
                if approver_id == 4:
                    print(f"   ✅ 实例{instance_id}应该出现在Vivian的待审批列表中")
                else:
                    print(f"   ❌ 实例{instance_id}不属于Vivian审批")
        
        # 3. 检查报销单对象是否存在
        print("\n3️⃣ 检查报销单对象是否存在:")
        for instance_id, object_type, object_id, current_step in pending_instances:
            if object_type == 'expense':
                cur.execute("""
                    SELECT expense_number, status FROM expenses WHERE id = %s;
                """, (object_id,))
                
                expense_info = cur.fetchone()
                if expense_info:
                    expense_number, expense_status = expense_info
                    print(f"   实例{instance_id}: 报销单{expense_number}, 状态={expense_status} ✅")
                else:
                    print(f"   实例{instance_id}: 报销单对象不存在 ❌")
        
        # 4. 模拟get_user_pending_approvals的完整查询
        print("\n4️⃣ 模拟get_user_pending_approvals的完整查询:")
        cur.execute("""
            SELECT 
                ai.id as instance_id,
                ai.object_type,
                ai.object_id,
                ai.status,
                ai.current_step,
                ast.step_name,
                ast.approver_user_id,
                e.expense_number
            FROM approval_instance ai
            JOIN approval_step ast ON ai.current_step = ast.id
            JOIN expenses e ON ai.object_id = e.id
            WHERE ai.status = 'PENDING'
              AND ai.object_type = 'expense'
              AND ast.approver_user_id = 4
            ORDER BY ai.started_at DESC;
        """)
        
        results = cur.fetchall()
        print(f"   查询结果: {len(results)} 条记录")
        for result in results:
            print(f"   - 实例{result[0]}: {result[7]} (状态: {result[3]})")
        
        conn.close()
        
        if len(results) > 0:
            print("\n✅ 数据库查询正常，问题可能在Python代码中")
            return True
        else:
            print("\n❌ 数据库查询无结果，需要检查查询逻辑")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接错误: {e}")
        return False

if __name__ == "__main__":
    debug_pending_approvals()