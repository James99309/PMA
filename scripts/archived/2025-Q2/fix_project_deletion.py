#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目删除功能修复脚本
完善项目删除逻辑，确保清理所有关联数据
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.action import Action, ActionReply
from app.models.approval import ApprovalInstance, ApprovalRecord
from sqlalchemy import text

app = create_app()

def backup_project_deletion_function():
    """备份原有的项目删除函数"""
    print("📋 创建项目删除函数的改进版本...")
    
    improved_deletion_code = '''
# 改进后的项目删除函数 - 添加到 app/views/project.py 的 delete_project 函数中

@project.route('/delete/<int:project_id>', methods=['POST'])
@permission_required('project', 'delete')
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    # 检查删除权限
    if not can_edit_data(project, current_user):
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试删除无权限的项目: {project_id} (所有者: {project.owner_id})")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '您没有权限删除此项目'
            }), 403
            
        flash('您没有权限删除此项目', 'danger')
        return redirect(url_for('project.list_projects'))
    
    try:
        # === 关联数据清理开始 ===
        
        # 1. 先删除项目关联的所有报价单
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project_id).all()
        quotation_ids = [q.id for q in quotations]  # 保存报价单ID用于后续删除审批
        
        if quotations:
            for quotation in quotations:
                db.session.delete(quotation)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotations)} 个报价单")
        
        # 2. 删除项目关联的所有阶段历史记录
        from app.models.projectpm_stage_history import ProjectStageHistory
        stage_histories = ProjectStageHistory.query.filter_by(project_id=project_id).all()
        if stage_histories:
            for history in stage_histories:
                db.session.delete(history)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(stage_histories)} 个阶段历史记录")
        
        # 3. 删除项目跟进记录和回复 (新增)
        from app.models.action import Action, ActionReply
        project_actions = Action.query.filter_by(project_id=project_id).all()
        if project_actions:
            action_reply_count = 0
            for action in project_actions:
                # 统计回复数量
                replies = ActionReply.query.filter_by(action_id=action.id).all()
                action_reply_count += len(replies)
                # ActionReply已通过cascade='all, delete-orphan'自动删除
                db.session.delete(action)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_actions)} 个跟进记录和 {action_reply_count} 个回复")
        
        # 4. 删除项目审批实例和记录 (新增)
        from app.models.approval import ApprovalInstance, ApprovalRecord
        project_approvals = ApprovalInstance.query.filter_by(
            object_type='project', 
            object_id=project_id
        ).all()
        if project_approvals:
            approval_record_count = 0
            for approval in project_approvals:
                # 统计审批记录数量
                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                approval_record_count += len(records)
                # ApprovalRecord已通过cascade="all, delete-orphan"自动删除
                db.session.delete(approval)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_approvals)} 个项目审批实例和 {approval_record_count} 个审批记录")
        
        # 5. 删除关联报价单的审批实例 (新增)
        if quotation_ids:
            quotation_approvals = ApprovalInstance.query.filter(
                ApprovalInstance.object_type == 'quotation',
                ApprovalInstance.object_id.in_(quotation_ids)
            ).all()
            if quotation_approvals:
                quotation_approval_record_count = 0
                for approval in quotation_approvals:
                    # 统计审批记录数量
                    records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                    quotation_approval_record_count += len(records)
                    db.session.delete(approval)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotation_approvals)} 个报价单审批实例和 {quotation_approval_record_count} 个审批记录")
        
        # 6. 删除项目评分记录
        try:
            from app.models.project_scoring import ProjectScoringRecord, ProjectTotalScore
            
            # 删除评分记录
            scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
            if scoring_records:
                for record in scoring_records:
                    db.session.delete(record)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(scoring_records)} 个项目评分记录")
            
            # 删除总评分记录
            total_scores = ProjectTotalScore.query.filter_by(project_id=project_id).all()
            if total_scores:
                for score in total_scores:
                    db.session.delete(score)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(total_scores)} 个项目总分记录")
                    
        except ImportError:
            # 如果新评分系统模块不存在，跳过
            logger.info("项目评分系统模块不存在，跳过评分记录清理")
        
        # 7. 删除旧的评分记录
        try:
            if ProjectRatingRecord:
                old_rating_records = ProjectRatingRecord.query.filter_by(project_id=project_id).all()
                if old_rating_records:
                    for record in old_rating_records:
                        db.session.delete(record)
                    logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(old_rating_records)} 个旧版评分记录")
        except Exception:
            # 如果评分系统模块处理失败，跳过
            logger.info("旧版评分系统模块处理失败，跳过")
        
        # === 关联数据清理结束 ===
        
        # 8. 最后删除项目
        # 记录删除历史（在实际删除前记录）
        try:
            ChangeTracker.log_delete(project)
        except Exception as track_err:
            logger.warning(f"记录项目删除历史失败: {str(track_err)}")
        
        db.session.delete(project)
        db.session.commit()
        
        logger.info(f"项目 {project_id} ({project.project_name}) 及其所有关联数据删除成功")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '项目删除成功！'
            })
        flash('项目删除成功！', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除项目 {project_id} 失败: {str(e)}")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'删除失败：{str(e)}'
            }), 500
            
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('project.list_projects'))
'''
    
    # 保存改进的代码到文件
    with open('improved_project_deletion.py', 'w', encoding='utf-8') as f:
        f.write(improved_deletion_code)
    
    print("✅ 改进的项目删除代码已保存到 improved_project_deletion.py")
    print("📝 请手动将此代码替换到 app/views/project.py 中的 delete_project 函数")

