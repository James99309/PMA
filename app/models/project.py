from app import db
from datetime import datetime
from sqlalchemy import event, Date, Column, Integer, String, DateTime, Text, ForeignKey
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
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    owner = relationship('User', backref='projects')
    
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

    @staticmethod
    def generate_authorization_code(project_type):
        """生成授权编号
        调用标准化的授权编号生成宏
        请参阅 app.utils.authorization 模块了解详细规则
        """
        return gen_auth_code(project_type)

@event.listens_for(Project, 'before_update')
def project_before_update(mapper, connection, target):
    """项目更新前事件监听器"""
    if target.current_stage != target._current_stage_previous and hasattr(target, '_current_stage_previous'):
        # 阶段变更，添加到描述字段
        from_stage = target._current_stage_previous or '未设置'
        to_stage = target.current_stage or '未设置'
        change_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        stage_change_log = f"[阶段变更] {from_stage} → {to_stage}, 时间: {change_time}"
        
        if target.stage_description:
            target.stage_description = stage_change_log + "\n\n" + target.stage_description
        else:
            target.stage_description = stage_change_log

@event.listens_for(Project, 'load')
def project_on_load(target, context):
    """项目加载时事件监听器，记录当前阶段值"""
    target._current_stage_previous = target.current_stage

@event.listens_for(Project, 'after_update')
def project_after_update(mapper, connection, target):
    """项目更新后事件监听器，记录阶段变更历史"""
    if hasattr(target, '_current_stage_previous') and target.current_stage != target._current_stage_previous:
        # 如果阶段发生变化，记录到历史表
        try:
            from app.models.projectpm_stage_history import ProjectStageHistory
            ProjectStageHistory.add_history_record(
                project_id=target.id, 
                from_stage=target._current_stage_previous,
                to_stage=target.current_stage,
                change_date=datetime.now(),
                remarks=f"自动记录: {target._current_stage_previous or '未设置'} → {target.current_stage or '未设置'}"
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"记录阶段历史失败: {str(e)}", exc_info=True) 