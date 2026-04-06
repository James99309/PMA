# -*- coding: utf-8 -*-
"""
Skill 执行引擎

执行 CliSkill 定义:
    1. 渲染 SQL 模板(填入用户参数 + 前序步骤结果)
    2. 顺序执行各查询步骤(通过 execute_safe_query 自动注入权限)
    3. 用 output_format 模板生成 Markdown 最终输出

安全:
    - 用户参数值仅做 值替换,不允许注入 SQL 片段
    - 字符串参数自动转义单引号并包裹 SQL 引号
    - 数值参数做类型校验
    - 日期参数生成 ISO 格式字符串
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 日期 / 周期自动计算
# ---------------------------------------------------------------------------

def _compute_period(period_value: str) -> tuple[str, str]:
    """根据 period 关键词计算 (start, end) 日期字符串(YYYY-MM-DD)。

    支持:
        this_week / last_week
        this_month / last_month
        this_quarter / last_quarter
        this_year / last_year
    """
    today = date.today()

    if period_value == 'this_week':
        monday = today - timedelta(days=today.weekday())
        return monday.isoformat(), today.isoformat()

    if period_value == 'last_week':
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(weeks=1)
        last_sunday = this_monday - timedelta(days=1)
        return last_monday.isoformat(), last_sunday.isoformat()

    if period_value == 'this_month':
        first = today.replace(day=1)
        return first.isoformat(), today.isoformat()

    if period_value == 'last_month':
        first_this = today.replace(day=1)
        last_day_prev = first_this - timedelta(days=1)
        first_prev = last_day_prev.replace(day=1)
        return first_prev.isoformat(), last_day_prev.isoformat()

    if period_value == 'this_quarter':
        q_month = ((today.month - 1) // 3) * 3 + 1
        first = today.replace(month=q_month, day=1)
        return first.isoformat(), today.isoformat()

    if period_value == 'last_quarter':
        q_month = ((today.month - 1) // 3) * 3 + 1
        first_this_q = today.replace(month=q_month, day=1)
        last_day_prev_q = first_this_q - timedelta(days=1)
        prev_q_month = ((last_day_prev_q.month - 1) // 3) * 3 + 1
        first_prev_q = last_day_prev_q.replace(month=prev_q_month, day=1)
        return first_prev_q.isoformat(), last_day_prev_q.isoformat()

    if period_value == 'this_year':
        first = today.replace(month=1, day=1)
        return first.isoformat(), today.isoformat()

    if period_value == 'last_year':
        first = today.replace(year=today.year - 1, month=1, day=1)
        last = today.replace(year=today.year - 1, month=12, day=31)
        return first.isoformat(), last.isoformat()

    raise ValueError(f'不支持的 period 值: {period_value}')


# ---------------------------------------------------------------------------
# 参数安全处理
# ---------------------------------------------------------------------------

_SAFE_PERIOD_VALUES = frozenset({
    'this_week', 'last_week', 'this_month', 'last_month',
    'this_quarter', 'last_quarter', 'this_year', 'last_year',
})


def _escape_sql_string(value: str) -> str:
    """转义字符串用于 SQL 字面量(防注入)。

    只允许作为值出现,返回带单引号包裹的结果:  'escaped_value'
    """
    # 替换单引号为两个单引号(SQL 标准转义)
    escaped = value.replace("'", "''")
    # 移除分号(阻止语句拼接)
    escaped = escaped.replace(';', '')
    # 移除注释符号
    escaped = escaped.replace('--', '')
    escaped = escaped.replace('/*', '')
    escaped = escaped.replace('*/', '')
    return f"'{escaped}'"


def _validate_and_prepare_params(
    param_defs: list[dict],
    raw_params: dict,
) -> dict[str, str]:
    """校验用户传入参数并转为 SQL-safe 替换值。

    Returns:
        dict 映射 param_name → 可直接替换到 SQL 中的字符串。
        对字符串参数,值已带单引号;对数值,是纯数字字符串。
    """
    prepared: dict[str, str] = {}
    period_start: str | None = None
    period_end: str | None = None

    for pdef in param_defs:
        name = pdef.get('name', '')
        ptype = pdef.get('type', 'string')
        required = pdef.get('required', False)
        default_value = pdef.get('default_value')

        value = raw_params.get(name)

        # 缺失处理
        if value is None or (isinstance(value, str) and not value.strip()):
            if default_value is not None:
                value = default_value
            elif required:
                raise ValueError(f'缺少必填参数: {name}')
            else:
                # 可选参数无默认值 → 空字符串
                value = ''

        # 按类型转换
        if ptype == 'number' or ptype == 'integer':
            try:
                num = float(value) if '.' in str(value) else int(value)
                prepared[name] = str(num)
            except (TypeError, ValueError):
                raise ValueError(f'参数 {name} 应为数字,实际值: {value}')

        elif ptype == 'period':
            str_val = str(value).strip().lower()
            if str_val not in _SAFE_PERIOD_VALUES:
                raise ValueError(
                    f'参数 {name} 的值 "{value}" 不在允许列表中。'
                    f'可选: {", ".join(sorted(_SAFE_PERIOD_VALUES))}'
                )
            prepared[name] = _escape_sql_string(str_val)
            period_start, period_end = _compute_period(str_val)

        elif ptype == 'date':
            # 校验 ISO 格式
            try:
                datetime.strptime(str(value), '%Y-%m-%d')
            except ValueError:
                raise ValueError(f'参数 {name} 应为 YYYY-MM-DD 格式,实际值: {value}')
            prepared[name] = _escape_sql_string(str(value))

        elif ptype == 'boolean':
            bool_val = str(value).lower() in ('true', '1', 'yes')
            prepared[name] = 'TRUE' if bool_val else 'FALSE'

        else:
            # 默认按字符串处理
            prepared[name] = _escape_sql_string(str(value))

    # 注入 period 特殊参数
    if period_start is not None:
        prepared['period_start'] = _escape_sql_string(period_start)
        prepared['period_end'] = _escape_sql_string(period_end)

    return prepared


# ---------------------------------------------------------------------------
# SQL 模板渲染
# ---------------------------------------------------------------------------

# 匹配 {xxx} 占位符,包括 {step.N.field} 和 {param_name}
_PLACEHOLDER_RE = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_.]*)\}')


def _render_sql_template(
    sql_template: str,
    params: dict[str, str],
    step_results: dict[str, dict],
) -> str:
    """将 SQL 模板中的占位符替换为实际值。

    占位符格式:
        {param_name}         — 用户参数(已经过安全转换)
        {step_name.N.field}  — 前序步骤第 N 行的某字段值
        {period_start}       — 由 period 参数自动计算
        {period_end}         — 由 period 参数自动计算
    """
    def _replacer(match: re.Match) -> str:
        key = match.group(1)

        # 直接参数匹配(含 period_start / period_end)
        if key in params:
            return params[key]

        # 步骤引用: step_name.N.field
        parts = key.split('.')
        if len(parts) == 3:
            step_name, idx_str, field = parts
            if step_name in step_results:
                try:
                    idx = int(idx_str)
                except ValueError:
                    logger.warning(f'[SkillEngine] 无效的行号引用: {key}')
                    return match.group(0)  # 原样保留

                rows = step_results[step_name].get('rows', [])
                columns = step_results[step_name].get('columns', [])

                if idx < 0 or idx >= len(rows):
                    logger.warning(
                        f'[SkillEngine] 步骤 {step_name} 行号 {idx} 越界'
                        f'(共 {len(rows)} 行)'
                    )
                    return 'NULL'

                if field not in columns:
                    logger.warning(
                        f'[SkillEngine] 步骤 {step_name} 无字段 {field},'
                        f' 可用: {columns}'
                    )
                    return 'NULL'

                col_idx = columns.index(field)
                val = rows[idx][col_idx]
                if val is None:
                    return 'NULL'
                # 数值直接返回,字符串转义
                if isinstance(val, (int, float)):
                    return str(val)
                return _escape_sql_string(str(val))

        # 未匹配 → 原样保留(让 execute_safe_query 报错更明确)
        logger.warning(f'[SkillEngine] 未解析的占位符: {{{key}}}')
        return match.group(0)

    return _PLACEHOLDER_RE.sub(_replacer, sql_template)


# ---------------------------------------------------------------------------
# 输出模板渲染
# ---------------------------------------------------------------------------

def _render_markdown_table(columns: list[str], rows: list[list]) -> str:
    """将查询结果渲染为 Markdown 表格。"""
    if not columns:
        return '(无数据)'
    if not rows:
        return f'| {" | ".join(columns)} |\n| {" | ".join(["---"] * len(columns))} |\n| (无记录) |'

    # 表头
    lines = [
        '| ' + ' | '.join(str(c) for c in columns) + ' |',
        '| ' + ' | '.join(['---'] * len(columns)) + ' |',
    ]
    # 数据行
    for row in rows:
        cells = []
        for val in row:
            s = '' if val is None else str(val)
            # 管道符转义
            s = s.replace('|', '\\|')
            cells.append(s)
        lines.append('| ' + ' | '.join(cells) + ' |')

    return '\n'.join(lines)


def _get_step_cell(step_results: dict, key: str) -> str:
    """解析 step_name.N.field 并返回单元格值的字符串形式。"""
    parts = key.split('.')
    if len(parts) != 3:
        return f'{{{key}}}'

    step_name, idx_str, field = parts
    if step_name not in step_results:
        return f'{{{key}}}'

    try:
        idx = int(idx_str)
    except ValueError:
        return f'{{{key}}}'

    result = step_results[step_name]
    rows = result.get('rows', [])
    columns = result.get('columns', [])

    if idx < 0 or idx >= len(rows):
        return '(N/A)'
    if field not in columns:
        return '(N/A)'

    col_idx = columns.index(field)
    val = rows[idx][col_idx]
    return '' if val is None else str(val)


def _render_output_template(
    template: str | None,
    params: dict[str, str],
    raw_params: dict,
    step_results: dict[str, dict],
) -> str:
    """渲染输出格式模板。

    支持的占位符:
        {step_name.table}     → 整个结果渲染为 Markdown 表格
        {step_name.N.field}   → 特定单元格值
        {step_name.count}     → 步骤结果行数
        {param_name}          → 用户输入的原始参数值(不带 SQL 引号)
        {if step_name}...{endif}  → 当步骤有数据时显示内容
        {if !step_name}...{endif} → 当步骤无数据时显示内容
    """
    if not template:
        return _fallback_output(step_results)

    output = template

    # 1. 处理条件块: {if step_name}...{endif} 和 {if !step_name}...{endif}
    # 正向条件
    def _replace_if_positive(match: re.Match) -> str:
        step_name = match.group(1)
        content = match.group(2)
        if step_name in step_results and step_results[step_name].get('row_count', 0) > 0:
            return content
        return ''

    output = re.sub(
        r'\{if\s+([a-zA-Z_]\w*)\}(.*?)\{endif\}',
        _replace_if_positive,
        output,
        flags=re.DOTALL,
    )

    # 反向条件
    def _replace_if_negative(match: re.Match) -> str:
        step_name = match.group(1)
        content = match.group(2)
        if step_name not in step_results or step_results[step_name].get('row_count', 0) == 0:
            return content
        return ''

    output = re.sub(
        r'\{if\s+!([a-zA-Z_]\w*)\}(.*?)\{endif\}',
        _replace_if_negative,
        output,
        flags=re.DOTALL,
    )

    # 2. 替换 {step_name.table}
    def _replace_table(match: re.Match) -> str:
        step_name = match.group(1)
        if step_name in step_results:
            result = step_results[step_name]
            return _render_markdown_table(
                result.get('columns', []),
                result.get('rows', []),
            )
        return f'(步骤 {step_name} 无数据)'

    output = re.sub(r'\{([a-zA-Z_]\w*)\.table\}', _replace_table, output)

    # 3. 替换 {step_name.count}
    def _replace_count(match: re.Match) -> str:
        step_name = match.group(1)
        if step_name in step_results:
            return str(step_results[step_name].get('row_count', 0))
        return '0'

    output = re.sub(r'\{([a-zA-Z_]\w*)\.count\}', _replace_count, output)

    # 4. 替换 {step_name.N.field}
    def _replace_cell(match: re.Match) -> str:
        return _get_step_cell(step_results, match.group(1))

    output = re.sub(
        r'\{([a-zA-Z_]\w+\.\d+\.[a-zA-Z_]\w*)\}',
        _replace_cell,
        output,
    )

    # 5. 替换 {param_name} — 用原始值(人类可读),不是 SQL 安全值
    def _replace_param(match: re.Match) -> str:
        key = match.group(1)
        # 先看原始参数
        if key in raw_params:
            return str(raw_params[key])
        # 再看 period_start / period_end(去掉引号)
        if key in params:
            val = params[key]
            # 去掉 SQL 单引号包裹
            if val.startswith("'") and val.endswith("'"):
                return val[1:-1]
            return val
        return match.group(0)

    output = re.sub(r'\{([a-zA-Z_]\w*)\}', _replace_param, output)

    return output.strip()


def _fallback_output(step_results: dict[str, dict]) -> str:
    """无输出模板时的默认输出:按步骤逐个输出表格。"""
    parts: list[str] = []
    for step_name, result in step_results.items():
        columns = result.get('columns', [])
        rows = result.get('rows', [])
        row_count = result.get('row_count', 0)
        parts.append(f'### {step_name} ({row_count} 行)')
        parts.append(_render_markdown_table(columns, rows))
        parts.append('')
    return '\n'.join(parts).strip() if parts else '(查询完成,无数据返回)'


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------

class SkillEngine:
    """执行 CliSkill 定义的引擎。

    典型调用:
        result = SkillEngine.execute(skill, params, user)
        # result = {'success': True, 'output': '...markdown...', 'raw_results': {...}}
    """

    @staticmethod
    def execute(skill, params: dict, user) -> dict:
        """执行一个技能定义并返回格式化结果。

        Args:
            skill: CliSkill 模型实例(含 parameters / queries / output_format)。
            params: 用户提供的参数字典(由 LLM 解析填充)。
            user: 当前用户对象(用于 execute_safe_query 的权限过滤)。

        Returns:
            {
                'success': True,
                'output': '格式化的 Markdown 字符串',
                'raw_results': {step_name: {columns, rows, row_count}},
            }
            或
            {
                'success': False,
                'error': '错误描述',
            }
        """
        skill_name = getattr(skill, 'name', '?')
        logger.info(f'[SkillEngine] 开始执行技能: {skill_name}, 参数: {params}')

        # --- 1. 校验并准备参数 ---
        param_defs = skill.parameters or []
        try:
            prepared_params = _validate_and_prepare_params(param_defs, params)
        except ValueError as e:
            logger.warning(f'[SkillEngine] 参数校验失败: {e}')
            return {'success': False, 'error': f'参数错误: {e}'}

        # --- 2. 顺序执行 SQL 查询 ---
        queries = skill.queries or []
        if not queries:
            return {'success': False, 'error': '技能未定义查询步骤'}

        step_results: dict[str, dict] = {}

        from app.services.chat_db_query import execute_safe_query

        for i, query_def in enumerate(queries):
            sql_template = query_def.get('sql', '').strip()
            step_name = query_def.get('as_name', f'step_{i}')
            step_desc = query_def.get('description', '')

            if not sql_template:
                logger.warning(f'[SkillEngine] 步骤 {step_name} 的 SQL 为空,跳过')
                continue

            # 渲染 SQL 模板
            try:
                rendered_sql = _render_sql_template(
                    sql_template, prepared_params, step_results,
                )
            except Exception as e:
                logger.exception(f'[SkillEngine] 步骤 {step_name} SQL 渲染失败')
                return {
                    'success': False,
                    'error': f'步骤 {step_name} 模板渲染失败: {e}',
                }

            # 检查是否仍有未解析的占位符
            unresolved = _PLACEHOLDER_RE.findall(rendered_sql)
            # 过滤掉可能是 SQL 函数(如 extract)的误匹配
            real_unresolved = [
                p for p in unresolved
                if not p.startswith('step_') or '.' in p
                # 保留 step 引用类的未解析(可能真的缺依赖)
            ]
            if real_unresolved:
                logger.warning(
                    f'[SkillEngine] 步骤 {step_name} 仍有未解析占位符: {real_unresolved}'
                )

            logger.info(
                f'[SkillEngine] 执行步骤 {i + 1}/{len(queries)}: '
                f'{step_name} — {step_desc or "(无描述)"}'
            )
            logger.debug(f'[SkillEngine] 渲染后 SQL: {rendered_sql[:500]}')

            # 执行查询
            try:
                result = execute_safe_query(rendered_sql, user)
            except Exception as e:
                logger.exception(f'[SkillEngine] 步骤 {step_name} 查询执行异常')
                return {
                    'success': False,
                    'error': f'步骤 {step_name} 执行失败: {e}',
                }

            if not result.get('success'):
                error_msg = result.get('error', '查询失败')
                logger.warning(
                    f'[SkillEngine] 步骤 {step_name} 查询失败: {error_msg}'
                )
                return {
                    'success': False,
                    'error': f'步骤 {step_name} 查询失败: {error_msg}',
                }

            # 保存结果供后续步骤引用
            step_results[step_name] = {
                'columns': result.get('columns', []),
                'rows': result.get('rows', []),
                'row_count': result.get('row_count', len(result.get('rows', []))),
            }

            logger.info(
                f'[SkillEngine] 步骤 {step_name} 完成: '
                f'{step_results[step_name]["row_count"]} 行'
            )

        # --- 3. 渲染输出模板 ---
        try:
            output = _render_output_template(
                skill.output_format,
                prepared_params,
                params,          # 原始参数用于人类可读输出
                step_results,
            )
        except Exception as e:
            logger.exception('[SkillEngine] 输出模板渲染失败')
            # 降级:返回原始数据
            output = _fallback_output(step_results)
            output = f'(输出模板渲染失败,使用默认格式)\n\n{output}'

        logger.info(f'[SkillEngine] 技能 {skill_name} 执行完成')

        return {
            'success': True,
            'output': output,
            'raw_results': step_results,
        }
