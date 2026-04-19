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
                desc = pdef.get('description', '')
                raise ValueError(
                    f'缺少必填参数: {name} ({desc})。'
                    f'请从用户消息中提取该值并重新调用 invoke_skill。'
                )
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
    artifacts_out: list | None = None,
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

    # 2b. 替换 {step_name.artifact} 和 {step_name.artifact:"标题"}
    _arts = artifacts_out if artifacts_out is not None else []

    def _replace_artifact(match: re.Match) -> str:
        step_name = match.group(1)
        title = match.group(2) or ''
        return _collect_artifact_table(step_name, step_results, title, _arts)

    output = re.sub(r'\{([a-zA-Z_]\w*)\.artifact(?::"([^"]*)")?\}', _replace_artifact, output)

    # 2c. 替换 {step_name.artifact_card} 或 {step_name.artifact_card:"title=col,sub=col,tags=col1|col2,kv=col3|col4"}
    def _replace_artifact_card(match: re.Match) -> str:
        step_name = match.group(1)
        mapping_str = match.group(2) or ''
        return _collect_artifact_card(step_name, step_results, mapping_str, _arts)

    output = re.sub(r'\{([a-zA-Z_]\w*)\.artifact_card(?::"([^"]*)")?\}', _replace_artifact_card, output)

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


_ARTIFACT_CSS = """
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;font-size:13px;color:#111827;background:#fff;padding:4px}
  table{border-collapse:collapse;width:100%;font-size:13px}
  thead tr{background:#f9fafb;border-bottom:1px solid #e5e7eb}
  th{padding:8px 12px;text-align:left;font-weight:600;color:#374151;white-space:nowrap;font-size:12px;letter-spacing:.02em}
  td{padding:7px 12px;border-bottom:1px solid #f3f4f6;vertical-align:top;color:#111827}
  tbody tr:last-child td{border-bottom:none}
  tbody tr:hover td{background:#f9fafb}
  td.num{text-align:right;font-variant-numeric:tabular-nums;color:#374151}
  .empty{text-align:center;color:#9ca3af;padding:20px;font-size:12px}
  .card{display:flex;align-items:flex-start;gap:12px;padding:4px 0}
  .av{width:36px;height:36px;border-radius:50%;background:#e5e7eb;color:#374151;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0}
  .info{flex:1;min-width:0}
  .card-title{font-weight:600;font-size:14px;color:#111827}
  .card-sub{color:#6b7280;font-size:12px;margin-top:2px}
  .tags{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}
  .tag{font-size:11px;padding:2px 8px;border-radius:99px;background:#f3f4f6;color:#374151;border:0.5px solid #e5e7eb}
  .kv-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;margin-top:8px}
  .kv{padding:8px 10px;border:0.5px solid #e5e7eb;border-radius:8px;background:#f9fafb}
  .kv-label{font-size:11px;color:#9ca3af;margin-bottom:2px}
  .kv-value{font-size:13px;font-weight:600;color:#111827}
"""

def _build_artifact_html(title: str, body_html: str) -> dict:
    """包装成完整自包含 HTML 文档，供 iframe srcdoc 使用。"""
    html = (
        f'<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<style>{_ARTIFACT_CSS}</style></head>'
        f'<body>{body_html}</body></html>'
    )
    return {'title': title, 'html': html}


def _esc(v) -> str:
    return str(v).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if v is not None else ''


def _collect_artifact_table(step_name: str, step_results: dict, title: str, artifacts_out: list) -> str:
    """生成 Claude 极简风格表格 artifact。"""
    result = step_results.get(step_name)
    if not result or not result.get('rows'):
        return '(无数据)'

    columns = result.get('columns', [])
    rows = result.get('rows', [])

    # 数字列右对齐
    def _is_num(col_idx):
        for row in rows[:5]:
            v = row[col_idx] if col_idx < len(row) else None
            if v is not None and not isinstance(v, (int, float)):
                try: float(str(v).replace(',', ''))
                except ValueError: return False
        return True

    num_cols = {i for i in range(len(columns)) if _is_num(i)}

    thead = ''.join(f'<th>{_esc(c)}</th>' for c in columns)
    tbody = ''.join(
        '<tr>' + ''.join(
            f'<td class="num">{_esc(cell)}</td>' if i in num_cols else f'<td>{_esc(cell)}</td>'
            for i, cell in enumerate(row)
        ) + '</tr>'
        for row in rows
    ) or f'<tr><td colspan="{len(columns)}" class="empty">暂无数据</td></tr>'

    body_html = f'<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>'
    artifacts_out.append(_build_artifact_html(title or step_name, body_html))
    return f'*（{title or step_name}，共 {len(rows)} 条）*'