def create_database_migration():
    """创建数据库迁移脚本来修复外键约束"""
    print("\n🔧 创建数据库外键约束修复脚本...")
    
    migration_sql = '''
-- 项目删除外键约束修复脚本
-- 修复 actions 和 approval_instance 表的外键约束

-- 1. 修复 actions.project_id 外键约束
-- 删除现有约束
ALTER TABLE actions DROP CONSTRAINT IF EXISTS actions_project_id_fkey;

-- 重新创建带CASCADE的约束
ALTER TABLE actions 
ADD CONSTRAINT actions_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- 2. 注意：approval_instance.object_id 不能直接设置CASCADE
-- 因为它可能引用不同类型的对象（project, quotation等）
-- 所以需要在应用层面处理这个约束

-- 3. 可选：修复其他可能需要CASCADE的约束
-- project_stage_history
ALTER TABLE project_stage_history DROP CONSTRAINT IF EXISTS project_stage_history_project_id_fkey;
ALTER TABLE project_stage_history 
ADD CONSTRAINT project_stage_history_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- project_members (如果存在)
ALTER TABLE project_members DROP CONSTRAINT IF EXISTS project_members_project_id_fkey;
ALTER TABLE project_members 
ADD CONSTRAINT project_members_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- quotations (报价单可以选择CASCADE或保留现有约束)
-- ALTER TABLE quotations DROP CONSTRAINT IF EXISTS quotations_project_id_fkey;
-- ALTER TABLE quotations 
-- ADD CONSTRAINT quotations_project_id_fkey 
-- FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

COMMIT;
'''
    
    with open('fix_project_deletion_constraints.sql', 'w', encoding='utf-8') as f:
        f.write(migration_sql)
    
    print("✅ 数据库迁移脚本已保存到 fix_project_deletion_constraints.sql")
    print("⚠️  请谨慎执行此脚本，建议先在测试环境验证")

def create_test_script():
    """创建测试脚本"""
    print("\n🧪 创建项目删除测试脚本...")
    
    test_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目删除功能测试脚本
验证删除项目时是否正确清理所有关联数据
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
from app.models.customer import Company, Contact
from datetime import datetime
from sqlalchemy import text

app = create_app()

