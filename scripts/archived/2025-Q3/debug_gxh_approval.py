#!/usr/bin/env python3
"""调试gxh审批列表问题的专用脚本"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/Users/nijie/Documents/PMA')

# 设置环境变量
os.environ['DATABASE_URL'] = 'postgresql://nijie:@localhost:5432/pma_local'

def debug_gxh_approval_issue():
    """调试gxh看不到审批实例222的问题"""
    
    print("🔍 调试gxh审批列表问题")
    print("=" * 60)
    
    # 初始化Flask应用
    from app import create_app
    from app.models.approval import ApprovalInstance, ApprovalStatus
    from app.helpers.approval_helpers import get_step_actual_approver, get_current_step_info
    from app.models.user import User
    
    app = create_app()
    
    with app.app_context():
        # 获取关键信息
        gxh_user = User.query.filter_by(username='gxh').first()
        instance_222 = ApprovalInstance.query.get(222)
        
        print(f"🔍 基本信息检查:")
        print(f"   - gxh用户: {gxh_user.real_name if gxh_user else 'NOT FOUND'} (ID: {gxh_user.id if gxh_user else 'N/A'})")
        print(f"   - 审批实例222: {instance_222 is not None}")
        if instance_222:
            print(f"   - 实例状态: {instance_222.status}")
            print(f"   - 当前步骤: {instance_222.current_step}")
            print(f"   - 对象类型: {instance_222.object_type}")
        
        print(f"\n🔍 步骤1: 测试get_current_step_info函数")
        try:
            current_step_info = instance_222.get_current_step_info()
            print(f"   ✅ get_current_step_info成功返回")
            if current_step_info:
                print(f"   - 步骤类型: {type(current_step_info)}")
                if isinstance(current_step_info, dict):
                    print(f"   - 步骤ID: {current_step_info.get('step_id')}")
                    print(f"   - 步骤名称: {current_step_info.get('step_name')}")
                    print(f"   - 审批人类型: {current_step_info.get('approver_type')}")
                    print(f"   - 分支条件: {bool(current_step_info.get('branch_condition'))}")
                else:
                    print(f"   - 对象属性: {dir(current_step_info) if hasattr(current_step_info, '__dict__') else 'No attributes'}")
            else:
                print(f"   ❌ get_current_step_info返回None")
                return
        except Exception as e:
            print(f"   ❌ get_current_step_info异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        print(f"\n🔍 步骤2: 测试get_step_actual_approver函数")
        try:
            actual_approver = get_step_actual_approver(current_step_info, instance_222)
            print(f"   ✅ get_step_actual_approver执行完成")
            if actual_approver:
                print(f"   - 审批人: {actual_approver.real_name} ({actual_approver.username})")
                print(f"   - 审批人ID: {actual_approver.id}")
                print(f"   - 是否为gxh: {actual_approver.id == gxh_user.id}")
            else:
                print(f"   ❌ get_step_actual_approver返回None")
        except Exception as e:
            print(f"   ❌ get_step_actual_approver异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"\n🔍 步骤3: 模拟get_user_pending_approvals的核心逻辑")
        try:
            # 获取所有PENDING实例
            base_instances = ApprovalInstance.query.filter(
                ApprovalInstance.status == ApprovalStatus.PENDING
            ).all()
            print(f"   - 总PENDING实例数: {len(base_instances)}")
            
            # 筛选gxh的审批实例
            valid_instance_ids = []
            for instance in base_instances:
                if instance.id == 222:
                    print(f"   🎯 检查实例222:")
                    try:
                        step_info = instance.get_current_step_info()
                        print(f"      - 步骤信息获取: {'成功' if step_info else '失败'}")
                        
                        if step_info:
                            approver = get_step_actual_approver(step_info, instance)
                            print(f"      - 审批人解析: {'成功' if approver else '失败'}")
                            
                            if approver:
                                print(f"      - 解析结果: {approver.real_name} (ID:{approver.id})")
                                print(f"      - 匹配gxh: {approver.id == gxh_user.id}")
                                
                                if approver.id == gxh_user.id:
                                    valid_instance_ids.append(instance.id)
                                    print(f"      ✅ 实例222应该出现在gxh的审批列表中")
                                else:
                                    print(f"      ❌ 实例222不属于gxh审批")
                            else:
                                print(f"      ❌ 无法解析审批人")
                        else:
                            print(f"      ❌ 无法获取步骤信息")
                    except Exception as e:
                        print(f"      ❌ 处理实例222时异常: {str(e)}")
            
            print(f"\n🔍 步骤4: 最终结果")
            print(f"   - gxh的有效审批实例ID: {valid_instance_ids}")
            print(f"   - 实例222是否在列表中: {222 in valid_instance_ids}")
            
            if 222 not in valid_instance_ids:
                print(f"\n🚨 问题确认: gxh的审批列表中确实没有实例222")
                print(f"   需要检查分支条件匹配逻辑或步骤信息解析逻辑")
            else:
                print(f"\n✅ 逻辑检查: gxh应该能看到实例222")
                print(f"   问题可能在数据库查询或分页逻辑中")
                
        except Exception as e:
            print(f"   ❌ 核心逻辑测试异常: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_gxh_approval_issue()