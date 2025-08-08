#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本管理数据初始化脚本

确保版本管理系统有基础数据可显示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import create_app
from app.extensions import db
from app.models.version_management import VersionRecord, FeatureChange
from app.utils.version_management_init import initialize_version_management, add_version_with_features
from datetime import datetime

def init_sample_data():
    """初始化示例数据"""
    print("🚀 初始化版本管理示例数据...")
    
    app = create_app()
    with app.app_context():
        try:
            # 1. 确保有当前版本记录
            current_version = VersionRecord.get_current_version()
            if not current_version:
                print("📦 创建当前版本记录...")
                success = initialize_version_management()
                if success:
                    current_version = VersionRecord.get_current_version()
                    print(f"✅ 创建当前版本: {current_version.version_number}")
                else:
                    print("❌ 创建当前版本失败")
                    return False
            else:
                print(f"✅ 当前版本已存在: {current_version.version_number}")
            
            # 2. 检查是否有功能变更记录
            change_count = FeatureChange.query.filter_by(version_id=current_version.id).count()
            print(f"📊 当前版本已有 {change_count} 个变更记录")
            
            if change_count == 0:
                print("📝 添加示例功能变更记录...")
                
                # 添加示例功能变更
                sample_changes = [
                    {
                        'change_type': 'feature',
                        'module_name': 'version',
                        'title': '版本管理系统',
                        'description': '新增完整的版本管理功能，支持版本记录、升级日志、功能变更追踪等',
                        'priority': 'high',
                        'impact_level': 'major',
                        'test_status': 'passed'
                    },
                    {
                        'change_type': 'improvement',
                        'module_name': 'ui',
                        'title': '界面优化',  
                        'description': '优化了版本管理界面的用户体验，添加了响应式设计和自动加载功能',
                        'priority': 'medium',
                        'impact_level': 'minor',
                        'test_status': 'passed'
                    },
                    {
                        'change_type': 'feature',
                        'module_name': 'automation',
                        'title': '自动版本管理',
                        'description': '支持基于Git提交的自动版本升级和智能版本号生成',
                        'priority': 'high',
                        'impact_level': 'major',
                        'test_status': 'passed'
                    }
                ]
                
                for change_data in sample_changes:
                    change = FeatureChange(
                        version_id=current_version.id,
                        change_type=change_data['change_type'],
                        module_name=change_data['module_name'],
                        title=change_data['title'],
                        description=change_data['description'],
                        priority=change_data['priority'],
                        impact_level=change_data['impact_level'],
                        test_status=change_data['test_status'],
                        developer_name='开发团队',
                        created_at=datetime.now(),
                        completed_at=datetime.now()
                    )
                    db.session.add(change)
                
                # 更新版本统计
                current_version.total_features = 2
                current_version.total_fixes = 0  
                current_version.total_improvements = 1
                
                db.session.commit()
                print("✅ 示例功能变更记录添加成功")
            
            # 3. 验证数据
            print("\n📋 数据验证:")
            final_version = VersionRecord.get_current_version()
            final_changes = FeatureChange.query.filter_by(version_id=final_version.id).all()
            
            print(f"   版本号: {final_version.version_number}")
            print(f"   版本名称: {final_version.version_name}")
            print(f"   新功能数: {final_version.total_features}")
            print(f"   修复数: {final_version.total_fixes}")
            print(f"   改进数: {final_version.total_improvements}")
            print(f"   变更记录数: {len(final_changes)}")
            
            for change in final_changes:
                print(f"   - {change.change_type}: {change.title}")
            
            print("\n🎉 版本管理数据初始化完成！")
            return True
            
        except Exception as e:
            print(f"\n❌ 初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("版本管理数据初始化")
    print("=" * 50)
    
    success = init_sample_data()
    
    if success:
        print("\n✅ 初始化成功，现在可以查看版本管理界面")
        sys.exit(0)
    else:
        print("\n❌ 初始化失败")
        sys.exit(1)