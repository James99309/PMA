# -*- coding: utf-8 -*-
"""
数据库安全查询服务

为 AI 对话提供安全的只读 SQL 查询能力。
使用独立连接 + 只读事务 + SQL 白名单三层防御。
"""
import os
import re
import time
import logging

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 只读连接池（惰性初始化）
# ---------------------------------------------------------------------------

_readonly_engine = None


def _get_readonly_engine():
    """获取只读数据库连接引擎（优先使用 AI_DATABASE_URL）"""
    global _readonly_engine
    if _readonly_engine is None:
        url = os.environ.get('AI_DATABASE_URL') or os.environ.get('DATABASE_URL')
        if not url:
            raise RuntimeError('未配置数据库连接（AI_DATABASE_URL 或 DATABASE_URL）')
        _readonly_engine = create_engine(url, pool_size=2, max_overflow=3)
    return _readonly_engine


# ---------------------------------------------------------------------------
# 动态 Schema 读取（缓存 1 小时）
# ---------------------------------------------------------------------------

_schema_cache = None
_schema_cache_time = 0

_CORE_TABLES = [
    'companies', 'contacts', 'projects', 'quotations', 'quotation_details',
    'products', 'expenses', 'pricing_orders', 'users', 'tasks',
]

_HIDDEN_COLUMNS = {
    'users': {'password_hash', 'wechat_openid', 'wechat_nickname', 'wechat_avatar'},
}

_BUSINESS_NOTES = """
业务标注：
- projects.quotation_customer = 项目报价总额（单位：元）
- quotations.amount = 报价金额（单位：元）
- quotation_details.unit_price / total_price = 单价/总价（单位：元）
- expenses.total_amount = 报销总金额（单位：元）
- 注意：并非所有表都有 is_deleted 字段，请根据实际字段列表判断

枚举值中文映射（展示结果时必须使用中文标签）：
- companies.company_type: user=用户, designer=顾问, contractor=总包, integrator=集成, dealer=经销, distributor=分销, supplier=供应商, other=其他
- companies.status: active=活跃, normal=正常, to_follow=待跟进, dormant=休眠, churned=流失, inactive=停用
- companies.industry: manufacturing=制造, datacenter=数据中心, semiconductor=半导体, chemical=化工, energy=能源, transportation=交通, real_estate=地产, hospitality=酒店, technology=科技, other=其他
- projects.current_stage: discover=发现, embed=植入, pre_tender=标前, tendering=标中, awarded=中标, quoted=批价, signed=签约, lost=失败, paused=搁置, preliminary_design=初步设计
- projects.project_type: channel_follow=渠道, sales_focus=销售, business_opportunity=服务, sales_key=重点销售
- quotations.approval_status: draft=草稿, pending=审批中, approved=已通过, rejected=已拒绝, pre_tender_approved=标前通过, quoted_approved=批价通过
- expenses.status: draft=草稿, pending=审批中, approved=已通过, rejected=已拒绝, recalled=已召回, paid=已付款, awaiting_payment=待付款
- pricing_orders.status: draft=草稿, pending=审批中, approved=已通过, rejected=已拒绝
- tasks.priority: low=低, normal=普通, high=高, urgent=紧急
- tasks.status: todo=待办, in_progress=进行中, done=已完成, cancelled=已取消
- users.role: admin=管理员, ceo=总经理, sales_director=营销总监, service_manager=服务经理, channel_manager=渠道经理, product_manager=产品经理, solution_manager=方案经理, business_admin=商务助理, finance_director=财务总监, finace_director=财务总监, sales_manager=销售经理, hrdp_manager=HRDP经理, customer_sales=客户销售, dealer=经销商, user=普通用户
""".strip()


