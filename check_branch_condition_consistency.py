#!/usr/bin/env python3
"""
分支条件数据一致性检查和修复工具

这个脚本检查所有分支步骤的JSON快照和表记录之间的一致性，
并提供自动修复功能。
"""

import sys
import json
from datetime import datetime
from app import create_app, db
from app.models.approval import ApprovalStep
from app.models.approval_branch_condition import ApprovalBranchCondition
from app.services.branch_condition_service import BranchConditionService


def check_consistency():
    """检查数据一致性"""
    print("🔍 开始检查分支条件数据一致性...")
    
    # 获取所有分支步骤
    branch_steps = ApprovalStep.query.filter(ApprovalStep.step_type == 'branch').all()
    print(f"📊 找到 {len(branch_steps)} 个分支步骤")
    
    issues = []
    
    for step in branch_steps:
        print(f"\n🔍 检查步骤 {step.id}: {step.step_name}")
        
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
                print(f"  ❌ JSON解析错误")
                issues.append({
                    'step_id': step.id,
                    'step_name': step.step_name,
                    'issue': 'json_parse_error',
                    'description': 'JSON数据解析失败'
                })
                continue
        
        print(f"  📋 表记录: {len(table_records)} 个")
        print(f"  📋 JSON条件: {len(json_conditions)} 个")
        
        # 检查数量一致性
        if len(table_records) != len(json_conditions):
            print(f"  ⚠️ 数量不匹配: 表记录 {len(table_records)} vs JSON {len(json_conditions)}")
            issues.append({
                'step_id': step.id,
                'step_name': step.step_name,
                'issue': 'count_mismatch',
                'table_count': len(table_records),
                'json_count': len(json_conditions),
                'description': '表记录和JSON条件数量不匹配'
            })
        
        # 检查内容一致性
        if table_records:
            for i, record in enumerate(table_records):
                corresponding_json = None
                for json_cond in json_conditions:
                    if (json_cond.get('operator') == record.operator and 
                        json_cond.get('value') == record.field_value):
                        corresponding_json = json_cond
                        break
                
                if not corresponding_json:
                    print(f"  ❌ 表记录 {record.id} 在JSON中找不到对应项")
                    issues.append({
                        'step_id': step.id,
                        'step_name': step.step_name,
                        'issue': 'missing_json_counterpart',
                        'record_id': record.id,
                        'description': f'表记录 {record.id} 在JSON中找不到对应项'
                    })
                else:
                    # 检查字段一致性
                    if record.approver_id != corresponding_json.get('approver_id'):
                        print(f"  ⚠️ 审批人不匹配: 表 {record.approver_id} vs JSON {corresponding_json.get('approver_id')}")
                        issues.append({
                            'step_id': step.id,
                            'step_name': step.step_name,
                            'issue': 'approver_mismatch',
                            'record_id': record.id,
                            'description': '表记录和JSON的审批人不匹配'
                        })
                    
                    if record.action != corresponding_json.get('action'):
                        print(f"  ⚠️ 动作不匹配: 表 '{record.action}' vs JSON '{corresponding_json.get('action')}'")
                        issues.append({
                            'step_id': step.id,
                            'step_name': step.step_name,
                            'issue': 'action_mismatch',
                            'record_id': record.id,
                            'description': '表记录和JSON的动作不匹配'
                        })
        
        # 检查没有表记录但有JSON的情况
        elif json_conditions:
            print(f"  ❌ 有JSON条件但没有表记录")
            issues.append({
                'step_id': step.id,
                'step_name': step.step_name,
                'issue': 'missing_table_records',
                'description': '有JSON条件但没有对应的表记录'
            })
        
        if not table_records and not json_conditions:
            print(f"  ⚠️ 分支步骤没有任何条件")
            issues.append({
                'step_id': step.id,
                'step_name': step.step_name,
                'issue': 'no_conditions',
                'description': '分支步骤没有任何条件'
            })
    
    print(f"\n📊 检查完成，发现 {len(issues)} 个问题")
    return issues


