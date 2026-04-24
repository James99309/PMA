# Cross-NAS Bidirectional Chat Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 SG NAS ↔ CN NAS 双向私聊和群聊同步，CN 用户可在本地直接回复，SG 用户在原对话中收到回复。

**Architecture:** 在现有单向推送（SG→CN）基础上扩展双向通道。私聊回复通过 `reply_mode` 标识路由到原私聊对话；群聊首条消息触发 CN 镜像群创建，双向通过 `push-group` API 同步。所有跨系统用户身份通过邮箱匹配，SG 用户在 CN 显示为 `name [SG]`。

**Tech Stack:** Flask, SQLAlchemy, PostgreSQL, Alpine.js, httpx, Flask-Migrate (Alembic)

---

## 背景与约束

- CN NAS 运行于 `100.118.231.15:5002`，SG NAS 运行于 `100.87.155.40:5002`
- 两边共享同一套代码，通过 Docker 镜像部署
- 跨系统认证使用 `X-API-Key`（两边已配置相同 key）
- CN NAS 目前未启用 `CROSS_SYNC_ENABLED`
- 所有推送异步执行（后台线程），不阻塞主流程
- `User.is_active` 是 `@property`，查询必须用 `User._is_active == True`

---

## Task 1: DB Migration — 添加 sync_metadata 列

**Files:**
- Create: `migrations/versions/add_sync_metadata_to_chat_conversations.py`（由 flask db migrate 自动生成）
- Modify: `app/models/chat.py`

**Step 1: 在 model 加列**

在 `app/models/chat.py` 的 `ChatConversation` 类中，`is_deleted` 列之后加：

```python
sync_metadata = Column(Text, nullable=True)  # JSON: {"peer_sender_email": "..."} 或 {"peer_group_id": 7}
```

**Step 2: 生成 migration**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db migrate -m "add sync_metadata to chat_conversations"
```

预期：在 `migrations/versions/` 生成新文件，内容包含 `op.add_column('chat_conversations', sa.Column('sync_metadata', sa.Text(), nullable=True))`

**Step 3: 应用 migration（本地验证）**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

预期：`Running upgrade ... -> xxxx, add sync_metadata to chat_conversations`

**Step 4: Commit**

```bash
git add app/models/chat.py migrations/versions/
git commit -m "feat(chat): add sync_metadata column to ChatConversation for cross-NAS routing"
```

---

## Task 2: 私聊推送携带 sender_email

**Files:**
- Modify: `app/services/cross_sync_service.py:158-200`（`push_message_to_peer`）
- Modify: `app/services/chat_service.py:607-624`（触发推送处）

**Step 1: 更新 push_message_to_peer 签名和 payload**

在 `cross_sync_service.py` 的 `push_message_to_peer` 函数，加 `sender_email=None` 参数，payload 中加入该字段：

```python
def push_message_to_peer(recipient_email, sender_name, content, msg_type='chat', sender_email=None):
    # ... 现有检查不变 ...
    def _do_push():
        try:
            resp = httpx.post(
                f'{peer_url}/cross-sync/push',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                json={
                    'recipient_email': recipient_email,
                    'sender_name': sender_name,
                    'content': content,
                    'msg_type': msg_type,
                    'source_label': source_label,
                    'sender_email': sender_email or '',   # 新增
                },
                timeout=10.0,
            )
            # ... 现有日志不变 ...
```

**Step 2: chat_service.py 传入 sender_email**

在 `chat_service.py` 第 622 行的 `push_message_to_peer` 调用处，加上 `sender_email`：

```python
push_message_to_peer(
    other_user.email,
    sender_display,
    content.strip(),
    sender_email=sender_user.email if sender_user else None,   # 新增
)
```

**Step 3: 验证**

发一条 SG 私聊消息，检查 SG 日志确认推送成功，检查 CN 日志无报错。

**Step 4: Commit**

```bash
git add app/services/cross_sync_service.py app/services/chat_service.py
git commit -m "feat(cross-sync): include sender_email in private chat push payload"
```

---

## Task 3: CN 接收时存储 sender_email 到 sync_metadata

**Files:**
- Modify: `app/services/cross_sync_service.py:89-155`（`receive_message_from_peer`）

**Step 1: 在 receive_message_from_peer 存 sender_email**

在创建/获取 `conv` 后，加入：

```python
import json as _json