def get_db_schema():
    """从数据库动态读取核心表的字段结构，缓存 1 小时"""
    global _schema_cache, _schema_cache_time
    if _schema_cache and (time.time() - _schema_cache_time) < 3600:
        return _schema_cache

    try:
        engine = _get_readonly_engine()
        lines = ['可查询的数据库表（PostgreSQL）：\n']

        with engine.connect() as conn:
            for i, table in enumerate(_CORE_TABLES, 1):
                result = conn.execute(text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"
                ), {'t': table})

                hidden = _HIDDEN_COLUMNS.get(table, set())
                cols = [r[0] for r in result if r[0] not in hidden]

                if cols:
                    lines.append(f'{i}. {table}\n   字段: {", ".join(cols)}\n')
            conn.rollback()

        lines.append(f'\n{_BUSINESS_NOTES}')
        _schema_cache = '\n'.join(lines)
        _schema_cache_time = time.time()
        return _schema_cache

    except Exception as e:
        logger.error(f'动态读取数据库 schema 失败: {e}')
        # fallback: 仅返回表名列表 + 业务标注
        return (
            '可查询的数据库表：' + ', '.join(_CORE_TABLES)
            + '\n\n' + _BUSINESS_NOTES
        )


# ---------------------------------------------------------------------------
# SQL 安全校验
# ---------------------------------------------------------------------------

# 禁止的关键词（大写比较）
_FORBIDDEN_KEYWORDS = {
    'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE',
    'TRUNCATE', 'GRANT', 'REVOKE', 'COPY', 'EXECUTE', 'VACUUM',
    'REINDEX', 'CLUSTER', 'COMMENT', 'LOCK', 'SET ROLE',
}

# 允许的起始关键词
_ALLOWED_STARTS = ('SELECT', 'WITH')


def _validate_sql(sql):
    """校验 SQL 安全性

    Returns:
        str: 清理后的 SQL（带 LIMIT）
    Raises:
        ValueError: SQL 不安全
    """
    cleaned = sql.strip().rstrip(';').strip()
    if not cleaned:
        raise ValueError('SQL 不能为空')

    # 禁止多语句（分号分隔）
    # 排除字符串内的分号：简单检查去掉引号内容后是否还有分号
    no_strings = re.sub(r"'[^']*'", '', cleaned)
    if ';' in no_strings:
        raise ValueError('禁止执行多条 SQL 语句')

    upper = cleaned.upper()

    # 必须以允许的关键词开头
    if not any(upper.startswith(kw) for kw in _ALLOWED_STARTS):
        raise ValueError(f'仅允许 SELECT / WITH 查询，当前语句以 {upper.split()[0]} 开头')

    # 检查禁止的关键词（在去掉字符串字面量后检查，避免误杀）
    # 用单词边界匹配，避免误杀（如 "UPDATED_AT" 不该命中 "UPDATE"）
    upper_no_strings = no_strings.upper()
    for kw in _FORBIDDEN_KEYWORDS:
        pattern = rf'\b{kw}\b'
        if re.search(pattern, upper_no_strings):
            raise ValueError(f'SQL 中包含禁止的关键词: {kw}')

    # 自动添加 LIMIT（如果没有）
    if 'LIMIT' not in upper:
        cleaned += ' LIMIT 50'

    return cleaned


# ---------------------------------------------------------------------------
# 敏感表 → 权限模块映射
# ---------------------------------------------------------------------------

_SENSITIVE_TABLE_MODULE = {
    'companies': 'customer',
    'projects': 'project',
    'quotations': 'quotation',
    'expenses': 'expense',
}