def fix_consistency_issues(issues):
    """修复一致性问题"""
    if not issues:
        print("✅ 没有发现问题，无需修复")
        return
    
    print(f"\n🔧 开始修复 {len(issues)} 个问题...")
    
    fixed_count = 0
    skipped_count = 0
    
    for issue in issues:
        step_id = issue['step_id']
        step_name = issue['step_name']
        issue_type = issue['issue']
        
        print(f"\n🔧 修复步骤 {step_id} ({step_name}) - {issue['description']}")
        
        step = ApprovalStep.query.get(step_id)
        if not step:
            print(f"  ❌ 步骤不存在，跳过")
            skipped_count += 1
            continue
        
        try:
            if issue_type == 'missing_table_records':
                # JSON有数据但缺少表记录，从JSON同步到表
                print(f"  🔄 从JSON同步到表记录...")
                BranchConditionService.sync_step_json_snapshot(step)
                fixed_count += 1
                print(f"  ✅ 同步完成")
                
            elif issue_type == 'missing_json_counterpart' or issue_type == 'count_mismatch':
                # 表记录有数据但JSON不完整，从表同步到JSON
                print(f"  🔄 从表记录同步到JSON...")
                BranchConditionService.sync_step_json_snapshot(step)
                fixed_count += 1
                print(f"  ✅ 同步完成")
                
            elif issue_type in ['approver_mismatch', 'action_mismatch']:
                # 字段不匹配，以表记录为准更新JSON
                print(f"  🔄 以表记录为准更新JSON...")
                BranchConditionService.sync_step_json_snapshot(step)
                fixed_count += 1
                print(f"  ✅ 同步完成")
                
            elif issue_type == 'json_parse_error':
                # JSON解析错误，清空JSON并从表记录重建
                print(f"  🔄 清空JSON并从表记录重建...")
                step.branch_condition = None
                db.session.commit()
                BranchConditionService.sync_step_json_snapshot(step)
                fixed_count += 1
                print(f"  ✅ 重建完成")
                
            elif issue_type == 'no_conditions':
                # 没有任何条件，标记但不自动修复
                print(f"  ⚠️ 此步骤没有条件，需要手动检查是否正确")
                skipped_count += 1
                
            else:
                print(f"  ❓ 未知问题类型: {issue_type}")
                skipped_count += 1
                
        except Exception as e:
            print(f"  ❌ 修复失败: {str(e)}")
            skipped_count += 1
            db.session.rollback()
    
    print(f"\n📊 修复完成: ✅ {fixed_count} 个已修复, ⚠️ {skipped_count} 个跳过")


def generate_report(issues):
    """生成详细报告"""
    if not issues:
        print("\n✅ 数据一致性检查通过，所有分支步骤数据正常")
        return
    
    print("\n📊 详细问题报告:")
    print("=" * 80)
    
    issue_types = {}
    for issue in issues:
        issue_type = issue['issue']
        if issue_type not in issue_types:
            issue_types[issue_type] = []
        issue_types[issue_type].append(issue)
    
    for issue_type, type_issues in issue_types.items():
        print(f"\n🔍 问题类型: {issue_type} ({len(type_issues)} 个)")
        print("-" * 50)
        
        for issue in type_issues:
            print(f"  步骤 {issue['step_id']}: {issue['step_name']}")
            print(f"    描述: {issue['description']}")
            if 'record_id' in issue:
                print(f"    记录ID: {issue['record_id']}")
            if 'table_count' in issue and 'json_count' in issue:
                print(f"    数量: 表记录 {issue['table_count']}, JSON {issue['json_count']}")
            print()


def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        print("🚀 分支条件数据一致性检查工具")
        print("=" * 50)
        
        # 检查一致性
        issues = check_consistency()
        
        # 生成报告
        generate_report(issues)
        
        if issues:
            # 询问是否修复
            print(f"\n❓ 发现 {len(issues)} 个问题，是否进行自动修复？")
            print("⚠️ 修复会修改数据库数据，建议先备份数据库")
            
            response = input("输入 'yes' 确认修复，其他任何输入将退出: ").strip().lower()
            
            if response == 'yes':
                fix_consistency_issues(issues)
                print("\n🔍 修复后重新检查...")
                new_issues = check_consistency()
                if new_issues:
                    print(f"⚠️ 修复后仍有 {len(new_issues)} 个问题")
                    generate_report(new_issues)
                else:
                    print("✅ 所有问题已修复，数据一致性检查通过！")
            else:
                print("❌ 用户取消修复")
        
        print("\n🏁 检查完成")


if __name__ == '__main__':
    main()