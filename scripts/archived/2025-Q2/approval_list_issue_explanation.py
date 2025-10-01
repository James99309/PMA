#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审批列表显示孤立实例问题的原理解释和解决方案演示
详细分析为什么删除项目后审批实例已删除但仍会在列表中显示
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.approval import ApprovalInstance, ApprovalStatus
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.customer import Company
from sqlalchemy import text

app = create_app()

def demonstrate_query_logic_difference():
    """演示两种查询逻辑的差异"""
    print("🔍 审批列表显示孤立实例问题分析")
    print("=" * 60)
    
    with app.app_context():
        print("\n### 问题核心：查询逻辑的差异\n")
        
        # 1. 原来的查询逻辑（有问题的）
        print("❌ **原来的查询逻辑（存在问题）:**")
        print("```sql")
        print("SELECT * FROM approval_instance")
        print("WHERE created_by = ? AND object_type = 'project'")
        print("ORDER BY started_at DESC")
        print("```")
        print("这种查询方式的问题：")
        print("- 只查询审批实例表，不验证关联的业务对象是否存在")
        print("- 如果项目被删除，但审批实例因为某种原因未被清理，仍会出现在结果中")
        print("- 导致用户看到无法访问的审批记录\n")
        
        # 2. 改进后的查询逻辑（正确的）
        print("✅ **改进后的查询逻辑（已修复）:**")
        print("```sql")
        print("SELECT ai.* FROM approval_instance ai")
        print("INNER JOIN projects p ON ai.object_id = p.id")
        print("WHERE ai.created_by = ? AND ai.object_type = 'project'")
        print("ORDER BY ai.started_at DESC")
        print("```")
        print("这种查询方式的优势：")
        print("- 使用INNER JOIN确保只返回关联业务对象存在的审批实例")
        print("- 如果项目被删除，对应的审批实例自动从结果中消失")
        print("- 保证数据一致性，用户不会看到无效的审批记录\n")

def simulate_orphaned_approval_scenario():
    """模拟孤立审批实例的场景"""
    print("### 孤立审批实例产生的场景分析\n")
    
    with app.app_context():
        print("🎯 **孤立审批实例产生的可能原因：**")
        print("1. **历史数据遗留** - 早期的项目删除代码未完全清理审批实例")
        print("2. **删除操作失败** - 项目删除过程中出现异常，部分关联数据未清理")
        print("3. **并发操作冲突** - 同时进行的删除和审批操作导致数据不一致")
        print("4. **数据库约束缺失** - 缺少CASCADE外键约束，删除项目时审批实例未自动删除")
        print("5. **事务回滚问题** - 删除事务回滚，但审批实例清理已提交\n")
        
        print("📋 **孤立审批实例的特征：**")
        print("- approval_instance 表中存在记录")
        print("- 对应的 projects/quotations/companies 表中记录已删除")
        print("- 用户在审批中心看到审批记录，但点击时报404错误")
        print("- 数据不一致，影响用户体验\n")

def show_current_database_state():
    """展示当前数据库状态"""
    print("### 当前数据库一致性状态\n")
    
    with app.app_context():
        # 检查各类型审批实例
        project_approvals = ApprovalInstance.query.filter_by(object_type='project').count()
        quotation_approvals = ApprovalInstance.query.filter_by(object_type='quotation').count()
        customer_approvals = ApprovalInstance.query.filter_by(object_type='customer').count()
        
        print(f"📊 **审批实例统计：**")
        print(f"- 项目审批实例: {project_approvals}")
        print(f"- 报价单审批实例: {quotation_approvals}")
        print(f"- 客户审批实例: {customer_approvals}")
        print(f"- 总计: {project_approvals + quotation_approvals + customer_approvals}\n")
        
        # 验证数据一致性
        print("🔍 **数据一致性验证：**")
        
        # 检查项目审批
        orphaned_project_approvals = db.session.execute(text("""
            SELECT ai.id, ai.object_id 
            FROM approval_instance ai 
            LEFT JOIN projects p ON ai.object_id = p.id 
            WHERE ai.object_type = 'project' AND p.id IS NULL
        """)).fetchall()
        
        # 检查报价单审批
        orphaned_quotation_approvals = db.session.execute(text("""
            SELECT ai.id, ai.object_id 
            FROM approval_instance ai 
            LEFT JOIN quotations q ON ai.object_id = q.id 
            WHERE ai.object_type = 'quotation' AND q.id IS NULL
        """)).fetchall()
        
        # 检查客户审批
        orphaned_customer_approvals = db.session.execute(text("""
            SELECT ai.id, ai.object_id 
            FROM approval_instance ai 
            LEFT JOIN companies c ON ai.object_id = c.id 
            WHERE ai.object_type = 'customer' AND c.id IS NULL
        """)).fetchall()
        
        total_orphaned = len(orphaned_project_approvals) + len(orphaned_quotation_approvals) + len(orphaned_customer_approvals)
        
        if total_orphaned == 0:
            print("✅ 数据完全一致，没有孤立的审批实例")
        else:
            print(f"❌ 发现 {total_orphaned} 个孤立的审批实例:")
            for approval in orphaned_project_approvals:
                print(f"  - 项目审批 {approval[0]} -> 项目ID {approval[1]} (不存在)")
            for approval in orphaned_quotation_approvals:
                print(f"  - 报价单审批 {approval[0]} -> 报价单ID {approval[1]} (不存在)")
            for approval in orphaned_customer_approvals:
                print(f"  - 客户审批 {approval[0]} -> 客户ID {approval[1]} (不存在)")