def _requires_owner_id_check(sql, user):
    """检查非管理员用户对敏感表的聚合查询是否缺少 owner_id 条件

    Returns:
        str | None: 需要拒绝时返回错误信息，否则返回 None
    """
    role = getattr(user, 'role', 'user')
    logger.debug(f'[AI DB Query] _requires_owner_id_check - role={role}, sql={sql[:80]}')
    if role == 'admin':
        return None

    # 检查是否包含聚合函数
    if not re.search(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', sql, re.IGNORECASE):
        return None

    # 检查是否查询了敏感表
    queries_sensitive = any(
        re.search(rf'\b{t}\b', sql, re.IGNORECASE)
        for t in _SENSITIVE_TABLE_MODULE
    )
    if not queries_sensitive:
        return None

    # 检查 SQL 是否已包含 owner_id 引用
    if re.search(r'\bowner_id\b', sql, re.IGNORECASE):
        return None

    # 缺少 owner_id → 构造引导性错误信息
    username = getattr(user, 'username', '')
    return (
        f'安全限制：对敏感表的聚合查询（COUNT/SUM 等）必须包含 owner_id 条件。'
        f'查询自己的数据请使用 WHERE owner_id = '
        f"(SELECT id FROM users WHERE username='{username}')；"
        f'查询其他用户的数据请先查 users 表获取 id，再用 owner_id = 该id 过滤。'
    )


# ---------------------------------------------------------------------------
# SQL 表引用提取
# ---------------------------------------------------------------------------

# SQL 关键词（不会作为表别名）
_SQL_KEYWORDS = {
    'ON', 'WHERE', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS', 'FULL',
    'JOIN', 'AND', 'OR', 'NOT', 'IN', 'AS', 'SET', 'GROUP', 'ORDER',
    'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'EXCEPT', 'INTERSECT',
    'SELECT', 'FROM', 'INTO', 'VALUES', 'USING', 'NATURAL', 'CASE',
    'WHEN', 'THEN', 'ELSE', 'END', 'EXISTS', 'BETWEEN', 'LIKE', 'IS',
    'NULL', 'TRUE', 'FALSE', 'DISTINCT', 'ALL', 'ANY', 'SOME',
}


def _extract_table_refs(sql):
    """从 SQL 中提取表名和别名

    Returns:
        list[tuple[str, str]]: [(table_name, alias), ...]
        别名为小写；无别名时 alias == table_name
    """
    # 匹配 FROM table [AS] alias 和 JOIN table [AS] alias
    pattern = re.compile(
        r'(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?',
        re.IGNORECASE,
    )
    refs = []
    for match in pattern.finditer(sql):
        table = match.group(1).lower()
        alias = match.group(2)
        if alias and alias.upper() not in _SQL_KEYWORDS:
            alias = alias.lower()
        else:
            alias = table
        refs.append((table, alias))
    return refs


# ---------------------------------------------------------------------------
# 权限辅助函数
# ---------------------------------------------------------------------------

def _get_allowed_ids_for_module(user, module):
    """根据用户在指定模块的权限级别，返回允许的 owner_id 集合

    Returns:
        set[int] | None: 允许的 user IDs，None 表示无限制(system级)
    """
    from app.utils.access_control import (
        get_company_user_ids,
        get_department_user_ids,
        get_personal_viewable_user_ids,
    )

    level = user.get_permission_level(module)
    if level == 'system':
        return None  # 无限制
    elif level == 'company':
        return set(get_company_user_ids(user))
    elif level == 'department':
        return set(get_department_user_ids(user))
    else:  # personal
        return set(get_personal_viewable_user_ids(user))


# ---------------------------------------------------------------------------
# 权限注入（替代旧的验证方式）
# ---------------------------------------------------------------------------

def _inject_permission_filters(sql, user):
    """向 SQL 注入 owner_id IN (...) 权限过滤条件

    Args:
        sql: 已通过 _validate_sql 的 SQL
        user: 当前用户对象

    Returns:
        tuple[str, bool]: (注入权限条件后的 SQL, 是否注入了权限条件)

    Raises:
        PermissionError: 权限无法确定或为空
    """
    role = getattr(user, 'role', 'user')
    user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '?')
    logger.info(f'[AI DB Debug] _inject_permission_filters - user={user_name}, role={role}')
    if role == 'admin':
        logger.info(f'[AI DB Debug] 用户是 admin，跳过权限注入')
        return sql, False

    sql_upper = sql.upper()

    # CTE/WITH 查询 + 包含敏感表 → 暂不支持
    if sql_upper.lstrip().startswith('WITH'):
        has_sensitive = any(
            re.search(rf'\b{t}\b', sql, re.IGNORECASE)
            for t in _SENSITIVE_TABLE_MODULE
        )
        if has_sensitive:
            raise PermissionError(
                '暂不支持对包含敏感表的 WITH/CTE 查询进行权限过滤，'
                '请改用简单 SELECT 查询'
            )
        return sql, False

    # 提取表引用
    table_refs = _extract_table_refs(sql)
    logger.info(f'[AI DB Debug] 提取到的表引用: {table_refs}')

    # 构建权限条件
    conditions = []
    for table, alias in table_refs:
        module = _SENSITIVE_TABLE_MODULE.get(table)
        if not module:
            logger.info(f'[AI DB Debug] 表 {table} 不在敏感表列表中，跳过')
            continue

        # expenses 特殊处理：只允许查自己的
        if module == 'expense':
            allowed_ids = {user.id}
        else:
            try:
                allowed_ids = _get_allowed_ids_for_module(user, module)
            except Exception as e:
                logger.error(f'[AI DB Query] 获取权限失败 module={module}: {e}')
                raise PermissionError(f'无法获取 {table} 表的访问权限')

        logger.info(f'[AI DB Debug] 表 {table} (module={module}): allowed_ids={allowed_ids}')

        # system 级 → 无限制
        if allowed_ids is None:
            logger.info(f'[AI DB Debug] 表 {table}: system 级权限，无限制')
            continue

        if not allowed_ids:
            raise PermissionError(f'您没有 {table} 表的数据访问权限')

        # 前置检查：SQL 中的字面 owner_id 值是否在允许范围内
        # 匹配 owner_id = 5 或 alias.owner_id = 5（仅字面量数字）
        literal_pattern = rf'\b(?:{re.escape(alias)}\.)?owner_id\s*=\s*(\d+)'
        literal_match = re.search(literal_pattern, sql, re.IGNORECASE)
        if literal_match:
            target_id = int(literal_match.group(1))
            if target_id not in allowed_ids:
                raise PermissionError(
                    f'您无权查看 owner_id={target_id} 的 {table} 数据'
                )

        ids_str = ', '.join(str(i) for i in sorted(allowed_ids))
        conditions.append(f'{alias}.owner_id IN ({ids_str})')

    if not conditions:
        return sql, False

    inject_clause = ' AND '.join(conditions)

    # 找注入点：在 GROUP BY / ORDER BY / HAVING / LIMIT 之前
    inject_pattern = re.compile(
        r'\b(GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT)\b',
        re.IGNORECASE,
    )
    match = inject_pattern.search(sql)

    if match:
        pos = match.start()
        before = sql[:pos].rstrip()
        after = sql[pos:]
    else:
        before = sql
        after = ''

    # 判断是否已有 WHERE
    # 在注入点之前的部分中检查 WHERE
    if re.search(r'\bWHERE\b', before, re.IGNORECASE):
        injected = f'{before} AND {inject_clause} {after}'
    else:
        injected = f'{before} WHERE {inject_clause} {after}'

    logger.info(f'[AI DB Query] 权限注入: {inject_clause}')
    return injected.strip(), True


