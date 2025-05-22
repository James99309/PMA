from app import db
from datetime import datetime
import json


class SystemSettings(db.Model):
    """
    系统设置模型，用于存储全局系统配置参数
    """
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)  # 配置键名
    value = db.Column(db.Text, nullable=True)  # 配置值，以JSON字符串形式存储
    description = db.Column(db.String(255), nullable=True)  # 配置说明
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, key, default=None):
        """
        获取指定配置项的值
        
        Args:
            key: 配置键名
            default: 默认值，如果配置不存在则返回此值
            
        Returns:
            解析后的配置值
        """
        setting = cls.query.filter_by(key=key).first()
        if not setting or setting.value is None:
            return default
        
        try:
            # 尝试解析JSON格式的值
            return json.loads(setting.value)
        except (json.JSONDecodeError, TypeError):
            # 如果解析失败，直接返回字符串值
            return setting.value
    
    @classmethod
    def set(cls, key, value, description=None):
        """
        设置配置项的值
        
        Args:
            key: 配置键名
            value: 配置值
            description: 配置说明
            
        Returns:
            设置后的SystemSettings对象
        """
        setting = cls.query.filter_by(key=key).first()
        
        if not setting:
            # 如果配置项不存在，创建新的配置项
            setting = cls(key=key)
            
        # 非字符串值转换为JSON字符串存储
        if not isinstance(value, str):
            setting.value = json.dumps(value)
        else:
            setting.value = value
            
        # 如果提供了说明，则更新
        if description is not None:
            setting.description = description
            
        db.session.add(setting)
        db.session.commit()
        
        return setting
    
    @classmethod
    def delete(cls, key):
        """
        删除指定配置项
        
        Args:
            key: 配置键名
            
        Returns:
            bool: 删除是否成功
        """
        setting = cls.query.filter_by(key=key).first()
        if not setting:
            return False
            
        db.session.delete(setting)
        db.session.commit()
        return True
    
    def __repr__(self):
        return f"<SystemSettings {self.key}>"

# 默认配置参数定义
DEFAULT_SETTINGS = {
    'customer_activity_threshold': {
        'value': 1,  # 默认1天
        'description': '客户活跃度阈值（天）- 超过指定天数无活动则标记为不活跃'
    },
    'project_activity_threshold': {
        'value': 7,  # 默认7天
        'description': '项目活跃度阈值（天）- 超过指定天数无活动则标记为不活跃'
    }
}

def initialize_default_settings():
    """初始化默认系统设置"""
    for key, config in DEFAULT_SETTINGS.items():
        # 只有当设置不存在时才创建默认设置
        if SystemSettings.query.filter_by(key=key).first() is None:
            SystemSettings.set(
                key=key,
                value=config['value'],
                description=config['description']
            ) 