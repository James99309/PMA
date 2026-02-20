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


# ── Keyword detection for DB prompt injection ───────────────────────

_DB_KEYWORDS = {
    '数据', '查询', '统计', '多少', '报销', '项目', '客户', '报价',
    '订单', '产品', '销售', '业绩', '金额', '合同', '人员', '任务',
    '部门', '公司', '联系人', '费用', '预算', '排名', '对比', '汇总',
    '分析', '趋势', '增长', '下降', '同比', '环比', '利润', '成本',
    '跟进', '新建', '创建', '添加', '修改', '记录',
    'data', 'query', 'report', 'sales', 'project', 'customer',
    'expense', 'quotation', 'product', 'order', 'task',
}


def _needs_db_prompt(message):
    """判断用户消息是否可能需要数据库查询"""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in _DB_KEYWORDS)


# ── Main entry point ─────────────────────────────────────────────────

def _build_db_tool_prompt(user, conversation_id=None):
    """构建数据库查询工具、文件上传工具和表单交互工具说明，注入到发送给 OpenClaw 的消息中"""
    try:
        from app.services.chat_db_query import get_db_schema, get_permission_context

        prompt = ''
        user_id = user.id

        pma_base_url = os.environ.get('PMA_API_BASE_URL', '').rstrip('/')
        ai_token = os.environ.get('PMA_AI_QUERY_TOKEN', '')

        # DB 查询工具和文件上传工具需要 PMA_API_BASE_URL + PMA_AI_QUERY_TOKEN
        if pma_base_url and ai_token:
            db_schema = get_db_schema()
            permission_context = get_permission_context(user)

            prompt += (
                '[系统提示] 你可以通过 HTTP 工具查询 PMA 数据库来回答数据相关问题。\n'
                f'API: POST {pma_base_url}/chat/api/ai/db-query\n'
                f'Header: Authorization: Bearer {ai_token}\n'
                f'Content-Type: application/json\n'
                f'Body: {{"sql": "SELECT ...", "user_id": {user_id}}}\n'
                f'\n'
                f'响应格式: {{"success": true, "columns": [...], "rows": [...], "row_count": N}}\n'
                f'如果 success=false，error 字段包含错误信息。\n'
                f'\n'
                f'{db_schema}\n'
                f'\n'
                f'{permission_context}\n'
                f'\n'
                f'重要：只允许 SELECT 查询，系统会自动按用户权限过滤数据。\n'
            )

            # 文件上传工具说明
            if conversation_id:
                prompt += (
                    f'\n[文件分享工具] 当你生成了文件（Excel、CSV、PDF、图片等）需要分享给用户下载时，'
                    f'请使用以下 API 上传文件到聊天对话中，用户即可在聊天界面直接点击下载。\n'
                    f'API: POST {pma_base_url}/chat/api/ai/upload-file\n'
                    f'Header: Authorization: Bearer {ai_token}\n'
                    f'Content-Type: multipart/form-data\n'
                    f'curl 示例:\n'
                    f'curl -X POST {pma_base_url}/chat/api/ai/upload-file \\\n'
                    f'  -H "Authorization: Bearer {ai_token}" \\\n'
                    f'  -F "file=@/path/to/generated_file.xlsx" \\\n'
                    f'  -F "conversation_id={conversation_id}" \\\n'
                    f'  -F "user_id={user_id}"\n'
                    f'\n'
                    f'上传成功后文件会自动出现在聊天对话中，请在回复中告知用户"文件已上传到对话中，可直接下载"。\n'
                    f'重要：请务必在生成文件后主动调用此 API 上传，不要告诉用户"无法提供下载链接"。\n'
                )
        else:
            logger.info('PMA_API_BASE_URL 或 PMA_AI_QUERY_TOKEN 未配置，跳过 DB 查询和文件上传工具注入')

        # 表单交互工具说明（不依赖 PMA_API_BASE_URL，始终注入）
        if conversation_id:
            prompt += (
                '\n\n=== [表单交互工具 - 最高优先级] ===\n'
                '当用户要求添加、新建、创建、修改客户、联系人、项目、报销单或跟进记录时，'
                '你必须在回复末尾插入表单标记。系统会自动将标记转换为交互式表单。\n'
                '\n'
                '【最重要 - 回复格式要求（违反任何一条都是严重错误）】\n'
                '- 回复正文只需简短的一句话（如"好的，请在表单中确认信息"），然后紧跟标记\n'
                '- 绝对禁止在回复中出现以下任何内容：\n'
                '  * 数据库表名（projects, companies, contacts 等）\n'
                '  * 字段名（is_deleted, id, company_name 等技术字段名）\n'
                '  * SQL语句或查询过程\n'
                '  * 数据库ID编号（如 "ID: 642"、"(id=528)" 等）\n'
                '  * 你的推理过程或思考步骤\n'
                '  * "根据规则"、"表单交互工具"、"标记" 等内部术语\n'
                '  * "查询结果显示"、"数据库中" 等技术表述\n'
                '- 用户看到的是一个智能助手，不是数据库管理员\n'
                '\n'
                '【重要行为准则】\n'
                '- 新建客户：用户说"添加/新建/创建客户XXX" → 立即附上 [[FORM:create_customer|{...}]]\n'
                '- 修改客户：查到客户后，立即附上 [[FORM:edit_customer|{...}]]\n'
                '- 添加联系人：查到公司后，立即附上 [[FORM:create_contact|{...}]]\n'
                '- 修改联系人：查到联系人后，立即附上 [[FORM:edit_contact|{...}]]\n'
                '- 新建项目：用户说"新建/创建项目" → 立即附上 [[FORM:create_project|{...}]]\n'
                '- 修改项目：查到项目后，立即附上 [[FORM:edit_project|{...}]]\n'
                '- 新建报销单：用户说"报销/记一笔费用" → 立即附上 [[FORM:create_expense|{...}]]\n'
                '- 快速跟进：查到客户和联系人后，立即附上 [[FORM:create_action|{...}]]\n'
                '\n'
                '【标记格式 - 严格遵守，标记必须在回复最末尾】\n'
                '- 新建客户: [[FORM:create_customer|{"company_name":"从对话提取","country":"如有","company_type":"如有","address":"如有"}]]\n'
                '- 修改客户: [[FORM:edit_customer|{"id":客户ID,"company_name":"如需修改","address":"如需修改"}]]\n'
                '- 新建联系人: [[FORM:create_contact|{"company_id":公司ID,"name":"姓名","phone":"如有","email":"如有"}]]\n'
                '- 修改联系人: [[FORM:edit_contact|{"id":联系人ID,"company_id":公司ID,"name":"如需修改","phone":"如需修改"}]]\n'
                '- 新建项目: [[FORM:create_project|{"project_name":"项目名","project_type":"channel_follow/sales_focus/business_opportunity","report_source":"channel/sales/marketing","industry":"如有"}]]\n'
                '- 修改项目: [[FORM:edit_project|{"id":项目ID,"project_name":"如需修改"}]]\n'
                '  (修改前必须先查数据库确认项目ID，但查询过程和结果不要展示给用户)\n'
                '- 新建报销单: [[FORM:create_expense|{"expense_category":"meals/entertainment/local_transport/travel_accommodation/office_supplies/communication/fuel/parking/other","description":"费用说明","invoice_amount":金额,"expense_date":"YYYY-MM-DD"}]]\n'
                '- 快速跟进: [[FORM:create_action|{"company_id":公司ID,"contact_id":联系人ID,"communication":"跟进内容"}]]\n'
                '  (必须先查数据库确认公司和联系人ID，但查询过程不要展示给用户)\n'
                '\n'
                '【规则】\n'
                '1. 只在用户明确要求新增/修改/添加数据时触发，纯查询搜索不触发\n'
                '2. prefill JSON 中只填对话中已知的信息，未知字段留空或不填\n'
                '3. 不要提及标记本身，用户看不到标记，只会看到表单\n'
                '4. 标记必须是回复的最后一行\n'
                '\n'
                '【内部查询SQL（仅供你内部使用，绝不展示给用户）】\n'
                '查客户: SELECT id, company_name FROM companies WHERE company_name ILIKE \'%关键词%\' AND is_deleted = false\n'
                '查联系人: SELECT c.id, c.name, c.company_id, co.company_name FROM contacts c JOIN companies co ON c.company_id = co.id WHERE c.name ILIKE \'%关键词%\'\n'
                '查项目: SELECT id, project_name FROM projects WHERE project_name ILIKE \'%关键词%\' AND is_deleted = false\n'
                '\n'
                '【查询结果处理规则】\n'
                '精确匹配1个 → 直接附上表单标记，简短告知用户（如"找到了XXX项目，请确认修改"）\n'
                '匹配多个 → 简短说明，然后在回复末尾附上选项标记 [[CHOICES:选项1|选项2|...]]，系统会自动渲染为可点击按钮\n'
                '匹配0个 → 自然语言告知"没有找到包含XXX的项目"\n'
                '绝对不要猜测ID，绝对不要在回复中显示ID编号\n'
                '\n'
                '【选项标记格式 - 匹配多个时使用】\n'
                '当查询到多个结果需要用户选择时，在回复末尾附上带ID的选项标记：\n'
                '[[CHOICES:表单动作|名称1:ID1|名称2:ID2|名称3:ID3]]\n'
                '第一个参数是表单动作（edit_project/edit_customer/edit_contact等），后面是"名称:数据库ID"对\n'
                '选项文本只放实体名称（客户名/项目名/联系人名），不要带"修改""新建"等动作词\n'
                '动作上下文放在回复正文中（如"找到多个相关项目，请选择要修改的："）\n'
                '标记会被系统自动转换为可点击按钮，用户点击后直接打开表单，无需再次等待\n'
                '\n'
                '【正确回复示例】\n'
                '用户: "帮我添加客户 ABC Corp" → "好的，请在表单中完善信息。\\n\\n[[FORM:create_customer|{...}]]"\n'
                '用户: "修改赵东来的电话" → 查到1个 → "找到了赵东来，请确认修改。\\n\\n[[FORM:edit_contact|{\\"id\\":695,\\"company_id\\":528}]]"\n'
                '用户: "修改上海建筑的地址" → 查到1个 → "找到了上海建筑工程公司，请确认修改。\\n\\n[[FORM:edit_customer|{\\"id\\":528}]]"\n'
                '用户: "我要修改武汉中心项目" → 查到2个(id=642和id=701) → "找到多个相关项目，请选择要修改的：\\n\\n[[CHOICES:edit_project|武汉中心辅助楼:642|武汉中心主楼:701]]"\n'
                '\n'
                '【错误回复示例 - 绝对禁止】\n'
                '❌ "查询projects表，发现is_deleted字段..."\n'
                '❌ "找到以下项目：武汉中心辅助楼 (ID: 642)"\n'
                '❌ "根据数据库查询结果，共有2条记录..."\n'
                '❌ "我需要先查询数据库确认项目信息..."\n'
            )

        return prompt
    except Exception as e:
        logger.warning(f'构建工具提示失败: {e}')
        return ''


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

    # 仅当消息可能涉及数据查询时，才注入 DB 工具说明（减少非数据问题的思考延迟）
    if user and _needs_db_prompt(message):
        db_prompt = _build_db_tool_prompt(user, conversation_id=conversation_id)
        if db_prompt:
            _perf_db_injected = True
            _perf_prompt_len = len(db_prompt)
            message = f'{user_identity}\n{db_prompt}\n[用户消息] {message}'
            logger.info(f'[OpenClaw-Perf] DB提示已注入, prompt_chars={_perf_prompt_len}, msg="{_perf_msg_preview}"')
    elif user_identity:
        message = f'{user_identity}\n[用户消息] {message}'
        logger.info(f'[OpenClaw-Perf] 用户标识已注入(无DB提示), msg="{_perf_msg_preview}"')

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
        scopes = ['operator.read', 'operator.write']

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
                    # Model and usage info is inside message object, not payload top-level
                    if msg_obj and isinstance(msg_obj, dict):
                        model_name = msg_obj.get('model', model_name)
                        provider = msg_obj.get('provider', '')
                        if provider and '/' not in model_name:
                            model_name = f'{provider}/{model_name}'
                        msg_usage = msg_obj.get('usage', {})
                        if isinstance(msg_usage, dict):
                            prompt_tokens = msg_usage.get('input', msg_usage.get('input_tokens', 0))
                            completion_tokens = msg_usage.get('output', msg_usage.get('output_tokens', 0))
                    # Fallback: check payload top-level for backward compatibility
                    if model_name == 'openclaw':
                        model_name = payload.get('model', 'openclaw')
                    if not prompt_tokens and not completion_tokens:
                        usage = payload.get('usage', {})
                        if isinstance(usage, dict):
                            prompt_tokens = usage.get('input_tokens', usage.get('input', 0))
                            completion_tokens = usage.get('output_tokens', usage.get('output', 0))
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
                if stream_type not in ('assistant',):
                    logger.info(f'[OpenClaw-Agent] stream={stream_type} payload_keys={list(payload.keys())} data_keys={list(data.keys()) if isinstance(data, dict) else type(data).__name__}')

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
                    logger.info(f'[OpenClaw-Lifecycle] phase={phase} data_keys={list(data.keys())} full={json.dumps(data, ensure_ascii=False)[:500]}')
                    if phase == 'start':
                        q.put({'type': 'agent_status', 'message': '正在思考...'})
                    elif phase == 'error':
                        error_msg = data.get('error', '')
                        if error_msg:
                            q.put({'type': 'agent_status', 'message': f'错误: {error_msg}'})
                    # phase='end' — handled by chat final event

                elif stream_type not in ('assistant', 'compaction', 'error', ''):
                    logger.info(f'[OpenClaw-Agent] unhandled stream={stream_type} data={json.dumps(data, ensure_ascii=False)[:300] if isinstance(data, dict) else str(data)[:300]}')

        final_model = f'openclaw/{model_name}' if '/' not in model_name else model_name
        logger.info(f'[OpenClaw-Done] model_name={model_name} final_model={final_model} tokens={prompt_tokens}/{completion_tokens}')
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
