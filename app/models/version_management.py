#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本管理数据模型

此模块定义了版本管理相关的数据模型：
1. VersionRecord - 版本记录
2. UpgradeLog - 升级日志
3. FeatureChange - 功能变更记录
"""

from app.extensions import db
from datetime import datetime
from sqlalchemy import text

class VersionRecord(db.Model):
    """版本记录表"""
    __tablename__ = 'version_records'
    
    id = db.Column(db.Integer, primary_key=True)
    version_number = db.Column(db.String(20), nullable=False, unique=True, comment='版本号，如1.0.0')
    version_name = db.Column(db.String(100), comment='版本名称')
    release_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='发布日期')
    description = db.Column(db.Text, comment='版本描述')
    is_current = db.Column(db.Boolean, default=False, comment='是否为当前版本')
    environment = db.Column(db.String(20), default='production', comment='环境：development/production')
    
    # 版本统计信息
    total_features = db.Column(db.Integer, default=0, comment='新增功能数量')
    total_fixes = db.Column(db.Integer, default=0, comment='修复问题数量')
    total_improvements = db.Column(db.Integer, default=0, comment='改进数量')
    
    # 技术信息
    git_commit = db.Column(db.String(40), comment='Git提交哈希')
    build_number = db.Column(db.String(20), comment='构建号')
    
    # 关联关系
    upgrade_logs = db.relationship('UpgradeLog', backref='version', lazy='dynamic', cascade='all, delete-orphan')
    feature_changes = db.relationship('FeatureChange', backref='version', lazy='dynamic', cascade='all, delete-orphan')
    
    # 创建和更新时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<VersionRecord {self.version_number}>'
    
    @classmethod
    def get_current_version(cls):
        """获取当前版本"""
        return cls.query.filter_by(is_current=True).first()
    
    @classmethod
    def set_current_version(cls, version_number):
        """设置当前版本"""
        # 先将所有版本设为非当前版本
        cls.query.update({'is_current': False})
        # 设置指定版本为当前版本
        version = cls.query.filter_by(version_number=version_number).first()
        if version:
            version.is_current = True
            db.session.commit()
            return version
        return None
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'version_number': self.version_number,
            'version_name': self.version_name,
            'release_date': self.release_date.strftime('%Y-%m-%d %H:%M:%S') if self.release_date else None,
            'description': self.description,
            'is_current': self.is_current,
            'environment': self.environment,
            'total_features': self.total_features,
            'total_fixes': self.total_fixes,
            'total_improvements': self.total_improvements,
            'git_commit': self.git_commit,
            'build_number': self.build_number,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class UpgradeLog(db.Model):
    """升级日志表"""
    __tablename__ = 'upgrade_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('version_records.id'), nullable=False, comment='版本ID')
    from_version = db.Column(db.String(20), comment='升级前版本')
    to_version = db.Column(db.String(20), nullable=False, comment='升级后版本')
    upgrade_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='升级时间')
    upgrade_type = db.Column(db.String(20), default='manual', comment='升级类型：manual/automatic')
    status = db.Column(db.String(20), default='success', comment='升级状态：success/failed/rollback')
    
    # 升级详情
    upgrade_notes = db.Column(db.Text, comment='升级说明')
    error_message = db.Column(db.Text, comment='错误信息（如果升级失败）')
    duration_seconds = db.Column(db.Integer, comment='升级耗时（秒）')
    
    # 操作人员
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='操作人员ID')
    operator_name = db.Column(db.String(50), comment='操作人员姓名')
    
    # 环境信息
    environment = db.Column(db.String(20), comment='升级环境')
    server_info = db.Column(db.Text, comment='服务器信息')
    
    def __repr__(self):
        return f'<UpgradeLog {self.from_version} -> {self.to_version}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'version_id': self.version_id,
            'from_version': self.from_version,
            'to_version': self.to_version,
            'upgrade_date': self.upgrade_date.strftime('%Y-%m-%d %H:%M:%S') if self.upgrade_date else None,
            'upgrade_type': self.upgrade_type,
            'status': self.status,
            'upgrade_notes': self.upgrade_notes,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds,
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'environment': self.environment,
            'server_info': self.server_info
        }

class FeatureChange(db.Model):
    """功能变更记录表"""
    __tablename__ = 'feature_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('version_records.id'), nullable=False, comment='版本ID')
    
    # 变更基本信息
    change_type = db.Column(db.String(20), nullable=False, comment='变更类型：feature/fix/improvement/security')
    module_name = db.Column(db.String(50), comment='模块名称')
    title = db.Column(db.String(200), nullable=False, comment='变更标题')
    description = db.Column(db.Text, comment='详细描述')
    
    # 优先级和影响
    priority = db.Column(db.String(20), default='medium', comment='优先级：low/medium/high/critical')
    impact_level = db.Column(db.String(20), default='minor', comment='影响级别：minor/major/breaking')
    
    # 技术信息
    affected_files = db.Column(db.Text, comment='影响的文件列表（JSON格式）')
    git_commits = db.Column(db.Text, comment='相关Git提交（JSON格式）')
    
    # 测试信息
    test_status = db.Column(db.String(20), default='pending', comment='测试状态：pending/passed/failed')
    test_notes = db.Column(db.Text, comment='测试说明')
    
    # 开发信息
    developer_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='开发人员ID')
    developer_name = db.Column(db.String(50), comment='开发人员姓名')
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    
    def __repr__(self):
        return f'<FeatureChange {self.title}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'version_id': self.version_id,
            'change_type': self.change_type,
            'module_name': self.module_name,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'impact_level': self.impact_level,
            'affected_files': self.affected_files,
            'git_commits': self.git_commits,
            'test_status': self.test_status,
            'test_notes': self.test_notes,
            'developer_id': self.developer_id,
            'developer_name': self.developer_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        }

class SystemMetrics(db.Model):
    """系统指标记录表"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    version_id = db.Column(db.Integer, db.ForeignKey('version_records.id'), comment='版本ID')
    
    # 性能指标
    avg_response_time = db.Column(db.Float, comment='平均响应时间（毫秒）')
    max_response_time = db.Column(db.Float, comment='最大响应时间（毫秒）')
    error_rate = db.Column(db.Float, comment='错误率（百分比）')
    
    # 使用指标
    active_users = db.Column(db.Integer, comment='活跃用户数')
    total_requests = db.Column(db.Integer, comment='总请求数')
    database_size = db.Column(db.BigInteger, comment='数据库大小（字节）')
    
    # 系统资源
    cpu_usage = db.Column(db.Float, comment='CPU使用率（百分比）')
    memory_usage = db.Column(db.Float, comment='内存使用率（百分比）')
    disk_usage = db.Column(db.Float, comment='磁盘使用率（百分比）')
    
    # 记录时间
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录时间')
    
    def __repr__(self):
        return f'<SystemMetrics {self.recorded_at}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'version_id': self.version_id,
            'avg_response_time': self.avg_response_time,
            'max_response_time': self.max_response_time,
            'error_rate': self.error_rate,
            'active_users': self.active_users,
            'total_requests': self.total_requests,
            'database_size': self.database_size,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'recorded_at': self.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if self.recorded_at else None
        } 