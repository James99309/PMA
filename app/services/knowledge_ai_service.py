# -*- coding: utf-8 -*-
"""
知识库 AI 服务 — DeepSeek Chat + 智谱 AI Embedding

Chat 和 Embedding 供应商解耦，通过环境变量切换，统一使用 openai 包。
"""
import os
import logging
import time
from typing import List, Generator

from openai import OpenAI

logger = logging.getLogger(__name__)


# ── Embedding 客户端 ─────────────────────────────────────────────

def _get_embedding_client():
    """根据 EMBEDDING_PROVIDER 环境变量返回对应的 OpenAI 兼容客户端"""
    provider = os.getenv('EMBEDDING_PROVIDER', 'zhipu').lower()
    if provider == 'zhipu':
        api_key = os.getenv('ZHIPU_API_KEY', '')
        base_url = os.getenv('ZHIPU_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4')
        return OpenAI(api_key=api_key, base_url=base_url), os.getenv('ZHIPU_EMBEDDING_MODEL', 'embedding-3')
    elif provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY', '')
        return OpenAI(api_key=api_key), os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    else:
        raise ValueError(f"不支持的 Embedding 供应商: {provider}")


def _get_embedding_dimension():
    return int(os.getenv('ZHIPU_EMBEDDING_DIMENSION', '1024'))


# ── Chat 客户端 ──────────────────────────────────────────────────

def _get_chat_client():
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    return OpenAI(api_key=api_key, base_url=base_url), model


# ── 公开 API ─────────────────────────────────────────────────────

def generate_embeddings(texts: List[str], max_retries: int = 3) -> List[List[float]]:
    """
    批量生成文本向量。

    Args:
        texts: 文本列表（每批最多 25 条）
        max_retries: 失败重试次数

    Returns:
        与 texts 等长的向量列表，每个向量长度 = ZHIPU_EMBEDDING_DIMENSION
    """
    if not texts:
        return []

    client, model = _get_embedding_client()
    dimension = _get_embedding_dimension()
    batch_size = 25
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(max_retries):
            try:
                kwargs = {'model': model, 'input': batch}
                # 智谱支持 dimensions 参数
                provider = os.getenv('EMBEDDING_PROVIDER', 'zhipu').lower()
                if provider == 'zhipu':
                    kwargs['dimensions'] = dimension

                resp = client.embeddings.create(**kwargs)
                batch_embeddings = [item.embedding for item in resp.data]
                all_embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                logger.warning(f"Embedding 请求失败 (batch {i}, attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

    return all_embeddings


def chat_completion_stream(messages: list, temperature: float = 0.3) -> Generator[str, None, None]:
    """
    DeepSeek Chat 流式返回。

    Args:
        messages: OpenAI 格式的消息列表
        temperature: 采样温度

    Yields:
        逐 token 的文本片段
    """
    client, model = _get_chat_client()
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            max_tokens=2000,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"DeepSeek Chat 流式请求失败: {e}")
        yield f"\n\n[错误] AI 服务暂时不可用，请稍后再试。"


def chat_completion(messages: list, temperature: float = 0.3) -> tuple:
    """
    DeepSeek Chat 非流式返回。

    Returns:
        (回答文本, tokens_used)
    """
    client, model = _get_chat_client()
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )
        content = resp.choices[0].message.content if resp.choices else ''
        tokens_used = resp.usage.total_tokens if resp.usage else 0
        return content, tokens_used
    except Exception as e:
        logger.error(f"DeepSeek Chat 请求失败: {e}")
        return f"[错误] AI 服务暂时不可用: {e}", 0
