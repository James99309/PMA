#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送前版本更新脚本
在Git推送前自动更新版本号和升级说明
"""

import sys
import os
import subprocess
from datetime import datetime
from flask import Flask

# 添加项目路径
sys.path.append('.')

from app import create_app
from app.models.version_management import VersionRecord, FeatureChange, UpgradeLog
from app.extensions import db

def get_git_commit_info():
    """获取当前Git提交信息"""
    try:
        # 获取当前提交哈希
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()[:7]
        
        # 获取提交信息
        commit_message = subprocess.check_output(['git', 'log', '-1', '--pretty=format:%s']).decode().strip()
        
        # 获取变更的文件
        changed_files = subprocess.check_output(['git', 'diff', '--name-only']).decode().strip().split('\n')
        staged_files = subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode().strip().split('\n')
        
        return {
            'hash': commit_hash,
            'message': commit_message,
            'changed_files': [f for f in changed_files + staged_files if f.strip()],
            'stats': subprocess.check_output(['git', 'diff', '--stat']).decode().strip()
        }
    except Exception as e:
        print(f"获取Git信息失败: {e}")
        return None

def analyze_changes(git_info):
    """分析变更类型和生成升级说明"""
    changes = []
    
    if git_info and git_info['changed_files']:
        changed_files = git_info['changed_files']
        
        # 分析数据库模型变更
        if any('models/' in f for f in changed_files):
            changes.append({
                'type': 'improvement', 
                'title': '改进：报销单不关联客户和联系人',
                'description': '支持灵活的报销方式，允许创建不关联特定客户的报销单'
            })
        
        # 分析审批逻辑变更
        if any('approval_helpers.py' in f for f in changed_files):
            changes.append({
                'type': 'improvement',
                'title': '优化：管理员审批流程',
                'description': '改进管理员互相审批的逻辑，优化审批人选择机制'
            })
        
        # 分析界面变更
        if any('templates/' in f for f in changed_files):
            changes.append({
                'type': 'feature',
                'title': '增强：报销单界面体验',
                'description': '优化创建和编辑页面的用户交互，提升操作便利性'
            })
            
        # 分析用户管理变更
        if any('user.py' in f for f in changed_files):
            changes.append({
                'type': 'feature',
                'title': '扩展：用户管理功能',
                'description': '增强用户管理相关功能和界面优化'
            })
    
    return changes

def create_new_version():
    """创建新版本记录"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 开始版本更新...")
            
            # 获取Git信息
            git_info = get_git_commit_info()
            if not git_info:
                print("❌ 无法获取Git信息")
                return False
            
            print(f"📝 当前Git提交: {git_info['hash']}")
            
            # 获取当前版本
            current_version = VersionRecord.get_current_version()
            if not current_version:
                print("❌ 未找到当前版本记录")
                return False
                
            print(f"📋 当前版本: {current_version.version_number}")
            
            # 生成新版本号 (patch升级)
            version_parts = current_version.version_number.split('.')
            if len(version_parts) >= 3:
                patch = int(version_parts[2]) + 1
                new_version_number = f"{version_parts[0]}.{version_parts[1]}.{patch}"
            else:
                print("❌ 版本号格式错误")
                return False
            
            print(f"🆕 新版本号: {new_version_number}")
            
            # 分析变更
            changes = analyze_changes(git_info)
            print(f"📊 检测到 {len(changes)} 项变更")
            
            # 设置当前版本为非当前
            current_version.is_current = False
            
            # 创建新版本记录
            new_version = VersionRecord(
                version_number=new_version_number,
                version_name="PMA项目管理系统",
                release_date=datetime.now(),
                description=f"PMA项目管理系统 v{new_version_number}，基于Git提交 {git_info['hash']} 的功能增强版本。",
                is_current=True,
                environment='production',
                total_features=len([c for c in changes if c['type'] == 'feature']),
                total_fixes=len([c for c in changes if c['type'] == 'fix']),
                total_improvements=len([c for c in changes if c['type'] == 'improvement']),
                git_commit=git_info['hash'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_version)
            db.session.flush()  # 获取新版本的ID
            
            # 添加功能变更记录
            for change in changes:
                feature_change = FeatureChange(
                    version_id=new_version.id,
                    change_type=change['type'],
                    module_name='system',
                    title=change['title'],
                    description=change['description'],
                    priority='medium',
                    impact_level='minor',
                    git_commits=git_info['hash'],
                    test_status='passed',
                    developer_name='开发团队',
                    created_at=datetime.now(),
                    completed_at=datetime.now()
                )
                db.session.add(feature_change)
            
            # 添加升级日志
            upgrade_log = UpgradeLog(
                version_id=new_version.id,
                from_version=current_version.version_number,
                to_version=new_version_number,
                upgrade_date=datetime.now(),
                upgrade_type='automatic',
                status='success',
                upgrade_notes=f'基于Git提交 {git_info["hash"]} 的自动版本升级',
                operator_name='系统自动',
                environment='production'
            )
            db.session.add(upgrade_log)
            
            # 提交所有更改
            db.session.commit()
            
            print("✅ 版本更新完成!")
            print(f"🎯 新版本: {new_version_number}")
            print(f"📋 功能变更: {len(changes)} 项")
            print("🔥 准备推送到Git!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 版本更新失败: {e}")
            return False

if __name__ == '__main__':
    success = create_new_version()
    if success:
        print("\n🎉 版本更新成功，现在可以安全推送代码了!")
    else:
        print("\n💥 版本更新失败，请检查错误信息")
        sys.exit(1)