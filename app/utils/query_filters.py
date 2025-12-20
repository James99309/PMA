# -*- coding: utf-8 -*-
"""
通用查询筛选工具

用于统一处理列表页面的筛选参数提取和查询构建，
支持多种筛选类型和参数别名兼容。

使用示例:
    from app.utils.query_filters import extract_filter_params, apply_filters_to_query

    # 定义筛选配置
    filter_config = {
        'owner_id': {
            'aliases': ['owner_filter', 'filter_owner_id'],
            'type': 'exact'
        },
        'is_active': {'type': 'boolean', 'default': True},
        'search': {'type': 'ilike', 'fields': ['project_name', 'authorization_code']}
    }

    # 提取筛选参数
    filters = extract_filter_params(request.args, filter_config)

    # 应用到查询
    query = apply_filters_to_query(query, Project, filters, filter_config)
"""

from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from sqlalchemy import or_, and_, func


# ============================================================
# 标准筛选类型处理器
# ============================================================

def _filter_exact(field, value):
    """精确匹配"""
    return field == value


def _filter_ilike(field, value):
    """模糊匹配（不区分大小写）"""
    return field.ilike(f'%{value}%')


def _filter_like(field, value):
    """模糊匹配（区分大小写）"""
    return field.like(f'%{value}%')


def _filter_boolean(field, value):
    """布尔值匹配"""
    if isinstance(value, bool):
        return field == value
    return field == (str(value).lower() in ['true', '1', 'yes'])


def _filter_in_list(field, value):
    """列表包含匹配"""
    if isinstance(value, str):
        values = [v.strip() for v in value.split(',') if v.strip()]
    else:
        values = value
    return field.in_(values) if values else None


def _filter_not_in(field, value):
    """列表排除匹配"""
    if isinstance(value, str):
        values = [v.strip() for v in value.split(',') if v.strip()]
    else:
        values = value
    return ~field.in_(values) if values else None


def _filter_gt(field, value):
    """大于"""
    return field > value


def _filter_gte(field, value):
    """大于等于"""
    return field >= value


def _filter_lt(field, value):
    """小于"""
    return field < value


def _filter_lte(field, value):
    """小于等于"""
    return field <= value


def _filter_not_equal(field, value):
    """不等于"""
    return field != value


def _filter_is_null(field, value):
    """是否为空"""
    if str(value).lower() in ['true', '1', 'yes']:
        return field.is_(None)
    return field.isnot(None)


# 筛选类型注册表
FILTER_TYPES: Dict[str, Callable] = {
    'exact': _filter_exact,
    'ilike': _filter_ilike,
    'like': _filter_like,
    'boolean': _filter_boolean,
    'in_list': _filter_in_list,
    'not_in': _filter_not_in,
    'gt': _filter_gt,
    'gte': _filter_gte,
    'lt': _filter_lt,
    'lte': _filter_lte,
    'not_equal': _filter_not_equal,
    'is_null': _filter_is_null,
}

# 自定义筛选处理器注册表
_custom_handlers: Dict[str, Callable] = {}


def register_filter_handler(name: str, handler: Callable):
    """
    注册自定义筛选处理器

    Args:
        name: 处理器名称
        handler: 处理函数，签名为 (query, model, value, config) -> query

    使用示例:
        def handle_updated_this_month(query, model, value, config):
            if value:
                today = datetime.now()
                first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                return query.filter(model.updated_at >= first_day)
            return query

        register_filter_handler('updated_this_month', handle_updated_this_month)
    """
    _custom_handlers[name] = handler


def get_filter_handler(name: str) -> Optional[Callable]:
    """获取自定义筛选处理器"""
    return _custom_handlers.get(name)


# ============================================================
# 项目管理专用筛选处理器
# ============================================================

def _handle_stage_not(query, model, value, config):
    """
    排除特定阶段的项目，同时排除历史上曾进入过关键状态的项目

    Args:
        query: 查询对象
        model: 模型类（需要有 current_stage 字段）
        value: 逗号分隔的阶段列表，如 'lost,paused,signed'
        config: 配置字典

    Returns:
        添加了排除条件的查询对象
    """
    from app import db
    from app.models.projectpm_stage_history import ProjectStageHistory

    excluded_stages = [s.strip() for s in value.split(',') if s.strip()]

    # 基础排除：当前阶段不在排除列表中
    for stage in excluded_stages:
        query = query.filter(model.current_stage != stage)

    # 增强逻辑：排除历史上曾进入 lost/paused 的项目
    critical_stages = [s for s in excluded_stages if s in ['lost', 'paused']]
    if critical_stages:
        historical_excluded_ids = db.session.query(ProjectStageHistory.project_id).filter(
            ProjectStageHistory.to_stage.in_(critical_stages)
        ).distinct().all()
        if historical_excluded_ids:
            excluded_ids = [p.project_id for p in historical_excluded_ids]
            query = query.filter(~model.id.in_(excluded_ids))

    return query


