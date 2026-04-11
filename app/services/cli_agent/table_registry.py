"""CLI 表归属注册表(运行时缓存)

从 cli_table_modules 加载表→模块的映射关系,解析 follow 链,执行表级访问检查。

设计要点:
- 表归属数据几乎不变,全量加载到内存,失效时间 5 分钟
- follow 模式递归解析到最终 module,失败返回 None
- check_table_access 按用户 + SQL 表列表逐张检查
- get_cli_allowed_owner_ids 返回 owner_id 集合(None = 系统级不限制)
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Iterable

logger = logging.getLogger(__name__)

_CACHE_TTL = 300  # 5 分钟

_lock = threading.Lock()
_registry_cache: dict[str, dict] | None = None
_registry_cache_ts: float = 0.0


def _load_registry() -> dict[str, dict]:
    """从 DB 加载全部 cli_table_modules(带 TTL 缓存)"""
    global _registry_cache, _registry_cache_ts

    now = time.time()
    if _registry_cache is not None and (now - _registry_cache_ts) < _CACHE_TTL:
        return _registry_cache

    with _lock:
        # double-check
        if _registry_cache is not None and (now - _registry_cache_ts) < _CACHE_TTL:
            return _registry_cache

        from app.models.cli_table_module import CliTableModule

        try:
            rows = CliTableModule.query.filter_by(is_active=True).all()
            registry = {r.table_name: r.to_dict() for r in rows}
            _registry_cache = registry
            _registry_cache_ts = now
            logger.info(f'[CLI Registry] 加载 {len(registry)} 条表归属记录')
            return registry
        except Exception as e:
            logger.error(f'[CLI Registry] 加载失败: {e}')
            # 失败时保留旧缓存(如果有),否则返回空字典(会全部拦截)
            return _registry_cache or {}


def invalidate_cache():
    """外部可调用以强制下次重新加载(数据变更后)"""
    global _registry_cache, _registry_cache_ts
    with _lock:
        _registry_cache = None
        _registry_cache_ts = 0.0


def resolve_table_module(table_name: str, registry: dict | None = None) -> str | None:
    """解析表最终归属的权限模块

    - mode='module' → 直接返回 module
    - mode='follow' → 递归查 parent_table,直到找到 mode='module' 的表
    - 未登记 / 解析失败 → 返回 None

    防御无限循环: 最多递归 10 次。
    """
    reg = registry if registry is not None else _load_registry()
    visited = set()
    current = table_name

    for _ in range(10):
        if current in visited:
            logger.error(f'[CLI Registry] follow 链出现循环: {table_name} → {current}')
            return None
        visited.add(current)

        entry = reg.get(current)
        if not entry:
            return None
        mode = entry.get('mode')
        if mode == 'module':
            return entry.get('module')
        if mode == 'follow':
            parent = entry.get('parent_table')
            if not parent:
                return None
            current = parent
            continue
        return None

    logger.error(f'[CLI Registry] follow 链超过 10 层: {table_name}')
    return None


def check_table_access(user, table_names: Iterable[str]) -> str | None:
    """检查用户是否可通过 CLI 查询这批表

    Returns:
        None 表示通过; 否则返回给 LLM/用户的错误信息(中文)。
    """
    reg = _load_registry()
    role = getattr(user, 'role', None)

    # 管理员无条件通过
    if role == 'admin':
        return None

    for table in table_names:
        entry = reg.get(table)
        if not entry:
            return f'安全限制: 表 {table} 未登记到 CLI 可查询清单, 请联系管理员添加归属'

        module = resolve_table_module(table, reg)
        if not module:
            return f'安全限制: 表 {table} 归属解析失败, 请联系管理员核对 cli_table_modules 配置'

        # cli_agent 模块本身不应出现在 SQL 里(它只是个功能开关),但留一个兜底
        if module == 'cli_agent':
            return f'安全限制: 表 {table} 归属异常(cli_agent 不是数据模块)'

        if not user.has_cli_permission(module):
            return f'安全限制: 你没有 {module} 模块的 CLI 查询权限(表 {table})'

    return None


def get_cli_allowed_owner_ids(user, module: str) -> set[int] | None:
    """按 CLI 权限级别返回允许的 owner_id 集合

    Returns:
        set[int] | None: None 表示系统级不限制; 空 set 表示无任何可见数据
    """
    from app.utils.access_control import (
        get_company_user_ids,
        get_department_user_ids,
        get_personal_viewable_user_ids,
    )

    if getattr(user, 'role', None) == 'admin':
        return None

    level = user.get_cli_permission_level(module)

    if level == 'system':
        return None
    if level == 'company':
        return set(get_company_user_ids(user))
    if level == 'department':
        return set(get_department_user_ids(user))
    # personal 或其他
    return set(get_personal_viewable_user_ids(user))


def get_registry_snapshot() -> dict[str, dict]:
    """给 UI 或调试用的只读快照"""
    return dict(_load_registry())
