#!/usr/bin/env python3
"""
数据库数据清理脚本
功能：
1. 清空未报备项目的报备日期（只有授权编号或申请中状态的项目才保留报备日期）
2. 将签约项目设置为锁定状态，并添加锁定理由

使用方法：
python3 database_cleanup_script.py

注意：
- 执行前请确保数据库已备份
- 建议先在测试环境运行
- 脚本会显示详细的执行结果
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        from app import create_app, db
        from app.models.project import Project
        from app.models.user import User
        
        print("=" * 60)
        print("🔧 数据库数据清理脚本")
        print("=" * 60)
        
        app = create_app()
        with app.app_context():
            # 获取管理员用户用于锁定操作
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                print("❌ 未找到管理员用户，无法执行锁定操作")
                return
            
            print(f"📝 使用管理员用户: {admin_user.username} (ID: {admin_user.id})")
            print()
            
            # ====================================
            # 任务1: 清空未报备项目的报备日期
            # ====================================
            print("🔍 任务1: 检查并清空未报备项目的报备日期")
            print("-" * 40)
            
            # 查找所有有报备日期的项目
            projects_with_report_time = Project.query.filter(
                Project.report_time.isnot(None)
            ).all()
            
            print(f"📊 找到 {len(projects_with_report_time)} 个有报备日期的项目")
            
            # 统计需要清空报备日期的项目
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
            
            print(f"✅ 需要保留报备日期的项目: {len(projects_to_keep)} 个")
            print(f"🗑️  需要清空报备日期的项目: {len(projects_to_clear)} 个")
            
            if projects_to_clear:
                print()
                print("📋 将要清空报备日期的项目列表:")
                for i, project in enumerate(projects_to_clear[:10], 1):  # 只显示前10个
                    auth_status = project.authorization_status or "无"
                    auth_code = project.authorization_code or "无"
                    print(f"  {i:2d}. {project.project_name[:30]:<30} | 授权编号: {auth_code:<15} | 状态: {auth_status}")
                
                if len(projects_to_clear) > 10:
                    print(f"     ... 还有 {len(projects_to_clear) - 10} 个项目")
                
                # 执行清空操作
                print()
                confirm = input("⚠️  确认清空这些项目的报备日期吗? (y/N): ").strip().lower()
                if confirm == 'y':
                    updated_count = 0
                    for project in projects_to_clear:
                        project.report_time = None
                        updated_count += 1
                    
                    db.session.commit()
                    print(f"✅ 已清空 {updated_count} 个项目的报备日期")
                else:
                    print("❌ 用户取消操作")
            else:
                print("✅ 无需清空任何项目的报备日期")
            
            print()
            
            # ====================================
            # 任务2: 锁定签约项目
            # ====================================
            print("🔒 任务2: 检查并锁定签约项目") 
            print("-" * 40)
            
            # 查找所有签约但未锁定的项目
            signed_unlocked_projects = Project.query.filter(
                Project.current_stage == 'signed',
                Project.is_locked == False
            ).all()
            
            print(f"📊 找到 {len(signed_unlocked_projects)} 个签约但未锁定的项目")
            
            if signed_unlocked_projects:
                print()
                print("📋 将要锁定的签约项目列表:")
                for i, project in enumerate(signed_unlocked_projects[:10], 1):  # 只显示前10个
                    auth_code = project.authorization_code or "无授权编号"
                    print(f"  {i:2d}. {project.project_name[:30]:<30} | 授权编号: {auth_code}")
                
                if len(signed_unlocked_projects) > 10:
                    print(f"     ... 还有 {len(signed_unlocked_projects) - 10} 个项目")
                
                # 执行锁定操作
                print()
                confirm = input("⚠️  确认锁定这些签约项目吗? (y/N): ").strip().lower()
                if confirm == 'y':
                    updated_count = 0
                    current_time = datetime.now()
                    
                    for project in signed_unlocked_projects:
                        project.is_locked = True
                        project.locked_reason = '项目已签约，自动锁定'
                        project.locked_by = admin_user.id
                        project.locked_at = current_time
                        updated_count += 1
                    
                    db.session.commit()
                    print(f"✅ 已锁定 {updated_count} 个签约项目")
                else:
                    print("❌ 用户取消操作")
            else:
                print("✅ 所有签约项目均已锁定")
            
            print()
            
            # ====================================
            # 总结
            # ====================================
            print("=" * 60)
            print("📋 数据清理完成总结")
            print("=" * 60)
            
            # 重新统计最终结果
            final_projects_with_report_time = Project.query.filter(
                Project.report_time.isnot(None)
            ).count()
            
            final_signed_locked_projects = Project.query.filter(
                Project.current_stage == 'signed',
                Project.is_locked == True
            ).count()
            
            print(f"📊 当前有报备日期的项目数量: {final_projects_with_report_time}")
            print(f"🔒 当前已锁定的签约项目数量: {final_signed_locked_projects}")
            print()
            print("🎉 数据清理脚本执行完成！")
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保在项目根目录下运行此脚本")
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()