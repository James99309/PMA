# -*- coding: utf-8 -*-
"""
RelatedDataService — 通用关联数据查询服务

设计目标:
- 各详情页(客户/项目/报价等)统一关联数据查询
- 按 view 权限 + 数据归属双重过滤
- 无权限模块自动跳过(不在返回中)
- 自适应:有数据则展示,空则按 UI 决定

用法:
    from app.utils.related_data import RelatedDataService

    related = RelatedDataService.fetch_all('company', company_id, current_user, limit=5)
    # → {'project': {'items': [...], 'has_more': bool, 'can_create': bool}, ...}
"""
from sqlalchemy.orm import Query


class RelatedDataService:
    """关联数据查询服务"""

    # _registry: {(entity_type, module_key): (query_fn, perm_module, sort_clause, eager_options)}
    _registry = {}

    @classmethod
    def register(cls, entity_type, module_key, query_fn, perm_module,
                 sort_clause=None, eager_options=None):
        """注册一种关联查询。

        Args:
            entity_type: 主实体类型,如 'company' / 'project'
            module_key:  关联模块 key,如 'project' / 'quotation'
            query_fn(entity_id, user) → SQLAlchemy Query:查询函数,需自带 viewable 过滤
            perm_module: 检查 view/create 权限用的模块 key
            sort_clause: 排序子句(SQLAlchemy 列表达式),默认 None = 用 query_fn 自带
            eager_options: 列表,eager load 选项,如 [joinedload(Project.owner)]
        """
        cls._registry[(entity_type, module_key)] = (
            query_fn, perm_module, sort_clause, eager_options or [],
        )

    @classmethod
    def fetch_all(cls, entity_type, entity_id, user, limit=None):
        """拉取该实体的所有可见关联(一次性 6-8 次 SQL,~100ms 量级)。

        Args:
            limit: None(默认)= 不截断,全部返回,由前端卡内滚动承载;
                   传整数则截断到该条数并置 has_more。

        Returns: {module_key: {
            'items':      [...],          # 列表(已排序)
            'has_more':   bool,           # 是否被截断(limit=None 时恒 False)
            'can_view':   True,           # 一定 True(否则 key 不存在)
            'can_create': bool,           # 是否能新建该模块数据
        }}

        无 view 权限的 module_key 不在返回中(完全不渲染该 section)。
        """
        result = {}
        for (et, mk), (qf, pm, sort, eager) in cls._registry.items():
            if et != entity_type:
                continue
            if not user.has_permission(pm, 'view'):
                continue
            q = qf(entity_id, user)
            for opt in eager:
                q = q.options(opt)
            if sort is not None:
                q = q.order_by(sort)
            if limit is None:
                items = q.all()
                has_more = False
            else:
                # 多拉 1 条用于判断 has_more,省一次 count
                items = q.limit(limit + 1).all()
                has_more = len(items) > limit
                items = items[:limit]
            result[mk] = {
                'items':      items,
                'has_more':   has_more,
                'can_view':   True,
                'can_create': user.has_permission(pm, 'create'),
            }
        return result
