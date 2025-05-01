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