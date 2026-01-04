# -*- coding: utf-8 -*-
"""
AI分析报告缓存模型

用于存储每日AI分析结果，避免频繁调用API
"""
from app import db
from datetime import date, datetime
import time
import hashlib
import json


class AIAnalysisCache(db.Model):
    """AI分析报告缓存表"""
    __tablename__ = 'ai_analysis_cache'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    analysis_date = db.Column(db.Date, nullable=False, index=True)  # 分析日期（按天缓存）
    analysis_type = db.Column(db.String(50), default='daily_report')  # 分析类型

    # AI分析结果（JSON格式）
    analysis_result = db.Column(db.JSON, nullable=True)
    # 原始数据快照（用于调试和验证）
    raw_data_snapshot = db.Column(db.JSON, nullable=True)
    # 数据哈希（用于检测数据变化）
    data_hash = db.Column(db.String(64), nullable=True)

    # AI模型信息
    ai_provider = db.Column(db.String(50), default='anthropic')  # openai/anthropic
    ai_model = db.Column(db.String(100))  # claude-3-5-sonnet等
    tokens_used = db.Column(db.Integer, default=0)

    # 状态
    status = db.Column(db.String(20), default='pending')  # pending/generating/success/failed
    error_message = db.Column(db.Text, nullable=True)

    # 时间戳
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)

    # 用户关系
    user = db.relationship('User', backref=db.backref('ai_analyses', lazy='dynamic'))

    # 唯一约束：每个用户每天每种类型只有一条记录
    __table_args__ = (
        db.UniqueConstraint('user_id', 'analysis_date', 'analysis_type',
                           name='uix_user_date_type'),
    )

    @classmethod
    def get_today_analysis(cls, user_id, analysis_type='daily_report'):
        """获取今日分析缓存"""
        return cls.query.filter_by(
            user_id=user_id,
            analysis_date=date.today(),
            analysis_type=analysis_type
        ).first()

    @classmethod
    def get_latest_analysis(cls, user_id, analysis_type='daily_report'):
        """获取最新的分析缓存（可能是今天或之前的）"""
        return cls.query.filter_by(
            user_id=user_id,
            analysis_type=analysis_type,
            status='success'
        ).order_by(cls.analysis_date.desc()).first()

    @classmethod
    def is_cache_valid(cls, user_id, data_hash, analysis_type='daily_report'):
        """
        检查缓存是否有效

        有效条件：
        1. 存在成功的缓存
        2. 数据哈希匹配（数据没有变化）
        """
        cache = cls.get_latest_analysis(user_id, analysis_type)
        if cache and cache.status == 'success' and cache.data_hash == data_hash:
            return True, cache
        return False, cache

    @staticmethod
    def calculate_data_hash(data):
        """计算数据的哈希值"""
        # 只提取关键数据计算哈希
        key_data = {
            'summary': data.get('summary', {}),
            'activity_score': data.get('activity_score', {}).get('score'),
            'expense_total': data.get('expense_budget', {}).get('expense_total'),
            'project_stages': data.get('project_stages', {})
        }
        data_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()


class UserDailyLoginRecord(db.Model):
    """用户每日登录记录（用于检测首次登录和控制弹窗显示）"""
    __tablename__ = 'user_daily_login_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    login_date = db.Column(db.Date, nullable=False, index=True)
    first_login_time = db.Column(db.Float, nullable=False)  # 当日首次登录时间
    report_shown = db.Column(db.Boolean, default=False)  # 是否已显示报告
    report_dismissed = db.Column(db.Boolean, default=False)  # 用户是否关闭了报告（今日不再显示）
    report_read = db.Column(db.Boolean, default=False)  # 用户是否已阅读完整报告

    user = db.relationship('User', backref=db.backref('daily_logins', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'login_date', name='uix_user_login_date'),
    )

    @classmethod
    def get_today_record(cls, user_id):
        """获取今日登录记录"""
        return cls.query.filter_by(
            user_id=user_id,
            login_date=date.today()
        ).first()

    @classmethod
    def is_first_login_today(cls, user_id):
        """检查今天是否首次登录"""
        record = cls.get_today_record(user_id)
        return record is None

    @classmethod
    def should_show_report(cls, user_id):
        """检查是否应该显示报告"""
        record = cls.get_today_record(user_id)
        if not record:
            return True  # 首次登录，显示报告
        # 如果用户勾选了"今日不再显示"，则不显示
        return not record.report_dismissed

    @classmethod
    def record_login(cls, user_id):
        """记录登录"""
        today = date.today()
        record = cls.get_today_record(user_id)

        if not record:
            record = cls(
                user_id=user_id,
                login_date=today,
                first_login_time=time.time()
            )
            db.session.add(record)
            db.session.commit()

        return record

    @classmethod
    def mark_report_dismissed(cls, user_id):
        """标记用户今日不再显示报告"""
        record = cls.get_today_record(user_id)
        if record:
            record.report_dismissed = True
            record.report_shown = True
            db.session.commit()
        return record

    @classmethod
    def mark_report_read(cls, user_id):
        """标记用户已阅读完整报告"""
        record = cls.get_today_record(user_id)
        if record:
            record.report_read = True
            record.report_shown = True
            db.session.commit()
        return record

    @classmethod
    def is_report_read(cls, user_id):
        """检查今日报告是否已读"""
        record = cls.get_today_record(user_id)
        return record.report_read if record else False

    @classmethod
    def has_unread_report(cls, user_id):
        """检查是否有未读的报告"""
        from app.models.ai_analysis_cache import AIAnalysisCache
        # 检查是否有成功生成的报告
        cache = AIAnalysisCache.get_latest_analysis(user_id)
        if not cache or cache.status != 'success':
            return False
        # 检查今日是否已读
        record = cls.get_today_record(user_id)
        if not record:
            return True  # 没有登录记录，视为未读
        return not record.report_read
