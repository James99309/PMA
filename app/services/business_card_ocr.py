# -*- coding: utf-8 -*-
"""
名片 OCR 服务 — 用 Claude vision 直接看图提取结构化字段

输入: 名片图片二进制 (用户拍照后裁剪干净的图)
输出: { name, company, position, phone, email, department, address,
        confidence: { 字段: 0.0-1.0 } }

使用 Claude Haiku (vision capable, 便宜, 不受 OAuth 模型门禁限制).
mac-proxy oat 路径已通 (chat_translation_service 同款客户端).
"""
import os
import json
import base64
import logging

import anthropic

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """复用 chat_translation_service 同款客户端构造逻辑 — base_url + 可选 bearer"""
    global _client
    if _client is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        base_url = os.environ.get('ANTHROPIC_BASE_URL')
        kwargs = {'api_key': api_key}
        if base_url:
            kwargs['base_url'] = base_url
        if os.environ.get('ANTHROPIC_USE_BEARER', '').lower() in ('1', 'true', 'yes'):
            kwargs['default_headers'] = {
                'Authorization': f'Bearer {api_key}',
                'anthropic-beta': 'oauth-2025-04-20',
            }
        _client = anthropic.Anthropic(**kwargs)
    return _client


SYSTEM_PROMPT = """You are a business card OCR engine.
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


def _detect_image_type(blob: bytes) -> str:
    """简单嗅探: jpg / png / webp"""
    if blob.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    if blob.startswith(b'\x89PNG'):
        return 'image/png'
    if blob[:4] == b'RIFF' and blob[8:12] == b'WEBP':
        return 'image/webp'
    return 'image/jpeg'  # default


def extract_card(image_blob: bytes) -> dict:
    """从名片图字节流提取字段。

    Returns:
        dict: 成功 → {success: True, data: {name, company, ..., confidence: {...}}}
              失败 → {success: False, message: '...'}
    """
    if not image_blob:
        return {'success': False, 'message': '图片为空'}

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return {'success': False, 'message': '未配置 ANTHROPIC_API_KEY'}

    media_type = _detect_image_type(image_blob)
    image_b64 = base64.standard_b64encode(image_blob).decode('ascii')
    model = os.environ.get('CARD_OCR_MODEL', 'claude-haiku-4-5-20251001')

    try:
        msg = _get_client().messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': media_type,
                            'data': image_b64,
                        },
                    },
                    {'type': 'text', 'text': '请提取这张名片的字段, 仅返回 JSON.'},
                ],
            }],
        )
        raw = msg.content[0].text.strip() if msg.content else ''
        # 防御性: 有时模型会包 ```json ... ```
        if raw.startswith('```'):
            raw = raw.strip('`').lstrip('json').strip()
        # 找第一个 { 到最后一个 } 之间
        start = raw.find('{')
        end = raw.rfind('}')
        if start >= 0 and end > start:
            raw = raw[start:end + 1]
        data = json.loads(raw)
        # 标准化 confidence 字典
        if not isinstance(data.get('confidence'), dict):
            data['confidence'] = {}
        return {'success': True, 'data': data}
    except json.JSONDecodeError as je:
        logger.error(f'名片 OCR JSON 解析失败: {je}, raw={raw[:200] if raw else ""}')
        return {'success': False, 'message': f'AI 返回格式异常: {str(je)[:80]}'}
    except anthropic.APIStatusError as e:
        logger.error(f'Claude vision API 错误: {e.status_code}')
        return {'success': False, 'message': f'AI 服务错误 ({e.status_code})'}
    except anthropic.APITimeoutError:
        logger.error('Claude vision API 超时')
        return {'success': False, 'message': '识别超时, 请重试'}
    except Exception as e:
        logger.error(f'名片 OCR 异常: {e}', exc_info=True)
        return {'success': False, 'message': f'识别失败: {str(e)[:80]}'}
