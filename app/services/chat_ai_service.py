# -*- coding: utf-8 -*-
"""
AI 对话服务

使用 DeepSeek API（OpenAI 兼容）提供 AI 对话的流式响应功能，
支持 function calling 进行数据库查询。

循环调用（最多 3 轮）：
  每轮非流式检测 tool call → 执行工具 → 追加结果 → 下一轮
  最终流式输出答案（tool_choice=none 强制纯文本）
"""
import json
import os
import logging
import re

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DeepSeek DSML 标签过滤
# ---------------------------------------------------------------------------

# 匹配完整 function_calls 块: <｜DSML｜function_calls>...</｜DSML｜function_calls>
_DSML_FUNC_BLOCK = re.compile(r'<｜DSML｜function_calls>.*</｜DSML｜function_calls>', re.DOTALL)
# 匹配原始 <｜DSML｜>...</｜DSML｜> 块
_DSML_WRAP_BLOCK = re.compile(r'<｜DSML｜>.*?</｜DSML｜>', re.DOTALL)
# 匹配单个 DSML 标签: <｜DSML｜xxx> 和旧格式 <｜xxx｜>
_DSML_TAG_PATTERN = re.compile(r'</?｜(?:DSML｜)?[^>]*>')
# 解析 DSML function_calls 中的 invoke 和 parameter
_DSML_INVOKE_PATTERN = re.compile(
    r'<｜DSML｜invoke\s+name="([^"]+)"[^>]*>(.*?)</｜DSML｜invoke>', re.DOTALL)
_DSML_PARAM_PATTERN = re.compile(
    r'<｜DSML｜parameter\s+name="([^"]+)"[^>]*>(.*?)</｜DSML｜parameter>', re.DOTALL)


def _normalize_dsml(text):
    """归一化 DSML 标签：统一管道符格式（DeepSeek 有时输出半角 |）"""
    if '｜' not in text and '|' not in text:
        return text
    # 先将半角 | 在 DSML 上下文中转为全角
    text = re.sub(r'<\|', '<｜', text)
    text = re.sub(r'\|>', '｜>', text)
    # 移除全角 ｜ 周围的空格
    return re.sub(r'\s*｜\s*', '｜', text)


def _clean_dsml(text):
    """移除 DeepSeek 内部 DSML 标签及其包裹的内容"""
    if not text or ('｜' not in text and '|' not in text):
        return text
    # 0. 归一化：移除 ｜ 周围空格，保证正则匹配
    text = _normalize_dsml(text)
    # 1. 尝试移除完整块
    text = _DSML_FUNC_BLOCK.sub('', text)
    text = _DSML_WRAP_BLOCK.sub('', text)
    # 2. Fallback: 如果仍有 DSML 标记（块模式未匹配），截断到第一个标记前
    if '｜DSML' in text:
        idx = text.find('<｜DSML')
        if idx < 0:
            idx = text.find('｜DSML')
        if idx >= 0:
            text = text[:idx]
    # 3. 清理残留的单个标签（旧格式）
    text = _DSML_TAG_PATTERN.sub('', text)
    return text.strip()


