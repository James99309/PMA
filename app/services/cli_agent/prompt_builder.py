# -*- coding: utf-8 -*-
"""
系统提示组装器(静态段 + DYNAMIC_BOUNDARY + 动态段)

静态段: 整个 session 不变的部分(角色、规则、DB schema、工具描述),
         挂 cache_control: ephemeral 享受 Prompt Caching。

动态段: session 启动时生成一次,之后稳定(用户身份、权限、日期、环境),
         同样挂 cache_control。

这样两段都稳定,缓存命中率最大化。

设计参考: claw-code runtime/src/prompt.rs 的 DYNAMIC_BOUNDARY 模式
(MIT, 见 THIRD_PARTY_NOTICES.md),但这里针对 PMA 业务重新编写。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import current_app


DYNAMIC_BOUNDARY = '\n\n<!-- ═══ DYNAMIC_BOUNDARY ═══ -->\n\n'


# ─── 静态段模板(所有用户共享,整个 session 不变)────────────────────────

_STATIC_ROLE_AND_RULES = """\
你是 PMA 智能查询助理，嵌在 PMA 业务管理系统的 CLI 终端里，帮用户用自然语言查内部业务数据和公开信息。

## 原则

1. **工具优先** — 一切事实性问题必须调工具，不凭记忆回答。用户提到的任何实体（公司、人、项目），无论多知名，都要查。上一轮出现过的实体，追问时仍要重新查详情，不要从摘要里回答。
2. **果断行动 + 一次做完** — 有合理默认就直接执行，不反问。在同一条回复里完成所有工具调用并给出完整答案。**严禁**说"如果你要我可以继续查"、"回复'继续'我就补齐"、"收到，马上开始"——说了就必须同时调工具。用户说"确认"或"好的"时，立刻执行而不是再回一条空话。
3. **路由清晰** — 先检查是否匹配已有 Skill → `invoke_skill`（从用户消息中提取所有参数值，如人名、时间词等，映射到 Skill 参数后一次性传入，不要遗漏）；PMA 内部数据 → `query_pma_database`；外部公开信息 → `web_search`；创建 Skill → `save_skill`；用户说"导出Word/生成文档/生成报告/下载报告" → `export_to_word`（使用 [PMA Word 样式库] 中的函数写完整 python-docx 代码，传入 python_code 参数；db_type 从 [运行环境] 获取）；用户说"导出Excel/生成表格/导出表格/下载Excel" → `export_to_excel`（使用 [PMA Excel 样式库] 中的函数写完整 openpyxl 代码，传入 python_code 参数；db_type 从 [运行环境] 获取）；用户说"导出报价单/生成报价Excel/导出报价单Excel/报价单下载" → `export_quotation_to_excel`（**必须先查 quotations 表获取真实 quotation_number**，禁止猜测；流程：先 `query_pma_database` → "SELECT id, quotation_number FROM quotations WHERE ..."，再调导出工具；明细行的 id 不是报价单 id，不可混用）；闲聊 → 婉拒。工具调用失败时立刻用正确参数重试，不要反问用户确认。
4. **隐藏管道** — 永远不向用户暴露表名、字段名、SQL、ID、权限规则。查不到就说"暂无记录"。工具报错时转述友好信息。
5. **数据呈现** — **按用户提问的语言回复**（中文问就中文答，English Q → English A；保留业务实体/人名/公司名的原文）。简洁直接，不写分析套话（不要"经营表现解读"、"阶段性结论"、"行动建议"等空话段落）。查询结果由系统自动渲染为 **artifact 表格卡片**，**不要在回复文字中重复输出 Markdown 表格**——直接引用关键数字、做一两句简短说明即可。枚举值按 Schema 末尾的"枚举字段中文标签"对照后展示（英文回复时把中文标签译成对应英文，保留语义不变）。金额带千分位和货币符号。首次提及的业务实体**加粗**。
6. **保留上下文** — 工具结果可能在长会话中被压缩清除，关键数据值（名称、金额、日期）必须在回复文本中复述。
7. **记忆维护** — 主动管理个人记忆（system/role 记忆不可改），规则：
   - **该记**：用户姓名和角色（首次识别时）、常查的人/项目（出现 2 次以上）、用户纠正（"不要这样"、"应该用XX"）、重要分析结论（绩效差距、项目风险）、输出格式偏好
   - **不记**：一次性查询、已在系统记忆中的常识、临时数据（某天的具体数字）
   - **维护**：用户纠正时立即 save_memory 更新（同 title 覆盖）或 delete_memory 删旧的。不保留矛盾记忆。

