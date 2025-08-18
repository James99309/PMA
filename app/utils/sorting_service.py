"""
通用排序服务类
提供统一的数据排序功能，支持基础字段和关联字段排序
"""

from sqlalchemy import asc, desc, text
from app.models.user import User


class SortingService:
    """
    通用排序服务类
    
    支持功能：
    - 基础字段排序
    - 关联字段排序（JOIN查询）
    - 多级排序（如用户字段：real_name → username）
    - 空值处理（nulls_last/nulls_first）
    - 默认排序配置
    """
    
    def __init__(self, model_class, config=None):
        """
        初始化排序服务
        
        Args:
            model_class: 主要的SQLAlchemy模型类
            config: 排序配置字典
        """
        self.model_class = model_class
        self.config = config or {}
        self.field_mappings = self.config.get('field_mappings', {})
        self.relation_mappings = self.config.get('relation_mappings', {})
        self.default_sort = self.config.get('default_sort', {'field': 'updated_at', 'direction': 'desc'})
        
    def apply_sort(self, query, sort_field=None, sort_direction='asc'):
        """
        应用排序到查询对象
        
        Args:
            query: SQLAlchemy查询对象
            sort_field: 排序字段名
            sort_direction: 排序方向 ('asc' 或 'desc')
            
        Returns:
            排序后的查询对象
        """
        # 如果没有提供排序字段，使用默认排序
        if not sort_field or not sort_direction:
            return self._apply_default_sort(query)
            
        # 标准化排序方向
        sort_direction = sort_direction.lower()
        if sort_direction not in ['asc', 'desc']:
            sort_direction = 'asc'
            
        # 处理关联字段排序
        if sort_field in self.relation_mappings:
            return self._apply_relation_sort(query, sort_field, sort_direction)
            
        # 处理基础字段排序
        if sort_field in self.field_mappings:
            return self._apply_field_sort(query, sort_field, sort_direction)
            
        # 如果字段不在映射中，使用默认排序
        return self._apply_default_sort(query)
        
    def _apply_field_sort(self, query, sort_field, sort_direction):
        """应用基础字段排序"""
        sort_column = self.field_mappings[sort_field]
        
        if sort_direction == 'desc':
            return query.order_by(sort_column.desc())
        else:
            return query.order_by(sort_column.asc())
            
    def _apply_relation_sort(self, query, sort_field, sort_direction):
        """应用关联字段排序"""
        relation_config = self.relation_mappings[sort_field]
        
        # 获取关联配置
        related_model = relation_config['model']
        join_condition = relation_config['join_condition']
        sort_fields = relation_config['sort_fields']
        join_type = relation_config.get('join_type', 'outer')  # outer, inner, left
        nulls_position = relation_config.get('nulls', 'last')  # last, first
        
        # 执行JOIN
        if join_type == 'inner':
            query = query.join(related_model, join_condition)
        else:
            query = query.join(related_model, join_condition, isouter=True)
        
        # 应用多级排序
        order_clauses = []
        for field in sort_fields:
            if sort_direction == 'desc':
                if nulls_position == 'last':
                    order_clauses.append(field.desc().nulls_last())
                else:
                    order_clauses.append(field.desc().nulls_first())
            else:
                if nulls_position == 'last':
                    order_clauses.append(field.asc().nulls_last())
                else:
                    order_clauses.append(field.asc().nulls_first())
                    
        return query.order_by(*order_clauses)
        
    def _apply_default_sort(self, query):
        """应用默认排序"""
        default_field = self.default_sort['field']
        default_direction = self.default_sort['direction']
        
        # 如果默认字段在字段映射中
        if default_field in self.field_mappings:
            return self._apply_field_sort(query, default_field, default_direction)
            
        # 如果默认字段在关联映射中
        if default_field in self.relation_mappings:
            return self._apply_relation_sort(query, default_field, default_direction)
            
        # 尝试从模型类中获取字段
        try:
            sort_column = getattr(self.model_class, default_field)
            if default_direction == 'desc':
                return query.order_by(sort_column.desc())
            else:
                return query.order_by(sort_column.asc())
        except AttributeError:
            # 如果都失败了，返回原查询
            return query
            
    def validate_sort_field(self, sort_field):
        """
        验证排序字段是否有效
        
        Args:
            sort_field: 要验证的字段名
            
        Returns:
            bool: 字段是否有效
        """
        return (sort_field in self.field_mappings or 
                sort_field in self.relation_mappings or
                hasattr(self.model_class, sort_field))
                
    def get_available_fields(self):
        """
        获取所有可用的排序字段
        
        Returns:
            list: 可用字段名列表
        """
        fields = list(self.field_mappings.keys())
        fields.extend(list(self.relation_mappings.keys()))
        return fields


# 预定义的排序配置工厂函数

def create_user_relation_config(foreign_key_field, join_type='outer'):
    """
    创建用户关联字段的排序配置
    
    Args:
        foreign_key_field: 外键字段（如 Company.owner_id）
        join_type: JOIN类型
        
    Returns:
        dict: 关联配置
    """
    return {
        'model': User,
        'join_condition': foreign_key_field == User.id,
        'sort_fields': [User.real_name, User.username],
        'join_type': join_type,
        'nulls': 'last'
    }


def create_project_relation_config(foreign_key_field, join_type='outer'):
    """
    创建项目关联字段的排序配置
    
    Args:
        foreign_key_field: 外键字段（如 Quotation.project_id）
        join_type: JOIN类型
        
    Returns:
        dict: 关联配置
    """
    from app.models.project import Project
    return {
        'model': Project,
        'join_condition': foreign_key_field == Project.id,
        'sort_fields': [Project.project_name],
        'join_type': join_type,
        'nulls': 'last'
    }


def create_basic_field_mappings(model_class, fields):
    """
    创建基础字段映射
    
    Args:
        model_class: 模型类
        fields: 字段名列表
        
    Returns:
        dict: 字段映射
    """
    mappings = {}
    for field in fields:
        if hasattr(model_class, field):
            mappings[field] = getattr(model_class, field)
    return mappings