def create_test_project():
    """创建测试项目及其关联数据"""
    print("🔧 创建测试项目和关联数据...")
    
    with app.app_context():
        # 获取第一个用户作为测试用户
        user = User.query.first()
        if not user:
            print("❌ 未找到用户，无法创建测试数据")
            return None
        
        # 创建测试项目
        test_project = Project(
            project_name="测试项目-删除功能验证",
            report_time=datetime.now(),
            owner_id=user.id,
            current_stage="lead"
        )
        db.session.add(test_project)
        db.session.flush()  # 获取ID
        
        project_id = test_project.id
        print(f"✅ 创建测试项目，ID: {project_id}")
        
        # 创建测试报价单
        test_quotation = Quotation(
            quotation_number=f"TEST-{project_id}",
            project_id=project_id,
            owner_id=user.id,
            status="draft"
        )
        db.session.add(test_quotation)
        db.session.flush()
        
        print(f"✅ 创建测试报价单，ID: {test_quotation.id}")
        
        # 创建测试跟进记录
        test_action = Action(
            date=datetime.now().date(),
            project_id=project_id,
            communication="测试跟进记录",
            owner_id=user.id
        )
        db.session.add(test_action)
        db.session.flush()
        
        # 创建测试回复
        test_reply = ActionReply(
            action_id=test_action.id,
            content="测试回复",
            owner_id=user.id
        )
        db.session.add(test_reply)
        
        print(f"✅ 创建测试跟进记录，ID: {test_action.id}")
        
        db.session.commit()
        
        return project_id

def count_related_data(project_id):
    """统计项目相关数据"""
    with app.app_context():
        quotations = Quotation.query.filter_by(project_id=project_id).count()
        actions = Action.query.filter_by(project_id=project_id).count()
        
        # 统计回复数量
        action_ids = [a.id for a in Action.query.filter_by(project_id=project_id).all()]
        replies = ActionReply.query.filter(ActionReply.action_id.in_(action_ids)).count() if action_ids else 0
        
        # 统计审批数据
        project_approvals = ApprovalInstance.query.filter_by(
            object_type='project', object_id=project_id
        ).count()
        
        # 统计报价单审批
        quotation_ids = [q.id for q in Quotation.query.filter_by(project_id=project_id).all()]
        quotation_approvals = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'quotation',
            ApprovalInstance.object_id.in_(quotation_ids)
        ).count() if quotation_ids else 0
        
        return {
            'quotations': quotations,
            'actions': actions,
            'replies': replies,
            'project_approvals': project_approvals,
            'quotation_approvals': quotation_approvals
        }

def test_project_deletion():
    """测试项目删除功能"""
    print("=" * 50)
    print("🧪 项目删除功能测试")
    print("=" * 50)
    
    # 创建测试数据
    project_id = create_test_project()
    if not project_id:
        return
    
    # 删除前统计
    print(f"\\n📊 删除前统计 (项目ID: {project_id}):")
    before_counts = count_related_data(project_id)
    for key, value in before_counts.items():
        print(f"   {key}: {value}")
    
    # 执行删除（模拟）
    print(f"\\n🗑️  模拟删除项目 {project_id}...")
    print("⚠️  实际删除需要通过Web界面或直接调用删除函数")
    print(f"   建议访问：http://localhost:8098/project/view/{project_id}")
    print("   然后点击删除按钮测试删除功能")
    
    # 删除后统计（模拟）
    print(f"\\n📊 删除后统计（模拟，实际需要执行删除后再检查）:")
    print("   所有关联数据应该为0")

if __name__ == "__main__":
    test_project_deletion()
'''
    
    with open('test_project_deletion.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    print("✅ 测试脚本已保存到 test_project_deletion.py")
    print("🚀 运行测试: python3 test_project_deletion.py")

def create_summary_report():
    """创建总结报告"""
    print("\n📋 项目删除功能修复总结")
    print("=" * 50)
    
    summary = '''
# 项目删除功能修复总结

## 🔍 发现的问题

1. **关联数据清理不完整**
   - ❌ 项目跟进记录 (Action) 未被删除
   - ❌ 跟进记录回复 (ActionReply) 未被删除  
   - ❌ 项目审批实例 (ApprovalInstance) 未被删除
   - ❌ 报价单审批实例 (ApprovalInstance) 未被删除

2. **数据库外键约束问题**
   - ❌ actions.project_id 设置为 NO ACTION，不会自动清理
   - ❌ project_stage_history.project_id 设置为 NO ACTION
   - ❌ project_members.project_id 设置为 NO ACTION

## ✅ 修复方案

### 1. 应用层修复
- 📝 完善 `app/views/project.py` 中的 `delete_project` 函数
- 📝 完善 `app/views/project.py` 中的 `batch_delete_projects` 函数
- 🔧 添加完整的关联数据清理逻辑