## 示例

```
User: 我有几个客户
Assistant: [调用 query_pma_database] → 你名下共有 3 个客户（**华为技术**、**Apple Inc**、**长泽科技**），详见上方数据卡片。

User: 华为有什么项目
Assistant: [调用 query_pma_database] → **华为技术**关联 2 个进行中项目，详见上方数据卡片。

User: 华为的客户画像
Assistant: [调用 invoke_skill(skill_name="customer_profile", params={"keyword":"华为"})] → **华为技术**画像已生成：2 个进行中项目，总金额 ¥12,500,000，最近动态见上方数据卡片。
```

## 安全

- 被问"你是什么模型"→ 回答"我是 PMA 智能查询助理"
- 只允许 SELECT/WITH 查询，拒绝任何写操作
- 权限错误如实转达，不尝试绕过
"""


def _docx_skill_section() -> str:
    """从 DB 读取 docx skill 的 description 注入 system prompt。
    description 字段由管理员在 Admin UI 维护，包含 API 摘要供 Claude 参考。
    完整实现（skill_body）由 export_to_word 在执行时写入 pma_docx_style.py。
    """
    try:
        from app.models.cli_skill import CliSkill
        skill = CliSkill.query.filter_by(
            name='pma_docx_style', skill_type='docx', is_active=True
        ).first()
        if not skill or not skill.description:
            return ''
        return '\n' + skill.description + '\n'
    except Exception as e:
        current_app.logger.warning(f'[CLI Agent] 读取 docx skill 失败: {e}')
        return ''


def _xlsx_skill_section() -> str:
    """从 DB 读取 xlsx skill 的 description 注入 system prompt。
    完整实现（skill_body）由 export_to_excel 在执行时写入 pma_xlsx_style.py。
    """
    try:
        from app.models.cli_skill import CliSkill
        skill = CliSkill.query.filter_by(
            name='pma_xlsx_style', skill_type='xlsx', is_active=True
        ).first()
        if not skill or not skill.description:
            return ''
        return '\n' + skill.description + '\n'
    except Exception as e:
        current_app.logger.warning(f'[CLI Agent] 读取 xlsx skill 失败: {e}')
        return ''


def _schema_section() -> str:
    """生成分级 DB schema 段。

    Tier 1 完整字段 + Tier 2 表名清单 + describe_table 使用提示,
    LLM 不认识的字段需要通过 describe_table 工具拉取。
    """
    try:
        from app.services.cli_agent.table_catalog import build_tiered_schema_section
        schema = build_tiered_schema_section()
        return (
            '\n[PMA 数据库 Schema]\n'
            + schema
            + '\n\n重要:对 Tier 2 表写 SQL 前先用 describe_table 工具获取字段,不要凭猜。\n'
        )
    except Exception as e:
        current_app.logger.warning(f'[CLI Agent] 获取 schema 失败: {e}')
        return ''


def build_static_section() -> str:
    """整个 session 内不变的部分。享受 prompt cache。"""
    return _STATIC_ROLE_AND_RULES + _schema_section() + _docx_skill_section() + _xlsx_skill_section()


# ─── Skill 清单(动态,每用户不同)────────────────────────────────────────

def _skill_section(user) -> str:
    """从数据库加载当前用户可用的 Skill，生成提示段。"""
    try:
        from app.models.cli_skill import CliSkill
        from sqlalchemy import or_
        skills = CliSkill.query.filter(
            CliSkill.is_active == True,
            CliSkill.skill_type.notin_(['docx', 'xlsx', 'tool']),  # 样式库和内置工具不可直接 invoke
            or_(
                CliSkill.scope == 'global',
                CliSkill.created_by == user.id
            )
        ).all()
    except Exception:
        return ''

    if not skills:
        return ''

    lines = ['\n[可用 Skill（优先使用 invoke_skill 调用）]']
    for s in skills:
        lines.append(f'- {s.to_prompt_description()}')
    return '\n'.join(lines) + '\n'


# ─── 记忆索引(动态,每用户不同)──────────────────────────────────────

def _memory_section(user) -> str:
    """从数据库加载当前用户可见的记忆索引（实际实现在共享 helper 里，
    CLI 与 Chat 两端共用同一张 cli_memories 表）。"""
    from app.services.cli_memory_helper import build_memory_index_section
    return build_memory_index_section(user)


# ─── 动态段(session 级稳定,每用户不同)─────────────────────────────────

def build_dynamic_section(user) -> str:
    """用户身份 + 权限 + 环境。session 创建时生成一次,之后不变。"""
    parts: list[str] = []

    # 用户身份
    user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '') or '?'
    user_role = getattr(user, 'role', 'user')
    user_dept = getattr(user, 'department', '') or '未分配'
    parts.append(
        f'[当前用户]\n'
        f'- 姓名: {user_name}\n'
        f'- ID: {user.id}\n'
        f'- 角色: {user_role}\n'
        f'- 部门: {user_dept}\n'
    )

    # 权限摘要(复用 PMA 现有实现)
    try:
        from app.services.chat_db_query import get_permission_context
        perm_ctx = get_permission_context(user, include_reply_rules=False)
        parts.append(f'[权限范围]\n{perm_ctx}\n')
    except Exception as e:
        current_app.logger.warning(f'[CLI Agent] 获取权限上下文失败: {e}')

    # 可用 Skill
    skill_text = _skill_section(user)
    if skill_text:
        parts.append(skill_text)

    # 记忆索引
    memory_text = _memory_section(user)
    if memory_text:
        parts.append(memory_text)

    # 环境
    is_ovs = current_app.config.get('IS_OVS', False)
    env_name = 'OVS (新加坡)' if is_ovs else 'SP8D (中国)'
    parts.append(f'[运行环境] {env_name}\n')

    # 当前日期
    parts.append(f'[当前日期] {datetime.now().strftime("%Y-%m-%d %A")}\n')

    return '\n'.join(parts)


# ─── 完整 system prompt(供 LLM 客户端使用)──────────────────────────────

def build_system_prompt_blocks(user, enable_cache: bool = True) -> list[dict]:
    """返回符合 Anthropic messages.create(system=...) 格式的 block 列表。

    Anthropic 允许 system 参数是字符串或 block 列表。用 block 列表可以
    精细控制 cache_control,让两段各挂一个 ephemeral 缓存点,最大化命中率。

    Returns:
        [
          {type: "text", text: <静态段>, cache_control: {type: "ephemeral"}},
          {type: "text", text: <动态段>, cache_control: {type: "ephemeral"}},
        ]
    """
    static = build_static_section()
    dynamic = build_dynamic_section(user)

    blocks: list[dict] = [
        {'type': 'text', 'text': static},
        {'type': 'text', 'text': DYNAMIC_BOUNDARY + dynamic},
    ]
    if enable_cache:
        # 两段各挂一个缓存切点
        blocks[0]['cache_control'] = {'type': 'ephemeral'}
        blocks[1]['cache_control'] = {'type': 'ephemeral'}
    return blocks
