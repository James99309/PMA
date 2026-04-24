# -*- coding: utf-8 -*-
"""
LLM 客户端:基于 Anthropic Python SDK 的流式包装

负责:
    - 建立 Claude API 连接
    - 发起流式对话请求
    - 把 SDK 的事件流转换成统一的 StreamEvent 字典格式
    - 处理 tool_use / text_delta / message_stop 等事件
    - 统一的错误处理

设计为 provider 抽象层(v1 只实现 Claude,未来加 DeepSeek / Qwen 为中国部署)。

Provider 抽象通过子类化 BaseLLMClient 实现。
"""
from __future__ import annotations

import logging
import os
from typing import Iterator

logger = logging.getLogger(__name__)

# 模块级变量：记录当前活跃代理索引，在同一进程内跨请求保持状态
# 当 index=0 的代理遇到 usage limit 429 后切到 1，后续请求直接从 1 开始
_active_proxy_idx: int = 0


class LLMClientError(RuntimeError):
    """所有 LLM 调用层的异常统一成这个"""


class BaseLLMClient:
    """所有 provider 的基类。子类实现 stream()。"""

    def stream(
        self,
        system_blocks: list[dict],
        tools: list[dict],
        messages: list[dict],
        max_tokens: int = 4096,
    ) -> Iterator[dict]:
        """发起一次流式对话。

        Args:
            system_blocks: 系统提示,Anthropic block 列表格式(见 prompt_builder)
            tools: 工具定义列表(见 ToolRegistry.to_anthropic_tools())
            messages: 对话历史,Anthropic messages 格式
            max_tokens: 本轮最大输出 token 数

        Yields:
            StreamEvent dict,有以下几种 type:
                {'type': 'text_delta',   'text': '增量文本'}
                {'type': 'tool_use',     'id': '...', 'name': '...', 'input': {...}}
                {'type': 'message_stop', 'stop_reason': '...', 'usage': {...}}
                {'type': 'error',        'message': '...'}
        """
        raise NotImplementedError


# ─── Claude API 实现 ────────────────────────────────────────────────────