def _parse_dsml_tool_calls(content):
    """从文本中解析 DSML 格式的函数调用，返回 [(name, args_dict), ...]"""
    if not content or ('｜' not in content and '|' not in content):
        return []
    # 归一化：移除 ｜ 周围空格
    content = _normalize_dsml(content)
    if '｜DSML｜function_calls' not in content:
        return []

    # 方法1: 结构化解析 DSML invoke/parameter 标签
    results = []
    for invoke_match in _DSML_INVOKE_PATTERN.finditer(content):
        name = invoke_match.group(1)
        invoke_body = invoke_match.group(2)
        args = {}
        for param_match in _DSML_PARAM_PATTERN.finditer(invoke_body):
            args[param_match.group(1)] = param_match.group(2).strip()
        results.append((name, args))

    # 方法2: Fallback — 结构化解析失败时，直接提取 SQL
    if not results:
        sql_match = re.search(r'\b(SELECT\s+.+?)\s*(?:</?｜|$)', content,
                              re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
            exp = '查询数据库'
            exp_match = re.search(r'explanation[^>]*>([^<]+)', content)
            if exp_match:
                exp = exp_match.group(1).strip()
            results.append(('query_database', {'sql': sql, 'explanation': exp}))

    return results


# ---------------------------------------------------------------------------
# Function calling 工具定义
# ---------------------------------------------------------------------------

TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'query_database',
            'description': '查询 PMA 数据库获取业务数据。仅支持 SELECT 查询。用于回答关于客户、项目、报价、产品、报销等数据相关的问题。',
            'parameters': {
                'type': 'object',
                'properties': {
                    'sql': {
                        'type': 'string',
                        'description': '要执行的 SQL SELECT 查询语句',
                    },
                    'explanation': {
                        'type': 'string',
                        'description': '简要说明这条查询的目的',
                    },
                },
                'required': ['sql'],
            },
        },
    }
]


# ---------------------------------------------------------------------------
# System Prompt 构建
# ---------------------------------------------------------------------------

def _build_system_prompt_with_schema(user):
    """构建包含 DB schema + 权限上下文的 system prompt"""
    from app.services.chat_db_query import get_permission_context, get_db_schema

    user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '未知用户')
    department = getattr(user, 'department', None) or '未设置'
    role = getattr(user, 'role', None) or 'user'

    permission_context = get_permission_context(user)
    db_schema = get_db_schema()

    return (
        '你是 PMA（项目管理助手）系统的 AI 业务助手。\n\n'
        '你的能力：\n'
        '1. 查询 PMA 数据库回答业务问题（客户、项目、报价、产品、报销等）\n'
        '2. 帮助用户进行中英文翻译\n'
        '3. 提供数据分析和业务洞察\n'
        '4. 解答技术问题和操作指引\n\n'
        '当用户的问题涉及具体数据（如数量、列表、统计）时，请使用 query_database 工具查询数据库。\n'
        '不涉及数据查询的问题（翻译、解释概念等）则直接回答。\n\n'
        '重要：对于任何数据查询请求，你必须始终重新调用 query_database 工具获取最新数据，\n'
        '绝对不要根据对话历史中的旧查询结果来回答。历史数据可能已过期或受权限变更影响。\n\n'
        '如果查询失败（如字段不存在），请根据错误信息默默修正 SQL 后重新查询。\n'
        '重要：不要向用户解释修正过程（如"让我修正列名"），只展示最终查询结果。\n\n'
        '请根据用户使用的语言回复。回答应简洁、准确。\n'
        '展示查询结果时，用清晰的格式（表格或列表）呈现。\n\n'
        f'--- 数据库结构 ---\n{db_schema}\n\n'
        f'--- {permission_context} ---\n\n'
        f'当前用户：{user_name}，部门：{department}，角色：{role}'
    )


# ---------------------------------------------------------------------------
# 主入口：流式 AI 响应
# ---------------------------------------------------------------------------

