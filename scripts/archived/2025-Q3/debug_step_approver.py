#!/usr/bin/env python3
"""调试get_step_actual_approver函数"""

import json

def debug_step_approver():
    """调试步骤审批人确定逻辑"""
    
    # 模拟快照中的步骤数据
    step_data = {
        "step_id": 36,
        "step_order": 4,
        "step_name": "支付报销",
        "approver_type": "user",
        "approver_user_id": 4,
        "approver_username": "Vivian",
        "approver_real_name": "张琰",
        "action_type": "payment_processing"
    }
    
    print("🔍 调试get_step_actual_approver函数")
    print(f"步骤数据: {json.dumps(step_data, ensure_ascii=False, indent=2)}")
    
    # 模拟函数逻辑
    if isinstance(step_data, dict):
        approver_type = step_data.get('approver_type', 'user')
        approver_user_id = step_data.get('approver_user_id')
        action_type = step_data.get('action_type')
        
        print(f"\n📋 解析结果:")
        print(f"   approver_type: {approver_type}")
        print(f"   approver_user_id: {approver_user_id}")
        print(f"   action_type: {action_type}")
        
        # 根据审批人类型确定实际审批人
        if approver_type == 'next_level':
            print("   ➡️ 类型：上一级领导")
        elif approver_type == 'auto' or action_type == 'authorization':
            print("   ➡️ 类型：自动选择/授权")
        elif approver_type == 'user' and approver_user_id:
            print(f"   ➡️ 类型：固定用户 (用户ID: {approver_user_id})")
            print("   ✅ 应该返回用户ID=4的用户对象")
            return approver_user_id
        else:
            print("   ❌ 无法确定审批人")
            return None
    
    return None

if __name__ == "__main__":
    result = debug_step_approver()
    if result == 4:
        print("\n🎉 逻辑正确：应该返回Vivian(用户ID=4)")
    else:
        print(f"\n😞 逻辑有问题：返回了{result}")