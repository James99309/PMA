"""
统一中文映射管理器
整合所有映射逻辑，提供统一的映射接口
"""

import logging
from flask import current_app
from sqlalchemy import text
from app import db
from app.utils.table_chinese_mapping import get_table_chinese_name, is_table_mapped
from app.utils.field_chinese_mapping import get_field_chinese_name, is_field_mapped, get_form_fields_by_module
from app.utils.dictionary_helpers import (
    PROJECT_TYPE_LABELS, PROJECT_STAGE_LABELS, REPORT_SOURCE_LABELS,
    AUTHORIZATION_STATUS_LABELS, COMPANY_TYPE_LABELS
)
from app.utils.i18n import get_current_language

logger = logging.getLogger(__name__)

class ChineseMappingManager:
    """中文映射管理器"""
    
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5分钟缓存
    
    def get_table_display_name(self, table_name):
        """
        获取表的显示名称（中文）
        
        优先级：
        1. data_table_config配置表
        2. 全局表映射配置
        3. 原表名
        
        Args:
            table_name (str): 表名
            
        Returns:
            str: 表的中文显示名称
        """
        cache_key = f"table_display_{table_name}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 优先从配置表获取
            config_name = self._get_table_name_from_config(table_name)
            if config_name:
                self._cache[cache_key] = config_name
                return config_name
            
            # 降级到全局映射
            mapped_name = get_table_chinese_name(table_name)
            self._cache[cache_key] = mapped_name
            return mapped_name
            
        except Exception as e:
            logger.error(f"获取表显示名称失败: {e}")
            return table_name
    
    def get_field_display_name(self, table_name, field_name):
        """
        获取字段的显示名称（中文）
        
        优先级：
        1. data_field_config配置表
        2. 全局字段映射配置
        3. 字典映射（针对特定字段）
        4. 生成的友好名称
        
        Args:
            table_name (str): 表名
            field_name (str): 字段名
            
        Returns:
            str: 字段的中文显示名称
        """
        cache_key = f"field_display_{table_name}_{field_name}"
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 优先从配置表获取
            config_name = self._get_field_name_from_config(table_name, field_name)
            if config_name and self._has_chinese_chars(config_name):
                self._cache[cache_key] = config_name
                return config_name
            
            # 检查表特定的字段映射
            table_mappings = get_form_fields_by_module()
            if table_name in table_mappings and field_name in table_mappings[table_name]:
                table_specific_name = table_mappings[table_name][field_name]
                self._cache[cache_key] = table_specific_name
                return table_specific_name
            
            # 降级到全局字段映射
            mapped_name = get_field_chinese_name(field_name)
            if mapped_name != field_name:
                self._cache[cache_key] = mapped_name
                return mapped_name
            
            # 检查字典映射（特定业务字段）
            dict_name = self._get_field_name_from_dictionary(field_name)
            if dict_name:
                self._cache[cache_key] = dict_name
                return dict_name
            
            # 使用配置表的显示名称（即使是英文）
            if config_name:
                self._cache[cache_key] = config_name
                return config_name
            
            # 最终降级：生成友好名称
            friendly_name = self._generate_friendly_name(field_name)
            self._cache[cache_key] = friendly_name
            return friendly_name
            
        except Exception as e:
            logger.error(f"获取字段显示名称失败: {e}")
            return field_name
    
    def get_field_mapping_info(self, table_name, field_name):
        """
        获取字段的完整映射信息
        
        Args:
            table_name (str): 表名
            field_name (str): 字段名
            
        Returns:
            dict: 包含映射信息的字典
        """
        return {
            'field': field_name,
            'table': table_name,
            'display_name': self.get_field_display_name(table_name, field_name),
            'has_value_mapping': self._has_value_mapping(field_name),
            'mapping_type': self._get_mapping_type(field_name),
            'is_filterable': self._is_field_filterable(table_name, field_name),
            'data_type': self._get_field_data_type(table_name, field_name),
        }
    
    def get_supported_fields_for_table(self, table_name):
        """
        获取表的所有支持字段（已配置为可筛选的字段）
        
        Args:
            table_name (str): 表名
            
        Returns:
            list: 字段信息列表
        """
        try:
            # 从配置表获取可筛选字段
            configured_fields = self._get_configured_filterable_fields(table_name)
            
            if configured_fields:
                logger.info(f"从配置表获取 {table_name} 的字段，共 {len(configured_fields)} 个")
                return configured_fields
            
            # 降级：动态发现字段
            logger.info(f"配置表中未找到 {table_name}，使用动态发现")
            return self._discover_table_fields(table_name)
            
        except Exception as e:
            logger.error(f"获取表字段失败: {e}")
            return []
    
    def update_field_mapping_cache(self, table_name=None):
        """
        更新映射缓存
        
        Args:
            table_name (str, optional): 指定表名，如果不指定则清空所有缓存
        """
        if table_name:
            # 清空指定表的缓存
            keys_to_remove = [key for key in self._cache.keys() 
                            if key.startswith(f"field_display_{table_name}_") 
                            or key == f"table_display_{table_name}"]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # 清空所有缓存
            self._cache.clear()
    
    def _get_table_name_from_config(self, table_name):
        """从配置表获取表名"""
        try:
            query = text("""
                SELECT display_name 
                FROM data_table_config 
                WHERE table_name = :table_name AND is_active = true
            """)
            result = db.session.execute(query, {'table_name': table_name})
            row = result.fetchone()
            return row.display_name if row else None
        except Exception:
            return None
    
    def _get_field_name_from_config(self, table_name, field_name):
        """从配置表获取字段名"""
        try:
            query = text("""
                SELECT dfc.display_name 
                FROM data_field_config dfc
                JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
                WHERE dtc.table_name = :table_name 
                AND dfc.field_name = :field_name
                AND dtc.is_active = true
            """)
            result = db.session.execute(query, {
                'table_name': table_name, 
                'field_name': field_name
            })
            row = result.fetchone()
            return row.display_name if row else None
        except Exception:
            return None
    
    def _get_field_name_from_dictionary(self, field_name):
        """从字典映射获取字段名"""
        try:
            lang = get_current_language()
        except:
            lang = 'zh'
        
        # 检查特定字段的字典映射
        mapping_configs = {
            'project_type': PROJECT_TYPE_LABELS,
            'project_stage': PROJECT_STAGE_LABELS,
            'report_source': REPORT_SOURCE_LABELS,
            'authorization_status': AUTHORIZATION_STATUS_LABELS,
            'company_type': COMPANY_TYPE_LABELS,
        }
        
        if field_name in mapping_configs:
            # 这些字段有值映射，返回字段的中文名称
            field_labels = {
                'project_type': '项目类型',
                'project_stage': '项目阶段',
                'report_source': '报备来源',
                'authorization_status': '授权状态',
                'company_type': '企业类型',
            }
            return field_labels.get(field_name)
        
        return None
    
    def _has_value_mapping(self, field_name):
        """检查字段是否有值映射"""
        mapping_fields = [
            'project_type', 'project_stage', 'report_source',
            'authorization_status', 'company_type'
        ]
        return field_name in mapping_fields
    
    def _get_mapping_type(self, field_name):
        """获取映射类型"""
        if self._has_value_mapping(field_name):
            return 'value_mapping'
        return 'display_only'
    
    def _has_chinese_chars(self, text):
        """检查文本是否包含中文字符"""
        if not text:
            return False
        return any('\u4e00' <= char <= '\u9fff' for char in text)
    
    def _generate_friendly_name(self, field_name):
        """生成友好的字段名称"""
        return field_name.replace('_', ' ').title()
    
    def _is_field_filterable(self, table_name, field_name):
        """检查字段是否可筛选"""
        try:
            query = text("""
                SELECT dfc.is_filterable 
                FROM data_field_config dfc
                JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
                WHERE dtc.table_name = :table_name 
                AND dfc.field_name = :field_name
                AND dtc.is_active = true
            """)
            result = db.session.execute(query, {
                'table_name': table_name, 
                'field_name': field_name
            })
            row = result.fetchone()
            return row.is_filterable if row else False
        except Exception:
            return False
    
    def _get_field_data_type(self, table_name, field_name):
        """获取字段数据类型"""
        try:
            query = text("""
                SELECT dfc.data_type 
                FROM data_field_config dfc
                JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
                WHERE dtc.table_name = :table_name 
                AND dfc.field_name = :field_name
                AND dtc.is_active = true
            """)
            result = db.session.execute(query, {
                'table_name': table_name, 
                'field_name': field_name
            })
            row = result.fetchone()
            return str(row.data_type) if row else 'unknown'
        except Exception:
            return 'unknown'
    
    def _get_configured_filterable_fields(self, table_name):
        """获取配置的可筛选字段"""
        try:
            query = text("""
                SELECT 
                    dfc.field_name,
                    dfc.display_name,
                    dfc.data_type,
                    dfc.is_filterable,
                    dfc.is_aggregatable
                FROM data_field_config dfc
                JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
                WHERE dtc.table_name = :table_name
                AND dtc.is_active = true
                AND dfc.is_filterable = true
                AND dfc.field_name NOT IN ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')
                ORDER BY dfc.field_name
            """)
            
            result = db.session.execute(query, {'table_name': table_name})
            
            fields = []
            for row in result:
                field_name = row.field_name
                display_name = self.get_field_display_name(table_name, field_name)
                
                fields.append({
                    'field': field_name,
                    'label': display_name,
                    'has_mapping': self._has_value_mapping(field_name),
                    'type': str(row.data_type),
                    'is_aggregatable': row.is_aggregatable,
                    'is_filterable': True,
                })
            
            return fields
            
        except Exception as e:
            logger.error(f"获取配置字段失败: {e}")
            return []
    
    def _discover_table_fields(self, table_name):
        """动态发现表字段（降级方案）"""
        try:
            from sqlalchemy import inspect
            
            inspector = inspect(db.engine)
            columns = inspector.get_columns(table_name)
            
            fields = []
            for column in columns:
                field_name = column['name']
                
                # 跳过不适合的字段
                if self._should_skip_field(field_name):
                    continue
                
                display_name = self.get_field_display_name(table_name, field_name)
                
                fields.append({
                    'field': field_name,
                    'label': display_name,
                    'has_mapping': self._has_value_mapping(field_name),
                    'type': str(column['type']),
                    'is_aggregatable': False,
                    'is_filterable': True,
                })
            
            return fields
            
        except Exception as e:
            logger.error(f"动态字段发现失败: {e}")
            return []
    
    def _should_skip_field(self, field_name):
        """判断是否跳过字段"""
        skip_patterns = [
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'password', 'token', 'secret', 'hash'
        ]
        
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in skip_patterns)

# 全局映射管理器实例
mapping_manager = ChineseMappingManager()

# 便捷函数
def get_table_chinese_display_name(table_name):
    """获取表的中文显示名称"""
    return mapping_manager.get_table_display_name(table_name)

def get_field_chinese_display_name(table_name, field_name):
    """获取字段的中文显示名称"""
    return mapping_manager.get_field_display_name(table_name, field_name)

def get_table_supported_fields(table_name):
    """获取表的支持字段列表"""
    return mapping_manager.get_supported_fields_for_table(table_name)

def refresh_mapping_cache(table_name=None):
    """刷新映射缓存"""
    mapping_manager.update_field_mapping_cache(table_name)