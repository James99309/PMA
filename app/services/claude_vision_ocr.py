# -*- coding: utf-8 -*-
"""通用 Claude Vision OCR 引擎 — 看图提结构化字段

调用方传入 system prompt(含 schema)和图片字节流, 返回 {success, data}.
data 是模型按 schema 输出的 JSON 字典(含 confidence 子字典).

业务薄包装示例: business_card_ocr.extract_card / expense_invoice_ocr.extract_invoice
"""
import os
import json
import base64
import logging

import anthropic

logger = logging.getLogger(__name__)

_client = None


def get_client():
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


def detect_image_type(blob: bytes) -> str:
    """简单嗅探: jpg / png / webp / pdf"""
    if blob.startswith(b'%PDF'):
        return 'application/pdf'
    if blob.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    if blob.startswith(b'\x89PNG'):
        return 'image/png'
    if blob[:4] == b'RIFF' and blob[8:12] == b'WEBP':
        return 'image/webp'
    return 'image/jpeg'


def detect_prefer_lang() -> str:
    """按 PMA_DB_TYPE 决定双语场景优先返回中文还是英文。
    sp8d (中国) → zh; ovs (新加坡) → en; 其他 fallback zh
    """
    db_type = os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', '')
    return 'en' if db_type == 'ovs' else 'zh'


def extract_with_schema(
    image_blob: bytes,
    system_prompt: str,
    user_text: str = '请提取字段, 仅返回 JSON.',
    model: str = None,
    max_tokens: int = 1024,
) -> dict:
    """从图片字节流按 system_prompt 中定义的 schema 提取字段。

    Args:
        image_blob: 图片字节流
        system_prompt: 系统提示词,必须包含 JSON schema 定义和 "Output raw JSON only" 之类的强约束
        user_text: 用户消息文本(可选,默认通用)
        model: 模型名,默认从 env CLAUDE_VISION_MODEL 取,再 fallback haiku-4-5
        max_tokens: 最大输出 token

    Returns:
        success → {'success': True, 'data': {...schema 字段..., 'confidence': {...}}}
        失败    → {'success': False, 'message': '...'}
    """
    if not image_blob:
        return {'success': False, 'message': '图片为空'}

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return {'success': False, 'message': '未配置 ANTHROPIC_API_KEY'}

    media_type = detect_image_type(image_blob)
    is_pdf = media_type == 'application/pdf'
    image_b64 = base64.standard_b64encode(image_blob).decode('ascii')
    if model is None:
        model = os.environ.get('CLAUDE_VISION_MODEL', 'claude-haiku-4-5-20251001')

    # Claude 支持 type=image 和 type=document, document 用于 PDF (会自动 OCR 每页)
    content_block = {
        'type': 'document' if is_pdf else 'image',
        'source': {
            'type': 'base64',
            'media_type': media_type,
            'data': image_b64,
        },
    }

    raw = ''
    try:
        msg = get_client().messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{
                'role': 'user',
                'content': [
                    content_block,
                    {'type': 'text', 'text': user_text},
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
        logger.error(f'Vision OCR JSON 解析失败: {je}, raw={raw[:200] if raw else ""}')
        return {'success': False, 'message': f'AI 返回格式异常: {str(je)[:80]}'}
    except anthropic.APIStatusError as e:
        logger.error(f'Claude vision API 错误: {e.status_code}')
        return {'success': False, 'message': f'AI 服务错误 ({e.status_code})'}
    except anthropic.APITimeoutError:
        logger.error('Claude vision API 超时')
        return {'success': False, 'message': '识别超时, 请重试'}
    except Exception as e:
        logger.error(f'Vision OCR 异常: {e}', exc_info=True)
        return {'success': False, 'message': f'识别失败: {str(e)[:80]}'}