# ---------------------------------------------------------------------------
# 安全执行查询
# ---------------------------------------------------------------------------

def execute_safe_query(sql, user):
    """安全执行只读 SQL 查询

    Args:
        sql: SQL 查询语句
        user: 当前用户对象

    Returns:
        dict: {'success': True, 'columns': [...], 'rows': [...], 'row_count': N}
              或 {'success': False, 'error': '...'}
    """
    try:
        validated_sql = _validate_sql(sql)
    except ValueError as e:
        return {'success': False, 'error': str(e)}

    # 聚合查询 owner_id 强制检查（2026-02-15 新增）
    owner_check_error = _requires_owner_id_check(validated_sql, user)
    logger.info(f'[AI DB Query] owner_id 检查结果: {"拦截" if owner_check_error else "通过"}')
    if owner_check_error:
        user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '?')
        logger.info(
            f'[AI DB Query] 聚合查询缺少 owner_id - 用户 {user_name}(id={user.id}): {sql[:100]}'
        )
        return {'success': False, 'error': owner_check_error}

    # 权限注入
    user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '?')
    logger.info(f'[AI DB Debug] 原始 SQL (验证后): {validated_sql}')
    try:
        validated_sql, was_filtered = _inject_permission_filters(validated_sql, user)
    except PermissionError as e:
        logger.warning(
            f'[AI DB Query] 权限拒绝 - 用户 {user_name}(id={user.id}): {e}'
        )
        return {'success': False, 'error': f'权限不足: {str(e)}'}

    logger.info(f'[AI DB Debug] 最终 SQL (权限注入后): {validated_sql}')
    logger.info(f'[AI DB Debug] was_filtered={was_filtered}')

    engine = _get_readonly_engine()

    try:
        with engine.connect() as conn:
            # 设置只读事务 + 超时
            conn.execute(text("SET TRANSACTION READ ONLY"))
            conn.execute(text("SET LOCAL statement_timeout = '10s'"))

            result = conn.execute(text(validated_sql))
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchall()]

            # 始终回滚（只读，无需 commit）
            conn.rollback()

            # 将特殊类型转为字符串（如 datetime, Decimal）
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    if val is not None and not isinstance(val, (str, int, float, bool)):
                        rows[i][j] = str(val)

            logger.info(f'[AI DB Debug] 查询结果: columns={columns}, row_count={len(rows)}, rows={rows[:5]}')

            # 注入了权限条件但结果为空 → 视为权限不足，避免 AI 误判为 SQL 错误而重试
            if was_filtered and len(rows) == 0:
                logger.info(f'[AI DB Query] 权限拒绝 - 用户 {user_name}: 权限过滤后结果为空')
                return {
                    'success': False,
                    'error': '权限不足: 您无权查看目标数据，查询结果已被权限过滤',
                }

            # 聚合查询补充检查：COUNT/SUM 等永远返回至少 1 行，
            # 当结果为单行全零时视为权限过滤后的空结果
            # 改为检查 SQL 中的聚合函数，不再依赖列名（AI 可能用中文别名）
            if was_filtered and len(rows) == 1:
                has_agg = bool(re.search(
                    r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', validated_sql, re.IGNORECASE
                ))
                all_zero = all(v is None or v == 0 or v == '0' for v in rows[0])
                logger.info(f'[AI DB Debug] 聚合检查: was_filtered={was_filtered}, has_agg={has_agg}, all_zero={all_zero}, row_values={rows[0]}')
                if has_agg and all_zero:
                    logger.info(f'[AI DB Query] 权限拒绝 - 用户 {user_name}: 聚合查询结果为零（权限过滤）')
                    return {
                        'success': False,
                        'error': '权限不足: 您无权查看目标数据，查询结果已被权限过滤',
                    }

            return {
                'success': True,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
            }

    except Exception as e:
        logger.error(f'[AI DB Query] 执行失败: {e}')
        return {'success': False, 'error': f'查询执行失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 权限上下文生成
# ---------------------------------------------------------------------------

def get_permission_context(user):
    """生成用户权限描述文本，嵌入 system prompt

    Args:
        user: 当前用户对象

    Returns:
        str: 权限描述文本
    """
    username = getattr(user, 'username', '')
    return (
        '数据访问限制：\n'
        '- 系统会自动注入当前用户的权限过滤条件\n'
        '- 重要：对 companies/projects/quotations/expenses 表进行聚合查询（COUNT/SUM/AVG等）时，'
        '你必须在 WHERE 中包含 owner_id 条件\n'
        f'- 查询自己的数据：WHERE owner_id = (SELECT id FROM users WHERE username=\'{username}\')\n'
        '- 查询其他用户的数据：先 SELECT id FROM users WHERE real_name=\'目标用户名\'，再用 owner_id 过滤\n'
        '- products 表无访问限制\n'
        '- users 表仅允许查询 id, username, real_name, department, role 字段\n'
        '- 所有支持 is_deleted 的表必须添加 AND is_deleted = FALSE'
    )
