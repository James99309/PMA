# -*- coding: utf-8 -*-
"""文本语言归一化 — 把任意语言的自由文本统一成区域系统语言

可复用标准端口: 任何模块要"按区域统一文本语言"都调 translate_to。
- 区域 → 语言: 环境变量 PMA_DB_TYPE  ovs(海外)→'en' / sp8d(默认)→'zh'
- 纯 CJK 且无拉丁字母 → 视为已是中文, 目标 zh 时短路不调 AI
- 已是目标语言 → 由 prompt 约束"原样返回"
- 任何失败 → 返回原文, 绝不丢数据
模型默认 haiku, 复用 claude_vision_ocr.get_client() (同款 OAuth/bearer 处理)
"""
import os
import re
import logging

import anthropic
from app.services.claude_vision_ocr import get_client, detect_prefer_lang

logger = logging.getLogger(__name__)

_TRANSLATION_MODEL = os.environ.get('TRANSLATION_MODEL', 'claude-haiku-4-5-20251001')

# 中日韩统一表意文字(含扩展 A/B、兼容区) — 用于"纯中文"短路判定
_CJK_RE = re.compile(
    r'[㐀-䶿一-鿿豈-﫿\U00020000-\U0002a6df]'
)
_LATIN_RE = re.compile(r'[A-Za-z]')

_TARGET_NAME = {'en': 'English', 'zh': 'Simplified Chinese'}


def has_cjk(text: str) -> bool:
    """文本是否含中日韩表意文字。提交兜底用: 已归一(无 CJK)则跳过翻译,
    避免对已是英文的文本重复调 AI 造成提交延迟。"""
    return bool(text) and bool(_CJK_RE.search(text))


def normalize_lang_for_region() -> str:
    """区域 → 系统语言: ovs(海外)→'en', 其它(sp8d/默认)→'zh'。

    直接复用 claude_vision_ocr.detect_prefer_lang() 同款区域判定(读
    PMA_DB_TYPE / 兼容旧名 SUPABASE_DB_TYPE), 避免重复实现。
    """
    return detect_prefer_lang()


def translate_to(text: str, target_lang: str) -> str:
    """把 text 归一成 target_lang('en' | 'zh')。

    规则:
    - 空 / 纯空白 → 原样返回
    - 目标 zh 且文本是纯 CJK(无拉丁字母) → 视为已是中文, 不调 AI
    - 其余调 haiku: 已是目标语言则原样返回, 否则翻译;
      专有名词 / 票号 / 编号 / 数字 / 金额 / 日期一律保持原文
    - 任何异常 / 空结果 → 返回原文 (绝不丢数据)

    注意: 目标 en 不做 "纯 ASCII 即英文" 短路 —— 马来文等也是 ASCII,
    必须交给模型判定是否需要译成英文。
    """
    if not text or not text.strip():
        return text
    src = text.strip()

    # 目标 zh:只要已含中文即视为"已是中文",直接返回(不必因夹带英文词/产品名去调 AI 翻译,
    # 否则 CN 区域每次保存含中英混排的标题/描述/评论都要等 1~2s AI 调用,体感卡顿)。
    if target_lang == 'zh' and _CJK_RE.search(src):
        return text

    target_name = _TARGET_NAME.get(target_lang, 'English')
    system = (
        "You are a text language normalizer for an expense reimbursement system. "
        "The user message is a single short field value (an expense title, an "
        "expense description, or a line-item description). "
        f"If it is ALREADY written entirely in {target_name}, output it VERBATIM, "
        f"unchanged. Otherwise translate it into {target_name}. "
        "Preserve EXACTLY as written in the source (never translate or alter): "
        "company / brand / product names, person names, invoice or receipt "
        "numbers, license-plate numbers, model or part codes, and all digits, "
        "amounts, currency symbols and dates. Keep the same meaning, stay concise. "
        "Output ONLY the resulting text — no quotes, no labels, no explanation."
    )
    try:
        msg = get_client().messages.create(
            model=_TRANSLATION_MODEL,
            max_tokens=512,
            system=system,
            messages=[{'role': 'user', 'content': src[:1000]}],
        )
        out = (msg.content[0].text if msg.content else '').strip()
        out = out.strip('"\'\n').strip()
        return out or text
    except anthropic.APIStatusError as e:
        logger.warning(f'translate_to API error {getattr(e, "status_code", "?")}; 返回原文')
        return text
    except Exception as e:
        logger.warning(f'translate_to exception: {e}; 返回原文')
        return text


def normalize_region_text(text):
    """把用户手输自由文本同步归一成区域系统语言(SG→en / CN→zh)。

    任何模块「保存那一刻」调用即可: 草稿/记录一保存就是区域语言,
    详情/列表/报表立刻一致, 无需提交或异步等待。
    - 空 / 纯空白 → 原样返回
    - CN 纯中文 / 已是目标语言 → translate_to 内部短路, 零成本
    - 失败 → 返回原文 (绝不丢用户输入)
    expense 的 _normalize_region_text 即此逻辑; 这里作为标准复用入口,
    日历(worklog_service) / 任务(task_service) 等共用单一来源。
    """
    if not text or not str(text).strip():
        return text
    # 富文本/HTML 内容(评论/日报/描述里的内联图片等)不做 AI 翻译归一:
    # 翻译模型会把 HTML+图片URL 当成对话来回应("我看不到图片…"),导致内容被损坏。
    import re as _re
    if _re.search(r'<(img|span|div|p|br|a|ul|ol|li|strong|em|b|i|h[1-6])[\s>/]', str(text), _re.I):
        return text
    try:
        return translate_to(str(text).strip(), normalize_lang_for_region())
    except Exception as e:
        logger.warning(f'normalize_region_text 失败: {e}')
        return text
