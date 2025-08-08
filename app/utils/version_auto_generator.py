#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动版本号生成器

此模块提供自动版本号生成和管理功能：
1. 统一版本号获取
2. 基于数据库记录的自动递增
3. 版本升级说明集成
4. Git提交信息关联
"""

import os
import logging
import subprocess
from datetime import datetime
from typing import Dict, Optional
from flask import current_app
from app.extensions import db
from app.models.version_management import VersionRecord, FeatureChange, UpgradeLog

logger = logging.getLogger(__name__)

class VersionAutoGenerator:
    """版本自动生成器"""
    
    def __init__(self):
        self.base_major = 1
        self.base_minor = 2
        
    def get_unified_version(self):
        """获取统一的当前版本号"""
        try:
            # 优先级：环境变量 > 基于Git的当前版本 > 数据库当前版本 > 配置文件 > Git标签 > 默认值
            
            # 1. 环境变量（部署时设置）
            env_version = os.environ.get('APP_VERSION')
            if env_version:
                logger.info(f"使用环境变量版本: {env_version}")
                return env_version
            
            # 2. 检查Git记录是否需要更新版本
            latest_commit = self._get_latest_commit_info()
            if latest_commit:
                # 检查数据库中是否已有基于此提交的版本
                existing_version = VersionRecord.query.filter_by(git_commit=latest_commit['hash']).first()
                if existing_version:
                    # 确保此版本是当前版本
                    if not existing_version.is_current:
                        VersionRecord.query.update({'is_current': False})
                        existing_version.is_current = True
                        db.session.commit()
                        logger.info(f"更新当前版本为基于Git的版本: {existing_version.version_number}")
                    return existing_version.version_number
                
                # 如果没有基于此提交的版本，检查是否需要自动创建
                current_db_version = VersionRecord.get_current_version()
                if current_db_version:
                    # 检查数据库版本的Git提交是否与最新提交不同
                    if current_db_version.git_commit != latest_commit['hash']:
                        logger.info(f"检测到新的Git提交，开始自动创建新版本")
                        # 自动创建基于新Git提交的版本
                        new_version = self.auto_create_version_from_git()
                        if new_version:
                            logger.info(f"自动创建版本成功: {new_version.version_number}")
                            return new_version.version_number
                        else:
                            logger.warning("自动创建版本失败，使用当前数据库版本")
                    return current_db_version.version_number
                
            # 3. 数据库当前版本
            current_version = VersionRecord.get_current_version()
            if current_version:
                logger.info(f"使用数据库当前版本: {current_version.version_number}")
                return current_version.version_number
                
            # 4. 配置文件版本
            config_version = current_app.config.get('APP_VERSION')
            if config_version:
                logger.info(f"使用配置文件版本: {config_version}")
                # 创建基于最新Git提交的初始版本记录
                self._create_initial_version_with_git(config_version)
                return config_version
                
            # 5. Git标签版本
            git_version = self._get_latest_git_tag()
            if git_version:
                logger.info(f"使用Git标签版本: {git_version}")
                self._create_initial_version_with_git(git_version)
                return git_version
                
            # 6. 默认版本
            default_version = "1.2.0"
            logger.warning(f"使用默认版本: {default_version}")
            self._create_initial_version_with_git(default_version)
            return default_version
            
        except Exception as e:
            logger.error(f"获取统一版本号失败: {str(e)}")
            return "1.2.0"
    
    def generate_next_version(self, change_type='patch'):
        """
        生成下一个版本号
        
        Args:
            change_type: 变更类型 ('major', 'minor', 'patch')
        
        Returns:
            str: 新版本号
        """
        try:
            # 获取最新版本
            latest_version = VersionRecord.query.order_by(
                VersionRecord.release_date.desc()
            ).first()
            
            if latest_version:
                # 解析当前版本号
                version_parts = latest_version.version_number.split('.')
                if len(version_parts) >= 3:
                    major = int(version_parts[0])
                    minor = int(version_parts[1]) 
                    patch = int(version_parts[2])
                else:
                    major, minor, patch = self.base_major, self.base_minor, 0
            else:
                major, minor, patch = self.base_major, self.base_minor, 0
            
            # 根据变更类型递增
            if change_type == 'major':
                major += 1
                minor = 0
                patch = 0
            elif change_type == 'minor':
                minor += 1
                patch = 0
            else:  # patch
                patch += 1
            
            new_version = f"{major}.{minor}.{patch}"
            logger.info(f"生成新版本号: {new_version} (类型: {change_type})")
            
            return new_version
            
        except Exception as e:
            logger.error(f"生成版本号失败: {str(e)}")
            # 容错处理：基于时间戳生成
            timestamp = int(datetime.now().timestamp()) % 10000
            return f"{self.base_major}.{self.base_minor}.{timestamp}"
    
    def auto_create_version_from_git(self):
        """基于Git提交自动创建版本"""
        try:
            # 获取最新Git提交信息
            commit_info = self._get_latest_commit_info()
            if not commit_info:
                return None
            
            # 分析提交类型
            change_type = self._analyze_commit_type(commit_info['message'])
            
            # 生成新版本号
            new_version = self.generate_next_version(change_type)
            
            # 生成用户友好的升级说明
            user_friendly_description = self._generate_user_friendly_description(commit_info, new_version)
            
            # 创建版本记录
            version_record = VersionRecord(
                version_number=new_version,
                version_name=self._generate_version_name(commit_info['message']),
                description=user_friendly_description,
                git_commit=commit_info['hash'],
                environment=current_app.config.get('FLASK_ENV', 'production'),
                is_current=True  # 设为当前版本
            )
            
            # 设置其他版本为非当前版本
            VersionRecord.query.update({'is_current': False})
            
            db.session.add(version_record)
            db.session.commit()
            
            # 创建升级日志
            self._create_upgrade_log(version_record, commit_info)
            
            # 尝试自动生成功能变更记录
            self._auto_create_feature_changes(version_record, commit_info)
            
            logger.info(f"自动创建版本成功: {new_version}")
            return version_record
            
        except Exception as e:
            logger.error(f"自动创建版本失败: {str(e)}")
            db.session.rollback()
            return None
    
    def get_version_upgrade_info(self, version_number):
        """获取版本升级信息"""
        try:
            version = VersionRecord.query.filter_by(version_number=version_number).first()
            if not version:
                return None
                
            # 获取功能变更
            feature_changes = FeatureChange.query.filter_by(version_id=version.id).all()
            
            # 获取升级日志
            upgrade_logs = UpgradeLog.query.filter_by(version_id=version.id).all()
            
            # 统计信息
            changes_by_type = {
                'feature': [],
                'fix': [], 
                'improvement': [],
                'security': []
            }
            
            for change in feature_changes:
                change_type = change.change_type
                if change_type in changes_by_type:
                    changes_by_type[change_type].append(change.to_dict())
            
            upgrade_info = {
                'version': version.to_dict(),
                'changes_by_type': changes_by_type,
                'upgrade_logs': [log.to_dict() for log in upgrade_logs],
                'summary': {
                    'total_features': len(changes_by_type['feature']),
                    'total_fixes': len(changes_by_type['fix']),
                    'total_improvements': len(changes_by_type['improvement']),
                    'total_security': len(changes_by_type['security'])
                }
            }
            
            return upgrade_info
            
        except Exception as e:
            logger.error(f"获取版本升级信息失败: {str(e)}")
            return None
    
    def _create_initial_version(self, version_number):
        """创建初始版本记录"""
        try:
            existing = VersionRecord.query.filter_by(version_number=version_number).first()
            if existing:
                return existing
                
            initial_version = VersionRecord(
                version_number=version_number,
                version_name="PMA项目管理系统",
                description="系统当前运行版本，包含完整的项目管理、客户管理、报价管理、产品管理等功能。",
                is_current=True,
                environment=current_app.config.get('FLASK_ENV', 'production'),
                release_date=datetime.now()
            )
            
            db.session.add(initial_version)
            db.session.commit()
            logger.info(f"创建初始版本记录: {version_number}")
            return initial_version
            
        except Exception as e:
            logger.error(f"创建初始版本记录失败: {str(e)}")
            db.session.rollback()
            return None
    
    def _create_initial_version_with_git(self, version_number):
        """创建基于Git信息的初始版本记录"""
        try:
            existing = VersionRecord.query.filter_by(version_number=version_number).first()
            if existing:
                # 更新现有版本的Git信息
                latest_commit = self._get_latest_commit_info()
                if latest_commit and not existing.git_commit:
                    existing.git_commit = latest_commit['hash']
                    existing.release_date = datetime.now()
                    # 更新描述包含最新提交信息
                    if latest_commit['message']:
                        existing.description = f"系统当前运行版本，包含完整的项目管理功能。\n\n最新更新：{latest_commit['message']}"
                    db.session.commit()
                    logger.info(f"更新版本记录Git信息: {version_number}")
                return existing
            
            # 获取最新Git提交信息
            latest_commit = self._get_latest_commit_info()
            commit_hash = latest_commit['hash'] if latest_commit else None
            commit_message = latest_commit['message'] if latest_commit else ""
            
            # 构建描述信息
            description = "系统当前运行版本，包含完整的项目管理、客户管理、报价管理、产品管理等功能。"
            if commit_message:
                description += f"\n\n最新更新：{commit_message}"
                
            initial_version = VersionRecord(
                version_number=version_number,
                version_name="PMA项目管理系统",
                description=description,
                git_commit=commit_hash,
                is_current=True,
                environment=current_app.config.get('FLASK_ENV', 'production'),
                release_date=datetime.now()  # 使用当前时间而不是6月2日
            )
            
            # 设置其他版本为非当前版本
            VersionRecord.query.update({'is_current': False})
            
            db.session.add(initial_version)
            db.session.commit()
            logger.info(f"创建基于Git的初始版本记录: {version_number} (提交: {commit_hash})")
            return initial_version
            
        except Exception as e:
            logger.error(f"创建基于Git的初始版本记录失败: {str(e)}")
            db.session.rollback()
            return None
    
    def _get_latest_git_tag(self):
        """获取最新Git标签"""
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                tag = result.stdout.strip()
                # 清理标签格式 (如 v1.2.0 -> 1.2.0)
                if tag.startswith('v'):
                    tag = tag[1:]
                return tag
        except Exception as e:
            logger.debug(f"获取Git标签失败: {str(e)}")
        return None
    
    def _get_latest_commit_info(self):
        """获取最新Git提交信息"""
        try:
            # 获取提交哈希
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, timeout=5
            )
            
            # 获取提交信息
            msg_result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True, text=True, timeout=5
            )
            
            if hash_result.returncode == 0 and msg_result.returncode == 0:
                return {
                    'hash': hash_result.stdout.strip()[:8],  # 短哈希
                    'message': msg_result.stdout.strip()
                }
        except Exception as e:
            logger.debug(f"获取Git提交信息失败: {str(e)}")
        return None
    
    def _analyze_commit_type(self, commit_message):
        """分析提交类型"""
        message = commit_message.lower()
        
        # 分析提交信息中的关键词
        if any(keyword in message for keyword in ['breaking change', '重大变更', '架构']):
            return 'major'
        elif any(keyword in message for keyword in ['feat:', 'feature:', '新功能', '功能']):
            return 'minor'
        elif any(keyword in message for keyword in ['fix:', 'bug:', '修复', '问题']):
            return 'patch'
        else:
            return 'patch'  # 默认为补丁版本
    
    def _generate_version_name(self, commit_message):
        """生成版本名称"""
        # 从提交信息生成版本名称
        if '新功能' in commit_message or 'feat' in commit_message.lower():
            return "功能增强版本"
        elif '修复' in commit_message or 'fix' in commit_message.lower():
            return "问题修复版本"
        elif '优化' in commit_message or '改进' in commit_message:
            return "性能优化版本"
        else:
            return "常规更新版本"
    
    def _create_upgrade_log(self, version_record, commit_info):
        """创建升级日志"""
        try:
            # 获取前一个版本
            previous_version = VersionRecord.query.filter(
                VersionRecord.id != version_record.id
            ).order_by(VersionRecord.release_date.desc()).first()
            
            upgrade_log = UpgradeLog(
                version_id=version_record.id,
                from_version=previous_version.version_number if previous_version else None,
                to_version=version_record.version_number,
                upgrade_type='automatic',
                status='success',
                operator_name='系统自动',
                environment=current_app.config.get('FLASK_ENV', 'production'),
                upgrade_notes=f"基于Git提交自动升级\n提交: {commit_info['hash']}\n信息: {commit_info['message']}"
            )
            
            db.session.add(upgrade_log)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"创建升级日志失败: {str(e)}")
    
    def _auto_create_feature_changes(self, version_record, commit_info):
        """自动创建功能变更记录"""
        try:
            # 分析提交信息，尝试自动生成功能变更
            message = commit_info['message']
            change_type = self._analyze_commit_type(message)
            
            # 映射提交类型到功能变更类型
            type_mapping = {
                'major': 'feature',
                'minor': 'feature', 
                'patch': 'fix'
            }
            
            feature_change = FeatureChange(
                version_id=version_record.id,
                change_type=type_mapping.get(change_type, 'improvement'),
                title=message[:100],  # 截取前100个字符作为标题
                description=message,
                priority='medium',
                impact_level='minor',
                developer_name='开发团队',
                test_status='pending',
                git_commits=commit_info['hash'],
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            db.session.add(feature_change)
            db.session.commit()
            
            # 更新版本统计
            if change_type == 'feature':
                version_record.total_features += 1
            elif change_type == 'fix': 
                version_record.total_fixes += 1
            else:
                version_record.total_improvements += 1
                
            db.session.commit()
            
        except Exception as e:
            logger.error(f"自动创建功能变更记录失败: {str(e)}")
    
    def _generate_user_friendly_description(self, commit_info: Dict, version: str) -> str:
        """生成用户友好的版本描述"""
        try:
            # 导入升级说明生成器
            from app.utils.release_notes_generator import ReleaseNotesGenerator
            
            generator = ReleaseNotesGenerator()
            
            # 分析最近的变更
            changes = generator.analyze_git_changes()
            
            if not changes:
                # 如果无法自动分析，使用提交信息生成简单描述
                return self._generate_simple_description(commit_info['message'])
            
            # 生成结构化的功能列表
            description_parts = []
            description_parts.append(f"## {version} 版本更新")
            description_parts.append("")
            
            # 按类型分组变更
            changes_by_type = {
                'feature': [c for c in changes if c.type == 'feature'],
                'fix': [c for c in changes if c.type == 'fix'], 
                'ui': [c for c in changes if c.type == 'ui'],
                'improvement': [c for c in changes if c.type == 'improvement']
            }
            
            # 添加各类变更
            if changes_by_type['feature']:
                description_parts.append("### ✨ 新功能")
                for change in changes_by_type['feature']:
                    description_parts.append(f"- **{change.module}**: {change.title}")
                description_parts.append("")
            
            if changes_by_type['fix']:
                description_parts.append("### 🔧 问题修复")
                for change in changes_by_type['fix']:
                    description_parts.append(f"- **{change.module}**: {change.title}")
                description_parts.append("")
            
            if changes_by_type['ui']:
                description_parts.append("### 🎨 界面优化")
                for change in changes_by_type['ui']:
                    description_parts.append(f"- **{change.module}**: {change.title}")
                description_parts.append("")
            
            if changes_by_type['improvement']:
                description_parts.append("### ⚡ 系统改进")
                for change in changes_by_type['improvement']:
                    description_parts.append(f"- **{change.module}**: {change.title}")
                description_parts.append("")
            
            # 添加技术信息
            description_parts.append("### 📊 变更统计")
            description_parts.append(f"- 涉及模块: {len(set(c.module for c in changes))} 个")
            description_parts.append(f"- 修改文件: {sum(len(c.files) for c in changes)} 个")
            
            return "\n".join(description_parts)
            
        except Exception as e:
            logger.error(f"生成用户友好描述失败: {str(e)}")
            return self._generate_simple_description(commit_info['message'])
    
    def _generate_simple_description(self, commit_message: str) -> str:
        """生成简单的版本描述"""
        # 基于提交信息生成简单描述
        if '修复' in commit_message or 'fix' in commit_message.lower():
            return f"## 问题修复版本\n\n本次更新主要修复了系统中的问题，提升系统稳定性。\n\n**主要改进**: {commit_message}"
        elif '新功能' in commit_message or 'feat' in commit_message.lower():
            return f"## 功能增强版本\n\n本次更新新增了功能特性，提升用户体验。\n\n**主要功能**: {commit_message}"
        elif '优化' in commit_message or '界面' in commit_message:
            return f"## 优化改进版本\n\n本次更新优化了用户界面和系统性能。\n\n**主要优化**: {commit_message}"
        else:
            return f"## 常规更新版本\n\n系统常规更新维护。\n\n**更新内容**: {commit_message}"

# 全局实例
version_generator = VersionAutoGenerator()

def get_current_app_version():
    """获取当前应用版本号的统一接口"""
    return version_generator.get_unified_version()

def auto_upgrade_version():
    """自动升级版本的接口"""
    return version_generator.auto_create_version_from_git()

def get_upgrade_info(version_number=None):
    """获取升级信息的接口"""
    if not version_number:
        version_number = get_current_app_version()
    return version_generator.get_version_upgrade_info(version_number)