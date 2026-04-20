# -*- coding: utf-8 -*-
"""
Chat Agent Loop

结构参考 cli_agent/agent_loop.py,但适配聊天场景:

关键差异:
    1. 存储: 使用 ChatMessage 表(而非 CliSession.messages JSONB)。
       每轮调用只把最终的用户文本 + AI 文本写回;工具调用的 tool_use/tool_result
       blocks 只在本次 run() 内维持,不做跨轮持久化。
    2. 上下文: 下一轮调用时,从 ChatMessage 表按时间顺序读取最近 N 条文本消息,
       重建为纯文本 Anthropic messages 格式传给 LLM。
    3. 事件: emit 的事件直接对齐 chat.py/ai_stream 的协议
       ({'type': 'content', 'text': ...} / {'type': 'done', 'model': ...,
       'prompt_tokens': N, 'completion_tokens': N, 'full_text': ...})。
    4. 工具: 只注册 query_pma_database (+ 可选 export_to_word),
       query 走 execute_chat_safe_query (前端权限版)。

不做的事:
    - 不做自动压缩/摘要(聊天会话长度由 chat.py 的上下文预检查控制)
    - 不做 tool_use/tool_result 的数据库持久化(保持 ChatMessage 纯文本)
    - 不做 CLI 那种多 tab / 多 session 管理
"""
from __future__ import annotations

import logging
from typing import Iterator

from app import db
from app.models.chat import ChatMessage
from app.services.cli_agent import conversation as conv
from app.services.cli_agent.llm_client import BaseLLMClient, get_default_client
from app.services.chat_agent.prompt_builder import build_system_prompt_blocks
from app.services.chat_agent.tools import get_chat_default_registry
from app.services.cli_agent.tools import ToolRegistry

logger = logging.getLogger(__name__)


# 单轮 run 最多几次 "LLM→工具→LLM" 循环
_MAX_TOOL_ROUNDS_PER_RUN = 6

# 构建 LLM 请求时,总共加载多少条历史消息（用于生成摘要）
_HISTORY_LOAD_MESSAGES = 40
# 压缩后保留最近多少条消息原样（其余摘要化）
_HISTORY_KEEP_RECENT = 12


