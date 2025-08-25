#!/usr/bin/env python3
"""
分支条件数据迁移脚本

将现有的JSON格式分支条件数据迁移到新的独立数据表中
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.approval import ApprovalStep
from app.models.approval_branch_condition import ApprovalBranchCondition
from sqlalchemy import text


def validate_database_structure():
    """验证数据库结构是否准备就绪"""
    print("🔍 验证数据库结构...")
    
    try:
        # 检查新表是否存在
        with db.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_name = 'approval_branch_condition'"
            )).scalar()
            
            if result == 0:
                print("❌ 错误：approval_branch_condition 表不存在")
                print("请先执行 create_branch_condition_table.sql 创建表结构")
                return False
            
            print("✅ approval_branch_condition 表已存在")
            
            # 检查表结构
            columns = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'approval_branch_condition' "
                "ORDER BY ordinal_position"
            )).fetchall()
        
        required_columns = {
            'id', 'step_id', 'condition_order', 'operator', 'field_value',
            'approver_id', 'approver_type', 'action', 'created_at', 'updated_at'
        }
        
        existing_columns = {col[0] for col in columns}
        missing_columns = required_columns - existing_columns
        
        if missing_columns:
            print(f"❌ 错误：缺少必需字段: {missing_columns}")
            return False
        
        print(f"✅ 表结构验证通过，包含 {len(existing_columns)} 个字段")
        return True
        
    except Exception as e:
        print(f"❌ 数据库结构验证失败: {str(e)}")
        return False


def analyze_existing_data():
    """分析现有数据情况"""
    print("\n📊 分析现有分支条件数据...")
    
    # 查找所有分支步骤
    branch_steps = ApprovalStep.query.filter(
        ApprovalStep.step_type == 'branch'
    ).all()
    
    print(f"找到 {len(branch_steps)} 个分支步骤")
    
    steps_with_conditions = []
    total_conditions = 0
    
    for step in branch_steps:
        if step.branch_condition and 'conditions' in step.branch_condition:
            conditions = step.branch_condition['conditions']
            condition_count = len(conditions)
            
            steps_with_conditions.append({
                'step': step,
                'condition_count': condition_count,
                'conditions': conditions
            })
            
            total_conditions += condition_count
            
            print(f"  步骤 {step.id} ({step.step_name}): {condition_count} 个条件")
    
    print(f"\n📋 汇总:")
    print(f"  需要迁移的步骤: {len(steps_with_conditions)} 个")
    print(f"  需要迁移的条件: {total_conditions} 个")
    
    return steps_with_conditions


def check_conflicts():
    """检查可能的数据冲突"""
    print("\n🔍 检查数据冲突...")
    
    # 检查新表中是否已有数据
    existing_count = ApprovalBranchCondition.query.count()
    if existing_count > 0:
        print(f"⚠️ 警告：approval_branch_condition 表中已有 {existing_count} 条记录")
        response = input("是否清空表后重新迁移？(y/N): ").lower()
        if response == 'y':
            print("🗑️ 清空现有数据...")
            ApprovalBranchCondition.query.delete()
            db.session.commit()
            print("✅ 清空完成")
        else:
            print("❌ 迁移取消")
            return False
    
    return True


def migrate_step_conditions(step_data):
    """迁移单个步骤的条件数据"""
    step = step_data['step']
    conditions = step_data['conditions']
    
    print(f"\n🔄 迁移步骤 {step.id} ({step.step_name})...")
    
    migrated_conditions = []
    
    for index, condition_data in enumerate(conditions):
        try:
            # 创建新的条件记录
            condition = ApprovalBranchCondition.from_legacy_data(
                step_id=step.id,
                legacy_condition=condition_data,
                condition_order=index
            )
            
            # 检查重复
            existing = ApprovalBranchCondition.check_duplicate(
                step.id, condition.operator, condition.field_value
            )
            
            if existing:
                print(f"  ⚠️ 跳过重复条件: {condition.field_value} {condition.operator}")
                continue
            
            db.session.add(condition)
            migrated_conditions.append(condition)
            
            print(f"  ✅ 条件 {index + 1}: {condition.field_value} {condition.operator} → {condition.approver_type}")
            
        except Exception as e:
            print(f"  ❌ 条件 {index + 1} 迁移失败: {str(e)}")
            raise e
    
    # 更新原步骤的JSON标记
    if migrated_conditions:
        step.branch_condition.update({
            'migrated': True,
            'migrated_at': datetime.utcnow().isoformat(),
            'migrated_count': len(migrated_conditions)
        })
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(step, 'branch_condition')
        
        print(f"  📝 已标记步骤为已迁移状态")
    
    return len(migrated_conditions)


def execute_migration():
    """执行数据迁移"""
    print("\n🚀 开始数据迁移...")
    
    # 分析数据
    steps_data = analyze_existing_data()
    
    if not steps_data:
        print("✅ 没有需要迁移的数据")
        return True
    
    # 检查冲突
    if not check_conflicts():
        return False
    
    # 执行迁移
    total_migrated = 0
    successful_steps = 0
    failed_steps = 0
    
    try:
        for step_data in steps_data:
            try:
                migrated_count = migrate_step_conditions(step_data)
                total_migrated += migrated_count
                successful_steps += 1
            except Exception as e:
                print(f"❌ 步骤 {step_data['step'].id} 迁移失败: {str(e)}")
                failed_steps += 1
                db.session.rollback()
                continue
        
        # 提交所有更改
        db.session.commit()
        
        print(f"\n🎉 迁移完成!")
        print(f"  成功步骤: {successful_steps} 个")
        print(f"  失败步骤: {failed_steps} 个")
        print(f"  迁移条件: {total_migrated} 个")
        
        return failed_steps == 0
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 迁移过程中出现错误: {str(e)}")
        return False


def verify_migration():
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    
    # 统计新表数据
    new_table_count = ApprovalBranchCondition.query.count()
    print(f"新表中的条件数: {new_table_count}")
    
    # 统计已迁移的步骤
    migrated_steps = ApprovalStep.query.filter(
        ApprovalStep.step_type == 'branch',
        ApprovalStep.branch_condition.contains({'migrated': True})
    ).count()
    
    total_branch_steps = ApprovalStep.query.filter(
        ApprovalStep.step_type == 'branch'
    ).count()
    
    print(f"已迁移步骤: {migrated_steps} / {total_branch_steps}")
    
    # 详细验证每个步骤
    verification_passed = True
    
    for step in ApprovalStep.query.filter(ApprovalStep.step_type == 'branch').all():
        if not step.has_migrated_conditions():
            continue
            
        # 比较新旧数据
        old_conditions = step.branch_condition.get('conditions', [])
        new_conditions = ApprovalBranchCondition.get_step_conditions(step.id)
        
        if len(old_conditions) != len(new_conditions):
            print(f"❌ 步骤 {step.id} 条件数量不匹配: {len(old_conditions)} vs {len(new_conditions)}")
            verification_passed = False
        else:
            print(f"✅ 步骤 {step.id} 验证通过: {len(new_conditions)} 个条件")
    
    return verification_passed


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 分支条件数据迁移脚本")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 验证数据库结构
            if not validate_database_structure():
                return 1
            
            # 执行迁移
            if not execute_migration():
                print("❌ 迁移失败")
                return 1
            
            # 验证结果
            if not verify_migration():
                print("⚠️ 迁移验证发现问题")
                return 1
            
            print("\n🎉 迁移成功完成！")
            return 0
            
        except Exception as e:
            print(f"❌ 迁移脚本执行失败: {str(e)}")
            return 1


if __name__ == '__main__':
    from datetime import datetime
    exit_code = main()
    sys.exit(exit_code)