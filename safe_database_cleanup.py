#!/usr/bin/env python3
"""
安全的数据库数据清理脚本
功能：
1. 清空未报备项目的报备日期（只有授权编号或申请中状态的项目才保留报备日期）
2. 将签约项目设置为锁定状态，并添加锁定理由

特点：
- 详细的预览和确认
- 事务回滚支持
- 详细的执行日志
- 安全检查

使用方法：
python3 safe_database_cleanup.py [--preview-only] [--force]

参数说明：
--preview-only: 仅预览，不执行更新
--force: 跳过确认提示，直接执行
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def preview_report_time_cleanup():
    """预览需要清空报备日期的项目"""
    from app.models.project import Project
    
    # 查找所有有报备日期的项目
    projects_with_report_time = Project.query.filter(
        Project.report_time.isnot(None)
    ).all()
    
    # 分类项目
    projects_to_clear = []
    projects_to_keep = []
    
    for project in projects_with_report_time:
        # 保留报备日期的条件：仅当有授权编号时才保留
        should_keep_report_time = (
            project.authorization_code and len(project.authorization_code.strip()) > 0
        )
        
        if should_keep_report_time:
            projects_to_keep.append(project)
        else:
            projects_to_clear.append(project)
    
    return projects_to_clear, projects_to_keep

def preview_signed_project_locking():
    """预览需要锁定的签约项目"""
    from app.models.project import Project
    
    signed_unlocked_projects = Project.query.filter(
        Project.current_stage == 'signed',
        Project.is_locked == False
    ).all()
    
    return signed_unlocked_projects

def execute_report_time_cleanup(projects_to_clear, db):
    """执行清空报备日期操作"""
    updated_count = 0
    
    for project in projects_to_clear:
        print(f"  清空项目: {project.project_name[:50]} (ID: {project.id})")
        project.report_time = None
        updated_count += 1
    
    return updated_count

def execute_signed_project_locking(signed_projects, admin_user, db):
    """执行签约项目锁定操作"""
    updated_count = 0
    current_time = datetime.now()
    
    for project in signed_projects:
        print(f"  锁定项目: {project.project_name[:50]} (ID: {project.id})")
        project.is_locked = True
        project.locked_reason = '项目已签约，自动锁定'
        project.locked_by = admin_user.id
        project.locked_at = current_time
        updated_count += 1
    
    return updated_count

def main():
    parser = argparse.ArgumentParser(description='安全的数据库数据清理脚本')
    parser.add_argument('--preview-only', action='store_true', help='仅预览，不执行更新')
    parser.add_argument('--force', action='store_true', help='跳过确认提示，直接执行')
    
    args = parser.parse_args()
    
    try:
        from app import create_app, db
        from app.models.project import Project
        from app.models.user import User
        
        print("=" * 80)
        print("🔧 安全的数据库数据清理脚本")
        print("=" * 80)
        print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 模式: {'预览模式' if args.preview_only else '执行模式'}")
        print("=" * 80)
        
        app = create_app()
        with app.app_context():
            # 获取管理员用户
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user and not args.preview_only:
                print("❌ 未找到管理员用户，无法执行锁定操作")
                return
            
            if admin_user:
                print(f"👤 管理员用户: {admin_user.username} (ID: {admin_user.id})")
            print()
            
            # ====================================
            # 任务1: 分析报备日期清理
            # ====================================
            print("📋 任务1: 分析报备日期清理需求")
            print("-" * 50)
            
            projects_to_clear, projects_to_keep = preview_report_time_cleanup()
            
            print(f"📊 统计结果:")
            print(f"  - 总共有报备日期的项目: {len(projects_to_clear) + len(projects_to_keep)} 个")
            print(f"  - 需要保留报备日期: {len(projects_to_keep)} 个")
            print(f"  - 需要清空报备日期: {len(projects_to_clear)} 个")
            
            if projects_to_clear:
                print(f"\\n🗑️  需要清空报备日期的项目 (前15个):")
                for i, project in enumerate(projects_to_clear[:15], 1):
                    auth_status = project.authorization_status or "无"
                    auth_code = project.authorization_code or "无"
                    report_date = project.report_time.strftime('%Y-%m-%d') if project.report_time else "无"
                    print(f"  {i:2d}. {project.project_name[:35]:<35} | 报备日期: {report_date} | 授权: {auth_code[:12]:<12} | 状态: {auth_status}")
                
                if len(projects_to_clear) > 15:
                    print(f"     ... 还有 {len(projects_to_clear) - 15} 个项目")
            
            if projects_to_keep:
                print(f"\\n✅ 保留报备日期的项目 (前10个):")
                for i, project in enumerate(projects_to_keep[:10], 1):
                    auth_status = project.authorization_status or "无"
                    auth_code = project.authorization_code or "无"
                    report_date = project.report_time.strftime('%Y-%m-%d') if project.report_time else "无"
                    reason = "有授权编号"
                    print(f"  {i:2d}. {project.project_name[:35]:<35} | 报备日期: {report_date} | 原因: {reason}")
            
            print()
            
            # ====================================
            # 任务2: 分析签约项目锁定
            # ====================================
            print("🔒 任务2: 分析签约项目锁定需求")
            print("-" * 50)
            
            signed_unlocked_projects = preview_signed_project_locking()
            
            print(f"📊 统计结果:")
            print(f"  - 签约但未锁定的项目: {len(signed_unlocked_projects)} 个")
            
            if signed_unlocked_projects:
                print(f"\\n🔒 需要锁定的签约项目 (前15个):")
                for i, project in enumerate(signed_unlocked_projects[:15], 1):
                    auth_code = project.authorization_code or "无授权编号"
                    print(f"  {i:2d}. {project.project_name[:35]:<35} | 授权编号: {auth_code}")
                
                if len(signed_unlocked_projects) > 15:
                    print(f"     ... 还有 {len(signed_unlocked_projects) - 15} 个项目")
            
            print()
            
            # ====================================
            # 执行操作
            # ====================================
            if args.preview_only:
                print("👁️  预览模式完成，未执行任何更新操作")
                return
            
            if not projects_to_clear and not signed_unlocked_projects:
                print("✅ 无需执行任何清理操作")
                return
            
            print("⚠️  准备执行数据库更新操作")
            print("-" * 50)
            
            if not args.force:
                print("即将执行以下操作:")
                if projects_to_clear:
                    print(f"  1. 清空 {len(projects_to_clear)} 个项目的报备日期")
                if signed_unlocked_projects:
                    print(f"  2. 锁定 {len(signed_unlocked_projects)} 个签约项目")
                print()
                
                confirm = input("确认执行上述操作吗? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("❌ 用户取消操作")
                    return
            
            # 开始执行更新
            print("🚀 开始执行数据库更新...")
            
            try:
                
                # 执行报备日期清理
                if projects_to_clear:
                    print(f"\\n📝 正在清空 {len(projects_to_clear)} 个项目的报备日期:")
                    cleared_count = execute_report_time_cleanup(projects_to_clear, db)
                    print(f"✅ 已清空 {cleared_count} 个项目的报备日期")
                
                # 执行签约项目锁定
                if signed_unlocked_projects:
                    print(f"\\n🔒 正在锁定 {len(signed_unlocked_projects)} 个签约项目:")
                    locked_count = execute_signed_project_locking(signed_unlocked_projects, admin_user, db)
                    print(f"✅ 已锁定 {locked_count} 个签约项目")
                
                # 提交事务
                db.session.commit()
                print("\\n💾 所有更改已提交到数据库")
                
            except Exception as e:
                db.session.rollback()
                print(f"\\n❌ 执行失败，已回滚所有更改: {e}")
                raise
            
            # ====================================
            # 最终验证
            # ====================================
            print("\\n" + "=" * 80)
            print("📋 执行结果验证")
            print("=" * 80)
            
            # 重新统计
            final_projects_to_clear, final_projects_to_keep = preview_report_time_cleanup()
            final_signed_unlocked = preview_signed_project_locking()
            
            print(f"📊 最终统计:")
            print(f"  - 当前有报备日期的项目: {len(final_projects_to_clear) + len(final_projects_to_keep)} 个")
            print(f"  - 仍需清空报备日期的项目: {len(final_projects_to_clear)} 个")
            print(f"  - 仍未锁定的签约项目: {len(final_signed_unlocked)} 个")
            
            if len(final_projects_to_clear) == 0 and len(final_signed_unlocked) == 0:
                print("\\n🎉 数据清理完成！所有问题已修复。")
            else:
                print("\\n⚠️  仍有部分数据需要处理，请检查。")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在项目根目录下运行此脚本")
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()