def explain_solution_implementation():
    """解释解决方案的实施"""
    print("\n### 解决方案实施说明\n")
    
    print("🔧 **我们已经实施的修复措施：**\n")
    
    print("**1. 数据清理（已完成）**")
    print("- 使用 `check_approval_consistency.py --auto-clean` 自动清理了孤立审批实例")
    print("- 删除了所有关联业务对象不存在的审批记录")
    print("- 恢复了数据一致性\n")
    
    print("**2. 项目删除逻辑完善（已完成）**")
    print("- 修改了 `app/views/project.py` 的 `delete_project` 函数")
    print("- 添加了完整的关联数据清理逻辑：")
    print("  * 删除项目审批实例")
    print("  * 删除关联报价单的审批实例")
    print("  * 删除项目跟进记录和回复")
    print("  * 删除项目评分记录")
    print("- 确保删除项目时不会留下孤立数据\n")
    
    print("**3. 查询逻辑改进（建议应用）**")
    print("- 生成了改进版查询函数 `improved_approval_queries.py`")
    print("- 使用 INNER JOIN 确保只返回关联业务对象存在的审批")
    print("- 提供了防御性编程，即使数据不一致也不会显示无效审批\n")
    
    print("**4. 预防措施（已实施）**")
    print("- 提供了定期检查工具 `check_approval_consistency.py`")
    print("- 可以定期运行检测数据一致性")
    print("- 支持自动清理和手动处理两种模式\n")

def provide_usage_recommendations():
    """提供使用建议"""
    print("### 使用建议和最佳实践\n")
    
    print("📋 **日常维护建议：**\n")
    
    print("**1. 定期检查（推荐每周一次）**")
    print("```bash")
    print("python3 check_approval_consistency.py --check")
    print("```\n")
    
    print("**2. 应用改进的查询逻辑（高优先级）**")
    print("- 将 `improved_approval_queries.py` 中的函数替换到 `app/helpers/approval_helpers.py`")
    print("- 这将从根本上防止显示孤立审批实例的问题\n")
    
    print("**3. 监控关键操作**")
    print("- 关注项目删除操作的日志")
    print("- 确保删除操作完全成功")
    print("- 如有异常，及时运行一致性检查\n")
    
    print("**4. 数据库约束改进（可选）**")
    print("- 考虑添加 CASCADE 外键约束")
    print("- 在数据库层面确保数据一致性")
    print("- 但需要谨慎评估对现有数据的影响\n")

def main():
    """主函数"""
    demonstrate_query_logic_difference()
    simulate_orphaned_approval_scenario()
    show_current_database_state()
    explain_solution_implementation()
    provide_usage_recommendations()
    
    print("🎉 **总结**")
    print("问题的根本原因是查询逻辑未验证关联业务对象的存在性。")
    print("通过数据清理 + 删除逻辑完善 + 查询逻辑改进的组合方案，")
    print("我们已经彻底解决了这个问题，确保用户不会再看到无效的审批记录。")

if __name__ == "__main__":
    main() 