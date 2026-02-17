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


# ── Main entry point ─────────────────────────────────────────────────

def _build_db_tool_prompt(user, conversation_id=None):
    """构建数据库查询工具和文件上传工具说明，注入到发送给 OpenClaw 的消息中"""
    try:
        from app.services.chat_db_query import get_db_schema, get_permission_context

        pma_base_url = os.environ.get('PMA_API_BASE_URL', '').rstrip('/')
        ai_token = os.environ.get('PMA_AI_QUERY_TOKEN', '')

        if not pma_base_url or not ai_token:
            logger.warning('PMA_API_BASE_URL 或 PMA_AI_QUERY_TOKEN 未配置，跳过工具注入')
            return ''

        db_schema = get_db_schema()
        permission_context = get_permission_context(user)
        user_id = user.id

        prompt = (
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

        return prompt
    except Exception as e:
        logger.warning(f'构建工具提示失败: {e}')
        return ''


def get_openclaw_response_stream(message, conversation_history=None, session_id=None,
                                 user=None, conversation_id=None):
    """获取 OpenClaw 流式响应的生成器

    通过 WebSocket 直连 OpenClaw Gateway，发送用户消息并流式接收响应。
    保持与 DeepSeek 兼容的 SSE 格式。

    Args:
        message: 用户消息文本
        conversation_history: 对话历史（OpenClaw 自行管理 session，此参数仅供参考）
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
        yield {'type': 'content', 'text': '⚠️ OpenClaw 未配置。请联系管理员设置 OPENCLAW_GATEWAY_URL。'}
        yield {'type': 'done', 'model': 'none', 'prompt_tokens': 0, 'completion_tokens': 0}
        return

    token = os.environ.get('OPENCLAW_GATEWAY_TOKEN', '')
    if not session_id:
        session_id = f'pma-{uuid.uuid4().hex[:8]}'

    # 注入 DB 查询工具和文件上传工具说明到消息前
    if user:
        db_prompt = _build_db_tool_prompt(user, conversation_id=conversation_id)
        if db_prompt:
            message = f'{db_prompt}\n[用户消息] {message}'

    # Use a thread + queue to bridge async websockets → sync generator
    result_queue = queue.Queue()

    def _run():
        try:
            asyncio.run(_ws_chat(gateway_url, token, message, session_id, result_queue))
        except Exception as e:
            logger.error(f'OpenClaw WebSocket 线程异常: {e}', exc_info=True)
            result_queue.put({'type': 'content', 'text': f'⚠️ OpenClaw 服务异常：{e}'})
            result_queue.put({'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0})
        finally:
            result_queue.put(None)  # sentinel

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    while True:
        try:
            item = result_queue.get(timeout=_CHAT_TIMEOUT)
        except queue.Empty:
            logger.error('OpenClaw WebSocket 响应超时')
            yield {'type': 'content', 'text': '⚠️ OpenClaw 响应超时，请稍后重试。'}
            yield {'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0}
            return
        if item is None:
            return
        yield item


async def _ws_chat(url, token, message, session_key, q):
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
            q.put({'type': 'content', 'text': f'⚠️ OpenClaw 连接失败：{msg}'})
            q.put({'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0})
            return

        # ------ Step 3: Send chat.send request ------
        chat_id = _req_id()
        chat_req = {
            'type': 'req',
            'id': chat_id,
            'method': 'chat.send',
            'params': {
                'sessionKey': session_key,
                'message': message,
                'idempotencyKey': uuid.uuid4().hex,
            },
        }
        await ws.send(json.dumps(chat_req))

        # Wait for immediate ack (non-blocking – returns runId)
        chat_ack = await asyncio.wait_for(_recv_response(ws, chat_id), timeout=15)
        if not chat_ack.get('ok'):
            error = chat_ack.get('error', {})
            msg = error.get('message', '发送失败') if isinstance(error, dict) else str(error)
            q.put({'type': 'content', 'text': f'⚠️ OpenClaw 发送消息失败：{msg}'})
            q.put({'type': 'done', 'model': 'openclaw', 'prompt_tokens': 0, 'completion_tokens': 0})
            return

        run_id = chat_ack.get('payload', {}).get('runId', '')

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

                # Extract usage from final event
                if state == 'final':
                    usage = payload.get('usage', {})
                    if isinstance(usage, dict):
                        prompt_tokens = usage.get('input_tokens', usage.get('input', 0))
                        completion_tokens = usage.get('output_tokens', usage.get('output', 0))
                    model_name = payload.get('model', 'openclaw')
                    break

                if state in ('aborted', 'error'):
                    error_msg = payload.get('errorMessage', '')
                    if error_msg:
                        q.put({'type': 'content', 'text': f'\n⚠️ {error_msg}'})
                    break

            elif event_name == 'agent':
                # Agent lifecycle/tool events — optionally surface tool calls
                stream_type = payload.get('stream', '')
                data = payload.get('data', {})
                if stream_type == 'tool' and data.get('name'):
                    q.put({
                        'type': 'tool_call',
                        'name': data['name'],
                        'explanation': data.get('description', ''),
                    })

        q.put({
            'type': 'done',
            'model': f'openclaw/{model_name}' if '/' not in model_name else model_name,
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