# 存储 sender_email 到 sync_metadata（仅首次写入，不覆盖）
sender_email = data.get('sender_email', '').strip()
if sender_email:
    metadata = _json.loads(conv.sync_metadata or '{}')
    if 'peer_sender_email' not in metadata:
        metadata['peer_sender_email'] = sender_email
        conv.sync_metadata = _json.dumps(metadata, ensure_ascii=False)
```

**Step 2: 验证**

发一条 SG 私聊，在 CN 数据库确认：

```bash
ssh -p 72 james.sh@100.118.231.15 'sudo /usr/local/bin/docker exec pma-postgres psql -U pma pma_synology -c "SELECT id, name, sync_metadata FROM chat_conversations WHERE type='"'"'cross_system'"'"' ORDER BY id DESC LIMIT 3;"'
```

预期：`sync_metadata` 列显示 `{"peer_sender_email": "james@evertac.net"}`

**Step 3: Commit**

```bash
git add app/services/cross_sync_service.py
git commit -m "feat(cross-sync): store peer_sender_email in sync_metadata on receive"
```

---

## Task 4: SG 接收 CN 回复注入原私聊对话

**Files:**
- Modify: `app/services/cross_sync_service.py`（新增 `receive_private_reply_from_peer`）
- Modify: `app/api/v1/cross_sync.py:18-35`（`/push` 端点路由）

**Step 1: 新增 receive_private_reply_from_peer 函数**

在 `cross_sync_service.py` 的 `receive_message_from_peer` 函数之后添加：

```python
def receive_private_reply_from_peer(data):
    """
    接收 CN 的私聊回复，注入到 SG 原有私聊对话。
    sender_email: CN 回复者的邮箱（在 SG 上查找对应用户）
    recipient_email: SG 原发送者的邮箱
    """
    import json as _json

    sender_email = data.get('sender_email', '').strip().lower()
    recipient_email = data.get('recipient_email', '').strip().lower()
    content = data.get('content', '')

    if not sender_email or not recipient_email or not content:
        return {'success': False, 'message': '缺少必要字段: sender_email, recipient_email, content'}

    # 找 SG 本地用户（sender = CN 回复者，recipient = SG 原发送者）
    sender = User.query.filter(
        db.func.lower(User.email) == sender_email,
        User._is_active == True,
    ).first()
    recipient = User.query.filter(
        db.func.lower(User.email) == recipient_email,
        User._is_active == True,
    ).first()

    if not sender or not recipient:
        logger.warning(f"私聊回复注入失败: sender={sender_email}({bool(sender)}), recipient={recipient_email}({bool(recipient)})")
        return {'success': False, 'message': '用户未找到'}

    # 找两人之间的私聊对话
    sender_conv_ids = db.session.query(ChatParticipant.conversation_id).filter(
        ChatParticipant.user_id == sender.id
    ).subquery()
    recipient_conv_ids = db.session.query(ChatParticipant.conversation_id).filter(
        ChatParticipant.user_id == recipient.id
    ).subquery()

    conv = ChatConversation.query.filter(
        ChatConversation.type == 'private',
        ChatConversation.is_deleted == False,
        ChatConversation.id.in_(sender_conv_ids),
        ChatConversation.id.in_(recipient_conv_ids),
    ).first()

    if not conv:
        logger.warning(f"未找到私聊对话: {sender_email} <-> {recipient_email}")
        return {'success': False, 'message': '私聊对话未找到'}

    try:
        message = ChatMessage(
            conversation_id=conv.id,
            sender_id=sender.id,
            content=content,
            message_type='text',
            source_language='zh',
        )
        db.session.add(message)
        conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"私聊回复注入成功: conv_id={conv.id}, sender={sender_email}")
        return {'success': True, 'message': '回复注入成功'}
    except Exception as e:
        db.session.rollback()
        logger.error(f"私聊回复注入失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}
```

**Step 2: 更新 /push 端点路由**

在 `cross_sync.py` 的 `cross_sync_push` 函数中，根据 `reply_mode` 分流：

```python
@api_v1_bp.route('/cross-sync/push', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_push():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    if data.get('reply_mode'):
        from app.services.cross_sync_service import receive_private_reply_from_peer
        result = receive_private_reply_from_peer(data)
    else:
        required_fields = ['recipient_email', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必要字段: {field}'}), 400
        from app.services.cross_sync_service import receive_message_from_peer
        result = receive_message_from_peer(data)

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code
```

**Step 3: Commit**

```bash
git add app/services/cross_sync_service.py app/api/v1/cross_sync.py
git commit -m "feat(cross-sync): add receive_private_reply_from_peer and route reply_mode in /push"
```

---

## Task 5: CN send_message 触发私聊回复推送

**Files:**
- Modify: `app/services/chat_service.py`（`send_message` 函数，cross_system 处理块）

**Step 1: 在 send_message 加 cross_system 回推逻辑**

在 `chat_service.py` 现有 `# 跨系统推送（仅私聊，异步不阻塞）` 块（约第607行）之后，加新块：

```python
        # 跨系统回复推送（cross_system 对话 → 推回 SG）
        if conv and conv.type == 'cross_system':
            try:
                import json as _json
                from app.services.cross_sync_service import is_cross_sync_enabled, push_message_to_peer
                if is_cross_sync_enabled():
                    metadata = _json.loads(conv.sync_metadata or '{}')
                    peer_sender_email = metadata.get('peer_sender_email')
                    if peer_sender_email:
                        sender_user = User.query.get(sender_id)
                        sender_display = (sender_user.real_name or sender_user.username) if sender_user else ''
                        push_message_to_peer(
                            recipient_email=peer_sender_email,
                            sender_name=sender_display,
                            content=content.strip(),
                            msg_type='reply',
                            sender_email=sender_user.email if sender_user else None,
                            reply_mode=True,
                        )
            except Exception as ce:
                logger.warning(f"跨系统私聊回复推送失败: {ce}")
```

**Step 2: push_message_to_peer 加 reply_mode 参数**

更新 `push_message_to_peer` 签名加 `reply_mode=False`，payload 中加入：

```python
def push_message_to_peer(recipient_email, sender_name, content, msg_type='chat', sender_email=None, reply_mode=False):
    # ...
    json={
        'recipient_email': recipient_email,
        'sender_name': sender_name,
        'content': content,
        'msg_type': msg_type,
        'source_label': source_label,
        'sender_email': sender_email or '',
        'reply_mode': reply_mode,          # 新增
    },
```

**Step 3: Commit**

```bash
git add app/services/chat_service.py app/services/cross_sync_service.py
git commit -m "feat(cross-sync): trigger private reply push from cross_system conversation"
```

---

## Task 6: UI — cross_system 对话显示输入框

**Files:**
- Modify: `app/templates/components/tw_chat_panel.html`

**Step 1: 找到只读限制区块（约第1258行）**

当前结构：
```html
<!-- 跨系统只读提示条 -->
<template x-if="activeConv && activeConv.type === 'cross_system'">
  <div>...只读，无法回复... + 打开 SG PMA 按钮</div>
</template>

<!-- 输入区 -->
<template x-if="!contextExhausted && !(activeConv && activeConv.type === 'cross_system')">
  <!-- 输入框 -->
</template>
```

**Step 2: 改为信息提示条（保留 + 输入框并存）**

将只读提示条移到输入框上方，去掉"无法回复"文字，改为信息标识；输入区的排除条件去掉 `cross_system`：

```html
<!-- 跨系统来源提示条（私聊 cross_system：显示来源标签 + 打开 SG PMA 按钮） -->
<template x-if="activeConv && activeConv.type === 'cross_system'">
<div class="px-4 pt-2">
    <div class="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700/50 rounded-xl px-3 py-2 flex items-center justify-between gap-2 text-xs">
        <span class="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
            <span class="material-symbols-outlined text-sm">language</span>
            {{ _('来自 SG PMA 的消息，可直接回复') }}
        </span>
        <a href="https://sg-pma.jamesgpone.win" target="_blank" rel="noopener"
           class="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors flex-shrink-0">
            <span class="material-symbols-outlined text-xs">open_in_new</span>
            {{ _('打开 SG PMA') }}
        </a>
    </div>
</div>
</template>

<!-- 输入区：只排除 ai 和 cross_system_group（只读）以外的情况 -->
<template x-if="!contextExhausted && activeConv && activeConv.type !== 'ai'">
  <!-- 保持现有输入框代码不变 -->
</template>
```

注意：`cross_system_group` 镜像群也应显示输入框，所以输入区的条件只排除 `ai` 类型（含 context exhausted 逻辑保持不变）。

**Step 3: cross_system_group 提示条**

```html
<template x-if="activeConv && activeConv.type === 'cross_system_group'">
<div class="px-4 pt-2">
    <div class="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700/50 rounded-xl px-3 py-2 flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
        <span class="material-symbols-outlined text-sm">language</span>
        {{ _('此群已与 SG PMA 同步，回复将发送至 SG') }}
    </div>
</div>
</template>
```

**Step 4: Commit**

```bash
git add app/templates/components/tw_chat_panel.html
git commit -m "feat(chat-ui): enable reply in cross_system conversations, add cross_system_group info bar"
```

---

## Task 7: 群聊 — SG send_message 推送到 CN

**Files:**
- Modify: `app/services/cross_sync_service.py`（新增 `push_group_to_peer`）
- Modify: `app/services/chat_service.py`（`send_message` 加 group 推送块）

**Step 1: 新增 push_group_to_peer**

```python
def push_group_to_peer(sg_group_id, group_name, sender_name, sender_email, content, recipient_emails):
    """异步推送群消息到 CN（SG→CN 方向）"""
    if not is_cross_sync_enabled():
        return
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    if not peer_url:
        return

    def _do_push():
        try:
            resp = httpx.post(
                f'{peer_url}/cross-sync/push-group',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                json={
                    'sg_group_id': sg_group_id,
                    'group_name': group_name,
                    'sender_name': sender_name,
                    'sender_email': sender_email,
                    'content': content,
                    'recipient_emails': recipient_emails,
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                logger.info(f"群聊跨系统推送成功: sg_group_id={sg_group_id}")
            else:
                logger.warning(f"群聊跨系统推送失败: status={resp.status_code}, body={resp.text[:200]}")
        except Exception as e:
            logger.warning(f"群聊跨系统推送异常: {e}")

    import threading
    threading.Thread(target=_do_push, daemon=True).start()
```

**Step 2: chat_service.send_message 加 group 推送块**

在现有私聊推送块之后添加：

```python
        # 群聊跨系统推送（SG group → CN mirror group）
        if conv and conv.type == 'group':
            try:
                from app.services.cross_sync_service import is_cross_sync_enabled, push_group_to_peer
                if is_cross_sync_enabled():
                    sender_user = User.query.get(sender_id)
                    sender_display = (sender_user.real_name or sender_user.username) if sender_user else ''
                    # 收集所有其他参与者邮箱
                    other_parts = ChatParticipant.query.filter(
                        ChatParticipant.conversation_id == conversation_id,
                        ChatParticipant.user_id != sender_id,
                    ).all()
                    recipient_emails = []
                    for p in other_parts:
                        u = User.query.get(p.user_id)
                        if u and u.email:
                            recipient_emails.append(u.email)
                    if recipient_emails:
                        push_group_to_peer(
                            sg_group_id=conversation_id,
                            group_name=conv.name or '群聊',
                            sender_name=f'{sender_display} [SG]',
                            sender_email=sender_user.email if sender_user else '',
                            content=content.strip(),
                            recipient_emails=recipient_emails,
                        )
            except Exception as ce:
                logger.warning(f"群聊跨系统推送失败: {ce}")
```

**Step 3: Commit**

```bash
git add app/services/cross_sync_service.py app/services/chat_service.py
git commit -m "feat(cross-sync): push group messages to CN on SG send"
```

---

## Task 8: 群聊 — CN 接收消息并创建镜像群

**Files:**
- Modify: `app/services/cross_sync_service.py`（新增 `receive_group_message_from_peer`）
- Modify: `app/api/v1/cross_sync.py`（新增 `/push-group` 端点）

**Step 1: 新增 receive_group_message_from_peer**

```python
def receive_group_message_from_peer(data):
    """
    接收 SG 群消息，在 CN 创建/更新镜像群并写入消息。
    首次接收时自动按 recipient_emails 创建 cross_system_group 对话。
    """
    import json as _json

    sg_group_id = data.get('sg_group_id')
    group_name = data.get('group_name', '群聊')
    sender_name = data.get('sender_name', '未知 [SG]')
    sender_email = data.get('sender_email', '')
    content = data.get('content', '')
    recipient_emails = [e.lower() for e in data.get('recipient_emails', [])]

    if not sg_group_id or not content or not recipient_emails:
        return {'success': False, 'message': '缺少必要字段: sg_group_id, content, recipient_emails'}

    # 找 CN 本地匹配用户
    local_users = User.query.filter(
        db.func.lower(User.email).in_(recipient_emails),
        User._is_active == True,
    ).all()

    if not local_users:
        return {'success': False, 'message': f'CN 无对应用户: {recipient_emails}'}

    try:
        # 查找现有镜像群（遍历 cross_system_group 找 peer_group_id 匹配）
        mirror_conv = None
        candidates = ChatConversation.query.filter(
            ChatConversation.type == 'cross_system_group',
            ChatConversation.is_deleted == False,
            ChatConversation.sync_metadata.isnot(None),
        ).all()
        for c in candidates:
            meta = _json.loads(c.sync_metadata or '{}')
            if meta.get('peer_group_id') == sg_group_id:
                mirror_conv = c
                break

        # 首次：创建镜像群
        if not mirror_conv:
            mirror_conv = ChatConversation(
                type='cross_system_group',
                name=f'{group_name} · SG PMA',
                created_by=local_users[0].id,
                sync_metadata=_json.dumps({
                    'peer_group_id': sg_group_id,
                }, ensure_ascii=False),
            )
            db.session.add(mirror_conv)
            db.session.flush()

            for user in local_users:
                db.session.add(ChatParticipant(
                    conversation_id=mirror_conv.id,
                    user_id=user.id,
                    role='member',
                    last_read_at=datetime.now(timezone.utc),
                ))
            db.session.flush()
            logger.info(f"创建镜像群: conv_id={mirror_conv.id}, sg_group_id={sg_group_id}, members={[u.email for u in local_users]}")

        # 写入消息（JSON 格式，sender_id=NULL）
        msg_content = _json.dumps({
            'sender_name': sender_name,
            'text': content,
            'msg_type': 'chat',
        }, ensure_ascii=False)

        message = ChatMessage(
            conversation_id=mirror_conv.id,
            sender_id=None,
            content=msg_content,
            message_type='cross_system',
            source_language='zh',
        )
        db.session.add(message)
        mirror_conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"群聊消息写入成功: conv_id={mirror_conv.id}, sender={sender_name}")
        return {'success': True}

    except Exception as e:
        db.session.rollback()
        logger.error(f"接收群聊消息失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}
```

**Step 2: 新增 /push-group 端点**

在 `cross_sync.py` 末尾添加：

```python
@api_v1_bp.route('/cross-sync/push-group', methods=['POST'])
@require_api_key_or_jwt
def cross_sync_push_group():
    """接收跨系统群聊消息或群聊回复"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'}), 400

    if data.get('reply_mode'):
        from app.services.cross_sync_service import receive_group_reply_from_peer
        result = receive_group_reply_from_peer(data)
    else:
        from app.services.cross_sync_service import receive_group_message_from_peer
        result = receive_group_message_from_peer(data)

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code
```

**Step 3: Commit**

```bash
git add app/services/cross_sync_service.py app/api/v1/cross_sync.py
git commit -m "feat(cross-sync): receive group messages, auto-create CN mirror group on first message"
```

---

## Task 9: 群聊 — CN 回复推回 SG

**Files:**
- Modify: `app/services/cross_sync_service.py`（新增 `push_group_reply_to_peer`、`receive_group_reply_from_peer`）
- Modify: `app/services/chat_service.py`（`send_message` 加 cross_system_group 回推块）

**Step 1: 新增 push_group_reply_to_peer**

```python
def push_group_reply_to_peer(sg_group_id, sender_email, sender_name, content):
    """异步推送 CN 镜像群回复到 SG 原群"""
    if not is_cross_sync_enabled():
        return
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    if not peer_url:
        return

    def _do_push():
        try:
            resp = httpx.post(
                f'{peer_url}/cross-sync/push-group',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                json={
                    'sg_group_id': sg_group_id,
                    'sender_email': sender_email,
                    'sender_name': sender_name,
                    'content': content,
                    'reply_mode': True,
                },
                timeout=10.0,
            )
            if resp.status_code != 200:
                logger.warning(f"群聊回复推送失败: status={resp.status_code}, body={resp.text[:200]}")
        except Exception as e:
            logger.warning(f"群聊回复推送异常: {e}")

    import threading
    threading.Thread(target=_do_push, daemon=True).start()
```

**Step 2: 新增 receive_group_reply_from_peer（SG 侧）**

```python
def receive_group_reply_from_peer(data):
    """接收 CN 镜像群回复，注入到 SG 原群对话"""
    sg_group_id = data.get('sg_group_id')
    sender_email = data.get('sender_email', '').strip().lower()
    sender_name = data.get('sender_name', '未知用户')
    content = data.get('content', '')

    if not sg_group_id or not sender_email or not content:
        return {'success': False, 'message': '缺少必要字段'}

    conv = ChatConversation.query.get(sg_group_id)
    if not conv or conv.type != 'group' or conv.is_deleted:
        return {'success': False, 'message': f'群对话未找到: {sg_group_id}'}

    # 按邮箱找 SG 本地用户
    sender = User.query.filter(
        db.func.lower(User.email) == sender_email,
        User._is_active == True,
    ).first()

    try:
        import json as _json
        if sender:
            # 以真实用户身份注入
            message = ChatMessage(
                conversation_id=conv.id,
                sender_id=sender.id,
                content=content,
                message_type='text',
                source_language='zh',
            )
        else:
            # 用户在 SG 不存在，用 cross_system 格式标注
            message = ChatMessage(
                conversation_id=conv.id,
                sender_id=None,
                content=_json.dumps({'sender_name': f'{sender_name} [CN]', 'text': content}, ensure_ascii=False),
                message_type='cross_system',
                source_language='zh',
            )
        db.session.add(message)
        conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"群聊回复注入成功: conv_id={sg_group_id}, sender={sender_email}")
        return {'success': True}
    except Exception as e:
        db.session.rollback()
        logger.error(f"群聊回复注入失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}
```

**Step 3: chat_service.send_message 加 cross_system_group 回推**

```python
        # 群聊镜像回复推送（cross_system_group → 推回 SG 原群）
        if conv and conv.type == 'cross_system_group':
            try:
                import json as _json
                from app.services.cross_sync_service import is_cross_sync_enabled, push_group_reply_to_peer
                if is_cross_sync_enabled():
                    metadata = _json.loads(conv.sync_metadata or '{}')
                    peer_group_id = metadata.get('peer_group_id')
                    if peer_group_id:
                        sender_user = User.query.get(sender_id)
                        sender_display = (sender_user.real_name or sender_user.username) if sender_user else ''
                        push_group_reply_to_peer(
                            sg_group_id=peer_group_id,
                            sender_email=sender_user.email if sender_user else '',
                            sender_name=sender_display,
                            content=content.strip(),
                        )
            except Exception as ce:
                logger.warning(f"群聊镜像回复推送失败: {ce}")
```

**Step 4: Commit**

```bash
git add app/services/cross_sync_service.py app/services/chat_service.py
git commit -m "feat(cross-sync): CN mirror group replies push back to SG original group"
```

---

## Task 10: UI — cross_system_group 消息气泡显示 [SG] 标识

**Files:**
- Modify: `app/templates/components/tw_chat_panel.html`

**Step 1: 找到 cross_system 消息渲染模板（约第558行）**

现有 cross_system 消息已有 JSON 解析逻辑，在 `_parseCrossSystemPreview` 和消息气泡区域。

**Step 2: 确认 cross_system 气泡的 sender 显示**

cross_system 消息 `sender_id=null`，气泡头部应显示从 JSON content 中解析的 `sender_name`（如 `james.ni [SG]`）。确认现有模板已用 `msg.parsed_sender_name` 或类似字段显示。若没有，在 Alpine.js 的消息格式化函数中加解析：

```javascript
// 在 _formatMessage 或消息加载函数中
if (msg.message_type === 'cross_system') {
    try {
        const parsed = JSON.parse(msg.content);
        msg.cross_sender_name = parsed.sender_name || '';
        msg.cross_text = parsed.text || msg.content;
    } catch {
        msg.cross_sender_name = '';
        msg.cross_text = msg.content;
    }
}
```

**Step 3: 在消息列表渲染加地球图标**

在 cross_system 气泡左侧 sender 名称旁加小图标区分 SG 来源：

```html
<template x-if="msg.message_type === 'cross_system'">
  <div class="flex items-center gap-1 text-xs text-slate-500 mb-1">
      <span class="material-symbols-outlined text-emerald-500" style="font-size:14px">language</span>
      <span x-text="msg.cross_sender_name"></span>
  </div>
  <div class="rounded-2xl px-4 py-2.5 text-sm bg-emerald-50 dark:bg-emerald-900/20 text-slate-800 dark:text-slate-200">
      <p class="whitespace-pre-wrap" x-text="msg.cross_text"></p>
  </div>
</template>
```

**Step 4: Commit**

```bash
git add app/templates/components/tw_chat_panel.html
git commit -m "feat(chat-ui): show [SG] sender name and globe icon for cross_system messages in group"
```

---

## Task 11: 部署

**Step 1: 在本地应用 migration**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

**Step 2: 先部署 CN NAS（接收方先就绪）**

```bash
# 上传代码
cat app/models/chat.py | ssh -p 72 james.sh@100.118.231.15 'sudo tee /volume1/docker/pma/app/models/chat.py > /dev/null'
cat app/services/cross_sync_service.py | ssh -p 72 james.sh@100.118.231.15 'sudo tee /volume1/docker/pma/app/services/cross_sync_service.py > /dev/null'
cat app/services/chat_service.py | ssh -p 72 james.sh@100.118.231.15 'sudo tee /volume1/docker/pma/app/services/chat_service.py > /dev/null'
cat app/api/v1/cross_sync.py | ssh -p 72 james.sh@100.118.231.15 'sudo tee /volume1/docker/pma/app/api/v1/cross_sync.py > /dev/null'
cat app/templates/components/tw_chat_panel.html | ssh -p 72 james.sh@100.118.231.15 'sudo tee /volume1/docker/pma/app/templates/components/tw_chat_panel.html > /dev/null'
# 上传 migration 文件（找到新生成的版本文件名）
```

```bash
# CN NAS 应用 migration
ssh -p 72 james.sh@100.118.231.15 'cd /volume1/docker/pma/deploy/synology-cn && sudo /usr/local/bin/docker compose exec pma flask db upgrade 2>&1'
```

```bash
# CN NAS 加 .env 配置
ssh -p 72 james.sh@100.118.231.15 'sudo sh -c "echo \"CROSS_SYNC_ENABLED=true\" >> /volume1/docker/pma/deploy/synology-cn/.env && echo \"CROSS_SYNC_PEER_URL=http://100.87.155.40:5002/api/v1\" >> /volume1/docker/pma/deploy/synology-cn/.env"'
```

```bash
# CN NAS 重建并重启
ssh -p 72 james.sh@100.118.231.15 'cd /volume1/docker/pma/deploy/synology-cn && sudo /usr/local/bin/docker compose build pma 2>&1 | tail -3 && sudo /usr/local/bin/docker compose up -d pma 2>&1'
```

**Step 3: 部署 SG NAS**

```bash
# 上传代码（同上，换 SG 地址）
# SG 应用 migration
ssh admin@100.87.155.40 'cd /volume1/docker/pma/deploy/synology-sa && sudo sh -c "export PATH=/usr/local/bin:\$PATH && docker-compose exec pma flask db upgrade 2>&1"'
# SG 重建并重启
ssh admin@100.87.155.40 'cd /volume1/docker/pma/deploy/synology-sa && sudo sh -c "export PATH=/usr/local/bin:\$PATH && docker-compose build pma 2>&1 | tail -3 && docker-compose up -d pma 2>&1"'
```

**Step 4: 端到端验证**

```
1. SG james 私聊 liuwei 发消息 → CN liuwei 收到（现有功能）
2. CN liuwei 在 cross_system 对话回复 → SG james 在原私聊看到 liuwei 的回复 ✓
3. SG 建群含 liuwei，发第一条消息 → CN 自动建镜像群 "GroupName · SG PMA"
4. CN liuwei 在镜像群回复 → SG 群内 james/darryl 看到 liuwei 的消息 ✓
5. SG 群发第二条消息 → CN 镜像群正常显示 "james.ni [SG]" + 地球图标 ✓
```

---

## 关键约束备忘

- `User.is_active` 是 `@property`，**所有查询必须用 `User._is_active == True`**
- 推送全部走后台线程，函数无返回值
- CN 上 `CROSS_SYNC_API_KEY` 变量名为 `CROSS_SYSTEM_API_KEY`（现有），`require_api_key_or_jwt` 读的是 `CROSS_SYSTEM_API_KEY`，要确认 CN `.env` 已有此变量（已有 ✓）
- `cross_system_group` 是新的 conversation type 字符串值，`type VARCHAR(20)` 列已够长
