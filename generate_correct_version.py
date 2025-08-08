#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成正确的版本号

基于Git提交历史分析并生成准确的版本信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import subprocess
from datetime import datetime
from flask import Flask
from app import create_app
from app.extensions import db
from app.models.version_management import VersionRecord, FeatureChange
from app.utils.version_auto_generator import version_generator

def analyze_git_history():
    """分析Git历史，确定合适的版本号"""
    print("🔍 分析Git提交历史...")
    
    try:
        # 获取Git提交总数
        result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            commit_count = int(result.stdout.strip())
            print(f"📊 总提交数: {commit_count}")
        else:
            commit_count = 0
            
        # 获取最近的提交信息
        result = subprocess.run(['git', 'log', '-10', '--pretty=format:%h|%ad|%s', '--date=short'], 
                              capture_output=True, text=True, timeout=10)
        
        commits = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 3:
                        commits.append({
                            'hash': parts[0],
                            'date': parts[1], 
                            'message': parts[2]
                        })
        
        print(f"📋 最近10个提交:")
        for i, commit in enumerate(commits[:10]):
            print(f"   {i+1}. {commit['hash']} - {commit['message']} ({commit['date']})")
            
        # 分析提交类型分布
        feature_count = 0
        fix_count = 0
        improvement_count = 0
        
        for commit in commits:
            msg = commit['message'].lower()
            if any(keyword in msg for keyword in ['新增', '添加', 'feat', '功能', '实现']):
                feature_count += 1
            elif any(keyword in msg for keyword in ['修复', 'fix', '问题', '错误']):
                fix_count += 1
            elif any(keyword in msg for keyword in ['优化', '改进', '升级', '更新']):
                improvement_count += 1
                
        print(f"\n📈 最近提交分析:")
        print(f"   功能开发: {feature_count} 个")
        print(f"   问题修复: {fix_count} 个") 
        print(f"   优化改进: {improvement_count} 个")
        
        # 基于分析建议版本号
        major = 1  # 主版本号
        
        # 基于重大功能确定次版本号
        if commit_count > 100:
            minor = 3  # 大量提交，可能有重大功能
        elif commit_count > 50:
            minor = 2  # 中等提交量
        else:
            minor = 1  # 较少提交
            
        # 基于最近提交确定补丁版本号
        patch = fix_count + improvement_count
        
        suggested_version = f"{major}.{minor}.{patch}"
        print(f"\n💡 建议版本号: {suggested_version}")
        
        return suggested_version, commits[0] if commits else None, {
            'total_commits': commit_count,
            'features': feature_count,
            'fixes': fix_count,
            'improvements': improvement_count
        }
        
    except Exception as e:
        print(f"❌ Git分析失败: {str(e)}")
        return "1.2.1", None, {}

def generate_correct_version():
    """生成并设置正确的版本信息"""
    print("🚀 生成正确的版本信息...")
    
    app = create_app()
    with app.app_context():
        try:
            # 1. 分析Git历史
            suggested_version, latest_commit, stats = analyze_git_history()
            
            # 2. 检查当前数据库版本
            current_version = VersionRecord.get_current_version()
            print(f"\n📦 当前数据库版本: {current_version.version_number if current_version else '无'}")
            
            # 3. 使用版本生成器生成新版本号
            print(f"\n🔧 使用版本生成器...")
            if current_version:
                # 基于当前版本生成下一个版本
                next_version = version_generator.generate_next_version('patch')
                print(f"   自动生成的下一版本: {next_version}")
            else:
                next_version = suggested_version
                
            # 4. 创建或更新版本记录
            final_version = suggested_version  # 使用基于Git分析的版本号
            
            if current_version:
                # 更新现有版本
                print(f"\n📝 更新版本从 {current_version.version_number} 到 {final_version}")
                current_version.version_number = final_version
                
                if latest_commit:
                    current_version.git_commit = latest_commit['hash']
                    current_version.release_date = datetime.now()
                    
                # 更新描述
                current_version.description = f"PMA项目管理系统 v{final_version}，基于{stats['total_commits']}个Git提交的稳定版本。"
                
            else:
                # 创建新版本记录
                print(f"\n📦 创建新版本记录: {final_version}")
                current_version = VersionRecord(
                    version_number=final_version,
                    version_name="PMA项目管理系统",
                    description=f"PMA项目管理系统 v{final_version}，基于{stats['total_commits']}个Git提交的稳定版本。",
                    git_commit=latest_commit['hash'] if latest_commit else None,
                    is_current=True,
                    environment='production',
                    total_features=stats.get('features', 0),
                    total_fixes=stats.get('fixes', 0),
                    total_improvements=stats.get('improvements', 0),
                    release_date=datetime.now()
                )
                
                # 确保只有一个当前版本
                VersionRecord.query.update({'is_current': False})
                db.session.add(current_version)
            
            # 5. 提交更改
            db.session.commit()
            
            # 6. 验证结果
            final_version_record = VersionRecord.get_current_version()
            print(f"\n✅ 版本信息已更新:")
            print(f"   版本号: {final_version_record.version_number}")
            print(f"   版本名称: {final_version_record.version_name}")
            print(f"   Git提交: {final_version_record.git_commit}")
            print(f"   发布时间: {final_version_record.release_date}")
            print(f"   功能统计: {final_version_record.total_features}功能 + {final_version_record.total_fixes}修复 + {final_version_record.total_improvements}改进")
            
            return final_version_record
            
        except Exception as e:
            print(f"\n❌ 版本生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return None

if __name__ == "__main__":
    print("PMA版本号生成工具")
    print("=" * 50)
    
    version_record = generate_correct_version()
    
    if version_record:
        print(f"\n🎉 正确的版本号已生成: {version_record.version_number}")
        print("💡 现在版本管理界面将显示准确的版本信息")
        sys.exit(0)
    else:
        print("\n❌ 版本号生成失败")
        sys.exit(1)