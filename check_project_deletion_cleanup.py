#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目删除关联数据清理检查工具
检查删除项目时是否会正确清理所有关联数据
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.action import Action, ActionReply
from app.models.approval import ApprovalInstance, ApprovalRecord
from app.models.user import User
from sqlalchemy import text

app = create_app()

def check_database_constraints():
    """检查数据库外键约束配置"""
    print("🔍 检查数据库外键约束配置...")
    
    with app.app_context():
        try:
            # 检查actions表的外键约束
            result = db.session.execute(text("""
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                LEFT JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                    AND tc.table_schema = rc.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND ccu.table_name = 'projects'
                ORDER BY tc.table_name, tc.constraint_name;
            """))
            
            constraints = result.fetchall()
            
            print("\n📋 引用projects表的外键约束：")
            print("表名\t\t约束名\t\t\t字段\t\t删除规则")
            print("-" * 80)
            
            for constraint in constraints:
                table_name = constraint.table_name
                constraint_name = constraint.constraint_name
                column_name = constraint.column_name
                delete_rule = constraint.delete_rule or "NO ACTION"
                
                print(f"{table_name:<15}\t{constraint_name:<25}\t{column_name:<15}\t{delete_rule}")
                
        except Exception as e:
            print(f"❌ 检查数据库约束失败: {str(e)}")

def analyze_project_relationships(project_id):
    """分析指定项目的关联数据"""
    print(f"\n🔍 分析项目ID {project_id} 的关联数据...")
    
    with app.app_context():
        project = Project.query.get(project_id)
        if not project:
            print(f"❌ 项目ID {project_id} 不存在")
            return None
            
        print(f"📋 项目: {project.project_name}")
        
        # 检查报价单
        quotations = Quotation.query.filter_by(project_id=project_id).all()
        print(f"📄 关联报价单: {len(quotations)} 个")
        for q in quotations[:3]:  # 只显示前3个
            print(f"   - ID: {q.id}, 报价单号: {q.quotation_number}")
        if len(quotations) > 3:
            print(f"   ... 还有 {len(quotations) - 3} 个报价单")
            
        # 检查项目跟进记录
        actions = Action.query.filter_by(project_id=project_id).all()
        print(f"📝 项目跟进记录: {len(actions)} 个")
        for a in actions[:3]:  # 只显示前3个
            print(f"   - ID: {a.id}, 日期: {a.date}, 记录人: {a.owner.username if a.owner else '未知'}")
        if len(actions) > 3:
            print(f"   ... 还有 {len(actions) - 3} 个跟进记录")
            
        # 检查跟进记录的回复
        action_replies_count = 0
        for action in actions:
            replies = ActionReply.query.filter_by(action_id=action.id).all()
            action_replies_count += len(replies)
        print(f"💬 跟进记录回复: {action_replies_count} 个")
        
        # 检查项目审批实例
        approval_instances = ApprovalInstance.query.filter_by(
            object_type='project', 
            object_id=project_id
        ).all()
        print(f"✅ 项目审批实例: {len(approval_instances)} 个")
        for ai in approval_instances:
            print(f"   - ID: {ai.id}, 状态: {ai.status.value if ai.status else '未知'}, 创建时间: {ai.started_at}")
            
            # 检查审批记录
            approval_records = ApprovalRecord.query.filter_by(instance_id=ai.id).all()
            print(f"     审批记录: {len(approval_records)} 个")
            
        # 检查报价单审批实例
        quotation_approval_instances = []
        for quotation in quotations:
            q_instances = ApprovalInstance.query.filter_by(
                object_type='quotation',
                object_id=quotation.id
            ).all()
            quotation_approval_instances.extend(q_instances)
            
        print(f"📋 报价单审批实例: {len(quotation_approval_instances)} 个")
        for qai in quotation_approval_instances[:3]:  # 只显示前3个
            print(f"   - ID: {qai.id}, 报价单ID: {qai.object_id}, 状态: {qai.status.value if qai.status else '未知'}")
        if len(quotation_approval_instances) > 3:
            print(f"   ... 还有 {len(quotation_approval_instances) - 3} 个审批实例")
            
        # 检查项目评分记录
        try:
            from app.models.project_rating_record import ProjectRatingRecord
            rating_records = ProjectRatingRecord.query.filter_by(project_id=project_id).all()
            print(f"⭐ 项目评分记录: {len(rating_records)} 个")
        except ImportError:
            print("⭐ 项目评分记录: 模块不存在")
            
        # 检查项目评分系统记录
        try:
            from app.models.project_scoring import ProjectScoringRecord, ProjectTotalScore
            scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
            total_scores = ProjectTotalScore.query.filter_by(project_id=project_id).all()
            print(f"🎯 项目评分系统记录: {len(scoring_records)} 个评分记录, {len(total_scores)} 个总分记录")
        except ImportError:
            print("🎯 项目评分系统记录: 模块不存在")
            
        return {
            'project': project,
            'quotations': len(quotations),
            'actions': len(actions),
            'action_replies': action_replies_count,
            'project_approvals': len(approval_instances),
            'quotation_approvals': len(quotation_approval_instances),
            'rating_records': len(rating_records) if 'rating_records' in locals() else 0,
            'scoring_records': len(scoring_records) + len(total_scores) if 'scoring_records' in locals() else 0
        }

