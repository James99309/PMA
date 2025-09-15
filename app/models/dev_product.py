from datetime import datetime
from sqlalchemy import ForeignKey, Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app import db

class DevProduct(db.Model):
    __tablename__ = 'dev_products'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('product_categories.id'))
    subcategory_id = Column(Integer, ForeignKey('product_subcategories.id'))
    region_id = Column(Integer, ForeignKey('product_regions.id'))
    name = Column(String(100))
    model = Column(String(100))
    status = Column(String(50))
    unit = Column(String(20))
    retail_price = Column(Float)
    currency = Column(String(10), default='CNY')  # 货币类型
    description = Column(Text)
    image_path = Column(String(255))
    pdf_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    mn_code = Column(String(20))
    
    # 阶段跟踪相关字段
    stage_history = Column(JSON)  # 阶段历史记录
    stage_description = Column(Text)  # 阶段描述信息
    stage_records = Column(JSON)  # 阶段记录详情
    
    # 甘特图增强字段
    planned_duration_days = Column(Integer)  # 计划总工期
    actual_duration_days = Column(Integer)   # 实际工期
    risk_level = Column(String(20), default='medium')  # 风险等级
    baseline_date = Column(DateTime)        # 基线日期
    milestone_count = Column(Integer, default=0)  # 里程碑数量
    
    # 关联关系
    category = relationship("ProductCategory", foreign_keys=[category_id])
    subcategory = relationship("ProductSubcategory", foreign_keys=[subcategory_id])
    region = relationship("ProductRegion", foreign_keys=[region_id])
    owner = relationship("User", foreign_keys=[owner_id])
    creator = relationship("User", foreign_keys=[created_by])
    specs = relationship("DevProductSpec", back_populates="product", cascade="all, delete-orphan")
    
    # 甘特图相关关联
    milestones = relationship("DevProductMilestone", back_populates="product", cascade="all, delete-orphan")
    stage_attachments = relationship("StageAttachment", back_populates="product", cascade="all, delete-orphan")
    stage_reviews = relationship("StageReview", back_populates="product", cascade="all, delete-orphan")
    stage_dependencies = relationship("StageDependency", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DevProduct {self.model}>"
    
    @property
    def current_stage_key(self):
        """
        获取当前阶段键值
        将status字段转换为阶段键值
        """
        from app.config.stage_configs import status_to_stage_key
        return status_to_stage_key('rd_product', self.status or 'research')
    
    @property
    def current_stage_name(self):
        """
        获取当前阶段显示名称
        """
        from app.config.stage_configs import get_stage_by_key
        stage = get_stage_by_key('rd_product', self.current_stage_key)
        return stage['name'] if stage else self.status
    
    def get_stage_history(self):
        """
        获取格式化的阶段历史记录
        """
        if not self.stage_history:
            # 如果没有历史记录，基于创建时间生成初始记录
            initial_stage = {
                'stage': self.current_stage_key,
                'startDate': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
                'endDate': None,
                'user_id': self.created_by,
                'username': self.creator.username if self.creator else '系统'
            }
            return [initial_stage]
        
        return self.stage_history
    
    def update_stage(self, new_stage_key, user_id=None, description=None):
        """
        更新产品阶段
        
        Args:
            new_stage_key (str): 新的阶段键值
            user_id (int): 操作用户ID
            description (str): 阶段描述
        """
        from app.config.stage_configs import stage_key_to_status
        from datetime import datetime
        
        # 更新status字段
        old_status = self.status
        new_status = stage_key_to_status('rd_product', new_stage_key)
        self.status = new_status
        
        # 更新阶段历史
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 初始化历史记录（如果不存在）
        if not self.stage_history:
            self.stage_history = []
        
        # 结束当前阶段（如果存在）
        if self.stage_history:
            last_record = self.stage_history[-1]
            if not last_record.get('endDate'):
                last_record['endDate'] = current_time
        
        # 添加新阶段记录
        new_record = {
            'stage': new_stage_key,
            'startDate': current_time,
            'endDate': None,
            'user_id': user_id,
            'description': description,
            'previous_status': old_status
        }
        
        self.stage_history = self.stage_history + [new_record]  # 触发SQLAlchemy更新检测
        
        # 更新阶段描述
        if description:
            if self.stage_description:
                self.stage_description += f"\n[{current_time}] {description}"
            else:
                self.stage_description = f"[{current_time}] {description}"
        
        # 更新时间戳
        self.updated_at = datetime.now()
    
    def can_advance_to_stage(self, target_stage_key):
        """
        检查是否可以推进到指定阶段
        
        Args:
            target_stage_key (str): 目标阶段键值
            
        Returns:
            tuple: (can_advance, reason)
        """
        from app.config.stage_configs import validate_stage_transition
        return validate_stage_transition('rd_product', self.current_stage_key, target_stage_key)

class DevProductSpec(db.Model):
    __tablename__ = 'dev_product_specs'
    
    id = Column(Integer, primary_key=True)
    dev_product_id = Column(Integer, ForeignKey('dev_products.id'))
    field_name = Column(String(100))
    field_value = Column(String(255))
    field_code = Column(String(10))  # 规格编码，用于MN号生成
    
    # 关联关系
    product = relationship("DevProduct", back_populates="specs")
    
    def __repr__(self):
        return f"<DevProductSpec {self.field_name}: {self.field_value}>" 