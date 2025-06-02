from app import db
from datetime import datetime
import json

class ChangeLog(db.Model):
    """
    通用改动记录表
    记录所有模块的数据变更历史
    """
    __tablename__ = 'change_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 基本信息
    module_name = db.Column(db.String(50), nullable=False)  # 模块名称：project, quotation, customer
    table_name = db.Column(db.String(50), nullable=False)   # 表名
    record_id = db.Column(db.Integer, nullable=False)       # 记录ID
    
    # 操作信息
    operation_type = db.Column(db.String(20), nullable=False)  # 操作类型：CREATE, UPDATE, DELETE
    field_name = db.Column(db.String(100))                     # 字段名称（UPDATE时使用）
    old_value = db.Column(db.Text)                             # 修改前的值
    new_value = db.Column(db.Text)                             # 修改后的值
    
    # 用户和时间信息
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 允许为空，支持系统操作
    user_name = db.Column(db.String(80))                       # 冗余存储用户名，防止用户删除后无法查看
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 额外信息
    record_info = db.Column(db.String(255))                    # 记录描述信息
    description = db.Column(db.String(255))                    # 操作描述
    ip_address = db.Column(db.String(45))                      # 操作IP地址
    user_agent = db.Column(db.String(255))                     # 用户代理
    
    # 关联关系
    user = db.relationship('User', backref='change_logs')
    
    def __repr__(self):
        return f'<ChangeLog {self.module_name}.{self.table_name}[{self.record_id}] by {self.user_name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'module_name': self.module_name,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'operation_type': self.operation_type,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
    
    @classmethod
    def log_create(cls, module_name, table_name, record_id, user_id, user_name, 
                   description=None, ip_address=None, user_agent=None):
        """记录创建操作"""
        log = cls(
            module_name=module_name,
            table_name=table_name,
            record_id=record_id,
            operation_type='CREATE',
            user_id=user_id,
            user_name=user_name,
            description=description or f'创建了新的{module_name}记录',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_update(cls, module_name, table_name, record_id, field_name, old_value, new_value,
                   user_id, user_name, description=None, ip_address=None, user_agent=None):
        """记录更新操作"""
        # 如果值没有变化，不记录
        if str(old_value) == str(new_value):
            return None
            
        log = cls(
            module_name=module_name,
            table_name=table_name,
            record_id=record_id,
            operation_type='UPDATE',
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            user_id=user_id,
            user_name=user_name,
            description=description or f'修改了{field_name}字段',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_delete(cls, module_name, table_name, record_id, user_id, user_name,
                   description=None, ip_address=None, user_agent=None):
        """记录删除操作"""
        log = cls(
            module_name=module_name,
            table_name=table_name,
            record_id=record_id,
            operation_type='DELETE',
            user_id=user_id,
            user_name=user_name,
            description=description or f'删除了{module_name}记录',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def get_record_history(cls, module_name, table_name, record_id):
        """获取特定记录的变更历史"""
        return cls.query.filter_by(
            module_name=module_name,
            table_name=table_name,
            record_id=record_id
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_user_history(cls, user_id, limit=100):
        """获取用户的操作历史"""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
    
    @classmethod
    def get_module_history(cls, module_name, limit=100):
        """获取模块的操作历史"""
        return cls.query.filter_by(module_name=module_name)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all() 