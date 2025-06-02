#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本管理初始化脚本

此脚本用于：
1. 初始化版本管理数据
2. 创建初始版本记录
3. 设置系统默认版本
4. 记录历史升级信息
"""

import logging
from datetime import datetime
from app.extensions import db
from app.models.version_management import VersionRecord, UpgradeLog, FeatureChange
from flask import current_app

logger = logging.getLogger(__name__)

def initialize_version_management():
    """初始化版本管理系统 - 仅在没有任何版本记录时创建基础记录"""
    try:
        # 检查是否已经初始化
        existing_version = VersionRecord.query.first()
        if existing_version:
            logger.info("版本管理系统已经初始化，跳过初始化")
            return True
        
        # 获取当前应用版本
        app_version = current_app.config.get('APP_VERSION', '1.2.0')
        
        # 创建当前版本记录（不是演示数据）
        current_version = VersionRecord(
            version_number=app_version,
            version_name='PMA项目管理系统',
            description='PMA项目管理系统当前运行版本，包含完整的项目管理、客户管理、报价管理、产品管理等功能。',
            is_current=True,
            environment=current_app.config.get('FLASK_ENV', 'production'),
            total_features=0,  # 实际数据，不预设数量
            total_fixes=0,
            total_improvements=0,
            release_date=datetime.now()
        )
        
        db.session.add(current_version)
        db.session.commit()
        
        logger.info(f"版本管理系统初始化成功，创建当前版本: {app_version}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"版本管理系统初始化失败: {str(e)}")
        return False

def create_upgrade_record(from_version, to_version, operator_name=None, notes=None):
    """创建升级记录"""
    try:
        # 获取目标版本
        target_version = VersionRecord.query.filter_by(version_number=to_version).first()
        if not target_version:
            logger.error(f"目标版本不存在: {to_version}")
            return False
        
        # 创建升级日志
        upgrade_log = UpgradeLog(
            version_id=target_version.id,
            from_version=from_version,
            to_version=to_version,
            upgrade_type='manual',
            status='success',
            operator_name=operator_name or '系统',
            environment=current_app.config.get('FLASK_ENV', 'production'),
            upgrade_notes=notes or f'从版本 {from_version} 升级到 {to_version}',
            upgrade_date=datetime.now()
        )
        
        db.session.add(upgrade_log)
        
        # 设置为当前版本
        VersionRecord.set_current_version(to_version)
        
        db.session.commit()
        
        logger.info(f"升级记录创建成功: {from_version} -> {to_version}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建升级记录失败: {str(e)}")
        return False

def add_version_with_features(version_data, features_data=None):
    """添加新版本及其功能变更"""
    try:
        # 创建版本记录
        version = VersionRecord(
            version_number=version_data['version_number'],
            version_name=version_data.get('version_name'),
            description=version_data.get('description'),
            environment=version_data.get('environment', 'production'),
            total_features=version_data.get('total_features', 0),
            total_fixes=version_data.get('total_fixes', 0),
            total_improvements=version_data.get('total_improvements', 0),
            git_commit=version_data.get('git_commit'),
            build_number=version_data.get('build_number'),
            release_date=version_data.get('release_date', datetime.now())
        )
        
        db.session.add(version)
        db.session.flush()  # 获取ID
        
        # 添加功能变更记录
        if features_data:
            for feature_data in features_data:
                feature = FeatureChange(
                    version_id=version.id,
                    change_type=feature_data['change_type'],
                    module_name=feature_data.get('module_name'),
                    title=feature_data['title'],
                    description=feature_data.get('description'),
                    priority=feature_data.get('priority', 'medium'),
                    impact_level=feature_data.get('impact_level', 'minor'),
                    test_status=feature_data.get('test_status', 'passed'),
                    developer_name=feature_data.get('developer_name', '开发团队'),
                    created_at=datetime.now(),
                    completed_at=datetime.now()
                )
                db.session.add(feature)
        
        db.session.commit()
        
        logger.info(f"版本 {version_data['version_number']} 创建成功")
        return version
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建版本失败: {str(e)}")
        return None

def get_version_changelog(version_number):
    """获取版本更新日志"""
    try:
        version = VersionRecord.query.filter_by(version_number=version_number).first()
        if not version:
            return None
        
        # 获取功能变更
        changes = FeatureChange.query.filter_by(version_id=version.id).all()
        
        # 按类型分组
        changelog = {
            'version': version.to_dict(),
            'features': [],
            'fixes': [],
            'improvements': [],
            'security': []
        }
        
        for change in changes:
            change_dict = change.to_dict()
            if change.change_type == 'feature':
                changelog['features'].append(change_dict)
            elif change.change_type == 'fix':
                changelog['fixes'].append(change_dict)
            elif change.change_type == 'improvement':
                changelog['improvements'].append(change_dict)
            elif change.change_type == 'security':
                changelog['security'].append(change_dict)
        
        return changelog
        
    except Exception as e:
        logger.error(f"获取版本更新日志失败: {str(e)}")
        return None

def generate_release_notes(version_number):
    """生成版本发布说明"""
    changelog = get_version_changelog(version_number)
    if not changelog:
        return None
    
    version = changelog['version']
    notes = f"# {version['version_name']} ({version['version_number']})\n\n"
    notes += f"发布日期: {version['release_date']}\n\n"
    
    if version['description']:
        notes += f"## 版本描述\n{version['description']}\n\n"
    
    # 新功能
    if changelog['features']:
        notes += "## 🚀 新功能\n"
        for feature in changelog['features']:
            notes += f"- **{feature['title']}**: {feature['description']}\n"
        notes += "\n"
    
    # 问题修复
    if changelog['fixes']:
        notes += "## 🐛 问题修复\n"
        for fix in changelog['fixes']:
            notes += f"- **{fix['title']}**: {fix['description']}\n"
        notes += "\n"
    
    # 功能改进
    if changelog['improvements']:
        notes += "## ✨ 功能改进\n"
        for improvement in changelog['improvements']:
            notes += f"- **{improvement['title']}**: {improvement['description']}\n"
        notes += "\n"
    
    # 安全更新
    if changelog['security']:
        notes += "## 🔒 安全更新\n"
        for security in changelog['security']:
            notes += f"- **{security['title']}**: {security['description']}\n"
        notes += "\n"
    
    # 统计信息
    notes += "## 📊 统计信息\n"
    notes += f"- 新增功能: {version['total_features']}\n"
    notes += f"- 问题修复: {version['total_fixes']}\n"
    notes += f"- 功能改进: {version['total_improvements']}\n"
    
    return notes

# 预定义的版本升级数据 - 仅用于演示，不会自动应用
VERSION_UPGRADES = [
    {
        'version': {
            'version_number': '1.0.1',
            'version_name': 'PMA系统优化版本',
            'description': '修复了一些已知问题，优化了用户体验，增加了版本管理功能。',
            'total_features': 1,
            'total_fixes': 3,
            'total_improvements': 2
        },
        'features': [
            {
                'change_type': 'feature',
                'module_name': 'version',
                'title': '版本管理系统',
                'description': '新增完整的版本管理功能，支持版本记录、升级日志、功能变更追踪',
                'priority': 'high',
                'impact_level': 'major'
            },
            {
                'change_type': 'fix',
                'module_name': 'project',
                'title': '修复项目评分问题',
                'description': '修复了项目评分计算中的逻辑错误',
                'priority': 'high',
                'impact_level': 'minor'
            },
            {
                'change_type': 'fix',
                'module_name': 'approval',
                'title': '修复审批模板删除问题',
                'description': '修复了审批模板删除时的外键约束问题',
                'priority': 'medium',
                'impact_level': 'minor'
            },
            {
                'change_type': 'improvement',
                'module_name': 'ui',
                'title': '界面优化',
                'description': '优化了用户界面的响应速度和视觉效果',
                'priority': 'medium',
                'impact_level': 'minor'
            }
        ]
    }
]

def apply_version_upgrades():
    """应用预定义的版本升级 - 已禁用，防止自动创建演示数据"""
    logger.info("版本升级功能已禁用，不会自动创建演示数据")
    return True 