# -*- coding: utf-8 -*-
"""名片 OCR — Claude Vision 提取名片字段

通用引擎在 claude_vision_ocr.extract_with_schema, 本模块只负责名片专属的
schema/prompt 和双语规则.
"""
from app.services.claude_vision_ocr import extract_with_schema, detect_prefer_lang


_BASE_PROMPT = """You are a business card OCR engine.
Extract fields from the given business card image and return ONLY a JSON object.
Do NOT include explanation, markdown, or code fences. Output raw JSON only.

Schema:
{
  "name": string|null,           // 姓名 (本人, 不是公司名)
  "company": string|null,        // 公司全名
  "position": string|null,       // 职位 / 头衔
  "department": string|null,     // 部门
  "phone": string|null,          // 主要电话, 数字+可选区号 (优先手机)
  "email": string|null,          // 邮箱
  "address": string|null,        // 公司地址
  "confidence": {                // 每个字段 0.0-1.0 置信度
    "name": number,
    "company": number,
    "position": number,
    "department": number,
    "phone": number,
    "email": number,
    "address": number
  }
}

Rules:
- If a field is absent or unreadable, set value to null and confidence to 0.
- For phones, output digits only (strip spaces/dashes/parens), keep + if present.
- For Chinese names, output as-is in Chinese characters.
- Confidence reflects your certainty. Use 0.95+ for clearly printed text,
  0.7-0.9 for slightly blurry/handwritten, <0.7 for guessed."""


_LANG_RULE_ZH = """
- BILINGUAL CARDS: If a field is printed in BOTH Chinese AND English on the card,
  ALWAYS return the Chinese version as the primary value. Examples:
    "業務副理 / Sales Deputy Manager"  → return "業務副理"
    "採購部 / Purchasing Dept."         → return "採購部"
- COMPANY NAME: If both a Chinese employer name (e.g. 駿通公司) and an English
  brand name (e.g. MOTOROLA SOLUTIONS) appear, prefer the Chinese employer name.
  The brand may be a partner/affiliation, not the actual employer.
- If only English exists for a field (no Chinese version printed), use the English."""


_LANG_RULE_EN = """
- BILINGUAL CARDS: If a field is printed in BOTH Chinese AND English on the card,
  ALWAYS return the English version as the primary value. Examples:
    "業務副理 / Sales Deputy Manager"  → return "Sales Deputy Manager"
    "採購部 / Purchasing Dept."         → return "Purchasing Dept."
- If only Chinese exists for a field (no English version printed), use the Chinese."""


def _build_prompt(prefer_lang: str) -> str:
    rule = _LANG_RULE_EN if prefer_lang == 'en' else _LANG_RULE_ZH
    return _BASE_PROMPT + rule


def extract_card(image_blob: bytes) -> dict:
    """从名片图字节流提取字段。

    Returns:
        dict: 成功 → {success: True, data: {name, company, ..., confidence: {...}}}
              失败 → {success: False, message: '...'}
    """
    import os
    system_prompt = _build_prompt(detect_prefer_lang())
    model = os.environ.get('CARD_OCR_MODEL')  # 保留旧 env 名向后兼容
    return extract_with_schema(
        image_blob,
        system_prompt,
        user_text='请提取这张名片的字段, 仅返回 JSON.',
        model=model,
    )