def get_ai_response_stream(message, user, conversation_history=None):
    """获取 AI 流式响应的生成器（DeepSeek + function calling）

    Args:
        message: 用户发送的消息文本
        user: 当前用户对象
        conversation_history: 对话历史 [{role, content}, ...]

    Yields:
        dict: 包含以下类型之一：
            - {'type': 'content', 'text': '...'} 内容片段
            - {'type': 'tool_call', 'name': '...', 'explanation': '...'} 工具调用通知
            - {'type': 'done', 'model': '...', 'prompt_tokens': N, 'completion_tokens': N}
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        logger.warning('未配置 DEEPSEEK_API_KEY')
        yield {'type': 'content', 'text': '⚠️ AI 服务未配置。请联系管理员设置 DEEPSEEK_API_KEY 环境变量。'}
        yield {'type': 'done', 'model': 'none', 'prompt_tokens': 0, 'completion_tokens': 0}
        return

    try:
        yield from _stream_deepseek_with_tools(message, user, api_key, conversation_history)
    except Exception as e:
        logger.error(f'DeepSeek 流式响应异常: {e}', exc_info=True)
        yield {'type': 'content', 'text': '抱歉，AI 服务暂时不可用，请稍后重试。'}
        yield {'type': 'done', 'model': 'error', 'prompt_tokens': 0, 'completion_tokens': 0}


# ---------------------------------------------------------------------------
# DeepSeek + Function Calling 循环调用（最多 3 轮）
# ---------------------------------------------------------------------------

MAX_TOOL_ROUNDS = 3


def _stream_deepseek_with_tools(message, user, api_key, conversation_history=None):
    """DeepSeek 循环调用：每轮非流式检测 tool call → 执行 → 最终流式输出"""
    model = os.environ.get('DEEPSEEK_CHAT_MODEL', 'deepseek-chat')
    base_url = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1').rstrip('/')
    system_prompt = _build_system_prompt_with_schema(user)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    # 构建消息列表
    messages = [{'role': 'system', 'content': system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({'role': 'user', 'content': message})

    total_prompt_tokens = 0
    total_completion_tokens = 0

    from app.services.chat_db_query import execute_safe_query

    # ── 循环：非流式检测 tool call，最多 MAX_TOOL_ROUNDS 轮 ──
    used_tools = False

    for round_idx in range(MAX_TOOL_ROUNDS):
        body = {
            'model': model,
            'messages': messages,
            'tools': TOOLS,
            'max_tokens': 2048,
            'stream': False,
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f'{base_url}/chat/completions', headers=headers, json=body)
            resp.raise_for_status()
            resp_data = resp.json()

        usage = resp_data.get('usage', {})
        total_prompt_tokens += usage.get('prompt_tokens', 0)
        total_completion_tokens += usage.get('completion_tokens', 0)

        choice = resp_data.get('choices', [{}])[0]
        assistant_msg = choice.get('message', {})
        tool_calls = assistant_msg.get('tool_calls')

        if not tool_calls:
            raw_content = assistant_msg.get('content', '')

            # ── 检测 DSML 文本型函数调用（模型未使用 API tool_calls，而是输出 DSML 文本）──
            dsml_calls = _parse_dsml_tool_calls(raw_content)
            if dsml_calls:
                logger.info(f'[AI] 检测到 DSML 文本型工具调用（第 {round_idx + 1} 轮），解析执行')
                used_tools = True
                # 不保留中间过程文本，防止模型在最终回复中回显
                messages.append({'role': 'assistant', 'content': ''})

                for func_name, args in dsml_calls:
                    if func_name == 'query_database':
                        sql = args.get('sql', '')
                        explanation = args.get('explanation', '查询数据库')
                        yield {'type': 'tool_call', 'name': func_name, 'explanation': explanation}
                        query_result = execute_safe_query(sql, user)

                        # 权限拒绝 → 立即中断，不浪费 token
                        error_msg = query_result.get('error', '')
                        if not query_result.get('success') and ('权限不足' in error_msg or '安全限制' in error_msg):
                            yield {'type': 'content', 'text': '抱歉，您没有权限查看该数据。请仅查询您有权限访问的业务数据。'}
                            yield {'type': 'done', 'model': model, 'prompt_tokens': total_prompt_tokens, 'completion_tokens': total_completion_tokens}
                            return

                        messages.append({
                            'role': 'user',
                            'content': f'以下是查询结果，请据此回答：\n{json.dumps(query_result, ensure_ascii=False, default=str)}',
                        })
                continue  # 继续下一轮，让模型基于查询结果生成回答

            # 无工具调用 — 该轮直接输出文本
            if not used_tools:
                # 从未调用过工具，直接返回文本
                content = _clean_dsml(raw_content)
                if content:
                    yield {'type': 'content', 'text': content}
                yield {
                    'type': 'done',
                    'model': model,
                    'prompt_tokens': total_prompt_tokens,
                    'completion_tokens': total_completion_tokens,
                }
                return
            else:
                # 已调用过工具，跳出循环进入最终流式输出
                break

        # ── 有工具调用 — 执行数据库查询 ──
        used_tools = True
        # 剥离中间过程文本（如"让我修正SQL..."），防止模型在最终回复中回显
        msg_for_context = dict(assistant_msg)
        msg_for_context['content'] = ''
        messages.append(msg_for_context)

        for tc in tool_calls:
            func = tc.get('function', {})
            func_name = func.get('name', '')
            try:
                args = json.loads(func.get('arguments', '{}'))
            except json.JSONDecodeError:
                args = {}

            if func_name == 'query_database':
                sql = args.get('sql', '')
                explanation = args.get('explanation', '查询数据库')

                yield {'type': 'tool_call', 'name': func_name, 'explanation': explanation}

                query_result = execute_safe_query(sql, user)

                # 权限拒绝 → 立即中断，不浪费 token
                error_msg = query_result.get('error', '')
                if not query_result.get('success') and ('权限不足' in error_msg or '安全限制' in error_msg):
                    yield {'type': 'content', 'text': '抱歉，您没有权限查看该数据。请仅查询您有权限访问的业务数据。'}
                    yield {'type': 'done', 'model': model, 'prompt_tokens': total_prompt_tokens, 'completion_tokens': total_completion_tokens}
                    return

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tc.get('id', ''),
                    'content': json.dumps(query_result, ensure_ascii=False, default=str),
                })
            else:
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tc.get('id', ''),
                    'content': json.dumps({'error': f'未知工具: {func_name}'}, ensure_ascii=False),
                })

        logger.info(f'[AI] Tool calling 第 {round_idx + 1} 轮完成')

    # ── 最终流式输出（tool_choice=none 强制纯文本） ──
    final_body = {
        'model': model,
        'messages': messages,
        'tools': TOOLS,
        'tool_choice': 'none',
        'max_tokens': 2048,
        'stream': True,
        'stream_options': {'include_usage': True},
    }

    prompt_tokens_final = 0
    completion_tokens_final = 0

    # DSML 流式抑制：一旦检测到 ｜ 字符，进入抑制模式，缓冲所有后续内容
    _dsml_mode = False
    _dsml_buffer = ''

    with httpx.Client(timeout=60.0) as client:
        with client.stream('POST', f'{base_url}/chat/completions', headers=headers, json=final_body) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith('data: '):
                    continue
                data_str = line[6:]
                if data_str.strip() == '[DONE]':
                    break
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = data.get('choices', [])
                if choices:
                    delta = choices[0].get('delta', {})
                    content = delta.get('content')
                    if content:
                        # DSML 抑制：流式 chunk 中检测到全角 ｜ 则缓冲
                        if _dsml_mode or '｜' in content or '<|' in content:
                            _dsml_mode = True
                            _dsml_buffer += content
                            continue

                        content = _clean_dsml(content)
                        if content:
                            yield {'type': 'content', 'text': content}

                usage_data = data.get('usage')
                if usage_data:
                    prompt_tokens_final = usage_data.get('prompt_tokens', 0)
                    completion_tokens_final = usage_data.get('completion_tokens', 0)

    # 刷新 DSML 缓冲区：清理后输出残留的有效文本
    if _dsml_buffer:
        cleaned = _clean_dsml(_dsml_buffer)
        if cleaned:
            yield {'type': 'content', 'text': cleaned}

    total_prompt_tokens += prompt_tokens_final
    total_completion_tokens += completion_tokens_final

    yield {
        'type': 'done',
        'model': model,
        'prompt_tokens': total_prompt_tokens,
        'completion_tokens': total_completion_tokens,
    }
