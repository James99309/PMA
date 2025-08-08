#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于最新Git提交更新版本记录

将当前版本更新为基于最新Git提交的版本信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import create_app
from app.extensions import db
from app.models.version_management import VersionRecord, FeatureChange
from app.utils.version_auto_generator import version_generator
from datetime import datetime, timezone
import subprocess
import dateutil.parser

def get_git_info():
    """获取Git提交信息"""
    try:
        # 获取最新提交的详细信息
        result = subprocess.run([
            'git', 'log', '-1', 
            '--pretty=format:%H|%h|%ad|%s', 
            '--date=iso'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) >= 4:
                return {
                    'full_hash': parts[0],
                    'short_hash': parts[1],
                    'date': parts[2],
                    'message': parts[3]
                }
    except Exception as e:
        print(f"获取Git信息失败: {e}")
    return None

def update_current_version_to_git():
    """更新当前版本为基于最新Git提交的版本"""
    print("🔄 基于最新Git提交更新版本记录...")
    
    app = create_app()
    with app.app_context():
        try:
            # 1. 获取最新Git信息
            git_info = get_git_info()
            if not git_info:
                print("❌ 无法获取Git信息")
                return False
                
            print(f"📋 最新Git提交信息:")
            print(f"   提交哈希: {git_info['short_hash']}")
            print(f"   提交时间: {git_info['date']}")
            print(f"   提交信息: {git_info['message']}")
            
            # 2. 获取当前版本记录
            current_version = VersionRecord.get_current_version()
            if not current_version:
                print("❌ 没有找到当前版本记录")
                return False
                
            print(f"📦 当前版本记录:")
            print(f"   版本号: {current_version.version_number}")
            print(f"   发布时间: {current_version.release_date}")
            print(f"   Git提交: {current_version.git_commit or '未设置'}")
            
            # 3. 检查是否需要更新
            needs_update = False
            if current_version.git_commit != git_info['short_hash']:
                print(f"🔄 Git提交已变更，需要更新版本记录")
                needs_update = True
            else:
                print(f"✅ 版本记录已是最新的Git提交")
            
            # 解析Git日期并处理时区
            from datetime import datetime
            import dateutil.parser
            git_date = dateutil.parser.parse(git_info['date'])
            
            # 将数据库时间转换为带时区的时间进行比较
            if current_version.release_date.tzinfo is None:
                # 数据库时间是naive，假设是UTC时间
                from datetime import timezone
                db_date = current_version.release_date.replace(tzinfo=timezone.utc)
            else:
                db_date = current_version.release_date
                
            # 转换为同一时区进行比较
            git_date_utc = git_date.astimezone(timezone.utc) if git_date.tzinfo else git_date
            db_date_utc = db_date.astimezone(timezone.utc) if db_date.tzinfo else db_date
            
            time_diff = abs((db_date_utc - git_date_utc).total_seconds())
            if time_diff > 3600:  # 超过1小时差异
                print(f"🕐 发布时间与Git提交时间不符，需要更新 (相差 {time_diff/3600:.1f} 小时)")
                needs_update = True
                
            if not needs_update:
                print("✅ 版本记录无需更新")
                return True
            
            # 4. 更新版本记录
            print(f"🔧 更新版本记录...")
            
            # 更新基本信息
            current_version.git_commit = git_info['short_hash']
            current_version.release_date = git_date
            
            # 更新描述，包含最新提交信息
            base_description = "系统当前运行版本，包含完整的项目管理、客户管理、报价管理、产品管理等功能。"
            current_version.description = f"{base_description}\n\n最新更新：{git_info['message']}"
            
            # 5. 检查是否需要添加基于提交信息的功能变更
            existing_change = FeatureChange.query.filter_by(
                version_id=current_version.id,
                git_commits=git_info['short_hash']
            ).first()
            
            if not existing_change:
                print(f"📝 添加基于Git提交的功能变更记录...")
                
                # 根据提交信息分析变更类型
                commit_msg_lower = git_info['message'].lower()
                if '修改' in git_info['message'] or '修复' in git_info['message'] or 'fix' in commit_msg_lower:
                    change_type = 'fix'
                    type_name = '修复'
                elif '新增' in git_info['message'] or '添加' in git_info['message'] or 'feat' in commit_msg_lower:
                    change_type = 'feature'
                    type_name = '新功能'
                elif '优化' in git_info['message'] or '改进' in git_info['message'] or '升级' in git_info['message']:
                    change_type = 'improvement'
                    type_name = '改进'
                else:
                    change_type = 'improvement'
                    type_name = '更新'
                
                # 创建功能变更记录
                new_change = FeatureChange(
                    version_id=current_version.id,
                    change_type=change_type,
                    module_name='system',
                    title=f"{type_name}: {git_info['message'][:50]}{'...' if len(git_info['message']) > 50 else ''}",
                    description=git_info['message'],
                    priority='medium',
                    impact_level='minor',
                    git_commits=git_info['short_hash'],
                    developer_name='开发团队',
                    test_status='passed',
                    created_at=git_date,
                    completed_at=git_date
                )
                
                db.session.add(new_change)
                
                # 更新版本统计
                if change_type == 'feature':
                    current_version.total_features += 1
                elif change_type == 'fix':
                    current_version.total_fixes += 1
                else:
                    current_version.total_improvements += 1
                
                print(f"   ✅ 添加{type_name}记录: {new_change.title}")
            
            # 6. 提交更改
            db.session.commit()
            
            # 7. 验证更新结果
            print(f"\n📊 更新后的版本信息:")
            updated_version = VersionRecord.get_current_version()
            print(f"   版本号: {updated_version.version_number}")
            print(f"   发布时间: {updated_version.release_date}")
            print(f"   Git提交: {updated_version.git_commit}")
            print(f"   新功能: {updated_version.total_features}")
            print(f"   修复: {updated_version.total_fixes}")
            print(f"   改进: {updated_version.total_improvements}")
            
            change_count = FeatureChange.query.filter_by(version_id=updated_version.id).count()
            print(f"   变更记录数: {change_count}")
            
            print(f"\n🎉 版本记录更新完成！现在版本信息将显示最新的Git提交时间和信息。")
            return True
            
        except Exception as e:
            print(f"\n❌ 更新失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("基于Git提交更新版本记录")
    print("=" * 50)
    
    success = update_current_version_to_git()
    
    if success:
        print("\n✅ 更新成功，版本管理界面现在将显示最新的Git信息")
        print("💡 建议刷新版本管理页面查看更新后的信息")
        sys.exit(0)
    else:
        print("\n❌ 更新失败")
        sys.exit(1)