def _handle_has_authorization(query, model, value, config):
    """
    筛选有/无授权编号的项目

    Args:
        query: 查询对象
        model: 模型类（需要有 authorization_code 字段）
        value: '1' 表示有授权编号，'0' 表示无授权编号
        config: 配置字典

    Returns:
        添加了筛选条件的查询对象
    """
    if value == '1':
        return query.filter(
            model.authorization_code.isnot(None),
            func.length(model.authorization_code) > 0
        )
    elif value == '0':
        return query.filter(
            or_(
                model.authorization_code.is_(None),
                func.length(model.authorization_code) == 0
            )
        )
    return query


def _handle_updated_this_month(query, model, value, config):
    """
    筛选本月有阶段变更的项目

    Args:
        query: 查询对象
        model: 模型类
        value: '1' 表示本月有更新
        config: 配置字典

    Returns:
        添加了筛选条件的查询对象
    """
    if value == '1':
        from app import db
        from app.models.projectpm_stage_history import ProjectStageHistory

        today = datetime.now().date()
        start_date = today.replace(day=1)

        project_ids = db.session.query(ProjectStageHistory.project_id).filter(
            ProjectStageHistory.change_date >= start_date
        ).distinct().all()

        if project_ids:
            ids = [p.project_id for p in project_ids]
            return query.filter(model.id.in_(ids))
        return query.filter(model.id == -1)  # 无匹配
    return query


# 注册项目管理专用处理器
register_filter_handler('stage_not', _handle_stage_not)
register_filter_handler('has_authorization', _handle_has_authorization)
register_filter_handler('updated_this_month', _handle_updated_this_month)


# ============================================================
# 参数提取函数
# ============================================================

def extract_filter_params(
    request_args: Dict[str, Any],
    filter_config: Dict[str, Dict[str, Any]],
    prefix: str = ''
) -> Dict[str, Any]:
    """
    从请求参数中提取筛选值

    支持:
    - 直接字段名: owner_id=1
    - 带前缀字段名: filter_owner_id=1
    - 别名兼容: owner_filter=1 -> owner_id=1

    Args:
        request_args: 请求参数字典 (request.args)
        filter_config: 筛选配置字典
        prefix: 可选的参数前缀 (如 'filter_')

    Returns:
        提取的筛选参数字典

    配置格式:
        {
            'field_name': {
                'aliases': ['alias1', 'alias2'],  # 可选，参数别名
                'type': 'exact',                   # 筛选类型
                'default': None,                   # 可选，默认值
                'required': False,                 # 可选，是否必需
            }
        }
    """
    filters = {}

    for field_name, config in filter_config.items():
        value = None

        # 1. 尝试直接字段名
        if field_name in request_args:
            value = request_args.get(field_name)

        # 2. 尝试带前缀的字段名
        if value is None and prefix:
            prefixed_name = f'{prefix}{field_name}'
            if prefixed_name in request_args:
                value = request_args.get(prefixed_name)

        # 3. 尝试别名
        if value is None:
            aliases = config.get('aliases', [])
            for alias in aliases:
                if alias in request_args:
                    value = request_args.get(alias)
                    break
                # 也尝试带前缀的别名
                if prefix:
                    prefixed_alias = f'{prefix}{alias}'
                    if prefixed_alias in request_args:
                        value = request_args.get(prefixed_alias)
                        break

        # 4. 使用默认值
        if value is None or value == '':
            default = config.get('default')
            if default is not None:
                value = default

        # 5. 存储非空值
        if value is not None and value != '':
            filters[field_name] = value

    return filters


def extract_sort_params(
    request_args: Dict[str, Any],
    default_sort: str = 'created_at',
    default_order: str = 'desc',
    allowed_fields: Optional[List[str]] = None
) -> tuple:
    """
    提取排序参数

    Args:
        request_args: 请求参数字典
        default_sort: 默认排序字段
        default_order: 默认排序方向 ('asc' 或 'desc')
        allowed_fields: 允许排序的字段列表，None表示不限制

    Returns:
        (sort_field, sort_order) 元组
    """
    sort_field = request_args.get('sort', default_sort)
    sort_order = request_args.get('order', default_order)

    # 验证排序方向
    if sort_order not in ['asc', 'desc']:
        sort_order = default_order

    # 验证排序字段
    if allowed_fields and sort_field not in allowed_fields:
        sort_field = default_sort

    return sort_field, sort_order


def extract_pagination_params(
    request_args: Dict[str, Any],
    default_offset: int = 0,
    default_limit: int = 30,
    max_limit: int = 100
) -> tuple:
    """
    提取分页参数

    Args:
        request_args: 请求参数字典
        default_offset: 默认偏移量
        default_limit: 默认每页数量
        max_limit: 最大每页数量

    Returns:
        (offset, limit) 元组
    """
    try:
        offset = int(request_args.get('offset', default_offset))
        offset = max(0, offset)
    except (ValueError, TypeError):
        offset = default_offset

    try:
        limit = int(request_args.get('limit', default_limit))
        limit = max(1, min(limit, max_limit))
    except (ValueError, TypeError):
        limit = default_limit

    return offset, limit


