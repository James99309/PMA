# -*- coding: utf-8 -*-
"""Wiki 专用 Claude 客户端

设计决策：
- 不用 Anthropic Python SDK —— SDK 对自定义 base_url 的 auth header
  格式和 SG NAS OAuth 代理不兼容（SDK 走 Authorization: Bearer，
  代理只吃 x-api-key；curl 实测 x-api-key 可直接通过）。
- 用 httpx 直接发 HTTP JSON 请求，匹配 curl 成功的调用格式。
- **trust_env=False** —— 必须禁用 httpx 对系统 HTTP_PROXY 的自动识别，
  否则本机 Clash 之类的 GFW 代理会拦截 Tailscale IP（100.x.x.x 不在它
  的直连列表），返回 503。ANTHROPIC_BASE_URL 是 Tailscale 私网地址，
  应该直连不经二道手。
- 非流式、一问一答，足够 Wiki 编译/问答/质检场景。
- 复用 CLI 已有的 ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL 环境变量。
- **必须注入 Claude Code 身份前缀** —— Anthropic 服务端对 OAuth 订阅
  token 调用 Sonnet/Opus 做了门禁，system[0] 必须以固定字符串开头否则
  返回伪 429（message="Error"，无 anthropic-ratelimit-* 头）。Haiku
  不受此限制。SG NAS 代理目前不替客户端加这个前缀，所以 Wiki 客户端
  必须自己加，和 CLI llm_client.py 的处理保持一致。
- **Opus/Sonnet 禁止自定义 temperature** —— SG NAS OAuth 代理对高级
  模型只允许默认 temperature（=1.0），传 0/0.1/0.5 会返回 400
  Invalid request data。只有 Haiku 允许任意 temperature。所以 Wiki
  客户端默认不传 temperature 字段，除非模型是 Haiku。
- 模型默认 Opus，可通过 WIKI_*_MODEL 环境变量覆盖。

参见 app/services/cli_agent/llm_client.py 对比流式场景的处理。
"""
import json
import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# 默认模型配置（可用环境变量覆盖）
# ══════════════════════════════════════════════════════════════════
#
# 模型 ID 说明：
# - claude-opus-4-6 是 API 接受的实际 ID，不带任何后缀
# - [1m] 是 Claude Code CLI 本地标注，表示启用了 1M context；**API 端通过
#   anthropic-beta: context-1m-2025-08-07 header 启用，不是靠模型名后缀**
# - WIKI_ENABLE_1M_CONTEXT 控制是否带上这个 header（默认 true），
#   Wiki 的 Ingest/Lint 都可能需要上 1M 窗口吞下数十篇文章
# 实测：通过 SG NAS 代理调 claude-opus-4-6[1m] 会 404，只能用 claude-opus-4-6

INGEST_MODEL = os.environ.get('WIKI_INGEST_MODEL', 'claude-opus-4-6')
QUERY_MODEL = os.environ.get('WIKI_QUERY_MODEL', 'claude-opus-4-6')
LINT_MODEL = os.environ.get('WIKI_LINT_MODEL', 'claude-opus-4-6')
META_MODEL = os.environ.get('WIKI_META_MODEL', 'claude-haiku-4-5-20251001')

# 1M 上下文 beta feature flag —— Anthropic 对 Opus 1M 还在 beta
# 参考: https://docs.anthropic.com/en/docs/build-with-claude/context-windows
ENABLE_1M_CONTEXT = os.environ.get('WIKI_ENABLE_1M_CONTEXT', 'true').lower() in ('true', '1', 'yes')
BETA_1M_HEADER = 'context-1m-2025-08-07'

# 默认 HTTP 超时（秒）—— Wiki 编译可能跑几十秒
DEFAULT_TIMEOUT = float(os.environ.get('WIKI_HTTP_TIMEOUT', '180'))


# ══════════════════════════════════════════════════════════════════
# 响应数据结构
# ══════════════════════════════════════════════════════════════════

@dataclass
class WikiLLMResponse:
    """Wiki 客户端返回结果"""
    text: str
    usage: dict  # {'input_tokens': int, 'output_tokens': int, 'model': str}

    def __str__(self) -> str:
        return self.text


class WikiClaudeError(RuntimeError):
    """Wiki Claude 调用异常"""


# ══════════════════════════════════════════════════════════════════
# 客户端
# ══════════════════════════════════════════════════════════════════

