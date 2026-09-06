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
from flask_babel import gettext as _

logger = logging.getLogger(__name__)

_client = None


def _vision_conf():
    """视觉专用端点配置，优先 CLAUDE_VISION_*，未配则回退全局 ANTHROPIC_*。

    背景：文本类 AI 走国内 GLM 代理(省)，但 GLM 经 Anthropic 兼容端点不读图。
    发票/名片 OCR 需要能读图的后端(如 Codex/ChatGPT gpt-5.4 视觉)，故视觉调用
    单独走 CLAUDE_VISION_BASE_URL + CLAUDE_VISION_API_KEY。两者都不配时行为不变。
    """
    api_key = os.environ.get('CLAUDE_VISION_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
    base_url = os.environ.get('CLAUDE_VISION_BASE_URL') or os.environ.get('ANTHROPIC_BASE_URL')
    bearer_flag = (os.environ.get('CLAUDE_VISION_USE_BEARER')
                   or os.environ.get('ANTHROPIC_USE_BEARER') or '')
    use_bearer = bearer_flag.lower() in ('1', 'true', 'yes')
    return api_key, base_url, use_bearer


def first_text(msg) -> str:
    """从 Anthropic 响应里取第一个 text 块的内容,取不到返回 ''。

    背景:推理型模型(gpt-5.x / 开启 extended thinking 的 Claude)会先返回
    ThinkingBlock,它没有 .text 属性。直接写 msg.content[0].text 会抛
    AttributeError,而调用方普遍是 `except Exception -> 返回兜底值`,
    于是 AI 功能静默失效(标题退回模板、翻译原样返回),界面上看不出报错。

    所有走 Anthropic SDK 取文本的地方都应该用这个函数,不要索引 content[0]。
    """
    for block in (getattr(msg, 'content', None) or []):
        if getattr(block, 'type', None) == 'text':
            return getattr(block, 'text', None) or ''
    return ''


def get_client():
    """复用 chat_translation_service 同款客户端构造逻辑 — base_url + 可选 bearer。
    视觉端点独立于文本端点(见 _vision_conf)。"""
    global _client
    if _client is None:
        api_key, base_url, use_bearer = _vision_conf()
        kwargs = {'api_key': api_key}
        if base_url:
            kwargs['base_url'] = base_url
        if use_bearer:
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


PDF_RASTER_MAX_PAGES = 3        # 发票基本 1 页, 留点余量; 再多纯属烧 token
PDF_RASTER_DPI = 150
IMAGE_MAX_EDGE = 1568           # Anthropic 建议的长边上限, 更大只会被上游缩回去


def pdf_to_png_pages(pdf_blob: bytes, max_pages: int = PDF_RASTER_MAX_PAGES,
                     dpi: int = PDF_RASTER_DPI) -> list:
    """PDF → 每页 PNG 字节流(最多 max_pages 页)。

    为什么不把 PDF 原样丢给模型: Anthropic 原生支持 type='document' 直接吃 PDF,
    但当前视觉后端是 Codex 代理(cli-proxy-api 把 /v1/messages 翻译成 Codex 的
    /v1/responses), 它会把 document 块**静默丢弃** —— 上游照样返 200, 模型手里
    却什么都没有(2026-09-06 实测: 模型直接回 NO_DOCUMENT_RECEIVED), 字段全 null
    反被当成"识别成功"。栅格化成图片走 image 块则一切正常。

    解析失败不抛异常, 返回空列表交调用方处理(PDF 可能加密/损坏)。
    """
    try:
        import fitz  # PyMuPDF, 见 requirements.txt
    except ImportError:
        logger.error('PyMuPDF(fitz) 未安装, PDF 无法栅格化')
        return []

    try:
        doc = fitz.open(stream=pdf_blob, filetype='pdf')
    except Exception as e:
        logger.error(f'PDF 打开失败: {e}')
        return []

    pages = []
    try:
        for idx in range(min(max_pages, doc.page_count)):
            page = doc[idx]
            scale = dpi / 72.0
            long_edge = max(page.rect.width, page.rect.height) or 1
            if long_edge * scale > IMAGE_MAX_EDGE:
                scale = IMAGE_MAX_EDGE / long_edge
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            pages.append(pix.tobytes('png'))
    except Exception as e:
        logger.error(f'PDF 栅格化失败(已渲染 {len(pages)} 页): {e}')
    finally:
        doc.close()
    return pages


def _image_block(blob: bytes, media_type: str) -> dict:
    """构造 Anthropic image content block。"""
    return {
        'type': 'image',
        'source': {
            'type': 'base64',
            'media_type': media_type,
            'data': base64.standard_b64encode(blob).decode('ascii'),
        },
    }


def _is_blank_result(data: dict) -> bool:
    """schema 字段全空 = 什么都没识别到。

    为什么要判: 上游可能返 200 + 一个字段全 null 的合法 JSON(比如图片/文档没真正
    送达模型)。若照旧当成功返回, 前端会把一行 0.00 当成"识别完成"展示 —— 识别失败
    伪装成识别成功, 比直接报错更难排查(2026-09-06 PDF 静默失效就是这么被掩盖的)。
    """
    if not isinstance(data, dict):
        return True
    for key, value in data.items():
        if key == 'confidence' or value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        return False
    return True


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
        return {'success': False, 'message': _('图片为空')}

    api_key = _vision_conf()[0]
    if not api_key:
        return {'success': False,
                'message': _('未配置视觉端点 API Key (CLAUDE_VISION_API_KEY / ANTHROPIC_API_KEY)')}

    media_type = detect_image_type(image_blob)
    if model is None:
        model = os.environ.get('CLAUDE_VISION_MODEL', 'claude-haiku-4-5-20251001')

    # PDF 一律先栅格化成图片再送 —— 当前视觉后端(Codex 代理)会丢弃 document 块,
    # 详见 pdf_to_png_pages 注释
    if media_type == 'application/pdf':
        png_pages = pdf_to_png_pages(image_blob)
        if not png_pages:
            return {'success': False, 'message': _('PDF 解析失败, 请改传图片')}
        content_blocks = [_image_block(p, 'image/png') for p in png_pages]
    else:
        content_blocks = [_image_block(image_blob, media_type)]

    raw = ''
    try:
        msg = get_client().messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{
                'role': 'user',
                'content': content_blocks + [
                    {'type': 'text', 'text': user_text},
                ],
            }],
        )
        # 取第一个 text 块 — 跳过 reasoning 模型可能先返回的 thinking 块(见 first_text)
        raw = first_text(msg).strip()
        # 防御性: 有时模型会包 ```json ... ```
        if raw.startswith('```'):
            raw = raw.strip('`').lstrip('json').strip()
        # 找第一个 { 到最后一个 } 之间
        start = raw.find('{')
        end = raw.rfind('}')
        if start >= 0 and end > start:
            raw = raw[start:end + 1]
        data = json.loads(raw)
        if _is_blank_result(data):
            logger.warning(f'Vision OCR 结果全空(model={model}, media={media_type}) '
                           f'— 视为识别失败')
            return {'success': False, 'message': _('未能从文件中识别出内容, 请手动填写')}
        # 标准化 confidence 字典
        if not isinstance(data.get('confidence'), dict):
            data['confidence'] = {}
        return {'success': True, 'data': data}
    except json.JSONDecodeError as je:
        logger.error(f'Vision OCR JSON 解析失败: {je}, raw={raw[:200] if raw else ""}')
        return {'success': False,
                'message': _('AI 返回格式异常: %(err)s', err=str(je)[:80])}
    except anthropic.APIStatusError as e:
        logger.error(f'Claude vision API 错误: {e.status_code}')
        return {'success': False,
                'message': _('AI 服务错误 (%(code)s)', code=e.status_code)}
    except anthropic.APITimeoutError:
        logger.error('Claude vision API 超时')
        return {'success': False, 'message': _('识别超时, 请重试')}
    except Exception as e:
        logger.error(f'Vision OCR 异常: {e}', exc_info=True)
        return {'success': False,
                'message': _('识别失败: %(err)s', err=str(e)[:80])}