def _parse_card_mapping(mapping_str: str, columns: list) -> dict:
    """解析 artifact_card 参数字符串，返回 {role: [col_name, ...]} 映射。

    格式: "title=姓名,sub=部门,tags=角色|职级,kv=入职日期|直属上级,_label=用户信息"
    _label 为卡片区块标题（不对应列名）。
    若未提供参数，自动按列顺序分配：第1列→title，第2列→sub，其余→kv。
    """
    mapping = {'title': [], 'sub': [], 'tags': [], 'kv': [], '_label': []}
    if mapping_str.strip():
        for part in mapping_str.split(','):
            part = part.strip()
            if '=' not in part:
                continue
            role, cols_str = part.split('=', 1)
            role = role.strip()
            if role == '_label':
                mapping['_label'] = [cols_str.strip()]
                continue
            col_names = [c.strip() for c in cols_str.split('|') if c.strip()]
            if role in mapping:
                mapping[role] = col_names
    else:
        # 自动分配
        if len(columns) >= 1:
            mapping['title'] = [columns[0]]
        if len(columns) >= 2:
            mapping['sub'] = [columns[1]]
        if len(columns) > 2:
            mapping['kv'] = list(columns[2:])
    return mapping


def _collect_artifact_card(step_name: str, step_results: dict, mapping_str: str, artifacts_out: list) -> str:
    """生成可配置的 Claude 极简风格卡片 artifact。

    占位符: {step.artifact_card} 或 {step.artifact_card:"title=姓名,sub=部门,tags=角色|职级,kv=入职日期"}
    """
    result = step_results.get(step_name)
    if not result or not result.get('rows'):
        return '(无数据)'

    columns = result.get('columns', [])
    rows = result.get('rows', [])
    mapping = _parse_card_mapping(mapping_str, columns)

    def _get_val(row, col_name):
        return str(row[columns.index(col_name)]) if col_name in columns else ''

    cards_html = []
    for row in rows:
        title_val = ' '.join(_get_val(row, c) for c in mapping['title'] if _get_val(row, c))
        sub_val = ' · '.join(_get_val(row, c) for c in mapping['sub'] if _get_val(row, c))
        tag_vals = [_get_val(row, c) for c in mapping['tags'] if _get_val(row, c)]
        kv_vals = [(c, _get_val(row, c)) for c in mapping['kv'] if _get_val(row, c)]

        initial = _esc(title_val[0].upper()) if title_val else '?'
        sub_html = f'<div class="card-sub">{_esc(sub_val)}</div>' if sub_val else ''
        tags_html = (
            '<div class="tags">' + ''.join(f'<span class="tag">{_esc(t)}</span>' for t in tag_vals) + '</div>'
        ) if tag_vals else ''
        kv_html = (
            '<div class="kv-grid">' +
            ''.join(f'<div class="kv"><div class="kv-label">{_esc(k)}</div><div class="kv-value">{_esc(v)}</div></div>' for k, v in kv_vals) +
            '</div>'
        ) if kv_vals else ''

        cards_html.append(
            f'<div class="card">'
            f'<div class="av">{initial}</div>'
            f'<div class="info">'
            f'<div class="card-title">{_esc(title_val)}</div>'
            f'{sub_html}{tags_html}{kv_html}'
            f'</div></div>'
        )

    sep = '<hr style="border:none;border-top:0.5px solid #f3f4f6;margin:8px 0">'
    body_html = sep.join(cards_html)
    display_label = mapping['_label'][0] if mapping['_label'] else step_name
    artifacts_out.append(_build_artifact_html(display_label, body_html))

    summary = title_val if len(rows) == 1 else f'{len(rows)} 条记录'
    return f'*（{summary}）*'


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
# Python 渲染函数执行（SQL skill render body）
# ---------------------------------------------------------------------------

