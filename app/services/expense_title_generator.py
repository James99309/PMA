# -*- coding: utf-8 -*-
"""报销主题 AI 生成 — 用 Claude haiku 根据"报销说明"产生一个简短主题

输入: description (str) — 报销说明文字
输出: title (str) — 5-12 字的中文主题, 例: "苏州客户拜访"

复用 claude_vision_ocr.get_client() 的客户端构造(同款 OAuth/bearer 处理)
模型默认 haiku (便宜 + 快, 不受 OAuth 模型门禁限制)
"""
import os
import logging

import anthropic
from app.services.claude_vision_ocr import get_client

logger = logging.getLogger(__name__)


_PROMPT = """根据用户填写的报销说明, 生成一个 5-12 个中文字符的简短主题.

要求:
- 用名词或动名词短语, 不带标点
- 突出关键场景(地点/客户/事项类型), 不要复述全文
- 例:
  说明 "2026年4月29日苏州客户技术对接陪同张工现场调试设备" → 主题 "苏州客户拜访"
  说明 "上海长宁机房日常巡检" → 主题 "上海机房巡检"
  说明 "招待中油客户陪同晚餐" → 主题 "招待 · 中油客户"
  说明 "PMA Singapore demo 客户拜访" → 主题 "SG 客户拜访"

仅输出主题文字, 不带引号/解释/前缀."""


_PROMPT_EN = """Generate a concise 3-6 word English title for an expense claim,
based on the user's expense description.

Requirements:
- Noun or gerund phrase, Title Case, no punctuation
- Highlight the key scenario (place / client / activity), do not restate the text
- Translate to English even if the description is in Chinese or another language
- Examples:
  description "2026年4月29日苏州客户技术对接陪同张工现场调试设备" -> "Suzhou Client Site Support"
  description "上海长宁机房日常巡检" -> "Shanghai Server Room Inspection"
  description "招待中油客户陪同晚餐" -> "PetroChina Client Dinner"
  description "PMA Singapore demo 客户拜访" -> "Singapore Client Demo Visit"

Output ONLY the title text, no quotes / explanation / prefix."""


_PROMPT_TASK = """根据用户填写的任务描述, 生成一个 5-15 个中文字符的简短任务标题.

要求:
- 用名词或动宾短语概括任务目标, 不带标点
- 突出要做的事(动作 + 对象), 不要复述全文
- 例:
  描述 "完成 PMA 移动端与后端的接口联调, 覆盖任务/工时/通知" → 标题 "移动端接口联调"
  描述 "整理防爆直放站核准证申办所需材料并提交" → 标题 "核准证申办材料整理"
  描述 "本周完成报价单批量导出功能的前端开发" → 标题 "报价批量导出开发"

仅输出标题文字, 不带引号/解释/前缀."""


_PROMPT_TASK_EN = """Generate a concise 3-7 word English task title based on the user's task description.

Requirements:
- Verb phrase or noun phrase summarizing the task goal, Title Case, no punctuation
- Highlight the action + object, do not restate the text
- Translate to English even if the description is in Chinese or another language

Output ONLY the title text, no quotes / explanation / prefix."""


_PROMPTS = {
    ('expense', 'zh'): _PROMPT, ('expense', 'en'): _PROMPT_EN,
    ('task', 'zh'): _PROMPT_TASK, ('task', 'en'): _PROMPT_TASK_EN,
}


def generate_title(description: str, fallback: str = '未命名',
                   lang: str = 'zh', domain: str = 'expense') -> str:
    """根据描述用 AI 生成简短标题(通用:报销/任务等,domain 决定语境).

    Args:
        description: 描述文字
        fallback: AI 调用失败时的兜底标题
        lang: 'zh'|'en';'en' 直接生成英文标题
        domain: 'expense'|'task' — 选用对应语境 prompt

    Returns:
        str: 生成的标题(成功) 或 fallback(失败)
    """
    if not description or not description.strip():
        return fallback

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return fallback

    desc = description.strip()[:500]  # 限制输入长度防滥用
    model = os.environ.get('EXPENSE_TITLE_MODEL', 'claude-haiku-4-5-20251001')

    try:
        system_prompt = _PROMPTS.get((domain, lang)) or (_PROMPT_EN if lang == 'en' else _PROMPT)
        msg = get_client().messages.create(
            model=model,
            max_tokens=64,
            system=system_prompt,
            messages=[{
                'role': 'user',
                'content': desc,
            }],
        )
        raw = (msg.content[0].text if msg.content else '').strip()
        # 防御: 去掉可能的引号 / 句号 / 多行
        title = raw.strip('"\'\n。.： :「」').split('\n')[0].strip()
        if 1 <= len(title) <= 60:  # 英文标题更长, 放宽到 60
            return title
        return fallback
    except anthropic.APIStatusError as e:
        logger.warning(f'expense title gen API error: {e.status_code}')
        return fallback
    except Exception as e:
        logger.warning(f'expense title gen exception: {e}')
        return fallback