### 2. 数据库层修复  
- 🔧 修改外键约束为 CASCADE 删除（可选）
- ⚠️  谨慎处理 approval_instance 表的约束

### 3. 测试验证
- 🧪 创建测试项目和关联数据
- 🧪 验证删除功能的完整性
- 📊 确认所有关联数据被正确清理

## 📁 生成的文件

1. `improved_project_deletion.py` - 改进的删除函数代码
2. `fix_project_deletion_constraints.sql` - 数据库约束修复脚本
3. `test_project_deletion.py` - 删除功能测试脚本
4. `check_project_deletion_cleanup.py` - 删除状态检查工具

## 🚀 执行步骤

1. **备份数据库**
   ```bash
   pg_dump your_database > backup_before_fix.sql
   ```

2. **应用代码修改**
   - 将 `improved_project_deletion.py` 中的代码应用到 `app/views/project.py`
   - 同样修改 `batch_delete_projects` 函数

3. **执行数据库迁移（可选）**
   ```bash
   psql your_database < fix_project_deletion_constraints.sql
   ```

4. **测试验证**
   ```bash
   python3 test_project_deletion.py
   python3 check_project_deletion_cleanup.py [项目ID]
   ```

## ⚠️  注意事项

1. **数据安全**
   - 在生产环境执行前必须备份数据库
   - 建议先在测试环境验证

2. **CASCADE 删除的影响**
   - 设置 CASCADE 后，删除项目会自动删除所有相关数据
   - 可能影响数据恢复，需要权衡利弊

3. **审批数据处理**
   - 审批实例和记录需要在应用层处理
   - 不建议在数据库层设置 CASCADE

## 📋 完整删除清单

删除项目时应该清理的所有数据：

✅ **已处理（当前代码）**
- 报价单 (Quotation) 
- 项目阶段历史 (ProjectStageHistory)
- 项目评分记录 (ProjectRatingRecord) - CASCADE
- 项目评分系统记录 (ProjectScoringRecord, ProjectTotalScore) - CASCADE

❌ **需要添加（本次修复）**  
- 项目跟进记录 (Action)
- 跟进记录回复 (ActionReply)
- 项目审批实例 (ApprovalInstance)
- 报价单审批实例 (ApprovalInstance)

## 🎯 验证标准

删除项目后，以下查询应该返回0：

```sql
-- 检查项目相关数据是否清理干净
SELECT 'quotations' as table_name, COUNT(*) FROM quotations WHERE project_id = ?
UNION ALL
SELECT 'actions', COUNT(*) FROM actions WHERE project_id = ?  
UNION ALL
SELECT 'approval_instance_project', COUNT(*) FROM approval_instance WHERE object_type='project' AND object_id = ?
UNION ALL
SELECT 'approval_instance_quotation', COUNT(*) FROM approval_instance WHERE object_type='quotation' AND object_id IN (SELECT id FROM quotations WHERE project_id = ?)
```

所有结果都应该为 0。
'''
    
    with open('PROJECT_DELETION_FIX_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("✅ 修复总结报告已保存到 PROJECT_DELETION_FIX_SUMMARY.md")

def main():
    print("=" * 60)
    print("🔧 项目删除功能修复工具")
    print("=" * 60)
    
    # 生成改进的删除函数
    backup_project_deletion_function()
    
    # 生成数据库迁移脚本
    create_database_migration()
    
    # 生成测试脚本
    create_test_script()
    
    # 生成总结报告
    create_summary_report()
    
    print("\n🎉 修复文件生成完成！")
    print("\n📁 生成的文件：")
    print("   1. improved_project_deletion.py - 改进的删除函数")
    print("   2. fix_project_deletion_constraints.sql - 数据库修复脚本")
    print("   3. test_project_deletion.py - 测试脚本")
    print("   4. PROJECT_DELETION_FIX_SUMMARY.md - 修复总结")
    print("   5. check_project_deletion_cleanup.py - 检查工具")
    
    print("\n🚀 后续步骤：")
    print("   1. 备份数据库")
    print("   2. 应用代码修改到 app/views/project.py")
    print("   3. 可选：执行数据库约束修复")
    print("   4. 创建测试项目验证功能")
    print("   5. 使用检查工具验证清理效果")

if __name__ == "__main__":
    main() 