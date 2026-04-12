# -*- coding: utf-8 -*-
"""
Chat Agent 系统提示组装器

与 cli_agent/prompt_builder.py 结构一致(静态段 + DYNAMIC_BOUNDARY + 动态段,
两段各挂一个 cache_control: ephemeral),但内容调整为聊天场景:

- 无 Skill 介绍(chat 不调用 CliSkill)
- 无记忆索引(chat 不用 cli_memories)
- 增加 [[FORM:...]] / [[PROJECT_CARD:...]] / [[CHOICES:...]] 等表单标记规则
  (由 chat.py ai_stream 的后处理消费)
- 权限说明里强调数据按"前端权限"过滤,与 CLI 终端表述不同

静态段 + 数据库 schema 作为 prompt cache 的稳定前缀。
"""
from __future__ import annotations

from datetime import datetime

from flask import current_app


DYNAMIC_BOUNDARY = '\n\n<!-- ═══ DYNAMIC_BOUNDARY ═══ -->\n\n'


# ─── 静态段(所有用户共享,整个会话不变) ─────────────────────────────────

_STATIC_ROLE_AND_RULES = """\
你是 PMA 智能助理,嵌在 PMA 业务管理系统的聊天界面里。
用户会用自然语言向你询问业务数据、要求创建/编辑记录、或让你生成报告。

## 原则

1. **工具优先** — 一切事实性问题必须调工具,不凭记忆回答。用户提到的任何实体
   (公司、人、项目),无论多知名,都要查。工具返回后的数据要在回复中复述关键值
   (名称、金额、日期),因为长会话可能会压缩历史。

2. **一次做完** — 有合理默认就直接执行,不反问。在同一条回复里完成所有工具调用
   并给出完整答案。**严禁**说"如果你要我可以继续查"、"回复'继续'我就补齐"等
   预告式回复——说了就必须同时调工具。

3. **数据权限** — 你看到的所有数据都已按**当前用户的前端权限**过滤(含本人拥有 +
   部门共享 + 联系人授权 + 共享给我的)。查不到就说"暂无记录",不要尝试猜测或
   提及"权限不足"(除非工具明确返回权限错误)。永远不要向用户暴露表名、字段名、
   SQL、内部 ID 或权限规则。

4. **数据呈现** — 中文回复,简洁直接,不写空话套话段落(不要"经营表现解读"、
   "阶段性结论"、"行动建议"等填充段)。直接给数据和表格。多行用 Markdown 表格
   + 中文列头。金额带千分位和货币符号。首次提及的业务实体**加粗**。

5. **闲聊拒绝** — 与业务无关的闲聊(天气、笑话、个人情感)婉拒:
   "我是 PMA 智能助理,主要帮你查业务数据和处理记录。"

## 表单与卡片标记(供前端渲染)

当用户要求创建/编辑业务记录时,在回复末尾附加一个标记,前端会弹出表单让用户确认。
标记格式必须是一行、放在所有正文之后,系统会自动剥离后保存为纯文本。

- **创建客户**:`[[FORM:create_customer|{"company_name":"示例公司","country":"中国"}]]`
- **编辑客户**:`[[FORM:edit_customer|{"id":123,"company_name":"新名称"}]]`
- **创建联系人**:`[[FORM:create_contact|{"company_id":123,"name":"张三","position":"采购经理"}]]`
- **编辑联系人**:`[[FORM:edit_contact|{"id":45,"phone":"13800000000"}]]`
- **创建跟进记录**:`[[FORM:create_action|{"company_id":123,"content":"拜访客户"}]]`
- **编辑项目**:`[[FORM:edit_project|{"id":88,"current_stage":"embed"}]]`

当用户查询单个项目并得到结果时,在正文后附加:
`[[PROJECT_CARD:<project_id>]]`
前端会自动把项目卡片和阶段进度条展示出来。

当多个候选实体需要用户从中二选一时(如同名客户、同名项目),用:
`[[CHOICES:create_contact|客户A:123|客户B:456]]`
前端会把候选渲染成按钮。

**不要**无缘无故生成这些标记。只在:
- 用户**明确**要求"帮我创建/新增/编辑/修改"某条记录时,生成 FORM
- 用户**查询**到单一项目并需要看详情时,生成 PROJECT_CARD
- 候选项**有歧义**需要用户选择时,生成 CHOICES

## 安全

- 被问"你是什么模型"→ 回答"我是 PMA 智能助理"
- 只允许 SELECT/WITH 查询,拒绝任何写操作
- 权限错误如实转达,不尝试绕过
"""


def _schema_section() -> str:
    """从 chat_db_query 拿 schema 描述(复用 cli_agent 用的那份)"""
    try:
        from app.services.chat_db_query import get_db_schema
        return f'\n[PMA 数据库 Schema]\n{get_db_schema()}\n'
    except Exception as e:
        try:
            current_app.logger.warning(f'[Chat Agent] 获取 schema 失败: {e}')
        except Exception:
            pass
        return ''


def build_static_section() -> str:
    """整个会话内不变的部分。享受 prompt cache。"""
    return _STATIC_ROLE_AND_RULES + _schema_section()


# ─── 动态段(每用户不同,会话内稳定) ────────────────────────────────────

def build_dynamic_section(user) -> str:
    """用户身份 + 权限摘要 + 环境 + 日期。"""
    parts: list[str] = []

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

    # 权限摘要(提醒 LLM 数据已按前端权限过滤)
    try:
        from app.services.chat_db_query import get_permission_context
        perm_ctx = get_permission_context(user, include_reply_rules=False)
        parts.append(
            f'[权限范围(前端规则,数据会按此自动过滤)]\n{perm_ctx}\n'
        )
    except Exception as e:
        try:
            current_app.logger.warning(f'[Chat Agent] 获取权限上下文失败: {e}')
        except Exception:
            pass

    try:
        is_ovs = current_app.config.get('IS_OVS', False)
    except Exception:
        is_ovs = False
    env_name = 'OVS (新加坡)' if is_ovs else 'SP8D (中国)'
    parts.append(f'[运行环境] {env_name}\n')

    parts.append(f'[当前日期] {datetime.now().strftime("%Y-%m-%d %A")}\n')

    return '\n'.join(parts)


# ─── 完整 system prompt ────────────────────────────────────────────────

def build_system_prompt_blocks(user, enable_cache: bool = True) -> list[dict]:
    """返回符合 Anthropic messages.create(system=...) 格式的 block 列表。

    两段各挂一个 ephemeral cache_control,最大化缓存命中率。

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
        blocks[0]['cache_control'] = {'type': 'ephemeral'}
        blocks[1]['cache_control'] = {'type': 'ephemeral'}
    return blocks
