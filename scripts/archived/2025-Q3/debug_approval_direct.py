#!/usr/bin/env python3
"""直接调试待审批查询逻辑"""

import json

def debug_get_current_step_info():
    """模拟get_current_step_info方法"""
    
    # 模拟快照数据
    template_snapshot = {
        "template_id": 30,
        "template_name": "报销单流程",
        "object_type": "expense",
        "created_at": "2025-08-05T14:16:33.410984",
        "steps": [
            {"step_id": 33, "step_order": 1, "step_name": "上级审批", "approver_type": "next_level", "approver_user_id": None},
            {"step_id": 34, "step_order": 2, "step_name": "财务审批", "approver_type": "user", "approver_user_id": 4},
            {"step_id": 35, "step_order": 3, "step_name": "总经理审核", "approver_type": "user", "approver_user_id": 5},
            {"step_id": 36, "step_order": 4, "step_name": "支付报销", "approver_type": "user", "approver_user_id": 4, "action_type": "payment_processing"}
        ]
    }
    
    current_step = 36  # 当前步骤ID是36（支付报销）
    
    print(f"🔍 调试get_current_step_info方法")
    print(f"当前步骤: {current_step}")
    print(f"快照中的步骤数: {len(template_snapshot['steps'])}")
    
    # 模拟get_current_step_info逻辑
    steps = template_snapshot['steps']
    if isinstance(steps, list) and len(steps) > 0:
        # 快照数据（字典列表）
        if isinstance(steps[0], dict):
            print("✅ 使用快照数据（字典列表）")
            for step in steps:
                print(f"   检查步骤: step_id={step.get('step_id')}, step_order={step.get('step_order')}, 查找={current_step}")
                if step.get('step_id') == current_step:
                    print(f"✅ 找到匹配步骤: {json.dumps(step, ensure_ascii=False, indent=2)}")
                    return step
    
    print("❌ 没有找到匹配的步骤")
    return None

def debug_get_step_actual_approver():
    """模拟get_step_actual_approver函数"""
    
    # 获取当前步骤信息
    step = debug_get_current_step_info()
    if not step:
        print("❌ 无法获取步骤信息")
        return None
    
    print(f"\n🔍 调试get_step_actual_approver函数")
    
    # 获取步骤信息
    if isinstance(step, dict):
        approver_type = step.get('approver_type', 'user')
        approver_user_id = step.get('approver_user_id')
        action_type = step.get('action_type')
        
        print(f"解析结果:")
        print(f"   approver_type: {approver_type}")
        print(f"   approver_user_id: {approver_user_id}")
        print(f"   action_type: {action_type}")
        
        # 根据审批人类型确定实际审批人
        if approver_type == 'next_level':
            print("   ➡️ 类型：上一级领导")
            return None  # 这里需要实际的用户查询
        elif approver_type == 'auto' or action_type == 'authorization':
            print("   ➡️ 类型：自动选择/授权")
            return None  # 这里需要实际的用户查询
        elif approver_type == 'user' and approver_user_id:
            print(f"   ➡️ 类型：固定用户 (用户ID: {approver_user_id})")
            # 模拟User.query.get(approver_user_id)
            if approver_user_id == 4:
                print("   ✅ 返回Vivian用户对象（模拟）")
                return {"id": 4, "username": "Vivian", "real_name": "张琰"}
            else:
                print(f"   ❌ 用户ID {approver_user_id} 不是Vivian")
                return None
        else:
            print("   ❌ 无法确定审批人")
            return None
    
    return None

def main():
    """主测试函数"""
    print("="*60)
    print("🚀 开始调试待审批查询逻辑")
    print("="*60)
    
    # 测试步骤1：获取当前步骤信息
    step_info = debug_get_current_step_info()
    
    # 测试步骤2：确定实际审批人
    actual_approver = debug_get_step_actual_approver()
    
    # 测试步骤3：检查是否匹配Vivian
    vivian_user_id = 4
    print(f"\n🎯 最终结果检查:")
    print(f"   查询用户ID: {vivian_user_id}")
    print(f"   实际审批人: {actual_approver}")
    
    if actual_approver and actual_approver.get('id') == vivian_user_id:
        print(f"   ✅ 匹配成功！实例应该出现在待审批列表中")
        return True
    else:
        print(f"   ❌ 不匹配，实例不会出现在待审批列表中")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "="*60)
    if success:
        print("🎉 调试结果：逻辑正确，问题可能在其他地方")
    else:
        print("😞 调试结果：发现逻辑问题")
    print("="*60)