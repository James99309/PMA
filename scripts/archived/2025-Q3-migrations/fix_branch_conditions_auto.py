#!/usr/bin/env python3
"""
自动修复分支条件数据一致性问题
"""

import sys
import json
from datetime import datetime
from app import create_app, db
from app.models.approval import ApprovalStep
from app.models.approval_branch_condition import ApprovalBranchCondition
from app.services.branch_condition_service import BranchConditionService


def fix_all_branch_conditions():
    """自动修复所有分支条件的数据一致性"""
    print("🚀 开始自动修复分支条件数据一致性...")
    
    # 获取所有分支步骤
    branch_steps = ApprovalStep.query.filter(ApprovalStep.step_type == 'branch').all()
    print(f"📊 找到 {len(branch_steps)} 个分支步骤")
    
    fixed_count = 0
    error_count = 0
    
    for step in branch_steps:
        print(f"\n🔧 修复步骤 {step.id}: {step.step_name}")
        
        try:
            # 获取表记录
            table_records = ApprovalBranchCondition.query.filter(
                ApprovalBranchCondition.step_id == step.id
            ).all()
            print(f"  📋 当前表记录: {len(table_records)} 个")
            
            # 显示表记录详情
            for record in table_records:
                print(f"    - {record.id}: {record.operator} '{record.field_value}' -> 审批人 {record.approver_id}, 动作 '{record.action}'")
            
            # 获取JSON数据
            json_conditions = []
            if step.branch_condition:
                if isinstance(step.branch_condition, dict):
                    json_conditions = step.branch_condition.get('conditions', [])
                else:
                    try:
                        bc = json.loads(step.branch_condition)
                        json_conditions = bc.get('conditions', [])
                    except:
                        print(f"  ❌ JSON解析错误，将清空并重建")
                        step.branch_condition = None
                        db.session.commit()
            
            print(f"  📋 当前JSON条件: {len(json_conditions)} 个")
            
            # 以表记录为准，重新生成JSON快照
            print(f"  🔄 以表记录为准，重新同步JSON快照...")
            BranchConditionService.sync_step_json_snapshot(step)
            db.session.commit()
            
            # 验证修复结果
            step = ApprovalStep.query.get(step.id)  # 重新获取
            new_json_conditions = []
            if step.branch_condition:
                if isinstance(step.branch_condition, dict):
                    new_json_conditions = step.branch_condition.get('conditions', [])
                else:
                    bc = json.loads(step.branch_condition)
                    new_json_conditions = bc.get('conditions', [])
            
            print(f"  ✅ 修复后JSON条件: {len(new_json_conditions)} 个")
            if len(new_json_conditions) == len(table_records):
                print(f"  ✅ 数据一致性修复成功")
                fixed_count += 1
            else:
                print(f"  ⚠️ 修复后仍有数量差异")
                
        except Exception as e:
            print(f"  ❌ 修复失败: {str(e)}")
            error_count += 1
            db.session.rollback()
            import traceback
            print(f"     详细错误: {traceback.format_exc()}")
    
    print(f"\n📊 修复完成: ✅ {fixed_count} 个已修复, ❌ {error_count} 个失败")
    
    return fixed_count, error_count


def verify_fixes():
    """验证修复结果"""
    print("\n🔍 验证修复结果...")
    
    branch_steps = ApprovalStep.query.filter(ApprovalStep.step_type == 'branch').all()
    all_good = True
    
    for step in branch_steps:
        # 获取表记录
        table_records = ApprovalBranchCondition.query.filter(
            ApprovalBranchCondition.step_id == step.id
        ).all()
        
        # 获取JSON数据
        json_conditions = []
        if step.branch_condition:
            try:
                if isinstance(step.branch_condition, dict):
                    json_conditions = step.branch_condition.get('conditions', [])
                else:
                    bc = json.loads(step.branch_condition)
                    json_conditions = bc.get('conditions', [])
            except:
                pass
        
        if len(table_records) == len(json_conditions):
            print(f"  ✅ 步骤 {step.id} ({step.step_name}): 表记录 {len(table_records)} = JSON条件 {len(json_conditions)}")
        else:
            print(f"  ❌ 步骤 {step.id} ({step.step_name}): 表记录 {len(table_records)} ≠ JSON条件 {len(json_conditions)}")
            all_good = False
    
    if all_good:
        print("\n✅ 所有分支步骤的数据一致性验证通过！")
    else:
        print("\n❌ 仍有数据一致性问题")
    
    return all_good


def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        print("🚀 分支条件数据一致性自动修复工具")
        print("=" * 50)
        
        # 自动修复
        fixed_count, error_count = fix_all_branch_conditions()
        
        if error_count == 0:
            # 验证修复结果
            success = verify_fixes()
            if success:
                print("\n🎉 所有分支条件数据已成功修复并验证！")
                return 0
            else:
                print("\n⚠️ 修复过程完成，但验证发现仍有问题")
                return 1
        else:
            print(f"\n❌ 修复过程中有 {error_count} 个错误")
            return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)