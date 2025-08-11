"""
性能优化工具类 - 针对Supabase数据库优化
用于优化列表页面的查询性能，减少网络往返次数
"""

from sqlalchemy import func, case, text
from flask import request
import logging

logger = logging.getLogger(__name__)

class ListPerformanceOptimizer:
    """列表页面性能优化器"""
    
    @staticmethod
    def optimize_stats_query(base_query, stat_fields):
        """
        优化统计查询 - 将多个COUNT查询合并为单个查询
        
        Args:
            base_query: SQLAlchemy基础查询对象
            stat_fields: 统计字段配置列表
            示例: [
                {'name': 'total_count', 'condition': None},
                {'name': 'active_count', 'condition': (Model.is_active == True)},
                {'name': 'inactive_count', 'condition': (Model.is_active == False)}
            ]
        
        Returns:
            dict: 统计结果字典
        """
        try:
            # 构建统计查询实体
            entities = []
            for field in stat_fields:
                if field['condition'] is None:
                    # 总计数
                    entities.append(func.count().label(field['name']))
                else:
                    # 条件计数
                    entities.append(
                        func.sum(case((field['condition'], 1), else_=0)).label(field['name'])
                    )
            
            # 执行单个查询获取所有统计
            result = base_query.with_entities(*entities).first()
            
            # 转换为字典
            stats = {}
            for i, field in enumerate(stat_fields):
                stats[field['name']] = getattr(result, field['name']) or 0
                
            logger.debug(f"统计查询优化: 合并了 {len(stat_fields)} 个查询")
            return stats
            
        except Exception as e:
            logger.warning(f"统计查询失败: {e}, 使用默认值")
            # 返回默认值
            return {field['name']: 0 for field in stat_fields}
    
    @staticmethod
    def optimize_list_query(query, page=1, per_page=100, max_records=1000):
        """
        优化列表查询 - 添加分页和记录限制
        
        Args:
            query: SQLAlchemy查询对象
            page: 页码 (默认1)
            per_page: 每页记录数 (默认100)
            max_records: 最大记录数限制 (默认1000)
        
        Returns:
            list: 查询结果列表
        """
        try:
            # 计算偏移量
            offset = (page - 1) * per_page
            
            # 限制最大记录数，防止查询过多数据
            limit = min(per_page, max_records - offset)
            if limit <= 0:
                return []
            
            # 执行分页查询
            results = query.offset(offset).limit(limit).all()
            
            logger.debug(f"列表查询优化: 页码={page}, 每页={per_page}, 返回={len(results)}条")
            return results
            
        except Exception as e:
            logger.error(f"列表查询失败: {e}")
            return []
    
    @staticmethod
    def get_pagination_params():
        """
        从请求参数中获取分页参数
        
        Returns:
            tuple: (page, per_page)
        """
        try:
            page = max(1, int(request.args.get('page', 1)))
        except (ValueError, TypeError):
            page = 1
            
        try:
            per_page = min(200, max(10, int(request.args.get('per_page', 50))))
        except (ValueError, TypeError):
            per_page = 50
            
        return page, per_page
    
    @staticmethod 
    def optimize_search_query(query, model, search_term, search_fields):
        """
        优化搜索查询 - 改进LIKE查询性能
        
        Args:
            query: SQLAlchemy查询对象
            model: 模型类
            search_term: 搜索词
            search_fields: 搜索字段列表
        
        Returns:
            query: 优化后的查询对象
        """
        if not search_term or not search_term.strip():
            return query
            
        search_term = search_term.strip()
        
        # 如果搜索词很短，使用精确匹配或前缀匹配
        if len(search_term) <= 2:
            conditions = []
            for field in search_fields:
                field_attr = getattr(model, field)
                # 精确匹配
                conditions.append(field_attr == search_term)
                # 前缀匹配
                conditions.append(field_attr.like(f'{search_term}%'))
        else:
            # 使用标准模糊匹配
            conditions = []
            for field in search_fields:
                field_attr = getattr(model, field)
                conditions.append(field_attr.ilike(f'%{search_term}%'))
        
        # 使用OR连接所有条件
        from sqlalchemy import or_
        return query.filter(or_(*conditions))

class DatabaseConnectionOptimizer:
    """数据库连接优化器"""
    
    @staticmethod
    def execute_with_timeout(connection, sql, timeout_seconds=30):
        """
        执行SQL with timeout
        
        Args:
            connection: 数据库连接
            sql: SQL语句
            timeout_seconds: 超时时间（秒）
        
        Returns:
            查询结果
        """
        try:
            # 设置语句超时
            connection.execute(text(f'SET statement_timeout = {timeout_seconds * 1000}'))
            result = connection.execute(sql)
            return result
        except Exception as e:
            logger.error(f"SQL执行超时或失败: {e}")
            raise
        finally:
            # 重置超时设置
            try:
                connection.execute(text('SET statement_timeout = 0'))
            except:
                pass