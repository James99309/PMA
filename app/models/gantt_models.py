from datetime import datetime
from sqlalchemy import ForeignKey, Column, Integer, String, Text, DateTime, BigInteger
from sqlalchemy.orm import relationship
from app import db


class DevProductMilestone(db.Model):
    """研发产品里程碑模型"""
    __tablename__ = 'dev_product_milestones'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('dev_products.id', ondelete='CASCADE'), nullable=False)
    stage_key = Column(String(50), nullable=False)  # 所属主阶段
    name = Column(String(200), nullable=False)      # 里程碑名称
    description = Column(Text)                      # 里程碑描述
    planned_start_date = Column(DateTime)           # 计划开始时间
    planned_end_date = Column(DateTime)             # 计划完成时间
    actual_start_date = Column(DateTime)            # 实际开始时间
    actual_end_date = Column(DateTime)              # 实际完成时间
    status = Column(String(50), default='planned') # 状态：planned/in_progress/completed/cancelled
    progress = Column(Integer, default=0)           # 完成进度 (0-100)
    priority = Column(Integer, default=3)           # 优先级 (1-5)
    order_index = Column(Integer, default=0)        # 排序序号
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    product = relationship("DevProduct", back_populates="milestones")
    creator = relationship("User", foreign_keys=[created_by])
    attachments = relationship("StageAttachment", back_populates="milestone", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DevProductMilestone {self.name}>"
    
    @property 
    def duration_days(self):
        """计算里程碑持续天数"""
        if self.planned_start_date and self.planned_end_date:
            return (self.planned_end_date - self.planned_start_date).days
        return 0
    
    @property
    def is_overdue(self):
        """判断是否已逾期"""
        if self.status not in ['completed'] and self.planned_end_date:
            return datetime.now() > self.planned_end_date
        return False


class StageDependency(db.Model):
    """阶段依赖关系模型"""
    __tablename__ = 'stage_dependencies'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('dev_products.id', ondelete='CASCADE'), nullable=False)
    predecessor_stage = Column(String(50), nullable=False)    # 前置阶段
    successor_stage = Column(String(50), nullable=False)      # 后续阶段
    dependency_type = Column(String(30), default='finish_to_start')  # 依赖类型
    lag_days = Column(Integer, default=0)                     # 延迟天数
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    product = relationship("DevProduct", back_populates="stage_dependencies")
    
    def __repr__(self):
        return f"<StageDependency {self.predecessor_stage} -> {self.successor_stage}>"


class StageAttachment(db.Model):
    """阶段附件模型"""
    __tablename__ = 'stage_attachments'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('dev_products.id', ondelete='CASCADE'), nullable=False)
    stage_key = Column(String(50), nullable=False)           # 关联阶段
    milestone_id = Column(Integer, ForeignKey('dev_product_milestones.id', ondelete='CASCADE'))  # 关联里程碑(可选)
    file_name = Column(String(255), nullable=False)          # 文件名
    file_path = Column(String(500), nullable=False)          # 文件路径
    file_size = Column(BigInteger)                           # 文件大小(字节)
    file_type = Column(String(50))                           # 文件类型
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)                               # 附件描述
    
    # 关联关系
    product = relationship("DevProduct", back_populates="stage_attachments")
    milestone = relationship("DevProductMilestone", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<StageAttachment {self.file_name}>"
    
    @property
    def file_size_mb(self):
        """返回文件大小(MB)"""
        if self.file_size:
            return round(self.file_size / 1024 / 1024, 2)
        return 0


class StageReview(db.Model):
    """阶段评审记录模型"""
    __tablename__ = 'stage_reviews'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('dev_products.id', ondelete='CASCADE'), nullable=False)
    stage_key = Column(String(50), nullable=False)           # 评审阶段
    review_type = Column(String(50), default='stage_gate')   # 评审类型
    reviewer_id = Column(Integer, ForeignKey('users.id'))    # 评审人
    review_result = Column(String(30))                       # 评审结果: approved/rejected/pending
    review_comments = Column(Text)                           # 评审意见
    review_date = Column(DateTime)                           # 评审时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    product = relationship("DevProduct", back_populates="stage_reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    def __repr__(self):
        return f"<StageReview {self.stage_key} - {self.review_result}>"
    
    @property
    def is_approved(self):
        """判断是否已通过评审"""
        return self.review_result == 'approved'
    
    @property
    def is_pending(self):
        """判断是否待评审"""
        return self.review_result == 'pending' or self.review_result is None