_SAFE_BUILTINS = {
    '__builtins__': {
        'str': str, 'int': int, 'float': float, 'bool': bool,
        'len': len, 'range': range, 'sorted': sorted, 'reversed': reversed,
        'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
        'dict': dict, 'list': list, 'set': set, 'frozenset': frozenset, 'tuple': tuple,
        'sum': sum, 'min': min, 'max': max, 'round': round, 'abs': abs,
        'isinstance': isinstance, 'type': type,
        'print': print,  # 调试用，输出到 server log
        'True': True, 'False': False, 'None': None,
    }
}


def _execute_render_body(
    code: str,
    step_results: dict[str, dict],
    raw_params: dict,
) -> tuple[str, list]:
    """执行 SQL skill 的 Python 渲染函数，返回 (Markdown字符串, artifacts列表)。

    代码必须定义 `def render(results, params): return str`。
    render 函数可调用注入的辅助函数：
      artifact_table(step_name, title='')  → 生成表格 artifact，返回占位文字
      artifact_card(step_name, mapping='') → 生成卡片 artifact，返回占位文字
    执行失败时降级到 _fallback_output 并附加错误提示。
    """
    collected_artifacts: list = []

    def _helper_artifact_table(step_name: str, title: str = '') -> str:
        return _collect_artifact_table(step_name, step_results, title, collected_artifacts)

    def _helper_artifact_card(step_name: str, mapping: str = '') -> str:
        return _collect_artifact_card(step_name, step_results, mapping, collected_artifacts)

    namespace: dict = dict(_SAFE_BUILTINS)
    namespace['artifact_table'] = _helper_artifact_table
    namespace['artifact_card'] = _helper_artifact_card

    try:
        exec(compile(code, '<skill_render_body>', 'exec'), namespace)  # noqa: S102
    except SyntaxError as e:
        logger.warning(f'[SkillEngine] render_body 编译失败: {e}')
        return _fallback_output(step_results) + f'\n\n> ⚠️ 渲染函数语法错误: {e}', []

    render_fn = namespace.get('render')
    if not callable(render_fn):
        logger.warning('[SkillEngine] render_body 未定义 render() 函数')
        return _fallback_output(step_results) + '\n\n> ⚠️ 渲染函数未定义 render(results, params)', []

    try:
        result = render_fn(step_results, raw_params)
        if not isinstance(result, str):
            result = str(result)
        return result.strip(), collected_artifacts
    except Exception as e:
        logger.warning(f'[SkillEngine] render_body 执行异常: {e}')
        return _fallback_output(step_results) + f'\n\n> ⚠️ 渲染函数执行失败: {e}', []


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

        # --- 3. 渲染输出 ---
        # 优先级：SQL skill_body render() > output_format 模板 > fallback 默认
        artifacts: list[dict] = []
        try:
            if skill.skill_type == 'sql' and skill.skill_body:
                output, body_artifacts = _execute_render_body(skill.skill_body, step_results, params)
                artifacts.extend(body_artifacts)
            else:
                output = _render_output_template(
                    skill.output_format,
                    prepared_params,
                    params,
                    step_results,
                    artifacts_out=artifacts,
                )
        except Exception as e:
            logger.exception('[SkillEngine] 输出渲染失败')
            output = _fallback_output(step_results)
            output = f'(输出渲染失败,使用默认格式)\n\n{output}'

        logger.info(
            f'[SkillEngine] 技能 {skill_name} 执行完成，'
            f'artifacts={len(artifacts)}'
        )

        return {
            'success': True,
            'output': output,
            'artifacts': artifacts,
            'raw_results': step_results,
        }