def check_deletion_coverage():
    """检查项目删除代码的覆盖范围"""
    print("\n🔍 检查项目删除代码的覆盖范围...")
    
    print("\n✅ 当前删除代码已覆盖的关联数据:")
    print("1. ✅ 报价单 (Quotation) - 手动删除")
    print("2. ✅ 项目阶段历史 (ProjectStageHistory) - 手动删除")
    print("3. ✅ 项目评分记录 (ProjectRatingRecord) - 手动删除")
    print("4. ✅ 项目评分系统记录 (ProjectScoringRecord, ProjectTotalScore) - 手动删除")
    
    print("\n❌ 当前删除代码未覆盖的关联数据:")
    print("1. ❌ 项目跟进记录 (Action) - 未处理")
    print("2. ❌ 跟进记录回复 (ActionReply) - 未处理")
    print("3. ❌ 项目审批实例 (ApprovalInstance) - 未处理")
    print("4. ❌ 审批记录 (ApprovalRecord) - 未处理")
    print("5. ❌ 报价单审批实例 (ApprovalInstance) - 未处理")
    
    print("\n🔧 数据库约束清理情况:")
    print("1. ✅ project_rating_records.project_id - CASCADE删除")
    print("2. ✅ project_scoring_records.project_id - CASCADE删除")  
    print("3. ✅ project_total_scores.project_id - CASCADE删除")
    print("4. ❓ actions.project_id - 需要确认约束设置")
    print("5. ❓ approval_instance.object_id (项目) - 需要确认约束设置")

def simulate_project_deletion(project_id, dry_run=True):
    """模拟项目删除过程"""
    print(f"\n🧪 {'模拟' if dry_run else '执行'}项目删除 (ID: {project_id})...")
    
    with app.app_context():
        project = Project.query.get(project_id)
        if not project:
            print(f"❌ 项目ID {project_id} 不存在")
            return
            
        print(f"目标项目: {project.project_name}")
        
        # 分析关联数据
        data_summary = analyze_project_relationships(project_id)
        
        if not dry_run:
            print("\n⚠️  实际删除功能暂未实现，请手动使用系统删除功能")
            return
            
        print(f"\n📊 删除影响范围总结:")
        print(f"   📄 报价单: {data_summary['quotations']} 个")
        print(f"   📝 项目跟进记录: {data_summary['actions']} 个")
        print(f"   💬 跟进记录回复: {data_summary['action_replies']} 个")
        print(f"   ✅ 项目审批实例: {data_summary['project_approvals']} 个")
        print(f"   📋 报价单审批实例: {data_summary['quotation_approvals']} 个")
        print(f"   ⭐ 评分记录: {data_summary['rating_records']} 个")
        print(f"   🎯 评分系统记录: {data_summary['scoring_records']} 个")

def recommend_fixes():
    """推荐修复方案"""
    print("\n💡 推荐修复方案:")
    
    print("\n1. 📝 完善项目删除代码 - 在 app/views/project.py 的 delete_project 函数中:")
    print("""
    # 删除项目跟进记录和回复
    from app.models.action import Action, ActionReply
    project_actions = Action.query.filter_by(project_id=project_id).all()
    for action in project_actions:
        # ActionReply已通过cascade='all, delete-orphan'自动删除
        db.session.delete(action)
    
    # 删除项目审批实例和记录
    from app.models.approval import ApprovalInstance, ApprovalRecord
    project_approvals = ApprovalInstance.query.filter_by(
        object_type='project', object_id=project_id
    ).all()
    for approval in project_approvals:
        # ApprovalRecord已通过cascade="all, delete-orphan"自动删除
        db.session.delete(approval)
    
    # 删除关联报价单的审批实例
    quotation_ids = [q.id for q in quotations]
    quotation_approvals = ApprovalInstance.query.filter(
        ApprovalInstance.object_type == 'quotation',
        ApprovalInstance.object_id.in_(quotation_ids)
    ).all()
    for approval in quotation_approvals:
        db.session.delete(approval)
    """)
    
    print("\n2. 🔧 确认数据库外键约束 - 检查以下表的外键约束是否设置了CASCADE:")
    print("   - actions.project_id")
    print("   - approval_instance.object_id (当object_type='project'时)")
    
    print("\n3. 🧪 测试验证 - 建议步骤:")
    print("   a. 在测试环境创建测试项目")
    print("   b. 为测试项目添加各种关联数据")
    print("   c. 执行删除操作")
    print("   d. 验证所有关联数据是否被正确清理")
    
    print("\n4. 📋 完整的删除检查清单:")
    print("   ✅ 报价单及其明细")
    print("   ✅ 项目阶段历史")
    print("   ✅ 项目评分记录")
    print("   ❌ 项目跟进记录")
    print("   ❌ 跟进记录回复")
    print("   ❌ 项目审批实例")
    print("   ❌ 报价单审批实例")

def main():
    print("=" * 60)
    print("🗑️  项目删除关联数据清理检查工具")
    print("=" * 60)
    
    # 检查数据库约束
    check_database_constraints()
    
    # 检查删除代码覆盖范围
    check_deletion_coverage()
    
    # 推荐修复方案
    recommend_fixes()
    
    # 如果提供了项目ID，分析具体项目
    if len(sys.argv) > 1:
        try:
            project_id = int(sys.argv[1])
            simulate_project_deletion(project_id, dry_run=True)
        except ValueError:
            print(f"❌ 无效的项目ID: {sys.argv[1]}")
    else:
        print("\n💡 使用方法: python check_project_deletion_cleanup.py [项目ID]")
        print("   不提供项目ID时只进行通用检查")
        print("   提供项目ID时会分析该项目的具体关联数据")

if __name__ == "__main__":
    main() 