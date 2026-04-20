# -*- coding: utf-8 -*-
"""
Agent Loop:把 LLM、工具、对话、持久化串起来的主循环

流程:
    用户发消息
    → 追加到 Conversation (CliSession.messages)
    → while True:
        调用 LLM 流式
        → 把 text_delta 推给前端
        → 收集 tool_use 块
        → 如果没有 tool_use, 结束本轮
        → 如果有 tool_use, 执行每个工具, 追加 tool_result
        → 继续下一轮调用 LLM (让 LLM 基于工具结果继续回答)
    → 持久化 Session, 累加 usage
"""
from __future__ import annotations

import logging
from typing import Callable, Iterator

from app import db
from app.models.cli_session import CliSession
from app.services.cli_agent import conversation as conv
from app.services.cli_agent.compaction import compact, should_compact
from app.services.cli_agent.config import CLI_CONTEXT_REJECT, CLI_LLM_MAX_TOKENS, CLI_SESSION_MAX_TURNS
from app.services.cli_agent.usage import estimate_messages_tokens
from app.services.cli_agent.llm_client import BaseLLMClient, get_default_client
from app.services.cli_agent.base_agent_loop import BaseAgentLoop
from app.services.cli_agent.prompt_builder import build_system_prompt_blocks
from app.services.cli_agent.tools import ToolRegistry, get_default_registry

logger = logging.getLogger(__name__)


# 单次 run 内最多几次"LLM→工具→LLM"循环(防失控)
_MAX_TOOL_ROUNDS_PER_RUN = 6