class ChatAgentLoop:
    """一个聊天对话的 Agent Loop 执行器"""

    def __init__(
        self,
        conversation_id: int,
        user,
        llm_client: BaseLLMClient | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self.conversation_id = conversation_id
        self.user = user
        self.llm = llm_client or get_default_client()
        self.tools = tool_registry or get_chat_default_registry()

    # ─── 主入口 ──────────────────────────────────────────────────────

    def run(self, user_input: str) -> Iterator[dict]:
        """处理一条用户输入,流式 yield 事件给 chat.py 的 ai_stream 消费。

        **注意**: 调用方需要负责把 user_input 作为 ChatMessage 写入数据库
        (chat.py 已经做了这一步,见 ai_stream 685-694 行)。这里只读历史、
        跑 loop、累加 token,最终 AI 回复由 chat.py 写回 ChatMessage。

        产出的事件:
            {'type': 'thinking', 'message': '...'}    状态提示(可选)
            {'type': 'content',  'text': '...'}        AI 文本增量
            {'type': 'tool_status', 'name': '...', 'phase': 'start|done|error'}
            {'type': 'done', 'model': '...', 'prompt_tokens': N,
             'completion_tokens': N, 'full_text': '...'}
            {'type': 'error', 'message': '...'}
        """
        if not user_input or not user_input.strip():
            yield {'type': 'error', 'message': '输入不能为空'}
            return

        # 1. 从 ChatMessage 表加载历史,重建 Anthropic messages 格式
        try:
            history_messages = self._load_history_as_messages()
        except Exception as e:
            logger.exception('[Chat Agent] 加载历史失败')
            yield {'type': 'error', 'message': f'加载对话历史失败: {e}'}
            return

        # 检测对话中未被 AI 处理过的文件附件，构造 content block
        file_blocks: list[dict] = []
        pending_file_msgs: list = []
        try:
            from app.services.chat_agent.file_processor import (
                get_pending_file_messages, build_file_content_blocks, mark_files_processed,
            )
            pending_file_msgs = get_pending_file_messages(self.conversation_id)
            if pending_file_msgs:
                file_blocks = build_file_content_blocks(pending_file_msgs)
                names = [m.file_name for m in pending_file_msgs if m.file_name]
                if file_blocks:
                    logger.info(f'[Chat Agent] 附带 {len(file_blocks)} 个文件: {names}')
        except Exception:
            logger.warning('[Chat Agent] 文件处理失败，继续纯文本对话', exc_info=True)

        # 追加本轮用户输入 + 文件 block(不写库,chat.py 已写过)
        user_content = file_blocks + [conv.text_block(user_input)]
        history_messages.append(
            {'role': 'user', 'content': user_content}
        )

        # 2. 构建 system prompt(享受 prompt cache)
        try:
            system_blocks = build_system_prompt_blocks(self.user)
        except Exception as e:
            logger.exception('[Chat Agent] 构建系统提示失败')
            yield {'type': 'error', 'message': f'构建系统提示失败: {e}'}
            return

        # chat 只注册 1–2 个工具,tools 前缀远低于 Anthropic 最小可缓存 token 数;
        # 挂 cache_control 会让 4321 proxy 直接 503(而非 Anthropic 官方文档的静默忽略)。
        tool_defs = self.tools.to_anthropic_tools(enable_cache_on_last=False)

        # 3. 运行 agent loop
        total_prompt_tokens = 0
        total_completion_tokens = 0
        model_name: str | None = None
        full_text = ''

        rounds = 0
        while rounds < _MAX_TOOL_ROUNDS_PER_RUN:
            rounds += 1
            if rounds == 1:
                yield {'type': 'thinking', 'message': '正在思考...'}
            else:
                yield {
                    'type': 'thinking',
                    'message': f'继续处理 (第 {rounds} 轮)...',
                }

            collected_blocks: list[dict] = []
            current_text = ''
            pending_tool_uses: list[dict] = []
            had_error = False

            for event in self.llm.stream(
                system_blocks=system_blocks,
                tools=tool_defs,
                messages=history_messages,
            ):
                etype = event.get('type')

                if etype == 'text_delta':
                    text = event.get('text', '')
                    current_text += text
                    full_text += text
                    yield {'type': 'content', 'text': text}

                elif etype == 'tool_use':
                    if current_text:
                        collected_blocks.append(conv.text_block(current_text))
                        current_text = ''
                    tu = conv.tool_use_block(
                        name=event['name'],
                        tool_input=event['input'],
                        tool_use_id=event['id'],
                    )
                    collected_blocks.append(tu)
                    pending_tool_uses.append(tu)
                    yield {
                        'type': 'tool_status',
                        'name': event['name'],
                        'phase': 'start',
                    }

                elif etype == 'message_stop':
                    if current_text:
                        collected_blocks.append(conv.text_block(current_text))
                        current_text = ''
                    usage = event.get('usage', {}) or {}
                    total_prompt_tokens += (
                        (usage.get('input_tokens') or 0)
                        + (usage.get('cache_read_input_tokens') or 0)
                        + (usage.get('cache_creation_input_tokens') or 0)
                    )
                    total_completion_tokens += usage.get('output_tokens') or 0
                    model_name = event.get('model') or model_name

                elif etype == 'error':
                    yield {
                        'type': 'error',
                        'message': event.get('message', '未知错误'),
                    }
                    had_error = True
                    break

            if had_error:
                # 带文件时 LLM 报错 → 标记文件已处理 + 降级为纯文本重试
                if pending_file_msgs and file_blocks and rounds == 1:
                    try:
                        mark_files_processed(pending_file_msgs)
                        db.session.commit()
                    except Exception:
                        logger.warning('[Chat Agent] 标记失败文件已处理异常', exc_info=True)
                    logger.info('[Chat Agent] 文件导致 LLM 错误，降级为纯文本重试')
                    history_messages[-1] = {
                        'role': 'user',
                        'content': [conv.text_block(
                            f'{user_input}\n\n（注：用户附带了文件但处理失败，请告知用户文件无法识别）'
                        )],
                    }
                    file_blocks = []
                    pending_file_msgs = []
                    had_error = False
                    full_text = ''
                    rounds = 0
                    continue
                return

            # LLM 返回空响应兜底
            if not collected_blocks and not pending_tool_uses:
                fallback = '抱歉,我暂时无法处理这个请求。请换个说法再试。'
                yield {'type': 'content', 'text': fallback}
                full_text += fallback
                break

            # 把本轮 assistant 回复追加到 in-memory messages(供下一轮 LLM 调用)
            if collected_blocks:
                history_messages.append(
                    {'role': 'assistant', 'content': collected_blocks}
                )

            if not pending_tool_uses:
                break

            # 执行所有 tool_use,生成 tool_result,追加为 user 消息
            tool_results: list[dict] = []
            for tu in pending_tool_uses:
                try:
                    tool = self.tools.get(tu['name'])
                    if tool is None:
                        output = {'error': f'未知工具: {tu["name"]}'}
                        is_error = True
                    else:
                        output = tool.execute(tu['input'], {'user': self.user})
                        is_error = isinstance(output, dict) and 'error' in output
                except Exception as e:
                    logger.exception(f'[Chat Agent] 工具 {tu["name"]} 执行异常')
                    output = {'error': f'工具执行异常: {e}'}
                    is_error = True

                tool_results.append(conv.tool_result_block(
                    tool_use_id=tu['id'],
                    content=output,
                    is_error=is_error,
                ))
                yield {
                    'type': 'tool_status',
                    'name': tu['name'],
                    'phase': 'error' if is_error else 'done',
                }
                # 文件导出工具：把下载链接推给前端
                if not is_error and isinstance(output, dict) and output.get('download_url'):
                    yield {
                        'type': 'download',
                        'filename': output.get('filename', '导出文件'),
                        'download_url': output['download_url'],
                    }

            history_messages.append({'role': 'user', 'content': tool_results})

        # 4. 标记文件消息为已处理（只在 LLM 成功响应后）
        if pending_file_msgs and file_blocks:
            try:
                mark_files_processed(pending_file_msgs)
                db.session.commit()
            except Exception:
                logger.warning('[Chat Agent] 标记文件已处理失败', exc_info=True)

        # 5. 收尾: emit done 事件
        yield {
            'type': 'done',
            'model': model_name or 'claude',
            'prompt_tokens': total_prompt_tokens,
            'completion_tokens': total_completion_tokens,
            'full_text': full_text,
        }

    # ─── 内部辅助 ────────────────────────────────────────────────────

    def _load_history_as_messages(self) -> list[dict]:
        """从 ChatMessage 表读最近历史,转成 Anthropic messages 纯文本格式。

        超过 _HISTORY_KEEP_RECENT 条时对旧消息生成规则摘要（不调 LLM），
        保留最近 _HISTORY_KEEP_RECENT 条原样，避免长对话静默丢失上下文。
        """
        rows = (
            ChatMessage.query.filter_by(
                conversation_id=self.conversation_id,
                is_deleted=False,
            )
            .filter(ChatMessage.message_type.in_(['text', 'form_result_card']))
            .order_by(ChatMessage.id.desc())
            .limit(_HISTORY_LOAD_MESSAGES)
            .all()
        )
        rows.reverse()  # 按时间正序

        # 转为 Anthropic messages 格式（纯文本，同 role 连续合并）
        all_messages: list[dict] = []
        for m in rows:
            if not (m.content or '').strip():
                continue
            role = 'assistant' if m.is_ai_response else 'user'
            text = m.content.strip()
            if all_messages and all_messages[-1]['role'] == role:
                all_messages[-1]['content'][0]['text'] += '\n\n' + text
            else:
                all_messages.append(
                    {'role': role, 'content': [conv.text_block(text)]}
                )

        # Anthropic 要求第一条必须是 user
        while all_messages and all_messages[0]['role'] != 'user':
            all_messages.pop(0)

        # 末尾如果是 user（刚写进 DB 的本轮输入），弹掉避免重复追加
        if all_messages and all_messages[-1]['role'] == 'user':
            all_messages.pop()

        # 超出保留数量时，对旧消息生成摘要
        if len(all_messages) > _HISTORY_KEEP_RECENT:
            old_messages = all_messages[:-_HISTORY_KEEP_RECENT]
            recent_messages = all_messages[-_HISTORY_KEEP_RECENT:]
            try:
                from app.services.cli_agent.compaction import _summarize_old_messages
                summary_text = _summarize_old_messages(old_messages)
                summary_msg = {
                    'role': 'user',
                    'content': [conv.text_block(
                        f'<chat_history_summary>\n{summary_text}\n</chat_history_summary>\n\n'
                        f'以上是之前 {len(old_messages)} 条消息的摘要，'
                        f'最近 {len(recent_messages)} 条消息保留原样如下。'
                    )],
                }
                return [summary_msg] + recent_messages
            except Exception:
                logger.warning('[Chat Agent] 历史摘要生成失败，回退到截断模式', exc_info=True)
                return recent_messages

        return all_messages
