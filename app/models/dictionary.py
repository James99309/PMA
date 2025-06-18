from app import db
from datetime import datetime
import time

class Dictionary(db.Model):
    """
    通用字典表模型
    用于管理系统中的字典字段，如角色、区域、行业、产品类别等
    """
    __tablename__ = 'dictionaries'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 字典类型，如'role'、'region'等
    key = db.Column(db.String(50), nullable=False)   # 字典键，用于存储
    value = db.Column(db.String(100), nullable=False) # 字典值，用于显示
    is_active = db.Column(db.Boolean, default=True)   # 是否启用
    is_vendor = db.Column(db.Boolean, default=False)  # 是否为厂商（仅对企业字典有效）
    sort_order = db.Column(db.Integer, default=0)     # 排序顺序
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)
    
    __table_args__ = (
        # 确保每种类型下的key是唯一的
        db.UniqueConstraint('type', 'key', name='uix_type_key'),
    )
    
    def to_dict(self):
        """将字典信息转为字典，用于API响应"""
        return {
            'id': self.id,
            'type': self.type,
            'key': self.key,
            'value': self.value,
            'is_active': self.is_active,
            'is_vendor': self.is_vendor,
            'sort_order': self.sort_order,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def __repr__(self):
        return f'<Dictionary {self.type}:{self.key}={self.value}>' 