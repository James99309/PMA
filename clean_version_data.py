#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理版本管理数据

删除不正确的演示数据，只保留真实基于Git的记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import create_app
from app.extensions import db
from app.models.version_management import VersionRecord, FeatureChange, UpgradeLog

def clean_demo_data():
    """清理演示数据，只保留基于Git的真实记录"""
    print("🧹 清理版本管理演示数据...")
    
    app = create_app()
    with app.app_context():
        try:
            # 1. 查看当前数据
            print("\n📋 当前数据库记录:")
            changes = FeatureChange.query.all()
            for change in changes:
                print(f"  - {change.title} (Git: {change.git_commits or '未设置'}, 时间: {change.created_at})")
            
            # 2. 删除没有Git提交记录的功能变更(演示数据)
            demo_changes = FeatureChange.query.filter(
                (FeatureChange.git_commits == None) | (FeatureChange.git_commits == '')
            ).all()
            
            print(f"\n🗑️ 发现 {len(demo_changes)} 个演示数据记录:")
            for change in demo_changes:
                print(f"  - 删除: {change.title} (创建时间: {change.created_at})")
                db.session.delete(change)
            
            # 3. 更新版本统计 - 重新计算基于真实记录
            current_version = VersionRecord.get_current_version()
            if current_version:
                real_changes = FeatureChange.query.filter_by(version_id=current_version.id).all()
                
                # 重新统计
                features = len([c for c in real_changes if c.change_type == 'feature'])
                fixes = len([c for c in real_changes if c.change_type == 'fix'])
                improvements = len([c for c in real_changes if c.change_type == 'improvement'])
                
                current_version.total_features = features
                current_version.total_fixes = fixes
                current_version.total_improvements = improvements
                
                print(f"\n📊 更新版本统计:")
                print(f"  - 新功能: {features}")
                print(f"  - 修复: {fixes}")
                print(f"  - 改进: {improvements}")
            
            # 4. 提交更改
            db.session.commit()
            
            # 5. 验证清理结果
            print(f"\n✅ 清理后的记录:")
            remaining_changes = FeatureChange.query.all()
            if remaining_changes:
                for change in remaining_changes:
                    git_info = f"Git: {change.git_commits}" if change.git_commits else "无Git记录"
                    print(f"  - {change.title} ({git_info})")
            else:
                print("  - 没有功能变更记录")
            
            # 6. 显示当前版本状态
            final_version = VersionRecord.get_current_version()
            if final_version:
                print(f"\n📦 当前版本状态:")
                print(f"  - 版本号: {final_version.version_number}")
                print(f"  - Git提交: {final_version.git_commit}")
                print(f"  - 发布时间: {final_version.release_date}")
                print(f"  - 功能统计: {final_version.total_features}功能 + {final_version.total_fixes}修复 + {final_version.total_improvements}改进")
            
            print(f"\n🎉 数据清理完成！现在版本管理只显示基于真实Git推送的记录。")
            return True
            
        except Exception as e:
            print(f"\n❌ 清理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("版本管理数据清理工具")
    print("=" * 50)
    
    success = clean_demo_data()
    
    if success:
        print("\n✅ 清理成功")
        print("💡 现在版本管理界面只会显示真实基于Git推送的功能记录")
        sys.exit(0)
    else:
        print("\n❌ 清理失败")
        sys.exit(1)