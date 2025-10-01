#!/usr/bin/env python3
"""调试gxh为什么看不到BX2025080405的待审批记录"""

def test_get_user_pending_approvals_logic():
    """模拟get_user_pending_approvals函数的逻辑"""
    
    print("🔍 调试get_user_pending_approvals函数逻辑")
    print(f"目标用户: gxh (user_id=13)")
    print(f"目标审批实例: BX2025080405 (instance_id=140)")
    
    # 模拟数据
    gxh_user_id = 13
    
    # 模拟审批实例140的数据
    instance_data = {
        'id': 140,
        'object_type': 'expense',
        'object_id': 30,
        'current_step': 1,  # step_order
        'status': 'PENDING',
        'created_by': 15,  # lihuawei
        'template_snapshot': {
            'steps': [
                {
                    'step_id': 33,
                    'step_order': 1,
                    'step_name': '上级审批',
                    'approver_type': 'next_level',
                    'approver_user_id': None
                },
                {
                    'step_id': 34,
                    'step_order': 2,
                    'step_name': '财务审批',
                    'approver_type': 'user',
                    'approver_user_id': 4  # Vivian
                }
            ]
        }
    }
    
    # 模拟用户数据
    users_data = {
        15: {'id': 15, 'username': 'lihuawei', 'real_name': '李华伟', 'department': '销售部', 'company_name': '和源通信（上海）股份有限公司', 'role': 'sales_manager', 'is_department_manager': False},
        13: {'id': 13, 'username': 'gxh', 'real_name': '郭小会', 'department': '销售部', 'company_name': '和源通信（上海）股份有限公司', 'role': 'sales_director', 'is_department_manager': True},
        4: {'id': 4, 'username': 'Vivian', 'real_name': '张琰'}
    }
    
    print(f"\n📋 步骤1: 获取当前步骤信息")
    print(f"current_step: {instance_data['current_step']}")
    
    # 获取当前步骤信息
    current_step_info = None
    for step in instance_data['template_snapshot']['steps']:
        if step['step_order'] == instance_data['current_step']:
            current_step_info = step
            print(f"✅ 找到匹配步骤: {step['step_name']}")
            break
    
    if not current_step_info:
        print("❌ 没有找到当前步骤信息")
        return False
    
    print(f"\n📋 步骤2: 确定实际审批人")
    print(f"审批人类型: {current_step_info['approver_type']}")
    
    if current_step_info['approver_type'] == 'next_level':
        # 获取审批实例创建人（提交人）
        creator_user = users_data[instance_data['created_by']]
        print(f"提交人: {creator_user['real_name']} ({creator_user['username']})")
        print(f"提交人部门: {creator_user['department']}")
        print(f"提交人公司: {creator_user['company_name']}")
        print(f"提交人是否部门经理: {creator_user['is_department_manager']}")
        
        # 模拟get_next_level_approver逻辑
        print(f"\n🔍 查找上级审批人:")
        
        # 如果用户有部门且不是部门负责人，查找同部门同公司的部门负责人
        if creator_user['department'] and creator_user['company_name'] and not creator_user['is_department_manager']:
            print(f"查找同部门部门负责人...")
            
            # 查找同部门负责人
            for user_id, user in users_data.items():
                if (user.get('department') == creator_user['department'] and 
                    user.get('company_name') == creator_user['company_name'] and
                    user.get('is_department_manager') == True and
                    user_id != creator_user['id']):
                    
                    actual_approver = user
                    print(f"✅ 找到部门负责人: {actual_approver['real_name']} ({actual_approver['username']}) - user_id={user_id}")
                    
                    # 检查是否匹配目标用户gxh
                    if user_id == gxh_user_id:
                        print(f"🎯 匹配成功！gxh是lihuawei的上级审批人")
                        return True
                    else:
                        print(f"❌ 不匹配，实际审批人不是gxh")
                        return False
    
    elif current_step_info['approver_type'] == 'user':
        approver_user_id = current_step_info['approver_user_id']
        print(f"固定审批人ID: {approver_user_id}")
        
        if approver_user_id == gxh_user_id:
            print(f"🎯 匹配成功！gxh是固定审批人")
            return True
        else:
            print(f"❌ 不匹配，固定审批人不是gxh")
            return False
    
    print(f"❌ 无法确定审批人")
    return False

if __name__ == "__main__":
    print("=" * 80)
    print("🕵️ DEBUG: 为什么gxh看不到BX2025080405的待审批记录")
    print("=" * 80)
    
    success = test_get_user_pending_approvals_logic()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 逻辑正确！BX2025080405应该出现在gxh的待审批列表中")
        print("🤔 如果gxh还是看不到，可能是前端或其他问题")
    else:
        print("😞 逻辑有问题，需要进一步调试")
    print("=" * 80)