# ============================================================
# 查询构建函数
# ============================================================

def apply_filters_to_query(
    query,
    model,
    filters: Dict[str, Any],
    filter_config: Dict[str, Dict[str, Any]]
):
    """
    将筛选条件应用到查询

    Args:
        query: SQLAlchemy 查询对象
        model: SQLAlchemy 模型类
        filters: 筛选参数字典 (由 extract_filter_params 返回)
        filter_config: 筛选配置字典

    Returns:
        添加了筛选条件的查询对象

    配置格式:
        {
            'field_name': {
                'type': 'exact',           # 筛选类型
                'field': 'db_field_name',  # 可选，实际数据库字段名
                'fields': ['field1', 'field2'],  # 可选，多字段OR搜索
                'handler': 'custom_handler_name',  # 可选，自定义处理器
            }
        }
    """
    for field_name, value in filters.items():
        if field_name not in filter_config:
            continue

        config = filter_config[field_name]

        # 检查是否有自定义处理器
        handler_name = config.get('handler')
        if handler_name:
            handler = get_filter_handler(handler_name)
            if handler:
                query = handler(query, model, value, config)
                continue

        filter_type = config.get('type', 'exact')
        filter_func = FILTER_TYPES.get(filter_type)

        if not filter_func:
            continue

        # 多字段OR搜索
        fields = config.get('fields')
        if fields:
            conditions = []
            for f in fields:
                if hasattr(model, f):
                    condition = filter_func(getattr(model, f), value)
                    if condition is not None:
                        conditions.append(condition)
            if conditions:
                query = query.filter(or_(*conditions))
            continue

        # 单字段搜索
        db_field_name = config.get('field', field_name)
        if hasattr(model, db_field_name):
            condition = filter_func(getattr(model, db_field_name), value)
            if condition is not None:
                query = query.filter(condition)

    return query


def apply_sort_to_query(
    query,
    model,
    sort_field: str,
    sort_order: str = 'desc'
):
    """
    将排序应用到查询

    Args:
        query: SQLAlchemy 查询对象
        model: SQLAlchemy 模型类
        sort_field: 排序字段名
        sort_order: 排序方向 ('asc' 或 'desc')

    Returns:
        添加了排序的查询对象
    """
    if hasattr(model, sort_field):
        field = getattr(model, sort_field)
        if sort_order == 'asc':
            query = query.order_by(field.asc())
        else:
            query = query.order_by(field.desc())

    return query


def apply_pagination_to_query(query, offset: int, limit: int):
    """
    将分页应用到查询

    Args:
        query: SQLAlchemy 查询对象
        offset: 偏移量
        limit: 每页数量

    Returns:
        添加了分页的查询对象
    """
    return query.offset(offset).limit(limit)


# ============================================================
# 便捷函数
# ============================================================

def build_list_query(
    query,
    model,
    request_args: Dict[str, Any],
    filter_config: Dict[str, Dict[str, Any]],
    default_sort: str = 'created_at',
    default_order: str = 'desc',
    apply_pagination: bool = False,
    page_size: int = 30
) -> tuple:
    """
    一站式构建列表查询

    Args:
        query: 基础查询对象
        model: SQLAlchemy 模型类
        request_args: 请求参数
        filter_config: 筛选配置
        default_sort: 默认排序字段
        default_order: 默认排序方向
        apply_pagination: 是否应用分页
        page_size: 每页数量

    Returns:
        (query, filters, sort_field, sort_order, offset, limit) 元组
    """
    # 提取筛选参数
    filters = extract_filter_params(request_args, filter_config)

    # 提取排序参数
    sort_field, sort_order = extract_sort_params(
        request_args, default_sort, default_order
    )

    # 应用筛选
    query = apply_filters_to_query(query, model, filters, filter_config)

    # 应用排序
    query = apply_sort_to_query(query, model, sort_field, sort_order)

    # 应用分页
    offset, limit = 0, page_size
    if apply_pagination:
        offset, limit = extract_pagination_params(
            request_args, default_limit=page_size
        )
        query = apply_pagination_to_query(query, offset, limit)

    return query, filters, sort_field, sort_order, offset, limit


def build_ajax_response(
    items: list,
    html: str,
    offset: int,
    limit: int,
    total_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    构建标准AJAX响应

    Args:
        items: 当前页数据列表
        html: 渲染的HTML内容
        offset: 当前偏移量
        limit: 每页数量
        total_count: 总数量（可选）

    Returns:
        标准响应字典
    """
    has_more = len(items) >= limit

    response = {
        'success': True,
        'html': html,
        'has_more': has_more,
        'offset': offset + len(items),
        'count': len(items)
    }

    if total_count is not None:
        response['total_count'] = total_count

    return response
