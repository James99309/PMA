#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版本时间戳

将版本记录的时间修正为Git提交的真实时间
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import subprocess
from datetime import datetime
from flask import Flask
from app import create_app
from app.extensions import db
from app.models.version_management import VersionRecord
import dateutil.parser

def get_git_commit_time(commit_hash):
    """获取指定Git提交的真实时间"""
    try:
        result = subprocess.run([
            'git', 'show', '-s', '--format=%ad', '--date=iso', commit_hash
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return dateutil.parser.parse(result.stdout.strip())
        return None
    except Exception as e:
        print(f"获取Git提交时间失败: {e}")
        return None

def fix_version_timestamp():
    """修复版本记录的时间戳"""
    print("🔧 修复版本记录时间戳...")
    
    app = create_app()
    with app.app_context():
        try:
            # 获取当前版本记录
            current_version = VersionRecord.get_current_version()
            if not current_version:
                print("❌ 没有找到当前版本记录")
                return False
                
            print(f"\n📦 当前版本记录:")
            print(f"   版本号: {current_version.version_number}")
            print(f"   记录时间: {current_version.release_date}")
            print(f"   Git提交: {current_version.git_commit}")
            
            if not current_version.git_commit:
                print("❌ 版本记录没有Git提交信息")
                return False
                
            # 获取Git提交的真实时间
            git_time = get_git_commit_time(current_version.git_commit)
            if not git_time:
                print("❌ 无法获取Git提交的真实时间")
                return False
                
            print(f"\n🕐 Git提交的真实时间: {git_time}")
            print(f"🕐 当前记录时间: {current_version.release_date}")
            
            # 比较时间差异
            time_diff = abs((current_version.release_date.replace(tzinfo=git_time.tzinfo) - git_time).total_seconds())
            print(f"⏱️  时间差异: {time_diff/3600:.1f} 小时")
            
            if time_diff < 300:  # 小于5分钟，认为是正确的
                print("✅ 时间差异很小，无需修正")
                return True
            
            # 修正时间
            print(f"\n🔄 修正版本记录时间...")
            print(f"   从: {current_version.release_date}")
            print(f"   到: {git_time}")
            
            current_version.release_date = git_time
            db.session.commit()
            
            # 验证修正结果
            updated_version = VersionRecord.get_current_version()
            print(f"\n✅ 时间修正完成:")
            print(f"   版本号: {updated_version.version_number}")
            print(f"   修正后时间: {updated_version.release_date}")
            print(f"   Git提交: {updated_version.git_commit}")
            
            # 显示最终界面效果
            print(f"\n🖥️ 界面显示效果:")
            print(f"   v{updated_version.version_number} [当前版本]")
            print(f"   📅 {updated_version.release_date.strftime('%Y年%m月%d日 %H:%M')}")
            print(f"   🔧 {updated_version.git_commit}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 修正失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("版本时间戳修正工具")
    print("=" * 50)
    
    success = fix_version_timestamp()
    
    if success:
        print("\n✅ 时间戳修正成功")
        print("💡 现在版本记录使用Git提交的真实时间")
        sys.exit(0)
    else:
        print("\n❌ 时间戳修正失败")
        sys.exit(1)