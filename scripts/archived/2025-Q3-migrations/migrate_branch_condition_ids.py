#!/usr/bin/env python3
"""
分支条件ID迁移脚本

为所有现有的分支条件添加唯一ID，确保新的编辑逻辑能正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.approval import ApprovalStep
from app.helpers.approval_branch_helpers import migrate_branch_condition_ids
from flask import current_app


def migrate_all_branch_conditions():
    """为所有现有的分支条件添加ID"""
    
    print("🚀 开始分支条件ID迁移...")
    
    # 查找所有有分支条件的步骤
    steps_with_conditions = ApprovalStep.query.filter(
        ApprovalStep.branch_condition.isnot(None),
        ApprovalStep.step_type == 'branch'
    ).all()
    
    print(f"📊 找到 {len(steps_with_conditions)} 个分支步骤需要检查")
    
    updated_count = 0
    error_count = 0
    
    for step in steps_with_conditions:
        try:
            print(f"\n🔍 检查步骤: {step.id} - {step.step_name}")
            
            # 检查是否需要迁移
            needs_update = migrate_branch_condition_ids(step)
            
            if needs_update:
                print(f"   ✅ 为步骤 {step.id} 添加了条件ID")
                updated_count += 1
                
                # 显示更新后的条件
                if step.branch_condition and 'conditions' in step.branch_condition:
                    conditions = step.branch_condition['conditions']
                    for i, condition in enumerate(conditions):
                        condition_id = condition.get('id', 'N/A')
                        condition_value = condition.get('value', 'N/A')
                        print(f"   📋 条件 {i+1}: ID={condition_id}, 值={condition_value}")
            else:
                print(f"   ⏭️  步骤 {step.id} 的条件已有ID，跳过")
                
        except Exception as e:
            print(f"   ❌ 处理步骤 {step.id} 时出错: {str(e)}")
            error_count += 1
            db.session.rollback()
            continue
    
    if updated_count > 0:
        try:
            db.session.commit()
            print(f"\n✅ 迁移完成！")
            print(f"   📊 已更新: {updated_count} 个步骤")
            print(f"   ❌ 错误: {error_count} 个步骤")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 提交数据库更改时出错: {str(e)}")
    else:
        print(f"\n✅ 所有分支条件都已经有ID，无需迁移")


def verify_migration():
    """验证迁移结果"""
    
    print("\n🔍 验证迁移结果...")
    
    # 查找所有分支步骤
    branch_steps = ApprovalStep.query.filter(
        ApprovalStep.step_type == 'branch',
        ApprovalStep.branch_condition.isnot(None)
    ).all()
    
    total_conditions = 0
    conditions_with_id = 0
    
    for step in branch_steps:
        if step.branch_condition and 'conditions' in step.branch_condition:
            conditions = step.branch_condition['conditions']
            total_conditions += len(conditions)
            
            for condition in conditions:
                if condition.get('id'):
                    conditions_with_id += 1
    
    print(f"📊 验证结果:")
    print(f"   总条件数: {total_conditions}")
    print(f"   有ID的条件数: {conditions_with_id}")
    print(f"   迁移完成度: {conditions_with_id/total_conditions*100:.1f}%" if total_conditions > 0 else "   无分支条件")


if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        print("=== 分支条件ID迁移脚本 ===")
        migrate_all_branch_conditions()
        verify_migration()
        print("\n🎉 迁移脚本执行完成！")