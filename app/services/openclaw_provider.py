# -*- coding: utf-8 -*-
"""
OpenClaw Gateway 集成

通过 WebSocket 直连 OpenClaw Gateway，将用户消息发送给 OpenClaw 智能体，
并以流式方式返回 AI 响应。使用与 DeepSeek 相同的 SSE yield 格式。

协议：OpenClaw Gateway WebSocket Protocol v3
  1. 客户端连接 ws://host:port
  2. 服务端发送 connect.challenge（nonce + ts）
  3. 客户端发送 connect 请求（含 device 签名 + token 认证）
  4. 客户端发送 chat.send 请求（用户消息）
  5. 服务端通过 chat event 帧流式返回内容
"""
import asyncio
import base64
import hashlib
import json
import logging
import os
import queue
import threading
import time
import uuid

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

# Default timeout for the entire chat exchange (seconds)
_CHAT_TIMEOUT = 120

# ── Tool name → friendly status mapping ─────────────────────────────
_TOOL_FRIENDLY_NAMES = {
    'query_database': '正在查询数据库...',
    'query_pma_database': '正在查询业务数据库...',
    'read_file': '正在读取文件...',
    'write_file': '正在写入文件...',
    'web_search': '正在搜索...',
    'execute_code': '正在执行代码...',
}


def _tool_friendly_name(tool_name):
    """将工具名转换为用户友好的自然语言状态"""
    if tool_name in _TOOL_FRIENDLY_NAMES:
        return _TOOL_FRIENDLY_NAMES[tool_name]
    return f'正在执行 {tool_name}...'

# Device identity file path
_IDENTITY_PATH = os.path.join(os.path.expanduser('~'), '.openclaw', 'pma-device-identity.json')


# ── Device identity helpers ──────────────────────────────────────────