class WikiClaudeClient:
    """Wiki 专用的 Claude HTTP 客户端（非流式，httpx 直调）"""

    ANTHROPIC_OFFICIAL = 'https://api.anthropic.com'
    ANTHROPIC_VERSION = '2023-06-01'

    # Anthropic OAuth 订阅 token 对 Sonnet/Opus 的身份门禁前缀
    # system[0] 必须以这串开头，否则返回 fake 429 (message="Error")
    OAUTH_IDENTITY_PREFIX = "You are Claude Code, Anthropic's official CLI for Claude."

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ):
        key = api_key or os.environ.get('ANTHROPIC_API_KEY', '').strip()
        if not key:
            raise WikiClaudeError(
                '未配置 ANTHROPIC_API_KEY 环境变量，无法调用 Wiki Claude 客户端。'
                '本地开发请检查 .env.local，NAS 部署请检查 docker-compose 环境变量。'
            )
        self._api_key = key

        url = base_url if base_url is not None else os.environ.get('ANTHROPIC_BASE_URL', '').strip()
        self._base_url = (url or self.ANTHROPIC_OFFICIAL).rstrip('/')

        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT

        # trust_env=False 禁用系统 HTTP_PROXY，避免本机 Clash/Shadowsocks
        # 把 Tailscale 内网请求错误地转给公网代理，返回 503。
        self._http = httpx.Client(trust_env=False, timeout=self._timeout)

        if url:
            logger.info(f'[Wiki Claude] base_url={self._base_url} (trust_env=False)')
        else:
            logger.info('[Wiki Claude] 直连 Anthropic 官方 API')

    def close(self):
        self._http.close()

    def complete(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 16000,
        temperature: float | None = None,
    ) -> WikiLLMResponse:
        """发起一次非流式对话请求。

        Args:
            system: 纯文本 system prompt
            user: 纯文本 user 消息
            model: 模型 ID，例如 'claude-opus-4-6'
            max_tokens: 最大输出 token 数
            temperature: 采样温度；**默认 None（不发送该字段）**
                        - Opus/Sonnet 走 SG NAS OAuth 代理时必须使用默认值
                          （=1.0），传任何自定义值都会 400
                        - 只有 Haiku 允许自定义 temperature
                        调用方若要控温，请确认走的不是 OAuth 代理

        Returns:
            WikiLLMResponse(text=..., usage={...})

        Raises:
            WikiClaudeError: API 调用失败、超时或解析异常
        """
        logger.info(
            f'[Wiki Claude] model={model} sys={len(system)}B user={len(user)}B '
            f'max_tokens={max_tokens} temp={temperature}'
        )

        # 把 system 字符串包成 blocks，并在 [0] 注入 OAuth 身份前缀
        system_blocks = [
            {'type': 'text', 'text': self.OAUTH_IDENTITY_PREFIX},
            {'type': 'text', 'text': system},
        ]

        payload = {
            'model': model,
            'max_tokens': max_tokens,
            'system': system_blocks,
            'messages': [{'role': 'user', 'content': user}],
        }
        # 只在明确传入 temperature 时发送该字段，避开 OAuth 代理对 Opus/Sonnet
        # 的限制。调用方默认不传就使用 Claude 的默认值（Wiki 场景够用）。
        if temperature is not None:
            payload['temperature'] = temperature

        headers = {
            'content-type': 'application/json',
            'x-api-key': self._api_key,
            'anthropic-version': self.ANTHROPIC_VERSION,
        }
        # 1M 上下文 beta flag（C6）—— Opus 默认 200K，带上这个 header 才拿到 1M。
        # Haiku 不支持 1M，但带上这个 header 也不会报错，所以统一带上即可。
        if ENABLE_1M_CONTEXT:
            headers['anthropic-beta'] = BETA_1M_HEADER

        url = f'{self._base_url}/v1/messages'

        try:
            resp = self._http.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as e:
            raise WikiClaudeError(f'Claude API 超时（{self._timeout}s）: {e}') from e
        except httpx.HTTPError as e:
            raise WikiClaudeError(f'Claude API 网络错误: {e}') from e

        if resp.status_code >= 400:
            body_preview = (resp.text or '')[:500]
            raise WikiClaudeError(
                f'Claude API HTTP {resp.status_code}: {body_preview}'
            )

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            raise WikiClaudeError(f'Claude API 返回非 JSON: {resp.text[:500]}') from e

        content_blocks = data.get('content') or []
        text = ''.join(
            block.get('text', '') for block in content_blocks if block.get('type') == 'text'
        )

        usage_raw = data.get('usage') or {}
        usage = {
            'input_tokens': usage_raw.get('input_tokens', 0) or 0,
            'output_tokens': usage_raw.get('output_tokens', 0) or 0,
            'model': model,
        }

        logger.info(
            f'[Wiki Claude] done model={model} '
            f'in={usage["input_tokens"]} out={usage["output_tokens"]} text={len(text)}B'
        )

        return WikiLLMResponse(text=text, usage=usage)
