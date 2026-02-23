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
    'companies', 'contacts', 'projects', 'project_customer_associations',
    'quotations', 'quotation_details', 'products', 'expenses',
    'pricing_orders', 'users', 'tasks',
]

_HIDDEN_COLUMNS = {
    'users': {'password_hash', 'wechat_openid', 'wechat_nickname', 'wechat_avatar'},
}

_BUSINESS_NOTES = """
业务标注：
- 金额字段单位均为元（projects.quotation_customer, quotations.amount, quotation_details.unit_price/total_price, expenses.total_amount）
- 枚举字段展示时请用中文标签
""".strip()

# 精简字段定义：表名→(中文描述, 关键字段列表)
_TABLE_SCHEMA = {
    'companies': ('客户公司', 'id, company_name, company_type, country, region, address, city, industry, status, owner_id, is_deleted'),
    'contacts': ('联系人', 'id, company_id, name, department, position, phone, email, is_primary, owner_id'),
    'projects': ('项目', 'id, project_name, project_type, report_source, current_stage, end_user, dealer, contractor, status, owner_id, created_by, is_deleted'),
    'project_customer_associations': ('项目客户关联', 'id, project_id, company_id, created_by'),
    'quotations': ('报价单', 'id, quotation_number, project_id, customer_id, contact_id, amount, currency, approval_status, owner_id'),
    'quotation_details': ('报价明细', 'id, quotation_id, product_name, product_model, brand, quantity, unit_price, total_price, product_mn'),
    'products': ('产品', 'id, product_name, model, brand, category, type, retail_price, currency, status'),
    'expenses': ('报销单', 'id, expense_number, title, customer_id, project_id, total_amount, currency, status, owner_id, is_deleted'),
    'pricing_orders': ('批价单', 'id, order_number, project_id, quotation_id, status, pricing_total_amount, currency, created_by'),
    'users': ('用户', 'id, username, real_name, company_name, department, role'),
    'tasks': ('任务', 'id, title, assignee_id, creator_id, status, priority, due_date, project_id, customer_id, is_deleted'),
}

_TABLE_RELATIONS = """
表关系:
- 项目↔客户: 通过 project_customer_associations(project_id, company_id) 多对多关联
- 联系人→公司: contacts.company_id
- 报价→项目: quotations.project_id，报价→客户: quotations.customer_id
- 报价明细→报价: quotation_details.quotation_id
- 费用→项目: expenses.project_id
- 批价单→项目: pricing_orders.project_id
- 任务→项目: tasks.project_id，任务→客户: tasks.customer_id
""".strip()

_QUERY_EXAMPLES = """
常见查询模板（直接使用，替换关键词即可）：
- 查某公司关联的项目: SELECT p.project_name, p.current_stage, p.status FROM projects p JOIN project_customer_associations pca ON pca.project_id=p.id JOIN companies c ON pca.company_id=c.id WHERE c.company_name ILIKE '%关键词%' AND p.is_deleted=false
- 查某项目的报价: SELECT q.quotation_number, q.amount, q.currency FROM quotations q JOIN projects p ON q.project_id=p.id WHERE p.project_name ILIKE '%关键词%'
- 查某公司的联系人: SELECT name, position, phone, email FROM contacts WHERE company_id=(SELECT id FROM companies WHERE company_name ILIKE '%关键词%' LIMIT 1)
""".strip()


def get_db_schema():
    """返回精简版数据库 schema（表名+关键字段），缓存 1 小时

    直接提供字段列表和表关系，AI 无需查询 information_schema 即可写出正确 SQL。
    """
    global _schema_cache, _schema_cache_time
    if _schema_cache and (time.time() - _schema_cache_time) < 3600:
        return _schema_cache

    lines = ['数据库表（关键字段）:\n']
    for table, (desc, fields) in _TABLE_SCHEMA.items():
        lines.append(f'{table}({desc}): {fields}')
    lines.append(f'\n{_TABLE_RELATIONS}')
    lines.append(f'\n{_BUSINESS_NOTES}')
    lines.append(f'\n{_QUERY_EXAMPLES}')

    _schema_cache = '\n'.join(lines)
    _schema_cache_time = time.time()
    return _schema_cache


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
# 子查询剥离（权限注入辅助）
# ---------------------------------------------------------------------------