def _b64url(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _generate_identity():
    """Generate a new Ed25519 key pair and derive device ID."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode('ascii')

    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode('ascii')

    # Raw 32-byte public key from SPKI DER (strip 12-byte prefix)
    spki_der = public_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    raw_pub = spki_der[-32:]

    device_id = hashlib.sha256(raw_pub).hexdigest()

    return {
        'deviceId': device_id,
        'publicKeyPem': public_pem,
        'privateKeyPem': private_pem,
        'rawPublicKey': raw_pub,
    }


def _load_or_create_identity():
    """Load persisted device identity or create a new one."""
    if os.path.exists(_IDENTITY_PATH):
        try:
            with open(_IDENTITY_PATH) as f:
                stored = json.load(f)
            if stored.get('version') == 1 and stored.get('privateKeyPem'):
                # Reconstruct raw public key
                private_key = serialization.load_pem_private_key(
                    stored['privateKeyPem'].encode(), password=None,
                )
                public_key = private_key.public_key()
                spki_der = public_key.public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                raw_pub = spki_der[-32:]
                device_id = hashlib.sha256(raw_pub).hexdigest()
                return {
                    'deviceId': device_id,
                    'publicKeyPem': stored['publicKeyPem'],
                    'privateKeyPem': stored['privateKeyPem'],
                    'rawPublicKey': raw_pub,
                }
        except Exception:
            logger.warning('无法读取 device identity 文件，将重新生成')

    identity = _generate_identity()
    os.makedirs(os.path.dirname(_IDENTITY_PATH), exist_ok=True)
    with open(_IDENTITY_PATH, 'w') as f:
        json.dump({
            'version': 1,
            'deviceId': identity['deviceId'],
            'publicKeyPem': identity['publicKeyPem'],
            'privateKeyPem': identity['privateKeyPem'],
            'createdAtMs': int(time.time() * 1000),
        }, f, indent=2)
    os.chmod(_IDENTITY_PATH, 0o600)
    return identity


def _sign_device_payload(private_pem: str, payload: str) -> str:
    """Sign payload with Ed25519 private key, return base64url signature."""
    private_key = serialization.load_pem_private_key(
        private_pem.encode(), password=None,
    )
    sig = private_key.sign(payload.encode('utf-8'))
    return _b64url(sig)


def _build_device_auth(identity, client_id, client_mode, role, scopes, token, nonce):
    """Build the device auth object for the connect request."""
    signed_at_ms = int(time.time() * 1000)
    scopes_str = ','.join(scopes)
    payload = '|'.join([
        'v2',
        identity['deviceId'],
        client_id,
        client_mode,
        role,
        scopes_str,
        str(signed_at_ms),
        token or '',
        nonce or '',
    ])
    signature = _sign_device_payload(identity['privateKeyPem'], payload)

    return {
        'id': identity['deviceId'],
        'publicKey': _b64url(identity['rawPublicKey']),
        'signature': signature,
        'signedAt': signed_at_ms,
        'nonce': nonce or '',
    }


# ── Keyword categories for layered prompt injection ──────────────────
# 按意图分类关键词，按需注入对应 prompt 层级，避免每次都塞全套

_FORM_KEYWORDS = {'新建', '创建', '添加', '报销', '记一笔'}
_EDIT_KEYWORDS = {'修改', '编辑', '更新', '改一下'}  # 需要 DB 查找 + 表单
_QUERY_KEYWORDS = {
    '查询', '统计', '多少', '排名', '对比', '汇总', '分析',
    '趋势', '增长', '下降', '同比', '环比', '数据',
    'query', 'report', 'data',
}
_ENTITY_KEYWORDS = {
    '项目', '客户', '报价', '订单', '产品', '公司', '联系人',
    '费用', '预算', '合同', '人员', '任务', '部门', '销售',
    '业绩', '金额', '利润', '成本', '跟进', '记录',
    'project', 'customer', 'expense', 'quotation', 'product',
    'order', 'task', 'sales',
}


def _detect_prompt_needs(message):
    """检测消息需要哪些 prompt 层级: 'form' / 'query' / 两者 / 空"""
    msg = message.lower()
    needs = set()

    if any(kw in msg for kw in _FORM_KEYWORDS):
        needs.add('form')
    if any(kw in msg for kw in _QUERY_KEYWORDS):
        needs.add('query')
    if any(kw in msg for kw in _EDIT_KEYWORDS):
        needs.add('form')
        needs.add('query')

    # "跟进" 需要先查客户/联系人再创建表单
    if '跟进' in msg and any(kw in msg for kw in ('新', '添', '创', '记', '做')):
        needs.add('form')
        needs.add('query')

    # 实体关键词不带动作词 → 推断为查询意图
    if not needs and any(kw in msg for kw in _ENTITY_KEYWORDS):
        needs.add('query')

    return needs


def _build_form_prompt(include_query_sql=False):
    """构建精简的表单交互工具提示（~700字 vs 旧版 ~3,500字）"""
    prompt = (
        '[表单工具] 用户要求创建/修改数据时，回复末尾插入标记，系统自动转为交互式表单。\n'
        '回复只需简短一句+标记。禁止暴露表名/字段名/SQL/ID编号/技术术语。\n'
        '标记格式（必须在回复最后一行）：\n'
        '- 新建客户: [[FORM:create_customer|{"company_name":"从对话提取","country":"如有","company_type":"如有","address":"如有"}]]\n'
        '- 修改客户: [[FORM:edit_customer|{"id":客户ID,"company_name":"如需修改","address":"如需修改"}]]\n'
        '- 新建联系人: [[FORM:create_contact|{"company_id":公司ID,"name":"姓名","phone":"如有","email":"如有"}]]\n'
        '- 修改联系人: [[FORM:edit_contact|{"id":联系人ID,"company_id":公司ID,"name":"如需修改","phone":"如需修改"}]]\n'
        '- 新建项目: [[FORM:create_project|{"project_name":"项目名","project_type":"channel_follow/sales_focus/business_opportunity","report_source":"channel/sales/marketing","industry":"如有"}]]\n'
        '- 修改项目: [[FORM:edit_project|{"id":项目ID,"project_name":"如需修改"}]]\n'
        '- 报销单: [[FORM:create_expense|{}]]（无需填字段，系统自动打开报销页面）\n'
        '- 跟进记录: [[FORM:create_action|{"company_id":公司ID,"contact_id":联系人ID,"communication":"跟进内容"}]]\n'
        'prefill JSON只填对话中已知信息，未知留空。标记必须在回复最后一行。\n'
        '匹配多个结果时用选项标记: [[CHOICES:动作|名称1:ID1|名称2:ID2]]，系统自动渲染为按钮。\n'
    )

    if include_query_sql:
        prompt += (
            '内部查询SQL（不展示给用户）：\n'
            "查客户: SELECT id,company_name FROM companies WHERE company_name ILIKE '%关键词%' AND is_deleted=false\n"
            "查联系人: SELECT c.id,c.name,c.company_id,co.company_name FROM contacts c JOIN companies co ON c.company_id=co.id WHERE c.name ILIKE '%关键词%'\n"
            "查项目: SELECT id,project_name FROM projects WHERE project_name ILIKE '%关键词%' AND is_deleted=false\n"
            '修改前必须先查DB获取ID，但查询过程不展示给用户。\n'
        )

    return prompt


# ── Main entry point ─────────────────────────────────────────────────

def _build_tool_prompt(user, conversation_id=None, needs=None):
    """按需构建工具提示，只注入必要的层级。

    needs: set containing 'form' and/or 'query'
    - form only:  ~700字  (创建类操作)
    - query only: ~1,200字 (数据查询)
    - form+query: ~1,900字 (修改类操作，需先查后改)
    - 旧版全量:   ~4,900字 (每次都塞)
    """
    if not needs:
        return ''

    try:
        parts = []
        user_id = user.id
        pma_base_url = os.environ.get('PMA_API_BASE_URL', '').rstrip('/')

        # 层级: DB 查询工具（schema + 权限 + 文件上传）
        if 'query' in needs:
            from app.services.chat_db_query import get_db_schema, get_permission_context
            db_schema = get_db_schema()
            permission_context = get_permission_context(user)
            parts.append(
                '[核心规则] 你是业务助理，不是程序员。回复只包含最终结果：\n'
                '- 涉及公司、项目、报价等业务数据时，必须使用 query_pma_database 查询，禁止凭记忆或之前的查询结果回答\n'
                '- 禁止展示查询步骤（"先查看X表"、"让我重新查询"、"尝试使用web_search"）\n'
                '- 禁止提及技术术语（表名、字段名、SQL、ID编号、权限规则）\n'
                '- 查不到就换方式查或简短告知，不要解释内部过程\n'
                '[回复风格] 用一条SQL尽量获取完整信息，避免多轮查询。回复简短直接，用数据说话。'
                '除非用户明确要求，不要主动做额外查询或展开分析。\n'
                '[外部搜索] 当用户询问公开信息（公司地址、行业资料、产品参数、新闻等），如果数据库查不到或查到的字段为空，'
                '必须自动调用 web_search 搜索互联网补充。禁止回复"暂无"、"暂未记录"、"无法查到"。\n'
                '[系统提示] 查询数据库时请使用 query_pma_database 工具，'
                f'传入 sql、user_id={user_id} 和 api_base_url="{pma_base_url}" 三个参数。'
                f'api_base_url 必须使用 "{pma_base_url}"，不可修改。'
                '禁止使用 exec/curl 调用数据库 API。\n'
                f'\n{db_schema}\n\n{permission_context}\n'
            )

            # 可视化标记（多结果选项 + 单项目卡片）
            parts.append(
                '[可视化标记] 查询匹配多个客户/项目等实体时，用选项标记让用户选择：'
                '[[CHOICES:名称1:ID1|名称2:ID2]]，系统渲染为可点击链接。'
                '查询明确指向单个项目时，末尾插入 [[PROJECT_CARD:项目ID]]，系统渲染为项目卡片（含阶段进度条）。'
                '使用PROJECT_CARD时，卡片已包含项目核心信息，文字部分只需一句简短总结，不要重复列出卡片中已有的字段。\n'
            )

            # 文件上传工具（仅查询场景可能生成文件需要上传）
            ai_token = os.environ.get('PMA_AI_QUERY_TOKEN', '')
            if conversation_id and pma_base_url and ai_token:
                parts.append(
                    f'[文件分享工具] 生成文件后用 POST {pma_base_url}/chat/api/ai/upload-file 上传到对话中'
                    f'（Header: Authorization: Bearer {ai_token}，'
                    f'multipart form-data: file, conversation_id={conversation_id}, user_id={user_id}）。'
                    f'文件名必须用中文描述性命名（如"李华伟活跃项目.xlsx"），禁止用系统编号命名。'
                    f'重要：读取和上传文件时必须使用二进制模式（open(path, "rb")），禁止用文本模式读取二进制文件，否则会导致文件损坏。'
                    f'上传成功后，必须将返回的 download_url 以 Markdown 链接格式写入回复，例如：[点击下载文件名](download_url)。\n'
                )

        # 层级: 表单交互工具
        if 'form' in needs and conversation_id:
            include_sql = 'query' in needs  # 修改类需要查询 SQL
            parts.append(_build_form_prompt(include_sql))

        return '\n'.join(parts)
    except Exception as e:
        logger.warning(f'构建工具提示失败: {e}')
        return ''


def send_openclaw_request(message, timeout=180):
    """发送请求到 OpenClaw 并等待完整响应（非流式）

    用于 AI 调研等不需要流式输出的场景。复用 _ws_chat WebSocket 连接，
    不注入用户身份和 DB 工具提示（纯净研究请求）。

    Args:
        message: 发送给 AI 的完整提示词
        timeout: 超时秒数（默认 180 秒，调研任务较慢）

    Returns:
        str: AI 的完整文本响应

    Raises:
        RuntimeError: 连接失败或超时
    """
    gateway_url = os.environ.get('OPENCLAW_GATEWAY_URL', '')
    if not gateway_url:
        raise RuntimeError('未配置 OPENCLAW_GATEWAY_URL')

    token = os.environ.get('OPENCLAW_GATEWAY_TOKEN', '')
    session_id = f'pma-research-{uuid.uuid4().hex[:8]}'

    result_queue = queue.Queue()

    def _run():
        try:
            asyncio.run(_ws_chat(gateway_url, token, message, session_id, result_queue))
        except Exception as e:
            logger.error(f'OpenClaw research 线程异常: {e}', exc_info=True)
            result_queue.put({'type': 'error', 'text': str(e)})
        finally:
            result_queue.put(None)  # sentinel

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # 收集所有 content 事件的文本
    collected = []
    start_time = time.time()

    while True:
        remaining = timeout - (time.time() - start_time)
        if remaining <= 0:
            raise RuntimeError(f'OpenClaw 请求超时（{timeout}s）')
        try:
            item = result_queue.get(timeout=min(remaining, 2.0))
        except queue.Empty:
            continue
        if item is None:
            break
        item_type = item.get('type', '')
        if item_type == 'content':
            text = item.get('text', '')
            # _ws_chat 连接失败时会发送 ⚠️ 开头的 content 事件
            if text.startswith('⚠️') and not collected:
                raise RuntimeError(text)
            collected.append(text)
        elif item_type == 'agent_status':
            # 记录工具调用状态，便于排查 web_search 等工具是否被调用
            msg = item.get('message', '')
            if msg:
                logger.info(f'[OpenClaw-Research] agent_status: {msg}')
        elif item_type == 'error':
            raise RuntimeError(f'OpenClaw 请求失败: {item.get("text", "")}')
        elif item_type == 'done':
            # _ws_chat 完成，不再等待
            break

    result = ''.join(collected)
    if not result.strip():
        raise RuntimeError('OpenClaw 返回了空响应')

    logger.info(f'[OpenClaw-Research] 完成, 响应长度={len(result)}')
    return result


def get_openclaw_response_stream(message, session_id=None,
                                 user=None, conversation_id=None):
    """获取 OpenClaw 流式响应的生成器

    通过 WebSocket 直连 OpenClaw Gateway，发送用户消息并流式接收响应。
    保持与 DeepSeek 兼容的 SSE 格式。

    Args:
        message: 用户消息文本
        session_id: OpenClaw session ID，用于保持对话上下文
        user: 当前用户对象（用于注入 DB 查询工具说明）
        conversation_id: 当前对话 ID（用于注入文件上传工具说明）

    Yields:
        dict: 与 DeepSeek 格式一致：
            - {'type': 'content', 'text': '...'} 内容
            - {'type': 'done', 'model': 'openclaw/...', ...}
    """
    gateway_url = os.environ.get('OPENCLAW_GATEWAY_URL', '')
    if not gateway_url:
        logger.warning('未配置 OPENCLAW_GATEWAY_URL')
        yield {'type': 'content', 'text': '⚠️ AI 服务未配置。请联系管理员设置 OPENCLAW_GATEWAY_URL。'}
        yield {'type': 'done', 'model': 'none', 'prompt_tokens': 0, 'completion_tokens': 0}
        return

    token = os.environ.get('OPENCLAW_GATEWAY_TOKEN', '')
    if not session_id:
        session_id = f'pma-{uuid.uuid4().hex[:8]}'

    # ① 准备阶段
    _perf_start = time.time()
    _perf_db_injected = False
    _perf_msg_preview = message[:50].replace('\n', ' ')
    yield {'type': 'status', 'message': '正在理解您的问题...'}

    # 注入用户身份到消息上下文（确保 AI 知道当前用户身份，实现 session 级隔离）
    user_name = ''
    if user:
        user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '') or ''
        user_identity = f'[系统] 当前用户: {user_name} (ID:{user.id})'
    else:
        user_identity = ''

    # 按需注入工具提示（分层：form / query / 两者），避免每次都塞全套 ~4,900 字
    needs = _detect_prompt_needs(message) if user else set()
    if needs:
        tool_prompt = _build_tool_prompt(user, conversation_id=conversation_id, needs=needs)
        if tool_prompt:
            _perf_db_injected = True
            _perf_prompt_len = len(tool_prompt)
            message = f'{user_identity}\n{tool_prompt}\n[用户消息] {message}'
            logger.info(f'[OpenClaw-Perf] 提示已注入 layers={needs}, prompt_chars={_perf_prompt_len}, msg="{_perf_msg_preview}"')
        elif user_identity:
            message = f'{user_identity}\n[用户消息] {message}'
            logger.info(f'[OpenClaw-Perf] 用户标识已注入(构建失败), msg="{_perf_msg_preview}"')
    elif user_identity:
        message = f'{user_identity}\n[用户消息] {message}'
        logger.info(f'[OpenClaw-Perf] 用户标识已注入(无工具提示), msg="{_perf_msg_preview}"')

    # ② 连接阶段
    yield {'type': 'status', 'message': '正在连接 AI 服务...'}

    # Use a thread + queue to bridge async websockets → sync generator
    result_queue = queue.Queue()

    def _run():
        try:
            user_id = user.id if user else None
            user_display = user_name if user else None
            asyncio.run(_ws_chat(gateway_url, token, message, session_id, result_queue,
                                 user_id=user_id, user_name=user_display))
        except Exception as e:
            logger.error(f'OpenClaw WebSocket 线程异常: {e}', exc_info=True)
            result_queue.put({'type': 'content', 'text': f'⚠️ AI 服务异常：{e}'})
            result_queue.put({'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0})
        finally:
            result_queue.put(None)  # sentinel

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # 分段超时：每秒检查一次，支持慢速提醒
    start_time = time.time()
    slow_warned = False
    _perf_first_token = False  # TTFT 标记

    while True:
        try:
            item = result_queue.get(timeout=1.0)
        except queue.Empty:
            elapsed = time.time() - start_time
            if elapsed > 15 and not slow_warned:
                slow_warned = True
                yield {'type': 'status', 'message': f'AI 思考时间较长（已等待 {int(elapsed)} 秒），请耐心等待...'}
            elif elapsed > _CHAT_TIMEOUT:
                logger.error('OpenClaw WebSocket 响应超时')
                yield {'type': 'content', 'text': '⚠️ AI 响应超时，请稍后重试。'}
                yield {'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0}
                return
            continue
        if item is None:
            # 流结束，记录总耗时
            _perf_total = time.time() - _perf_start
            logger.info(
                f'[OpenClaw-Perf] 完成 total={_perf_total:.1f}s '
                f'db_injected={_perf_db_injected} msg="{_perf_msg_preview}"'
            )
            return

        # 记录 TTFT（首个 content token 到达的时间）
        if not _perf_first_token and item.get('type') == 'content':
            _perf_first_token = True
            _perf_ttft = time.time() - _perf_start
            logger.info(
                f'[OpenClaw-Perf] TTFT={_perf_ttft:.1f}s '
                f'db_injected={_perf_db_injected} msg="{_perf_msg_preview}"'
            )

        # 收到消息后重置计时器
        start_time = time.time()
        slow_warned = False
        yield item


async def _ws_chat(url, token, message, session_key, q,
                    user_id=None, user_name=None):
    """Async WebSocket chat session with OpenClaw Gateway.

    Connects, authenticates (with device signing), sends a chat message,
    and streams back response events via the provided queue.
    """
    import websockets

    identity = _load_or_create_identity()

    async with websockets.connect(url, max_size=2**22) as ws:
        # ------ Step 1: Receive connect.challenge ------
        challenge_raw = await asyncio.wait_for(ws.recv(), timeout=10)
        challenge = json.loads(challenge_raw)

        nonce = ''
        if challenge.get('type') == 'event' and challenge.get('event') == 'connect.challenge':
            nonce = challenge.get('payload', {}).get('nonce', '')
        else:
            logger.warning(f'预期 connect.challenge，收到: {challenge}')

        # ------ Step 2: Send connect request with device auth ------
        client_id = 'gateway-client'
        client_mode = 'backend'
        role = 'operator'
        scopes = ['operator.read', 'operator.write', 'operator.admin']

        device_auth = _build_device_auth(
            identity, client_id, client_mode, role, scopes, token, nonce,
        )

        connect_id = _req_id()
        connect_req = {
            'type': 'req',
            'id': connect_id,
            'method': 'connect',
            'params': {
                'minProtocol': 3,
                'maxProtocol': 3,
                'client': {
                    'id': client_id,
                    'displayName': 'PMA Server',
                    'version': '1.0.0',
                    'platform': 'python',
                    'mode': client_mode,
                },
                'role': role,
                'scopes': scopes,
                'device': device_auth,
                'auth': {
                    'token': token,
                },
            },
        }
        await ws.send(json.dumps(connect_req))

        # Wait for connect response
        connect_res = await asyncio.wait_for(_recv_response(ws, connect_id), timeout=10)
        if not connect_res.get('ok'):
            error = connect_res.get('error', {})
            msg = error.get('message', '认证失败') if isinstance(error, dict) else str(error)
            logger.error(f'[OpenClaw] 连接失败: {msg}, device_id={identity["deviceId"][:12]}..., response={json.dumps(connect_res, ensure_ascii=False)[:300]}')
            q.put({'type': 'content', 'text': f'⚠️ AI 连接失败：{msg}'})
            q.put({'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0})
            return

        # 连接成功
        q.put({'type': 'status', 'message': '正在分析问题...'})

        # ------ Step 3: Send chat.send request ------
        chat_id = _req_id()
        chat_params = {
            'sessionKey': session_key,
            'message': message,
            'idempotencyKey': uuid.uuid4().hex,
        }
        # 附加用户 metadata（Gateway 会忽略未知字段，不影响功能）
        if user_id is not None:
            chat_params['metadata'] = {
                'userId': user_id,
                'userName': user_name or '',
                'source': 'pma',
            }
        chat_req = {
            'type': 'req',
            'id': chat_id,
            'method': 'chat.send',
            'params': chat_params,
        }
        await ws.send(json.dumps(chat_req))

        # Wait for immediate ack (non-blocking – returns runId)
        chat_ack = await asyncio.wait_for(_recv_response(ws, chat_id), timeout=15)
        if not chat_ack.get('ok'):
            error = chat_ack.get('error', {})
            msg = error.get('message', '发送失败') if isinstance(error, dict) else str(error)
            q.put({'type': 'content', 'text': f'⚠️ AI 发送消息失败：{msg}'})
            q.put({'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0})
            return

        run_id = chat_ack.get('payload', {}).get('runId', '')

        # chat.send 已接受，AI 正在思考
        q.put({'type': 'status', 'message': '正在思考...'})

        # ------ Step 4: Stream chat events ------
        model_name = 'openclaw'
        prompt_tokens = 0
        completion_tokens = 0
        _prev_text = ''  # Track accumulated text to extract incremental deltas

        async for raw in ws:
            frame = json.loads(raw)

            # Skip non-event frames (e.g. tick responses)
            if frame.get('type') != 'event':
                continue

            event_name = frame.get('event', '')
            payload = frame.get('payload', {})

            # Filter to our run
            if payload.get('runId') and payload['runId'] != run_id:
                continue

            if event_name == 'chat':
                state = payload.get('state', '')
                msg_obj = payload.get('message')
                if state == 'final':
                    logger.info(f'[OpenClaw-Chat-Final] payload_keys={list(payload.keys())} msg_keys={list(msg_obj.keys()) if isinstance(msg_obj, dict) else "N/A"} full_payload={json.dumps(payload, ensure_ascii=False)[:500]}')

                # Extract text content from message object
                if msg_obj and isinstance(msg_obj, dict):
                    content = msg_obj.get('content')
                    if isinstance(content, list):
                        # content blocks: [{"type": "text", "text": "..."}, ...]
                        text = ''.join(
                            block.get('text', '')
                            for block in content
                            if isinstance(block, dict) and block.get('type') == 'text'
                        )
                    elif isinstance(content, str):
                        text = content
                    else:
                        text = msg_obj.get('text', '')
                    if text and state in ('delta', 'final'):
                        # OpenClaw delta events carry accumulated full text,
                        # not incremental deltas. Extract the new portion.
                        incremental = text[len(_prev_text):] if len(text) > len(_prev_text) else ''
                        _prev_text = text
                        if incremental:
                            q.put({'type': 'content', 'text': incremental})
                elif msg_obj and isinstance(msg_obj, str):
                    if msg_obj and state in ('delta', 'final'):
                        incremental = msg_obj[len(_prev_text):] if len(msg_obj) > len(_prev_text) else ''
                        _prev_text = msg_obj
                        if incremental:
                            q.put({'type': 'content', 'text': incremental})

                # Extract model/usage from final event
                if state == 'final':
                    # Model and usage info: try message object first, then payload top-level
                    if msg_obj and isinstance(msg_obj, dict):
                        model_name = msg_obj.get('model', model_name)
                        provider = msg_obj.get('provider', '')
                        if provider and '/' not in model_name:
                            model_name = f'{provider}/{model_name}'
                        msg_usage = msg_obj.get('usage', {})
                        if isinstance(msg_usage, dict):
                            prompt_tokens = msg_usage.get('inputTokens', msg_usage.get('input', msg_usage.get('input_tokens', 0)))
                            completion_tokens = msg_usage.get('outputTokens', msg_usage.get('output', msg_usage.get('output_tokens', 0)))
                    # Fallback: check payload top-level
                    if model_name == 'openclaw':
                        model_name = payload.get('model', 'openclaw')
                    if not prompt_tokens and not completion_tokens:
                        usage = payload.get('usage', {})
                        if isinstance(usage, dict):
                            prompt_tokens = usage.get('inputTokens', usage.get('input_tokens', usage.get('input', 0)))
                            completion_tokens = usage.get('outputTokens', usage.get('output_tokens', usage.get('output', 0)))
                            if usage.get('model'):
                                model_name = usage['model']
                                if usage.get('provider') and '/' not in model_name:
                                    model_name = f"{usage['provider']}/{model_name}"
                    break

                if state in ('aborted', 'error'):
                    error_msg = payload.get('errorMessage', '')
                    if error_msg:
                        q.put({'type': 'content', 'text': f'\n⚠️ {error_msg}'})
                    break

            elif event_name == 'agent':
                # Agent lifecycle/tool/thinking events — mapped from OpenClaw Gateway protocol
                stream_type = payload.get('stream', '')
                data = payload.get('data', {})
                logger.debug(f'[OpenClaw-Agent] stream={stream_type} data_keys={list(data.keys()) if isinstance(data, dict) else type(data).__name__}')

                if stream_type == 'thinking':
                    # Use delta (incremental), NOT text (accumulated full text)
                    delta = data.get('delta', '') if isinstance(data, dict) else ''
                    if delta:
                        q.put({'type': 'thinking', 'text': delta})

                elif stream_type == 'tool' and isinstance(data, dict):
                    phase = data.get('phase', '')

                    if phase == 'start' and data.get('name'):
                        # Tool start → natural language status
                        friendly = _tool_friendly_name(data['name'])
                        q.put({'type': 'agent_status', 'message': friendly})
                    elif phase == 'result':
                        if data.get('isError'):
                            result_text = data.get('result', '')
                            if isinstance(result_text, (dict, list)):
                                result_text = json.dumps(result_text, ensure_ascii=False)[:100]
                            else:
                                result_text = str(result_text)[:100] if result_text else ''
                            q.put({'type': 'agent_status', 'message': f'⚠️ 工具执行出错: {result_text}'})
                        else:
                            # Success → clear status (will be replaced by next event)
                            q.put({'type': 'agent_status', 'message': ''})
                    # phase='update' partialResult — not forwarded

                elif stream_type == 'lifecycle' and isinstance(data, dict):
                    phase = data.get('phase', '')
                    logger.debug(f'[OpenClaw-Lifecycle] phase={phase}')
                    if phase == 'start':
                        q.put({'type': 'agent_status', 'message': '正在思考...'})
                    elif phase == 'error':
                        error_msg = data.get('error', '')
                        if error_msg:
                            q.put({'type': 'agent_status', 'message': f'错误: {error_msg}'})
                    # phase='end' — handled by chat final event

                elif stream_type not in ('assistant', 'compaction', 'error', ''):
                    logger.debug(f'[OpenClaw-Agent] unhandled stream={stream_type}')

        # ------ Step 5: 获取 session token 数据 ------
        # 优先: chat final event 中的 usage
        # 补充: sessions.status RPC 获取 session 级别累计数据
        if model_name == 'openclaw' or not prompt_tokens:
            # 方法 1: sessions.status RPC (session 级累计 token)
            try:
                ss_id = _req_id()
                await ws.send(json.dumps({
                    'type': 'req',
                    'id': ss_id,
                    'method': 'sessions.status',
                    'params': {'sessionKey': session_key},
                }))
                ss_res = await asyncio.wait_for(_recv_response(ws, ss_id), timeout=5)
                if ss_res.get('ok'):
                    ss = ss_res.get('payload', {})
                    # contextTokens = 当前上下文大小 (用于耗尽检查)
                    ctx_tokens = ss.get('contextTokens', 0)
                    in_tokens = ss.get('inputTokens', 0)
                    out_tokens = ss.get('outputTokens', 0)
                    if not prompt_tokens and (ctx_tokens or in_tokens):
                        prompt_tokens = ctx_tokens or in_tokens
                    if not completion_tokens and out_tokens:
                        completion_tokens = out_tokens
                    # 提取 model（如果 session status 提供）
                    if model_name == 'openclaw':
                        m = ss.get('model') or ss.get('modelOverride', '')
                        if m:
                            model_name = m
                    logger.info(f'[OpenClaw-SessionStatus] ctx={ctx_tokens} in={in_tokens} out={out_tokens} model={ss.get("model")}')
                else:
                    logger.warning(f'[OpenClaw-SessionStatus] error: {ss_res.get("error", {})}')
            except Exception as e:
                logger.warning(f'[OpenClaw-SessionStatus] failed: {e}')

            # 方法 2: chat.history fallback (应对 sessions.status 不可用)
            if model_name == 'openclaw' or not prompt_tokens:
                try:
                    hist_rpc_id = _req_id()
                    await ws.send(json.dumps({
                        'type': 'req',
                        'id': hist_rpc_id,
                        'method': 'chat.history',
                        'params': {'sessionKey': session_key},
                    }))
                    hist_res = await asyncio.wait_for(_recv_response(ws, hist_rpc_id), timeout=5)
                    if hist_res.get('ok'):
                        hist_data = hist_res.get('payload', {})
                        # payload 可能是 {messages: [...]} 或直接是 [...]
                        messages = hist_data if isinstance(hist_data, list) else hist_data.get('messages', hist_data.get('history', []))
                        if isinstance(messages, list) and messages:
                            # 只取最后一个 assistant message 的 usage（不累加）
                            for msg in reversed(messages):
                                if not isinstance(msg, dict):
                                    continue
                                if msg.get('role') == 'assistant':
                                    if model_name == 'openclaw' and msg.get('model'):
                                        model_name = msg['model']
                                        provider = msg.get('provider', '')
                                        if provider and '/' not in model_name:
                                            model_name = f'{provider}/{model_name}'
                                    msg_usage = msg.get('usage', {})
                                    if isinstance(msg_usage, dict):
                                        hist_in = msg_usage.get('inputTokens', msg_usage.get('input', msg_usage.get('input_tokens', 0))) or 0
                                        hist_out = msg_usage.get('outputTokens', msg_usage.get('output', msg_usage.get('output_tokens', 0))) or 0
                                        if hist_in > prompt_tokens:
                                            prompt_tokens = hist_in
                                        if hist_out > completion_tokens:
                                            completion_tokens = hist_out
                                    break  # 只取最后一个 assistant
                    else:
                        error_info = hist_res.get('error', {})
                        logger.warning(f'[OpenClaw-ChatHistory] error: {json.dumps(error_info, ensure_ascii=False)[:200]}')
                except Exception as e:
                    logger.warning(f'[OpenClaw-ChatHistory] failed: {e}')

        final_model = f'openclaw/{model_name}' if '/' not in model_name else model_name
        logger.info(f'[OpenClaw-Done] final_model={final_model} tokens={prompt_tokens}/{completion_tokens}')
        q.put({
            'type': 'done',
            'model': final_model,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
        })


async def _recv_response(ws, req_id):
    """Read frames until we get the response matching req_id.

    Non-matching events are buffered/discarded (they'll be read in the
    main streaming loop later if needed).
    """
    while True:
        raw = await ws.recv()
        frame = json.loads(raw)
        if frame.get('type') == 'res' and frame.get('id') == req_id:
            return frame
        # Ignore events received during handshake (e.g. tick, presence)


def _req_id():
    return uuid.uuid4().hex[:12]
