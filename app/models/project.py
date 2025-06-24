from app import db
from datetime import datetime
from sqlalchemy import event, Date, Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.authorization import generate_authorization_code as gen_auth_code

class Project(db.Model):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    project_name = Column(String(64), nullable=False, index=True)
    report_time = Column(Date, nullable=True)
    project_type = Column(String(64), nullable=True)
    report_source = Column(String(64), nullable=True)
    product_situation = Column(String(128), nullable=True)
    end_user = Column(String(128), nullable=True)
    design_issues = Column(String(128), nullable=True)
    dealer = Column(String(128), nullable=True)
    contractor = Column(String(128), nullable=True)
    system_integrator = Column(String(128), nullable=True)
    current_stage = Column(String(64), nullable=True)
    stage_description = Column(Text, nullable=True)
    authorization_code = Column(String(64), nullable=True, index=True)
    delivery_forecast = Column(Date, nullable=True)
    quotation_customer = Column(db.Float, nullable=True, default=0)  # 添加报价总额字段
    
    # 新增授权状态和反馈字段
    authorization_status = Column(String(20), nullable=True, default=None)  # None, 'pending', 'rejected'
    feedback = Column(Text, nullable=True)  # 存储申请反馈或驳回原因
    
    # 项目锁定相关字段
    is_locked = Column(Boolean, default=False, nullable=False)  # 是否锁定
    locked_reason = Column(String(100), nullable=True)  # 锁定原因
    locked_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # 锁定人
    locked_at = Column(DateTime, nullable=True)  # 锁定时间
    
    # 活跃度相关字段
    is_active = Column(Boolean, default=True, nullable=False)  # 是否活跃
    last_activity_date = Column(DateTime, default=func.now(), nullable=True)  # 最后活动时间
    activity_reason = Column(String(50), nullable=True)  # 活跃状态原因
    
    # 销售负责人字段
    vendor_sales_manager_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 厂商销售负责人
    
    # 项目评分字段 (1-5星)
    rating = Column(Integer, nullable=True)  # 项目评分，1-5星，NULL表示未评分
    
    # 行业字段
    industry = Column(String(50), nullable=True)  # 项目所属行业
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    # 明确指定外键字段，避免与locked_by外键冲突
    owner = relationship('User', foreign_keys=[owner_id], backref='projects')
    # 为locked_by添加关系
    locked_by_user = relationship('User', foreign_keys=[locked_by])
    # 为销售负责人添加关系
    vendor_sales_manager = relationship('User', foreign_keys=[vendor_sales_manager_id])
    
    # 修改关系定义，移除可能导致循环引用的配置
    quotations = db.relationship('Quotation', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.project_name}>'

    @property
    def formatted_report_time(self):
        """格式化报备时间"""
        try:
            return self.report_time.strftime('%Y-%m-%d') if self.report_time else ''
        except (AttributeError, ValueError):
            return ''

    @property
    def formatted_delivery_forecast(self):
        """格式化出货预测时间"""
        try:
            return self.delivery_forecast.strftime('%Y-%m-%d') if self.delivery_forecast else ''
        except (AttributeError, ValueError):
            return ''

    @property
    def formatted_updated_at(self):
        """格式化更新时间"""
        try:
            return self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        except (AttributeError, ValueError):
            return ''

    @property
    def rating_stars(self):
        """获取星级评分的HTML表示"""
        if not self.rating:
            return ''
        
        stars_html = ''
        for i in range(1, 6):
            if i <= self.rating:
                stars_html += '<i class="fas fa-star text-warning"></i>'
            else:
                stars_html += '<i class="far fa-star text-muted"></i>'
        return stars_html

    @property
    def industry_badge(self):
        """获取行业徽章HTML表示"""
        if not self.industry:
            return '<span class="badge bg-secondary">未分类</span>'
        
        # 行业颜色配置
        industry_colors = {
            'manufacturing': 'primary',      # 蓝色 - 制造业
            'healthcare': 'success',         # 绿色 - 医疗健康
            'education': 'info',             # 青色 - 教育
            'finance': 'warning',            # 黄色 - 金融
            'real_estate': 'danger',         # 红色 - 房地产
            'retail': 'light',               # 浅色 - 零售
            'transportation': 'dark',        # 深色 - 交通运输
            'energy': 'success',             # 绿色 - 能源
            'technology': 'primary',         # 蓝色 - 科技
            'government': 'secondary',       # 灰色 - 政府
            'hospitality': 'info',           # 青色 - 酒店服务
            'agriculture': 'success'         # 绿色 - 农业
        }
        
        # 行业名称映射
        industry_names = {
            'manufacturing': '制造业',
            'healthcare': '医疗健康',
            'education': '教育',
            'finance': '金融',
            'real_estate': '房地产',
            'retail': '零售',
            'transportation': '交通运输',
            'energy': '能源',
            'technology': '科技',
            'government': '政府',
            'hospitality': '酒店服务',
            'agriculture': '农业'
        }
        
        color = industry_colors.get(self.industry, 'secondary')
        name = industry_names.get(self.industry, self.industry)
        
        return f'<span class="badge bg-{color}">{name}</span>'

    @staticmethod
    def generate_authorization_code(project_type):
        """生成授权编号
        调用标准化的授权编号生成宏
        请参阅 app.utils.authorization 模块了解详细规则
        """
        return gen_auth_code(project_type)

@event.listens_for(Project, 'load')
def project_on_load(target, context):
    """项目加载时事件监听器，记录当前阶段值"""
    target._current_stage_previous = target.current_stage
    # 添加标志位，用于跳过重复的历史记录（默认为False）
    target._skip_history_recording = False

@event.listens_for(Project, 'after_update')
def project_after_update(mapper, connection, target):
    """项目更新后事件监听器，记录阶段变更历史"""
    # 检查是否需要跳过历史记录（如通过API已经添加了历史记录）
    if hasattr(target, '_skip_history_recording') and target._skip_history_recording:
        # 执行完一次后重置标志，确保下次更新时正常工作
        target._skip_history_recording = False
        return
        
    if hasattr(target, '_current_stage_previous') and target.current_stage != target._current_stage_previous:
        # 如果阶段发生变化，记录到历史表
        try:
            from app.models.projectpm_stage_history import ProjectStageHistory
            ProjectStageHistory.add_history_record(
                project_id=target.id, 
                from_stage=target._current_stage_previous,
                to_stage=target.current_stage,
                change_date=datetime.now(),
                remarks=f"自动记录: {target._current_stage_previous or '未设置'} → {target.current_stage or '未设置'}",
                commit=False  # 在事务中不要提交，让外层事务统一提交
            )
        except Exception as e:
            import logging
        target._skip_history_recording = False
        return
        
    if hasattr(target, '_current_stage_previous') and target.current_stage != target._current_stage_previous:
        # 如果阶段发生变化，记录到历史表
        try:
            from app.models.projectpm_stage_history import ProjectStageHistory
            ProjectStageHistory.add_history_record(
                project_id=target.id, 
                from_stage=target._current_stage_previous,
                to_stage=target.current_stage,
                change_date=datetime.now(),
                remarks=f"自动记录: {target._current_stage_previous or '未设置'} → {target.current_stage or '未设置'}",
                commit=False  # 在事务中不要提交，让外层事务统一提交
            )
        except Exception as e:
            import logging