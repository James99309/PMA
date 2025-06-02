#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本管理演示脚本

此脚本用于演示版本管理功能：
1. 创建新版本记录
2. 添加功能变更
3. 模拟升级过程
"""

import logging
from datetime import datetime, timedelta
from app.extensions import db
from app.models.version_management import VersionRecord, UpgradeLog, FeatureChange, SystemMetrics
from flask import current_app

logger = logging.getLogger(__name__)

def create_demo_versions():
    """创建演示版本数据"""
    try:
        # 检查是否已有演示数据
        demo_version = VersionRecord.query.filter_by(version_number='1.1.0').first()
        if demo_version:
            logger.info("演示版本数据已存在，跳过创建")
            return True
        
        # 创建版本 1.1.0
        version_110 = VersionRecord(
            version_number='1.1.0',
            version_name='功能增强版本',
            description='增加了版本管理功能、改进了用户界面、修复了多个已知问题。',
            is_current=False,
            environment='production',
            total_features=3,
            total_fixes=5,
            total_improvements=2,
            git_commit='abc123def456',
            build_number='110-20250602',
            release_date=datetime.now() - timedelta(days=7)
        )
        
        db.session.add(version_110)
        db.session.flush()
        
        # 添加 1.1.0 版本的功能变更
        features_110 = [
            {
                'change_type': 'feature',
                'module_name': 'version_management',
                'title': '版本管理系统',
                'description': '新增完整的版本管理功能，包括版本记录、升级日志、功能变更跟踪等',
                'priority': 'high',
                'impact_level': 'major',
                'developer_name': '开发团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'feature',
                'module_name': 'dashboard',
                'title': '仪表板改进',
                'description': '优化仪表板界面，增加更多统计图表和快捷操作',
                'priority': 'medium',
                'impact_level': 'minor',
                'developer_name': '前端团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'feature',
                'module_name': 'notification',
                'title': '通知系统',
                'description': '新增系统通知功能，支持实时消息推送',
                'priority': 'medium',
                'impact_level': 'minor',
                'developer_name': '后端团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'fix',
                'module_name': 'user',
                'title': '用户登录问题修复',
                'description': '修复了用户在某些情况下无法正常登录的问题',
                'priority': 'high',
                'impact_level': 'major',
                'developer_name': '安全团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'fix',
                'module_name': 'project',
                'title': '项目状态更新问题',
                'description': '修复了项目状态更新时的数据同步问题',
                'priority': 'medium',
                'impact_level': 'minor',
                'developer_name': '后端团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'improvement',
                'module_name': 'performance',
                'title': '性能优化',
                'description': '优化数据库查询性能，提升页面加载速度',
                'priority': 'medium',
                'impact_level': 'minor',
                'developer_name': '性能团队',
                'test_status': 'passed'
            }
        ]
        
        for feature_data in features_110:
            feature = FeatureChange(
                version_id=version_110.id,
                change_type=feature_data['change_type'],
                module_name=feature_data['module_name'],
                title=feature_data['title'],
                description=feature_data['description'],
                priority=feature_data['priority'],
                impact_level=feature_data['impact_level'],
                developer_name=feature_data['developer_name'],
                test_status=feature_data['test_status'],
                created_at=datetime.now() - timedelta(days=10),
                completed_at=datetime.now() - timedelta(days=7)
            )
            db.session.add(feature)
        
        # 创建版本 1.2.0
        version_120 = VersionRecord(
            version_number='1.2.0',
            version_name='重大功能更新',
            description='新增产品分析功能、工作记录系统、移动端适配等重要功能。',
            is_current=True,  # 设为当前版本
            environment='production',
            total_features=4,
            total_fixes=3,
            total_improvements=3,
            git_commit='def456ghi789',
            build_number='120-20250602',
            release_date=datetime.now()
        )
        
        db.session.add(version_120)
        db.session.flush()
        
        # 将之前的版本设为非当前版本
        VersionRecord.query.filter(VersionRecord.id != version_120.id).update({'is_current': False})
        
        # 添加 1.2.0 版本的功能变更
        features_120 = [
            {
                'change_type': 'feature',
                'module_name': 'product_analysis',
                'title': '产品分析系统',
                'description': '新增产品数据分析功能，支持多维度数据统计和可视化',
                'priority': 'high',
                'impact_level': 'major',
                'developer_name': '数据团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'feature',
                'module_name': 'work_records',
                'title': '工作记录系统',
                'description': '新增工作记录管理功能，支持工作时间跟踪和任务管理',
                'priority': 'high',
                'impact_level': 'major',
                'developer_name': '业务团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'feature',
                'module_name': 'mobile',
                'title': '移动端适配',
                'description': '优化移动端界面，提升移动设备使用体验',
                'priority': 'medium',
                'impact_level': 'minor',
                'developer_name': '前端团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'feature',
                'module_name': 'api',
                'title': 'API接口扩展',
                'description': '新增多个API接口，支持第三方系统集成',
                'priority': 'medium',
                'impact_level': 'minor',
                'developer_name': 'API团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'improvement',
                'module_name': 'security',
                'title': '安全性增强',
                'description': '加强系统安全防护，增加多层安全验证',
                'priority': 'high',
                'impact_level': 'major',
                'developer_name': '安全团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'improvement',
                'module_name': 'ui',
                'title': '界面优化',
                'description': '优化用户界面设计，提升用户体验',
                'priority': 'medium',
                'impact_level': 'minor',
                'developer_name': 'UI团队',
                'test_status': 'passed'
            },
            {
                'change_type': 'fix',
                'module_name': 'database',
                'title': '数据库连接问题修复',
                'description': '修复了高并发情况下的数据库连接问题',
                'priority': 'high',
                'impact_level': 'major',
                'developer_name': 'DBA团队',
                'test_status': 'passed'
            }
        ]
        
        for feature_data in features_120:
            feature = FeatureChange(
                version_id=version_120.id,
                change_type=feature_data['change_type'],
                module_name=feature_data['module_name'],
                title=feature_data['title'],
                description=feature_data['description'],
                priority=feature_data['priority'],
                impact_level=feature_data['impact_level'],
                developer_name=feature_data['developer_name'],
                test_status=feature_data['test_status'],
                created_at=datetime.now() - timedelta(days=3),
                completed_at=datetime.now()
            )
            db.session.add(feature)
        
        # 创建升级日志
        upgrade_110 = UpgradeLog(
            version_id=version_110.id,
            from_version='1.0.1',
            to_version='1.1.0',
            upgrade_type='automatic',
            status='success',
            operator_name='系统管理员',
            environment='production',
            upgrade_notes='自动升级到版本1.1.0，增加版本管理功能',
            duration_seconds=120,
            upgrade_date=datetime.now() - timedelta(days=7)
        )
        
        upgrade_120 = UpgradeLog(
            version_id=version_120.id,
            from_version='1.1.0',
            to_version='1.2.0',
            upgrade_type='manual',
            status='success',
            operator_name='系统管理员',
            environment='production',
            upgrade_notes='手动升级到版本1.2.0，新增产品分析和工作记录功能',
            duration_seconds=300,
            upgrade_date=datetime.now()
        )
        
        db.session.add(upgrade_110)
        db.session.add(upgrade_120)
        
        # 创建系统指标记录
        metrics = [
            SystemMetrics(
                version_id=version_110.id,
                avg_response_time=250.5,
                memory_usage=75.2,
                cpu_usage=45.3,
                recorded_at=datetime.now() - timedelta(days=7)
            ),
            SystemMetrics(
                version_id=version_110.id,
                error_rate=2.1,
                active_users=156,
                total_requests=12450,
                recorded_at=datetime.now() - timedelta(days=7)
            ),
            SystemMetrics(
                version_id=version_120.id,
                avg_response_time=180.3,
                memory_usage=68.8,
                cpu_usage=38.7,
                recorded_at=datetime.now()
            ),
            SystemMetrics(
                version_id=version_120.id,
                error_rate=1.5,
                active_users=203,
                total_requests=18750,
                recorded_at=datetime.now()
            )
        ]
        
        for metric in metrics:
            db.session.add(metric)
        
        db.session.commit()
        
        logger.info("演示版本数据创建成功")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建演示版本数据失败: {str(e)}")
        return False

def simulate_upgrade_process():
    """模拟升级过程"""
    try:
        # 模拟从1.1.0升级到1.2.0的过程
        current_version = VersionRecord.get_current_version()
        if not current_version or current_version.version_number != '1.2.0':
            logger.info("开始模拟升级过程...")
            
            # 设置当前版本为1.2.0
            success = VersionRecord.set_current_version('1.2.0')
            if success:
                logger.info("升级模拟完成，当前版本: 1.2.0")
                return True
            else:
                logger.error("升级模拟失败")
                return False
        else:
            logger.info("当前已是最新版本")
            return True
            
    except Exception as e:
        logger.error(f"模拟升级过程失败: {str(e)}")
        return False

def get_version_summary():
    """获取版本管理系统摘要"""
    try:
        summary = {
            'total_versions': VersionRecord.query.count(),
            'current_version': None,
            'total_upgrades': UpgradeLog.query.count(),
            'total_features': FeatureChange.query.count(),
            'recent_changes': []
        }
        
        # 获取当前版本
        current_version = VersionRecord.get_current_version()
        if current_version:
            summary['current_version'] = {
                'version_number': current_version.version_number,
                'version_name': current_version.version_name,
                'release_date': current_version.release_date.strftime('%Y-%m-%d'),
                'total_features': current_version.total_features,
                'total_fixes': current_version.total_fixes,
                'total_improvements': current_version.total_improvements
            }
        
        # 获取最近的功能变更
        recent_changes = FeatureChange.query.order_by(
            FeatureChange.completed_at.desc()
        ).limit(5).all()
        
        for change in recent_changes:
            summary['recent_changes'].append({
                'title': change.title,
                'change_type': change.change_type,
                'module_name': change.module_name,
                'completed_at': change.completed_at.strftime('%Y-%m-%d') if change.completed_at else None
            })
        
        return summary
        
    except Exception as e:
        logger.error(f"获取版本摘要失败: {str(e)}")
        return None 