class AgentLoop(BaseAgentLoop):
    """一个 Session 对应的 Agent Loop 执行器"""

    def __init__(
        self,
        session: CliSession,
        user,
        llm_client: BaseLLMClient | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        super().__init__(user=user, llm_client=llm_client, tools=tool_registry or get_default_registry())
        self.session = session

    # ─── 主入口 ─────────────────────────────────────────────────────

    def run(self, user_input: str) -> Iterator[dict]:
        """处理一条用户输入,流式 yield 事件给前端。

        产出的事件类型:
            {'type': 'status', 'message': '...'}          状态提示
            {'type': 'text_delta', 'text': '...'}         AI 文本增量
            {'type': 'tool_call', 'name': '...', 'input': {...}}   AI 要调工具
            {'type': 'tool_result', 'name': '...', 'output': {...}} 工具返回
            {'type': 'usage', 'usage': {...}}             本轮累计 usage
            {'type': 'done'}                               本次 run 完成
            {'type': 'error', 'message': '...'}           出错
        """
        if not user_input or not user_input.strip():
            yield {'type': 'error', 'message': '输入不能为空'}
            return

        # 硬上限保护
        if len(self.session.messages or []) >= CLI_SESSION_MAX_TURNS * 2:
            yield {
                'type': 'error',
                'message': f'会话已达到上限 ({CLI_SESSION_MAX_TURNS} 轮),请 /new 开新会话',
            }
            return

        # 追加用户消息
        self.session.append_message('user', [conv.text_block(user_input)])

        # 上下文管理：压缩或拒绝
        messages = self.session.messages or []
        est_tokens = estimate_messages_tokens(messages)

        if est_tokens >= CLI_CONTEXT_REJECT:
            yield {
                'type': 'error',
                'message': f'会话上下文已满 ({est_tokens:,} tokens)，请输入 /new 开新会话。',
            }
            return

        if should_compact(messages):
            logger.info(f'[CLI Agent] 触发压缩: {len(messages)} 条消息, ~{est_tokens} tokens')
            prev_summary = (self.session.compaction_meta or {}).get('last_summary')
            new_messages, summary = compact(messages, prev_summary)
            self.session.messages = new_messages
            count = (self.session.compaction_meta or {}).get('count', 0) + 1
            self.session.compaction_meta = {'count': count, 'last_summary': summary}
            yield {'type': 'status', 'message': f'上下文已压缩 (第 {count} 次)'}

        # 构建系统提示(每次重建,内容稳定,享受 prompt cache)
        try:
            system_blocks = build_system_prompt_blocks(self.user)
        except Exception as e:
            logger.exception('[CLI Agent] 构建系统提示失败')
            yield {'type': 'error', 'message': f'构建系统提示失败: {e}'}
            return

        tool_defs = self.tools.to_anthropic_tools()

        rounds = 0
        while rounds < _MAX_TOOL_ROUNDS_PER_RUN:
            rounds += 1
            yield {'type': 'status', 'message': f'思考中...' if rounds == 1 else f'继续处理 (第 {rounds} 轮)...'}

            # 从持久化的 messages 重建 request messages
            request_messages = list(self.session.messages or [])

            # 收集本轮输出
            collected_text_blocks: list[dict] = []
            current_text = ''
            pending_tool_uses: list[dict] = []
            had_error = False

            for event in self.llm.stream(
                system_blocks=system_blocks,
                tools=tool_defs,
                messages=request_messages,
                max_tokens=CLI_LLM_MAX_TOKENS,
            ):
                etype = event['type']

                if etype == 'text_delta':
                    current_text += event['text']
                    yield {'type': 'text_delta', 'text': event['text']}

                elif etype == 'tool_use':
                    # 先把当前累计的 text 固化为一个 text block
                    if current_text:
                        collected_text_blocks.append(conv.text_block(current_text))
                        current_text = ''
                    tool_use = conv.tool_use_block(
                        name=event['name'],
                        tool_input=event['input'],
                        tool_use_id=event['id'],
                    )
                    collected_text_blocks.append(tool_use)
                    pending_tool_uses.append(tool_use)
                    yield {
                        'type': 'tool_call',
                        'name': event['name'],
                        'input': event['input'],
                    }

                elif etype == 'message_stop':
                    # 收尾:把最后一段 text 也固化
                    if current_text:
                        collected_text_blocks.append(conv.text_block(current_text))
                        current_text = ''
                    # 累计 usage，记录模型名
                    self.session.accumulate_usage(event.get('usage', {}))
                    if event.get('model'):
                        self.session.model = event['model']
                    yield {
                        'type': 'usage',
                        'usage': event.get('usage', {}),
                        'model': event.get('model'),
                    }
                    # max_tokens 截断时 tool_use JSON 不完整,丢弃残缺工具调用
                    if event.get('stop_reason') == 'max_tokens' and not pending_tool_uses:
                        if collected_text_blocks:
                            # 只保留纯文本块,丢弃不完整的 tool_use 块
                            collected_text_blocks = [
                                b for b in collected_text_blocks if b.get('type') == 'text'
                            ]
                        truncation_msg = '回复内容过长被截断，请缩小查询范围后重试。'
                        collected_text_blocks.append(conv.text_block(truncation_msg))
                        yield {'type': 'text_delta', 'text': '\n\n' + truncation_msg}

                elif etype == 'error':
                    yield {'type': 'error', 'message': event.get('message', '未知错误')}
                    had_error = True
                    break

            if had_error:
                self._persist()
                return

            # 把 assistant 消息写入对话
            # 如果 LLM 返回空响应（无文本、无工具调用），插入兜底回复
            if not collected_text_blocks and not pending_tool_uses:
                fallback = conv.text_block('抱歉，我暂时无法处理这个请求。请换个说法再试，或输入 /new 开新会话。')
                self.session.append_message('assistant', [fallback])
                yield {'type': 'text_delta', 'text': fallback['text']}
                break

            if collected_text_blocks:
                self.session.append_message('assistant', collected_text_blocks)

            # 如果没有 tool_use,本次 run 结束
            if not pending_tool_uses:
                break

            # 执行所有 tool_use,生成对应的 tool_result
            tool_results: list[dict] = []
            for tu in pending_tool_uses:
                yield {
                    'type': 'status',
                    'message': f'正在执行 {self._friendly_tool_name(tu["name"])}...',
                }
                output, is_error = self._run_tool(tu)

                # invoke_skill 的 artifacts 直接推给前端，不经过 LLM
                if tu['name'] == 'invoke_skill' and not is_error:
                    arts = output.get('artifacts') or []
                    print(f'[agent_loop] invoke_skill artifacts count={len(arts)}', flush=True)
                    for art in arts:
                        yield {'type': 'artifact', 'title': art.get('title', ''), 'html': art.get('html', '')}

                # artifacts 体积大，不传给 LLM
                llm_output = output
                if tu['name'] == 'invoke_skill' and isinstance(output, dict) and 'artifacts' in output:
                    llm_output = {k: v for k, v in output.items() if k != 'artifacts'}

                tool_results.append(conv.tool_result_block(
                    tool_use_id=tu['id'],
                    content=llm_output,
                    is_error=is_error,
                ))
                yield {
                    'type': 'tool_result',
                    'name': tu['name'],
                    'output': llm_output,
                    'is_error': is_error,
                }

            # 工具结果作为 user 消息追加,进入下一轮
            self.session.append_message('user', tool_results)

        self._persist()
        yield {'type': 'done'}

    # ─── 辅助 ──────────────────────────────────────────────────────

    @staticmethod
    def _friendly_tool_name(name: str) -> str:
        mapping = {
            'query_pma_database': '查询业务数据库',
        }
        return mapping.get(name, name)

    def _persist(self) -> None:
        """把 session 的变更刷到数据库"""
        try:
            db.session.add(self.session)
            db.session.commit()
        except Exception:
            logger.exception('[CLI Agent] 持久化 Session 失败')
            db.session.rollback()