def _strip_subqueries(sql):
    """移除 SQL 中括号内的子查询，只保留主查询结构

    用于权限注入时确定主查询中引用了哪些表，
    避免将子查询内的表别名误注入到外层 WHERE。
    """
    result = []
    depth = 0
    for char in sql:
        if char == '(':
            depth += 1
            if depth == 1:
                result.append('()')
        elif char == ')':
            depth -= 1
        elif depth == 0:
            result.append(char)
    return ''.join(result)


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

    # 只提取主查询的表引用（忽略子查询内的表，避免作用域错误）
    main_query_sql = _strip_subqueries(sql)
    table_refs = _extract_table_refs(main_query_sql)
    logger.info(f'[AI DB Debug] 提取到的表引用(主查询): {table_refs}')

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

            # 检测空值并添加 web_search 提示
            has_empty = any(
                val is None or val == '' or val == '暂无'
                for row in rows for val in row
            )
            result = {
                'success': True,
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
            }
            if has_empty:
                result['hint'] = '部分字段为空，如用户需要该信息，请用 web_search 搜索公开信息补充'
            return result

    except Exception as e:
        logger.error(f'[AI DB Query] 执行失败: {e}')
        return {'success': False, 'error': f'查询执行失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 权限上下文生成
# ---------------------------------------------------------------------------

def get_permission_context(user):
    """生成用户权限描述文本，嵌入 system prompt

    包含完整的用户身份和权限摘要，让 AI 能在查询前判断是否越权。

    Args:
        user: 当前用户对象

    Returns:
        str: 权限描述文本
    """
    username = getattr(user, 'username', '')
    real_name = getattr(user, 'real_name', '') or username
    role = getattr(user, 'role', 'user')
    department = getattr(user, 'department', '') or '未分配'

    # 构建各模块权限级别摘要
    permission_lines = []
    if role == 'admin':
        permission_lines.append('角色: 管理员 — 拥有所有模块的 system 级权限，可查看全部数据')
    else:
        modules = ['customer', 'project', 'quotation', 'expense', 'product', 'order']
        module_names = {
            'customer': '客户', 'project': '项目', 'quotation': '报价',
            'expense': '报销单', 'product': '产品', 'order': '订单',
        }
        for mod in modules:
            level = user.get_permission_level(mod)
            can_view = user.has_permission(mod, 'view')
            if not can_view:
                permission_lines.append(f'  {module_names.get(mod, mod)}: 无权访问')
            else:
                scope_desc = {
                    'system': '全部数据',
                    'company': '同公司数据',
                    'department': '同部门数据',
                    'personal': '仅自己的数据+共享数据',
                }.get(level, level)
                permission_lines.append(f'  {module_names.get(mod, mod)}: {scope_desc}')

        # 报销单特殊说明
        expense_level = user.get_permission_level('expense')
        if expense_level == 'personal':
            permission_lines.append('  ⚠️ 报销单为个人隐私数据，仅可查看自己和直属下属的')

    permissions_block = '\n'.join(permission_lines)

    return (
        f'当前用户信息：\n'
        f'- 姓名: {real_name} (username: {username})\n'
        f'- 角色: {role}\n'
        f'- 部门: {department}\n'
        f'\n'
        f'数据权限摘要：\n'
        f'{permissions_block}\n'
        f'\n'
        f'数据库权限规则（仅限制数据库查询，不限制外部搜索）：\n'
        f'- 系统会自动对查询结果进行权限过滤，无需手动添加 owner_id 条件\n'
        f'- 如果用户请求的数据超出上述权限范围，告知该数据不在你的可查范围内\n'
        f'- products 表无访问限制\n'
        f'- users 表仅允许查询 id, username, real_name, department, role 字段\n'
        f'- 所有支持 is_deleted 的表必须添加 AND is_deleted = FALSE\n'
        f'\n'
        f'回复规范（严格遵守）：\n'
        f'- 只输出最终答案，禁止展示思考过程、查询步骤、重试过程\n'
        f'- 禁止出现：表名(companies/projects等)、字段名(owner_id/is_deleted等)、SQL语句、ID编号、权限规则\n'
        f'- 禁止说"让我查询一下"、"先查看X表"、"尝试使用web_search"、"重新查询"、"暂未记录"、"数据库中"\n'
        f'- 数据库查不到或返回字段为空时，静默使用 web_search 补充，不解释切换原因\n'
        f'- 都查不到就简短告知"暂无该信息"，不解释内部原因\n'
        f'- 用自然语言回复，像一个业务助理而非程序员'
    )