class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API 的流式客户端"""

    # Claude 3.5 Sonnet 的稳定模型 ID(支持 tool use + prompt caching)
    DEFAULT_MODEL = 'claude-3-5-sonnet-latest'

    # Anthropic 服务端对 OAuth 订阅 token 调用 Sonnet/Opus 做了门禁:
    # system[0] 必须以这串官方身份前缀开头,否则返回伪 429(message="Error",
    # 无 anthropic-ratelimit-* 头)。Haiku 不受此限制。
    OAUTH_IDENTITY_PREFIX = (
        "You are Claude Code, Anthropic's official CLI for Claude."
    )

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        from anthropic import Anthropic
        import httpx
        key = api_key or os.environ.get('ANTHROPIC_API_KEY', '')
        if not key:
            raise LLMClientError(
                '未配置 ANTHROPIC_API_KEY 环境变量,无法调用 Claude API'
            )
        self.model = model or os.environ.get('CLI_AGENT_MODEL', self.DEFAULT_MODEL)
        # trust_env=False 绕开 macOS 系统代理(scutil --proxy)和 HTTP_PROXY 环境变量。
        # 我们的 Tailscale 100.64.0.0/10 网段不在 macOS 代理例外列表里,本地 dev 时
        # httpx 默认会把 Tailscale 流量也扔进 127.0.0.1:1082 的 ClashX/V2Ray 代理,
        # 导致 api.anthropic.com / SG NAS 反代 全部 503。
        http = httpx.Client(trust_env=False, timeout=600)

        # 构建多代理客户端列表（支持 ANTHROPIC_BASE_URL + ANTHROPIC_BASE_URL_2 轮换）
        urls: list[str | None] = []
        u1 = base_url or os.environ.get('ANTHROPIC_BASE_URL', '').strip() or None
        u2 = os.environ.get('ANTHROPIC_BASE_URL_2', '').strip() or None
        if u1:
            urls.append(u1)
        if u2 and u2 != u1:
            urls.append(u2)
        if not urls:
            urls = [None]  # 直连 api.anthropic.com

        self._clients: list[Anthropic] = []
        for u in urls:
            kw: dict = {'api_key': key, 'http_client': http}
            if u:
                kw['base_url'] = u
            self._clients.append(Anthropic(**kw))
            logger.info(f'[CLI Agent LLM] 注册代理: {u or "api.anthropic.com (direct)"}')

        # 向后兼容：保留 _client 指向当前活跃客户端
        self._client = self._clients[0]

    @staticmethod
    def _is_usage_limit(e) -> bool:
        """判断是否应该切换到下一个代理账号。
        唯一不切换的情况：模型门禁伪 429（无 ratelimit 头 + message 为 "Error"）。
        所有其他 429（账号限额、速率限制等）都切换——另一个账号有独立配额。
        """
        try:
            headers: dict = {}
            if hasattr(e, 'response') and e.response is not None:
                headers = dict(e.response.headers)
            has_ratelimit_headers = any(
                k.lower().startswith('anthropic-ratelimit-') for k in headers
            )
            msg = ''
            if hasattr(e, 'body') and isinstance(e.body, dict):
                msg = e.body.get('error', {}).get('message', '')
            # 模型门禁伪 429：无 ratelimit 头 且 message 恰好是 "Error"
            if not has_ratelimit_headers and msg == 'Error':
                return False
            return True
        except Exception:
            return False

    def _rotate_proxy(self) -> None:
        global _active_proxy_idx
        old = _active_proxy_idx
        _active_proxy_idx = (_active_proxy_idx + 1) % len(self._clients)
        logger.warning(
            f'[CLI Agent LLM] 代理切换: index {old} → {_active_proxy_idx} '
            f'(共 {len(self._clients)} 个)'
        )

    def _iter_stream_events(self, stream) -> Iterator[dict]:
        """从 Anthropic stream 中提取标准化事件，供 stream() 复用。"""
        import json as _json
        current_block_type: str | None = None
        current_tool_use: dict | None = None
        current_tool_input_json: str = ''

        for event in stream:
            etype = getattr(event, 'type', '')

            if etype == 'content_block_start':
                block = getattr(event, 'content_block', None)
                btype = getattr(block, 'type', None)
                current_block_type = btype
                if btype == 'tool_use':
                    current_tool_use = {
                        'id': getattr(block, 'id', ''),
                        'name': getattr(block, 'name', ''),
                    }
                    current_tool_input_json = ''

            elif etype == 'content_block_delta':
                delta = getattr(event, 'delta', None)
                dtype = getattr(delta, 'type', '')
                if dtype == 'text_delta':
                    text = getattr(delta, 'text', '')
                    if text:
                        yield {'type': 'text_delta', 'text': text}
                elif dtype == 'input_json_delta':
                    current_tool_input_json += getattr(delta, 'partial_json', '')

            elif etype == 'content_block_stop':
                if current_block_type == 'tool_use' and current_tool_use is not None:
                    try:
                        tool_input = (
                            _json.loads(current_tool_input_json)
                            if current_tool_input_json else {}
                        )
                    except _json.JSONDecodeError as e:
                        logger.warning(
                            f'[CLI Agent LLM] tool_use input JSON 解析失败: {e}, '
                            f'raw={current_tool_input_json!r}'
                        )
                        tool_input = {}
                    yield {
                        'type': 'tool_use',
                        'id': current_tool_use['id'],
                        'name': current_tool_use['name'],
                        'input': tool_input,
                    }
                    current_tool_use = None
                    current_tool_input_json = ''
                current_block_type = None

        # 流结束，拿 stop_reason 和 usage
        final = stream.get_final_message()
        usage: dict = {}
        if hasattr(final, 'usage') and final.usage is not None:
            u = final.usage
            usage = {
                'input_tokens': getattr(u, 'input_tokens', 0) or 0,
                'output_tokens': getattr(u, 'output_tokens', 0) or 0,
                'cache_creation_input_tokens':
                    getattr(u, 'cache_creation_input_tokens', 0) or 0,
                'cache_read_input_tokens':
                    getattr(u, 'cache_read_input_tokens', 0) or 0,
            }
        yield {
            'type': 'message_stop',
            'stop_reason': getattr(final, 'stop_reason', None),
            'usage': usage,
            'model': self.model,
        }
        logger.info(
            f'[CLI Agent LLM] 完成 stop={getattr(final, "stop_reason", "?")} '
            f'usage={usage}'
        )

    def stream(
        self,
        system_blocks: list[dict],
        tools: list[dict],
        messages: list[dict],
        max_tokens: int = 4096,
    ) -> Iterator[dict]:
        from anthropic import RateLimitError, APIError

        patched_system = [
            {'type': 'text', 'text': self.OAUTH_IDENTITY_PREFIX},
            *system_blocks,
        ]
        n = len(self._clients)

        for attempt in range(n):
            # 从模块级活跃索引开始，保证进程内跨请求记住上次切换结果
            idx = _active_proxy_idx % n
            client = self._clients[idx]
            logger.info(
                f'[CLI Agent LLM] 请求 model={self.model} msgs={len(messages)} '
                f'tools={len(tools)} max_tokens={max_tokens} proxy={idx}'
            )
            try:
                with client.messages.stream(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=patched_system,
                    tools=tools if tools else None,
                    messages=messages,
                ) as stream:
                    yield from self._iter_stream_events(stream)
                return  # 成功，退出重试循环

            except RateLimitError as e:
                if attempt < n - 1 and self._is_usage_limit(e):
                    logger.warning(f'[CLI Agent LLM] proxy={idx} usage limit，切换代理重试')
                    self._rotate_proxy()
                    continue
                logger.exception('[CLI Agent LLM] RateLimitError（不可重试）')
                yield {'type': 'error', 'message': f'Claude API 速率限制: {e}'}
                return

            except APIError as e:
                logger.exception('[CLI Agent LLM] Anthropic APIError')
                yield {'type': 'error', 'message': f'Claude API 错误: {e}'}
                return

            except Exception as e:
                logger.exception('[CLI Agent LLM] 未预期错误')
                yield {'type': 'error', 'message': f'LLM 调用失败: {e}'}
                return


# ─── OpenAI 实现 ────────────────────────────────────────────────────────

def _extract_system_text(system_blocks) -> str:
    """把 Anthropic 风格的 system block 列表扁平化成单个字符串(OpenAI 格式)"""
    if isinstance(system_blocks, str):
        return system_blocks
    return '\n\n'.join(
        b.get('text', '') for b in system_blocks
        if isinstance(b, dict) and b.get('type') == 'text'
    )


def _anthropic_to_openai_messages(messages: list[dict]) -> list[dict]:
    """将 PMA 内部使用的 Anthropic 消息格式转成 OpenAI chat.completions 格式。

    关键差异处理:
    - Anthropic: tool_result 作为 role=user 的 content block
      OpenAI:  tool_result 作为独立的 role=tool 消息
    - Anthropic: tool_use 是 assistant content block
      OpenAI:  tool_calls 是 assistant 消息的独立字段
    - Anthropic: content 可以是字符串或 block 列表
      OpenAI:  content 通常是字符串,或 None(若有 tool_calls)
    """
    import json as _json
    result: list[dict] = []

    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')

        # 字符串 content 直接传
        if isinstance(content, str):
            result.append({'role': role, 'content': content})
            continue

        # 列表 content: 按类型拆分
        if role == 'user':
            text_parts: list[str] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get('type')
                if btype == 'text':
                    text_parts.append(block.get('text', ''))
                elif btype == 'tool_result':
                    # 先 flush 掉之前的 text(如果有)
                    if text_parts:
                        result.append({'role': 'user', 'content': '\n'.join(text_parts)})
                        text_parts = []
                    tr_content = block.get('content', '')
                    if not isinstance(tr_content, str):
                        tr_content = _json.dumps(tr_content, ensure_ascii=False, default=str)
                    result.append({
                        'role': 'tool',
                        'tool_call_id': block.get('tool_use_id', ''),
                        'content': tr_content,
                    })
            if text_parts:
                result.append({'role': 'user', 'content': '\n'.join(text_parts)})

        elif role == 'assistant':
            text_parts = []
            tool_calls: list[dict] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get('type')
                if btype == 'text':
                    text_parts.append(block.get('text', ''))
                elif btype == 'tool_use':
                    tool_calls.append({
                        'id': block.get('id', ''),
                        'type': 'function',
                        'function': {
                            'name': block.get('name', ''),
                            'arguments': _json.dumps(
                                block.get('input', {}), ensure_ascii=False
                            ),
                        },
                    })
            assistant_msg: dict = {
                'role': 'assistant',
                'content': '\n'.join(text_parts) if text_parts else None,
            }
            if tool_calls:
                assistant_msg['tool_calls'] = tool_calls
            result.append(assistant_msg)

    return result


def _anthropic_to_openai_tools(tools: list[dict]) -> list[dict]:
    """将内部工具定义转成 OpenAI function tool 定义"""
    out: list[dict] = []
    for t in tools or []:
        out.append({
            'type': 'function',
            'function': {
                'name': t.get('name', ''),
                'description': t.get('description', ''),
                'parameters': t.get(
                    'input_schema',
                    {'type': 'object', 'properties': {}},
                ),
            },
        })
    return out


class OpenAIClient(BaseLLMClient):
    """OpenAI Chat Completions API 的流式客户端。

    环境变量:
        OPENAI_API_KEY     必填
        OPENAI_BASE_URL    可选(Azure / 代理 / OpenAI 兼容服务)
        CLI_AGENT_MODEL    可选,默认 gpt-4o-mini

    注意:
    - ChatGPT Plus 订阅(chat.openai.com)**不包含** API 访问权。
      API key 需在 platform.openai.com 单独开通,按用量计费。
    - 中国大陆 IP 无法直接访问 api.openai.com,需配合 OPENAI_BASE_URL
      指向 Azure OpenAI、兼容代理或合规转发服务。
    """

    DEFAULT_MODEL = 'gpt-4o-mini'

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        from openai import OpenAI
        import httpx
        key = api_key or os.environ.get('OPENAI_API_KEY', '')
        if not key:
            raise LLMClientError(
                '未配置 OPENAI_API_KEY 环境变量,无法调用 OpenAI API。'
                '注意:ChatGPT Plus 订阅不含 API 访问权,需在 platform.openai.com 单独开通。'
            )
        # trust_env=False 同 ClaudeClient,绕开 macOS 系统代理,避免 Tailscale 流量被
        # ClashX/V2Ray 之类的本机代理截走。见 ClaudeClient.__init__ 的注释。
        self._client = OpenAI(
            api_key=key,
            base_url=base_url or os.environ.get('OPENAI_BASE_URL') or None,
            http_client=httpx.Client(trust_env=False, timeout=600),
        )
        self.model = model or os.environ.get('CLI_AGENT_MODEL', self.DEFAULT_MODEL)

    def stream(
        self,
        system_blocks: list[dict],
        tools: list[dict],
        messages: list[dict],
        max_tokens: int = 4096,
    ):
        import json as _json

        try:
            from openai import OpenAIError
        except ImportError:
            OpenAIError = Exception  # type: ignore

        # 格式转换
        openai_messages: list[dict] = [
            {'role': 'system', 'content': _extract_system_text(system_blocks)}
        ]
        openai_messages.extend(_anthropic_to_openai_messages(messages))
        openai_tools = _anthropic_to_openai_tools(tools) if tools else None

        logger.info(
            f'[CLI Agent LLM] OpenAI 请求 model={self.model} '
            f'msgs={len(openai_messages)} tools={len(openai_tools or [])}'
        )

        try:
            tool_calls_acc: dict[int, dict] = {}  # index → {id, name, arguments}
            usage_data: dict = {}
            finish_reason: str | None = None
            output_text_len: int = 0           # 追踪输出文本长度(用于离线估算)

            create_kwargs = dict(
                model=self.model,
                messages=openai_messages,
                tools=openai_tools,
                max_tokens=max_tokens,
                stream=True,
            )
            # stream_options 部分代理不支持,尝试启用
            try:
                stream = self._client.chat.completions.create(
                    **create_kwargs,
                    stream_options={'include_usage': True},
                )
            except Exception:
                logger.info('[CLI Agent LLM] stream_options 不受支持,降级为无 usage 流式')
                stream = self._client.chat.completions.create(**create_kwargs)

            for chunk in stream:
                # Usage 在最后一个 chunk(stream_options=include_usage)
                if getattr(chunk, 'usage', None) is not None:
                    u = chunk.usage
                    cached = 0
                    ptd = getattr(u, 'prompt_tokens_details', None)
                    if ptd is not None:
                        cached = getattr(ptd, 'cached_tokens', 0) or 0
                    usage_data = {
                        'input_tokens': getattr(u, 'prompt_tokens', 0) or 0,
                        'output_tokens': getattr(u, 'completion_tokens', 0) or 0,
                        'cache_read_input_tokens': cached,
                        'cache_creation_input_tokens': 0,
                    }

                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                delta = choice.delta

                # 文本增量
                if getattr(delta, 'content', None):
                    output_text_len += len(delta.content)
                    yield {'type': 'text_delta', 'text': delta.content}

                # Tool call 增量(OpenAI 分片发送,按 index 累加)
                if getattr(delta, 'tool_calls', None):
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {
                                'id': '', 'name': '', 'arguments': ''
                            }
                        if tc.id:
                            tool_calls_acc[idx]['id'] = tc.id
                        fn = getattr(tc, 'function', None)
                        if fn is not None:
                            if getattr(fn, 'name', None):
                                tool_calls_acc[idx]['name'] = fn.name
                            if getattr(fn, 'arguments', None):
                                tool_calls_acc[idx]['arguments'] += fn.arguments

                if choice.finish_reason:
                    finish_reason = choice.finish_reason

            # 流结束,把累积的 tool_calls 一次性 emit
            for idx in sorted(tool_calls_acc.keys()):
                tc = tool_calls_acc[idx]
                try:
                    tool_input = _json.loads(tc['arguments']) if tc['arguments'] else {}
                except _json.JSONDecodeError as e:
                    logger.warning(
                        f'[CLI Agent LLM] OpenAI tool_use 参数 JSON 解析失败: {e}, '
                        f'raw={tc["arguments"]!r}'
                    )
                    tool_input = {}
                yield {
                    'type': 'tool_use',
                    'id': tc['id'] or f'call_{idx}',
                    'name': tc['name'],
                    'input': tool_input,
                }

            # 如果代理不支持 stream_options 或返回全零，用离线估算兜底
            has_real_usage = usage_data and (
                usage_data.get('input_tokens', 0) > 0 or
                usage_data.get('output_tokens', 0) > 0
            )
            if not has_real_usage:
                import re as _re
                est_input = 0
                for m in openai_messages:
                    txt = str(m.get('content', ''))
                    cn = len(_re.findall(r'[\u4e00-\u9fff]', txt))
                    est_input += int(cn * 1.5 + (len(txt) - cn) / 4) + 5

                # 输出：文本 + 工具参数
                cn_out = len(_re.findall(r'[\u4e00-\u9fff]', str(output_text_len)))
                est_output = int(output_text_len / 4) + 5  # 粗估
                for idx in tool_calls_acc:
                    est_output += len(tool_calls_acc[idx].get('arguments', '')) // 4 + 20

                usage_data = {
                    'input_tokens': est_input,
                    'output_tokens': est_output,
                    'cache_read_input_tokens': 0,
                    'cache_creation_input_tokens': 0,
                    '_estimated': True,
                }

            # 映射 finish_reason 到我们统一的 stop_reason
            stop_map = {
                'stop': 'end_turn',
                'tool_calls': 'tool_use',
                'length': 'max_tokens',
                'content_filter': 'stop_sequence',
                'function_call': 'tool_use',
            }
            yield {
                'type': 'message_stop',
                'stop_reason': stop_map.get(finish_reason or '', finish_reason),
                'usage': usage_data,
                'model': self.model,
            }
            logger.info(
                f'[CLI Agent LLM] OpenAI 完成 finish={finish_reason} usage={usage_data}'
            )

        except OpenAIError as e:
            logger.exception('[CLI Agent LLM] OpenAI APIError')
            yield {'type': 'error', 'message': f'OpenAI API 错误: {e}'}
        except Exception as e:
            logger.exception('[CLI Agent LLM] 未预期错误')
            yield {'type': 'error', 'message': f'LLM 调用失败: {e}'}


# ─── 工厂方法 ───────────────────────────────────────────────────────────

def _auto_pick_openai_base_url() -> str | None:
    """根据 Flask config 的 IS_OVS 自动选 OpenAI 兼容端点。

    PMA CLI 始终用 OpenAI (via ChatGPT Plus OAuth 代理),只是代理的位置
    按部署环境不同:

    - **SG / OVS** (IS_OVS=True):
        SG NAS 在新加坡,可直连 api.openai.com。
        假设 SG NAS 本机已部署 `openai-oauth` 代理并 `codex login` 过。
        → http://127.0.0.1:10531/v1

    - **CN / SP8D 或本地 dev** (IS_OVS=False):
        中国大陆无法直连 api.openai.com,借道 Tailscale → Mac Mini (新加坡) 的代理。
        → http://100.110.41.83:10531/v1

    如果环境变量 OPENAI_BASE_URL 显式设了,会覆盖自动检测(适合本地开发或特殊情况)。

    Returns:
        str 如果能确定 base_url;None 如果无 Flask context(由调用方 fallback)
    """
    try:
        from flask import current_app
        is_ovs = bool(current_app.config.get('IS_OVS', False))
    except RuntimeError:
        return None

    if is_ovs:
        # SG OVS: 本机代理
        base_url = 'http://127.0.0.1:10531/v1'
        env = 'SG/OVS (local proxy)'
    else:
        # CN SP8D 或本地 dev: Mac Mini 桥(via Tailscale)
        base_url = 'http://100.110.41.83:10531/v1'
        env = 'CN/SP8D or local dev (Mac Mini bridge)'

    logger.info(
        f'[CLI Agent LLM] IS_OVS={is_ovs} 自动选 base_url={base_url} ({env})'
    )
    return base_url


def get_default_client() -> BaseLLMClient:
    """选择 LLM 客户端。

    PMA CLI 默认使用 OpenAI (经 openai-oauth 代理接入 ChatGPT Plus OAuth),
    **不提供 DeepSeek 等其他 provider 作为 fallback**——这是明确的架构选择。

    base_url 的解析顺序:
        1. 环境变量 OPENAI_BASE_URL 显式设置(最高优先,开发/调试用)
        2. 根据 Flask config IS_OVS 自动推断:
           - IS_OVS=True  → SG 本机代理 127.0.0.1:10531
           - IS_OVS=False → Mac Mini Tailscale 桥 100.110.41.83:10531
        3. 都没有 → 报错

    provider 覆盖:
        CLI_AGENT_PROVIDER=claude  改走 Anthropic Claude(需 ANTHROPIC_API_KEY)
        默认                        OpenAI(不带变量时)
    """
    provider = os.environ.get('CLI_AGENT_PROVIDER', 'openai').lower().strip()

    if provider == 'claude':
        base_url = os.environ.get('ANTHROPIC_BASE_URL', '').strip() or None
        return ClaudeClient(base_url=base_url)

    if provider == 'openai':
        # base_url:显式 env 优先,否则按 IS_OVS 自动推断
        base_url = os.environ.get('OPENAI_BASE_URL', '').strip() or None
        if not base_url:
            base_url = _auto_pick_openai_base_url()
        if not base_url:
            raise LLMClientError(
                '无法确定 OpenAI base_url。请在 .env 中设置 OPENAI_BASE_URL,'
                '或在有 Flask app context 的上下文中调用以便自动从 IS_OVS 推断。'
            )

        # api_key:openai-oauth 代理内部处理真实 OAuth,此处 key 只是占位
        api_key = os.environ.get('OPENAI_API_KEY', '').strip() or 'dummy-oauth-proxy'
        model = os.environ.get('CLI_AGENT_MODEL', '').strip() or 'gpt-5.3-codex'

        return OpenAIClient(api_key=api_key, model=model, base_url=base_url)

    raise LLMClientError(f'不支持的 CLI_AGENT_PROVIDER: {provider}')
