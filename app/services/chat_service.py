# -*- coding: utf-8 -*-
"""
聊天服务层

提供聊天系统的核心业务逻辑：
- 对话 CRUD（私聊、群聊、AI 对话）
- 消息发送与接收
- 未读计数
- 语言检测与翻译触发
- AI 对话管理
"""
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone

from app import db
from app.models.chat import (
    ChatConversation, ChatParticipant, ChatMessage, ChatTranslation
)
from app.models.user import User
from app.services.chat_agent.config import CHAT_CONTEXT_REJECT

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conversation ↔ Project 共享联动
# ---------------------------------------------------------------------------

def _load_meta(conv):
    """sync_metadata 字段反序列化，兼容 None / 非 JSON 字符串"""
    if not conv or not conv.sync_metadata:
        return {}
    try:
        m = json.loads(conv.sync_metadata)
        return m if isinstance(m, dict) else {}
    except (TypeError, ValueError):
        return {}


def _save_meta(conv, meta):
    conv.sync_metadata = json.dumps(meta, ensure_ascii=False) if meta else None


def _sync_project_share(conv, user_id, action):
    """如果会话挂在某个项目上（meta.project_id），把成员变化同步到 Project.shared_with_users。

    action: 'add' | 'remove'
    会自动 flush，但不 commit；调用方负责 commit/rollback。
    会跳过创建人/owner（项目 owner 已经天然可见）。
    """
    if not conv:
        return
    meta = _load_meta(conv)
    project_id = meta.get('project_id')
    if not project_id:
        return
    try:
        from app.models.project import Project
        project = Project.query.get(project_id)
        if not project:
            return
        if user_id == project.owner_id:
            return  # owner 不需要进 shared_with_users
        shared = list(project.shared_with_users or [])
        if action == 'add':
            if user_id not in shared:
                shared.append(user_id)
                project.shared_with_users = shared
                logger.info(f"项目 {project_id} 自动共享给用户 {user_id}（来自群聊 {conv.id}）")
        elif action == 'remove':
            if user_id in shared:
                shared = [u for u in shared if u != user_id]
                project.shared_with_users = shared
                logger.info(f"项目 {project_id} 取消对用户 {user_id} 的共享（来自群聊 {conv.id}）")
    except Exception as e:
        # 共享同步失败不应阻断聊天逻辑，仅记录日志
        logger.warning(f"同步项目共享失败 conv={conv.id} user={user_id} action={action}: {e}")


def _utc_iso(dt):
    """ISO 序列化, 给前端 Date() 正确解析。

    naive datetime: 视作本地时间, 不加 Z (PG `timestamp without time zone` 在
                    UTC+8 区会把 SQLAlchemy 写入的 aware UTC 转成本地存,
                    读回是 naive 本地; 加 Z 会让前端再偏移一个时区导致显示错乱)
    aware datetime: 标准 UTC ISO + Z
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.isoformat()
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


# ---------------------------------------------------------------------------
# 0. AI 回复后处理 — 清洗技术性措辞
# ---------------------------------------------------------------------------

_SANITIZE_PATTERNS = [
    (re.compile(r'(?:让我|我来|我先|我需要|尝试)(?:查询|搜索|查看|查找|检索)[^。，\n]*[。，]?\s*'), ''),
    (re.compile(r'显示[^。，\n]*(?:暂[无未]|为空)[^。，\n]*[。，]?\s*'), ''),
    (re.compile(r'数据库中[^。，\n]*[。，]?\s*'), ''),
]


def sanitize_ai_response(text):
    """清洗 AI 回复中的技术性措辞，用于 DB 存储版本。"""
    for pattern, replacement in _SANITIZE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


# ---------------------------------------------------------------------------
# 1. 语言检测
# ---------------------------------------------------------------------------

def detect_language(text):
    """
    检测文本语言。
    如果 CJK 字符占比 > 10%，返回 'zh'，否则返回 'en'。

    Args:
        text: 待检测的文本字符串

    Returns:
        str: 'zh' 或 'en'
    """
    if not text or not text.strip():
        return 'zh'

    cjk_count = 0
    total = 0
    for ch in text:
        if ch.isspace():
            continue
        total += 1
        # CJK Unified Ideographs 及扩展区
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or      # CJK Unified Ideographs
                0x3400 <= cp <= 0x4DBF or   # CJK Extension A
                0x20000 <= cp <= 0x2A6DF or # CJK Extension B
                0xF900 <= cp <= 0xFAFF or   # CJK Compatibility Ideographs
                0x2F800 <= cp <= 0x2FA1F or # CJK Compatibility Supplement
                0x3000 <= cp <= 0x303F or   # CJK Symbols and Punctuation
                0xFF00 <= cp <= 0xFFEF):    # Fullwidth Forms
            cjk_count += 1

    if total == 0:
        return 'zh'

    return 'zh' if (cjk_count / total) > 0.10 else 'en'


# ---------------------------------------------------------------------------
# 2. 获取用户的对话列表
# ---------------------------------------------------------------------------

def get_user_conversations(user_id, viewer_language=None):
    """
    获取用户的所有对话，按最后活动时间倒序排列。

    私聊显示对方名称，AI 对话显示 'AI 助手'，群聊显示群名称。
    每个对话包含未读消息计数、最后一条消息和成员信息。

    Args:
        user_id: 当前用户 ID
        viewer_language: 查看者语言偏好，用于最后消息显示翻译

    Returns:
        dict: {'success': True, 'data': [...]}
    """
    try:
        # 查询用户参与的所有未删除对话
        participations = (
            ChatParticipant.query
            .join(ChatConversation, ChatParticipant.conversation_id == ChatConversation.id)
            .filter(
                ChatParticipant.user_id == user_id,
                ChatConversation.is_deleted == False
            )
            .all()
        )

        conversations = []
        for part in participations:
            conv = ChatConversation.query.get(part.conversation_id)
            if not conv:
                continue

            # --- 计算未读消息数 ---
            # cross_system 消息 sender_id 为 NULL，需特殊处理
            unread_query = ChatMessage.query.filter(
                ChatMessage.conversation_id == conv.id,
                db.or_(
                    ChatMessage.sender_id != user_id,
                    ChatMessage.sender_id.is_(None)
                ),
                ChatMessage.is_deleted == False
            )
            if part.last_read_at:
                unread_query = unread_query.filter(
                    ChatMessage.created_at > part.last_read_at
                )
            unread_count = unread_query.count()

            # --- 最后一条消息 ---
            last_msg = (
                ChatMessage.query
                .filter(
                    ChatMessage.conversation_id == conv.id,
                    ChatMessage.is_deleted == False
                )
                .order_by(ChatMessage.created_at.desc())
                .first()
            )
            last_message = None
            if last_msg:
                # 卡片消息显示类型标签而非 JSON 内容
                msg_type = last_msg.message_type or 'text'
                if msg_type == 'cross_system':
                    # 跨系统消息：解析 JSON 提取预览
                    try:
                        import json
                        cs_data = json.loads(last_msg.content or '{}')
                        cs_sender = cs_data.get('sender_name', '')
                        cs_text = cs_data.get('text', '')[:30]
                        lm_content = f'{cs_sender}: {cs_text}' if cs_sender else cs_text
                    except Exception:
                        lm_content = last_msg.content[:50] if last_msg.content else ''
                elif msg_type == 'customer_card':
                    lm_content = '[客户卡片]'
                elif msg_type == 'project_card':
                    lm_content = '[项目卡片]'
                elif msg_type in ('image', 'video', 'file', 'voice', 'location'):
                    # 附件 content 是 JSON {text, name, address, ...}; 解析说明文字
                    name = ''; caption = ''
                    if last_msg.content:
                        try:
                            import json as _j
                            payload = _j.loads(last_msg.content)
                            if isinstance(payload, dict):
                                name = (payload.get('name') or '').strip()
                                caption = (payload.get('text') or '').strip()
                        except Exception:
                            pass
                    if msg_type == 'image':
                        lm_content = f'[图片]{" " + caption if caption else ""}'
                    elif msg_type == 'video':
                        lm_content = f'[视频]{" " + caption if caption else ""}'
                    elif msg_type == 'file':
                        lm_content = f'[文件] {name or last_msg.file_name or ""}'.rstrip()
                    elif msg_type == 'voice':
                        lm_content = '[语音]'
                    else:  # location
                        lm_content = f'[位置]{" " + name if name else ""}'
                elif msg_type == 'text_refs':
                    # 引用卡消息：取出 text 部分预览，并在末尾标记引用数
                    try:
                        import json as _j
                        payload = _j.loads(last_msg.content or '{}')
                        txt = (payload.get('text') or '').strip()[:40]
                        ref_count = len(payload.get('refs') or [])
                        suffix = f" [引用 ×{ref_count}]" if ref_count else ''
                        lm_content = (txt or '[引用卡片]') + suffix
                    except Exception:
                        lm_content = '[引用消息]'
                elif msg_type == 'stage_advance':
                    lm_content = '[阶段推进]'
                elif msg_type == 'system':
                    lm_content = last_msg.content[:50] if last_msg.content else '[系统消息]'
                else:
                    lm_content = last_msg.content[:50] if last_msg.content else ''

                # 如果查看者语言与消息源语言不同，尝试用翻译内容作为预览
                display_content = lm_content
                if (viewer_language and msg_type == 'text'
                        and last_msg.source_language
                        and viewer_language != last_msg.source_language):
                    trans = ChatTranslation.query.filter_by(
                        message_id=last_msg.id,
                        target_language=viewer_language
                    ).first()
                    if trans and trans.translated_content:
                        display_content = trans.translated_content[:50]

                # 发送者名称：跨系统消息从 JSON 提取，AI 消息显示 'AI'
                if msg_type == 'cross_system':
                    try:
                        import json
                        _cs = json.loads(last_msg.content or '{}')
                        lm_sender_name = _cs.get('sender_name', '')
                    except Exception:
                        lm_sender_name = ''
                elif last_msg.sender:
                    lm_sender_name = last_msg.sender.real_name or last_msg.sender.username
                else:
                    lm_sender_name = 'AI'

                last_message = {
                    'id': last_msg.id,
                    'content': display_content,
                    'message_type': msg_type,
                    'sender_id': last_msg.sender_id,
                    'sender_name': lm_sender_name,
                    'created_at': _utc_iso(last_msg.created_at),
                }

            # --- 参与者列表 ---
            members = ChatParticipant.query.filter_by(conversation_id=conv.id).all()
            participants = []
            for m in members:
                u = User.query.get(m.user_id)
                participants.append({
                    'user_id': m.user_id,
                    'role': m.role,
                    'user_name': (u.real_name or u.username) if u else None,
                    'department': u.department if u else None,
                })

            # --- 显示名称 ---
            if conv.type == 'cross_system':
                display_name = conv.name or '跨系统消息'
            elif conv.type == 'ai':
                display_name = conv.topic or 'AI 助手'
            elif conv.type == 'private':
                # 私聊：显示对方名称
                other = [p for p in participants if p['user_id'] != user_id]
                display_name = other[0]['user_name'] if other else conv.name or '私聊'
            else:
                display_name = conv.name or '群聊'

            # AI 对话：检查上下文 token 用量
            context_exhausted = False
            context_tokens = 0
            if conv.type == 'ai':
                _last_ai = (
                    ChatMessage.query
                    .filter_by(conversation_id=conv.id, is_ai_response=True)
                    .order_by(ChatMessage.id.desc())
                    .first()
                )
                if _last_ai:
                    context_tokens = _last_ai.ai_prompt_tokens or 0
                    if context_tokens > CHAT_CONTEXT_REJECT:
                        context_exhausted = True

            conversations.append({
                'id': conv.id,
                'type': conv.type,
                'name': display_name,
                'topic': conv.topic,
                'unread_count': unread_count,
                'last_message': last_message,
                'participants': participants,
                'created_at': _utc_iso(conv.created_at),
                'updated_at': _utc_iso(conv.updated_at),
                'context_exhausted': context_exhausted,
                'context_tokens': context_tokens,
            })

        # 按 updated_at 倒序排列（最近活动在前）
        conversations.sort(
            key=lambda c: c['updated_at'] or '',
            reverse=True
        )

        return {'success': True, 'data': conversations}

    except Exception as e:
        logger.error(f"获取用户对话列表失败: {e}", exc_info=True)
        return {'success': False, 'message': f'获取对话列表失败: {str(e)}', 'data': []}


# ---------------------------------------------------------------------------
# 3. 创建对话
# ---------------------------------------------------------------------------

def create_conversation(creator_id, participant_ids, conv_type=None, name=None, sync_metadata=None):
    """
    创建新对话。

    自动推断对话类型：
    - 0 个参与者 → ai（AI 对话，仅创建者）
    - 1 个参与者 → private（私聊）
    - 2+ 个参与者 → group（群聊）

    私聊时会检查是否已存在，避免重复创建。

    Args:
        creator_id: 创建者用户 ID
        participant_ids: 其他参与者 ID 列表（不含创建者）
        conv_type: 对话类型，可选。为 None 时自动推断
        name: 群聊名称，私聊和 AI 对话可不填

    Returns:
        dict: {'success': True, 'data': {'id': ..., ...}} 或错误信息
    """
    try:
        # 排除创建者自身，去重
        other_ids = list(set(pid for pid in (participant_ids or []) if pid != creator_id))

        # 自动推断对话类型
        if conv_type is None:
            if len(other_ids) == 0:
                conv_type = 'ai'
            elif len(other_ids) == 1:
                conv_type = 'private'
            else:
                conv_type = 'group'

        # 私聊去重检查
        if conv_type == 'private' and len(other_ids) == 1:
            existing = _find_private_conversation(creator_id, other_ids[0])
            if existing:
                return {
                    'success': True,
                    'data': {
                        'id': existing.id,
                        'type': existing.type,
                        'name': existing.name,
                        'created_at': _utc_iso(existing.created_at),
                    },
                    'message': '已存在的私聊对话',
                }

        # 验证参与者用户存在
        for uid in other_ids:
            user = User.query.get(uid)
            if not user:
                return {'success': False, 'message': f'用户 {uid} 不存在'}

        # 创建对话
        conv = ChatConversation(
            type=conv_type,
            name=name,
            created_by=creator_id,
        )
        if isinstance(sync_metadata, dict) and sync_metadata:
            _save_meta(conv, sync_metadata)
        db.session.add(conv)
        db.session.flush()  # 获取 conv.id

        # 添加创建者为 owner
        owner_part = ChatParticipant(
            conversation_id=conv.id,
            user_id=creator_id,
            role='owner',
            last_read_at=datetime.now(timezone.utc),
        )
        db.session.add(owner_part)

        # 添加其他参与者
        for uid in other_ids:
            member = ChatParticipant(
                conversation_id=conv.id,
                user_id=uid,
                role='member',
            )
            db.session.add(member)
            # 项目群联动：把项目共享给新成员
            _sync_project_share(conv, uid, 'add')

        db.session.commit()

        # 构建参与者列表 & 显示名称（与 get_user_conversations 逻辑一致）
        all_user_ids = [creator_id] + list(other_ids)
        participants = []
        for uid in all_user_ids:
            u = User.query.get(uid)
            participants.append({
                'user_id': uid,
                'role': 'owner' if uid == creator_id else 'member',
                'user_name': (u.real_name or u.username) if u else None,
                'department': u.department if u else None,
            })

        if conv_type == 'ai':
            display_name = 'AI 助手'
        elif conv_type == 'private':
            other = [p for p in participants if p['user_id'] != creator_id]
            display_name = other[0]['user_name'] if other else conv.name or '私聊'
        else:
            display_name = conv.name or '群聊'

        logger.info(f"创建对话成功: id={conv.id}, type={conv_type}, creator={creator_id}")
        return {
            'success': True,
            'data': {
                'id': conv.id,
                'type': conv.type,
                'name': display_name,
                'participants': participants,
                'created_at': _utc_iso(conv.created_at),
            },
            'message': '对话创建成功',
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建对话失败: {e}", exc_info=True)
        return {'success': False, 'message': f'创建对话失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 4. 查找已有的私聊对话
# ---------------------------------------------------------------------------

def _find_private_conversation(user_a_id, user_b_id):
    """
    查找两个用户之间已有的私聊对话。

    Args:
        user_a_id: 用户 A 的 ID
        user_b_id: 用户 B 的 ID

    Returns:
        ChatConversation 或 None
    """
    # 找到 user_a 参与的所有私聊
    a_convs = (
        db.session.query(ChatParticipant.conversation_id)
        .join(ChatConversation, ChatParticipant.conversation_id == ChatConversation.id)
        .filter(
            ChatParticipant.user_id == user_a_id,
            ChatConversation.type == 'private',
            ChatConversation.is_deleted == False,
        )
        .subquery()
    )

    # 在这些对话中，找到 user_b 也参与的
    result = (
        ChatParticipant.query
        .filter(
            ChatParticipant.conversation_id.in_(db.session.query(a_convs.c.conversation_id)),
            ChatParticipant.user_id == user_b_id,
        )
        .first()
    )

    if result:
        return ChatConversation.query.get(result.conversation_id)
    return None


# ---------------------------------------------------------------------------
# 5. 获取消息列表
# ---------------------------------------------------------------------------

def get_messages(conversation_id, user_id, since=None, limit=50):
    """
    获取对话中的消息列表，支持增量拉取。

    根据查看者的语言偏好附带翻译内容。

    Args:
        conversation_id: 对话 ID
        user_id: 查看者用户 ID
        since: ISO 格式时间戳，只返回此时间之后的消息（增量拉取）
        limit: 最大返回条数，默认 50

    Returns:
        dict: {'success': True, 'data': [...]}
    """
    try:
        # 验证用户是对话参与者
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
        ).first()
        if not participant:
            return {'success': False, 'message': '您不是该对话的参与者'}

        # 获取查看者语言偏好，无设置时回落到系统语言（sp8d→zh，ovs→en）
        viewer = User.query.get(user_id)
        if viewer and viewer.language_preference:
            viewer_lang = viewer.language_preference
        else:
            import os as _os
            _db_type = _os.environ.get('PMA_DB_TYPE') or _os.environ.get('SUPABASE_DB_TYPE', '')
            viewer_lang = 'en' if _db_type == 'ovs' else 'zh'

        # 构建查询
        query = ChatMessage.query.filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.is_deleted == False,
        )

        # 增量拉取：只获取 since 时间之后的消息
        # DB 存储 naive UTC，since 参数去掉时区后直接比较，避免 aware vs naive 偏差
        since_dt = None
        if since:
            if isinstance(since, str):
                since_dt = datetime.fromisoformat(since.replace('Z', '').replace('+00:00', ''))
            else:
                since_dt = since.replace(tzinfo=None) if hasattr(since, 'tzinfo') else since
            query = query.filter(ChatMessage.created_at > since_dt)

        # 按时间正序排列，最新的在最后
        messages_list = (
            query
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )

        data = []
        for msg in messages_list:
            msg_dict = msg.to_dict(viewer_language=viewer_lang)
            msg_dict['is_mine'] = (msg.sender_id == user_id)
            data.append(msg_dict)

        # 查询 since 之后被撤回的消息（用于轮询同步）
        recalled_ids = []
        if since_dt:
            recalled = (
                ChatMessage.query.filter(
                    ChatMessage.conversation_id == conversation_id,
                    ChatMessage.is_deleted == True,
                    ChatMessage.deleted_at != None,
                    ChatMessage.deleted_at > since_dt,
                )
                .with_entities(ChatMessage.id, ChatMessage.sender_id)
                .all()
            )
            recalled_ids = [{'id': r.id, 'sender_id': r.sender_id} for r in recalled]

        # 私聊场景：返回对方的 last_read_at，前端据此渲染"已读"
        peer_last_read_at = None
        conv = ChatConversation.query.get(conversation_id)
        if conv and conv.type == 'private':
            peer = ChatParticipant.query.filter(
                ChatParticipant.conversation_id == conversation_id,
                ChatParticipant.user_id != user_id,
            ).first()
            if peer and peer.last_read_at:
                peer_last_read_at = _utc_iso(peer.last_read_at)

        return {
            'success': True,
            'data': data,
            'recalled_ids': recalled_ids,
            'peer_last_read_at': peer_last_read_at,
        }

    except Exception as e:
        logger.error(f"获取消息失败: {e}", exc_info=True)
        return {'success': False, 'message': f'获取消息失败: {str(e)}', 'data': []}


# ---------------------------------------------------------------------------
# 6. 发送消息
# ---------------------------------------------------------------------------

def send_message(conversation_id, sender_id, content, reply_to_id=None, refs=None,
                 message_type='text', file_url=None, file_meta=None):
    """
    发送消息到对话。

    Args:
        refs: optional list of {type:'#'|'$', item:{...}} —— 项目/客户引用卡
              如果有 refs，message_type 设为 'text_refs'，content 序列化为
              JSON {"text": <原文>, "refs": [...]}
        message_type: 'text' / 'image' / 'file' / 'voice' / 'location'
        file_url:   附件 URL（NAS 路径），image/file/voice 时必填
        file_meta:  dict {name, size, duration?, lat?, lon?} → 序列化进 content
    """
    try:
        is_attachment = message_type in ('image', 'file', 'voice', 'location')
        if not is_attachment and (not content or not content.strip()):
            return {'success': False, 'message': '消息内容不能为空'}

        # 验证参与者身份
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=sender_id,
        ).first()
        if not participant:
            return {'success': False, 'message': '您不是该对话的参与者'}

        # 检测语言（仅文本时）
        source_lang = detect_language(content) if content else None

        # 决定最终 message_type / content
        msg_type = message_type or 'text'
        msg_content = (content or '').strip()
        if refs and not is_attachment:
            msg_type = 'text_refs'
            msg_content = json.dumps(
                {'text': msg_content, 'refs': refs},
                ensure_ascii=False,
            )
        elif is_attachment:
            # 附件 meta 与可选说明文字打包进 content（前端按 type 解析）
            payload = {'text': msg_content}
            if file_meta:
                payload.update(file_meta)
            msg_content = json.dumps(payload, ensure_ascii=False)

        # 创建消息
        message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=msg_content,
            message_type=msg_type,
            source_language=source_lang,
            reply_to_id=reply_to_id,
            file_url=file_url,
        )
        db.session.add(message)

        # 更新对话的 updated_at
        conv = ChatConversation.query.get(conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)

        # 更新发送者的 last_read_at
        participant.last_read_at = datetime.now(timezone.utc)

        db.session.commit()

        logger.info(
            f"消息发送成功: msg_id={message.id}, conv={conversation_id}, "
            f"sender={sender_id}, lang={source_lang}"
        )

        # 触发翻译（commit 后执行，避免事务问题）
        try:
            _trigger_translation(message.id, source_lang, conversation_id)
        except Exception as te:
            # 翻译失败不影响消息发送
            logger.warning(f"触发翻译失败: {te}")

        # 跨系统推送（仅私聊，异步不阻塞）
        if conv and conv.type == 'private':
            try:
                from app.services.cross_sync_service import is_cross_sync_enabled, push_message_to_peer
                if is_cross_sync_enabled():
                    sender_user = User.query.get(sender_id)
                    sender_display = (sender_user.real_name or sender_user.username) if sender_user else ''
                    # 找到私聊对方的邮箱
                    other_part = ChatParticipant.query.filter(
                        ChatParticipant.conversation_id == conversation_id,
                        ChatParticipant.user_id != sender_id,
                    ).first()
                    if other_part:
                        other_user = User.query.get(other_part.user_id)
                        if other_user and other_user.email:
                            push_message_to_peer(
                                other_user.email,
                                sender_display,
                                content.strip(),
                                sender_email=sender_user.email if sender_user else None,
                                source_lang=source_lang,
                            )
            except Exception as ce:
                logger.warning(f"跨系统推送失败: {ce}")

        # 跨系统私聊回复推送（cross_system 对话 → 推回对端）
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
                            source_lang=source_lang,
                        )
            except Exception as ce:
                logger.warning(f"跨系统私聊回复推送失败: {ce}")

        # 群聊跨系统推送（group → CN mirror group）
        if conv and conv.type == 'group':
            try:
                from app.services.cross_sync_service import is_cross_sync_enabled, push_group_to_peer
                if is_cross_sync_enabled():
                    sender_user = User.query.get(sender_id)
                    sender_display = (sender_user.real_name or sender_user.username) if sender_user else ''
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

        # 返回消息数据
        sender = User.query.get(sender_id)
        data = {
            'id': message.id,
            'conversation_id': conversation_id,
            'sender_id': sender_id,
            'sender_name': (sender.real_name or sender.username) if sender else None,
            'content': message.content,
            'source_language': source_lang,
            'created_at': _utc_iso(message.created_at),
        }
        # 如果是回复消息，附带被引用消息的预览
        if reply_to_id and message.reply_to:
            rt = message.reply_to
            rt_sender = User.query.get(rt.sender_id)
            data['reply_to'] = {
                'id': rt.id,
                'sender_name': (rt_sender.real_name or rt_sender.username) if rt_sender else None,
                'content': (rt.content or '')[:50],
                'message_type': rt.message_type or 'text',
                'file_name': rt.file_name,
                'file_url': rt.file_url,
            }
        return {
            'success': True,
            'data': data,
            'message': '消息发送成功',
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"发送消息失败: {e}", exc_info=True)
        return {'success': False, 'message': f'发送消息失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 7. 触发翻译
# ---------------------------------------------------------------------------

def _trigger_translation(message_id, source_lang, conversation_id):
    """
    为消息触发所需的翻译。

    获取对话中所有参与者的语言偏好，找出与源语言不同的目标语言，
    对每个目标语言调用翻译服务。

    Args:
        message_id: 消息 ID
        source_lang: 消息的源语言 ('zh' 或 'en')
        conversation_id: 对话 ID
    """
    try:
        # 获取对话的所有参与者
        participants = ChatParticipant.query.filter_by(
            conversation_id=conversation_id
        ).all()

        # 收集所有参与者的语言偏好
        target_langs = set()
        for part in participants:
            user = User.query.get(part.user_id)
            if user and user.language_preference:
                if user.language_preference != source_lang:
                    target_langs.add(user.language_preference)

        if not target_langs:
            return  # 所有人使用同一语言，无需翻译

        # 获取消息内容
        message = ChatMessage.query.get(message_id)
        if not message:
            return

        # 检查是否已有翻译
        existing_langs = set(
            t.target_language for t in
            ChatTranslation.query.filter_by(message_id=message_id).all()
        )
        needed_langs = target_langs - existing_langs

        if not needed_langs:
            return

        # 调用翻译服务
        try:
            from app.services.chat_translation_service import translate_text
        except ImportError:
            logger.warning("翻译服务 chat_translation_service 尚未实现，跳过翻译")
            return

        for target_lang in needed_langs:
            try:
                translated = translate_text(message.content, source_lang, target_lang)
                if translated:
                    translation = ChatTranslation(
                        message_id=message_id,
                        target_language=target_lang,
                        translated_content=translated,
                    )
                    db.session.add(translation)
            except Exception as te:
                logger.warning(f"翻译到 {target_lang} 失败: {te}")

        db.session.commit()
        logger.info(f"消息 {message_id} 翻译完成: {needed_langs}")

    except Exception as e:
        db.session.rollback()
        logger.error(f"翻译触发失败: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# 8. 标记已读
# ---------------------------------------------------------------------------

def mark_as_read(conversation_id, user_id):
    """
    将对话标记为已读（更新参与者的 last_read_at 为当前时间）。

    Args:
        conversation_id: 对话 ID
        user_id: 用户 ID

    Returns:
        dict: {'success': True, 'message': ...}
    """
    try:
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
        ).first()

        if not participant:
            return {'success': False, 'message': '您不是该对话的参与者'}

        participant.last_read_at = datetime.now(timezone.utc)
        db.session.commit()

        return {'success': True, 'message': '已标记为已读'}

    except Exception as e:
        db.session.rollback()
        logger.error(f"标记已读失败: {e}", exc_info=True)
        return {'success': False, 'message': f'标记已读失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 9. 获取总未读消息数
# ---------------------------------------------------------------------------

def get_total_unread_count(user_id):
    """
    获取用户所有对话的未读消息总数。

    Args:
        user_id: 用户 ID

    Returns:
        dict: {'success': True, 'data': {'total_unread': N}}
    """
    try:
        participations = (
            ChatParticipant.query
            .join(ChatConversation, ChatParticipant.conversation_id == ChatConversation.id)
            .filter(
                ChatParticipant.user_id == user_id,
                ChatConversation.is_deleted == False,
            )
            .all()
        )

        total = 0
        for part in participations:
            unread_query = ChatMessage.query.filter(
                ChatMessage.conversation_id == part.conversation_id,
                db.or_(
                    ChatMessage.sender_id != user_id,
                    ChatMessage.sender_id.is_(None)
                ),
                ChatMessage.is_deleted == False,
            )
            if part.last_read_at:
                unread_query = unread_query.filter(
                    ChatMessage.created_at > part.last_read_at
                )
            total += unread_query.count()

        return {'success': True, 'data': {'total_unread': total}}

    except Exception as e:
        logger.error(f"获取未读计数失败: {e}", exc_info=True)
        return {'success': False, 'message': f'获取未读计数失败: {str(e)}', 'data': {'total_unread': 0}}


# ---------------------------------------------------------------------------
# 10. 添加群聊成员
# ---------------------------------------------------------------------------

def add_participants(conversation_id, user_ids, current_user_id):
    """
    向对话中添加新成员。

    - 群聊：直接添加
    - 私聊：自动升级为群聊后添加
    - AI 对话：不允许添加

    已有成员会自动跳过，不会重复添加。

    Args:
        conversation_id: 对话 ID
        user_ids: 要添加的用户 ID 列表
        current_user_id: 操作者用户 ID

    Returns:
        dict: {'success': True, 'data': {'added': [...], 'skipped': [...], 'upgraded': bool, 'conv_type': str, 'conv_name': str, 'participants': [...]}}
    """
    try:
        conv = ChatConversation.query.get(conversation_id)
        if not conv:
            return {'success': False, 'message': '对话不存在'}

        if conv.is_deleted:
            return {'success': False, 'message': '对话已被删除'}

        if conv.type == 'ai':
            return {'success': False, 'message': 'AI 对话不能添加成员'}

        # 验证操作者是参与者
        operator = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=current_user_id,
        ).first()
        if not operator:
            return {'success': False, 'message': '您不是该对话的参与者'}

        upgraded = False
        added = []
        skipped = []

        for uid in user_ids:
            # 检查用户是否存在
            user = User.query.get(uid)
            if not user:
                skipped.append({'user_id': uid, 'reason': '用户不存在'})
                continue

            # 检查是否已是成员
            existing = ChatParticipant.query.filter_by(
                conversation_id=conversation_id,
                user_id=uid,
            ).first()
            if existing:
                skipped.append({'user_id': uid, 'reason': '已是成员'})
                continue

            member = ChatParticipant(
                conversation_id=conversation_id,
                user_id=uid,
                role='member',
            )
            db.session.add(member)
            # 项目群联动：把项目共享给新成员
            _sync_project_share(conv, uid, 'add')
            added.append(uid)

        if added:
            # 私聊自动升级为群聊
            if conv.type == 'private':
                conv.type = 'group'
                upgraded = True
                # flush 使新成员可查询
                db.session.flush()
                # 生成群名：所有成员名字拼接
                all_members = ChatParticipant.query.filter_by(
                    conversation_id=conversation_id).all()
                names = []
                for m in all_members:
                    u = User.query.get(m.user_id)
                    if u:
                        names.append(u.real_name or u.username)
                conv.name = '、'.join(names)

            conv.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"对话 {conversation_id} 添加成员: {added}" +
                        (f" (私聊→群聊升级)" if upgraded else ""))

        # 返回最新参与者列表
        all_members = ChatParticipant.query.filter_by(
            conversation_id=conversation_id).all()
        participants = []
        for m in all_members:
            u = User.query.get(m.user_id)
            participants.append({
                'user_id': m.user_id,
                'role': m.role,
                'user_name': (u.real_name or u.username) if u else None,
                'department': u.department if u else None,
            })

        return {
            'success': True,
            'data': {
                'added': added,
                'skipped': skipped,
                'upgraded': upgraded,
                'conv_type': conv.type,
                'conv_name': conv.name,
                'participants': participants,
            },
            'message': f'成功添加 {len(added)} 名成员',
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"添加成员失败: {e}", exc_info=True)
        return {'success': False, 'message': f'添加成员失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 10b. 移除群聊成员
# ---------------------------------------------------------------------------

def remove_participant(conversation_id, target_user_id, current_user_id):
    """从群聊中移除一名成员。

    规则：
    - 仅群聊允许移除（私聊、AI 不允许）
    - 操作者必须是参与者
    - 操作者可以移除自己（退群）
    - 移除他人需要 owner 权限（创建人）
    - 不能移除最后一名成员

    若会话挂在某个项目（meta.project_id），同时把目标用户从 Project.shared_with_users 移除。
    """
    try:
        conv = ChatConversation.query.get(conversation_id)
        if not conv or conv.is_deleted:
            return {'success': False, 'message': '对话不存在'}
        if conv.type != 'group':
            return {'success': False, 'message': '仅群聊支持移除成员'}

        operator = ChatParticipant.query.filter_by(
            conversation_id=conversation_id, user_id=current_user_id
        ).first()
        if not operator:
            return {'success': False, 'message': '您不是该对话的参与者'}

        target = ChatParticipant.query.filter_by(
            conversation_id=conversation_id, user_id=target_user_id
        ).first()
        if not target:
            return {'success': False, 'message': '该成员不在群聊中'}

        if target_user_id != current_user_id and operator.role != 'owner':
            return {'success': False, 'message': '只有群主可以移除其他成员'}

        # 不允许群里最后一人被移除（应改用删除会话）
        member_count = ChatParticipant.query.filter_by(conversation_id=conversation_id).count()
        if member_count <= 1:
            return {'success': False, 'message': '群聊中至少需保留一名成员'}

        db.session.delete(target)
        # 项目共享同步移除
        _sync_project_share(conv, target_user_id, 'remove')
        conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"对话 {conversation_id} 移除成员 {target_user_id}（操作者 {current_user_id}）")
        return {
            'success': True,
            'data': {'removed_user_id': target_user_id},
            'message': '成员已移除',
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"移除成员失败: {e}", exc_info=True)
        return {'success': False, 'message': f'移除成员失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 10c. 获取会话详情（含成员、关联项目等）
# ---------------------------------------------------------------------------

def get_conversation_detail(conversation_id, user_id):
    """返回群聊设置页所需的完整会话信息。

    Returns:
        dict: {
            'success': True,
            'data': {
                'id', 'type', 'name', 'created_at', 'announcement',
                'is_owner': bool,
                'participants': [{user_id, name, dept, role, is_self}, ...],
                'linked_project': {id, name, stage, amount, owner, region} | None,
            }
        }
    """
    try:
        conv = ChatConversation.query.get(conversation_id)
        if not conv or conv.is_deleted:
            return {'success': False, 'message': '对话不存在'}

        operator = ChatParticipant.query.filter_by(
            conversation_id=conversation_id, user_id=user_id
        ).first()
        if not operator:
            return {'success': False, 'message': '您不是该对话的参与者'}

        meta = _load_meta(conv)
        announcement = meta.get('announcement') or ''

        # 参与者
        members = []
        for p in conv.participants.all():
            u = p.user
            display_name = (u.real_name or u.username) if u else f'用户#{p.user_id}'
            members.append({
                'user_id': p.user_id,
                'name': display_name,
                'dept': (u.department if u else '') or '',
                'role': p.role,
                'is_self': p.user_id == user_id,
                'avatar': display_name[0] if display_name else '?',
            })

        # 关联项目
        linked_project = None
        if meta.get('project_id'):
            try:
                from app.models.project import Project
                from app.utils.dictionary_helpers import project_stage_label
                p = Project.query.get(meta['project_id'])
                if p and not getattr(p, 'is_deleted', False):
                    owner_name = ''
                    if p.owner:
                        owner_name = p.owner.real_name or p.owner.username or ''
                    linked_project = {
                        'id': p.id,
                        'name': p.project_name,
                        'stage': project_stage_label(p.current_stage) if p.current_stage else '',
                        'amount': float(p.quotation_customer or 0),
                        'owner': owner_name,
                        'region': p.region or '',
                    }
            except Exception as e:
                logger.warning(f"加载关联项目失败 conv={conversation_id}: {e}")

        return {
            'success': True,
            'data': {
                'id': conv.id,
                'type': conv.type,
                'name': conv.name or '',
                'created_at': _utc_iso(conv.created_at),
                'announcement': announcement,
                'is_owner': operator.role == 'owner',
                'participants': members,
                'linked_project': linked_project,
            },
        }
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}", exc_info=True)
        return {'success': False, 'message': f'获取会话详情失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 10c2. 发送系统消息（无 sender，message_type='system'）
# ---------------------------------------------------------------------------

def send_system_message(conversation_id, content, message_type='system'):
    """以系统身份给会话发一条消息（无 sender_id）。

    message_type:
      - 'system'：普通系统消息（居中斜体小字）
      - 'stage_advance'：阶段推进，content 应为 JSON 字符串包含
        {from_stage_label, to_stage_label, by_name, by_initial, note?}，前端用
        StageAdvanceCard 富卡渲染

    失败仅记录日志，不抛异常 —— 系统通知不应阻断主业务。
    """
    if not content or not content.strip():
        return None
    try:
        conv = ChatConversation.query.get(conversation_id)
        if not conv or conv.is_deleted:
            return None
        msg = ChatMessage(
            conversation_id=conversation_id,
            sender_id=None,
            content=content.strip(),
            message_type=message_type,
        )
        db.session.add(msg)
        conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"系统消息已发到会话 {conversation_id}: {content[:40]}")
        return msg.id
    except Exception as e:
        db.session.rollback()
        logger.warning(f"发送系统消息失败 conv={conversation_id}: {e}")
        return None


# ---------------------------------------------------------------------------
# 10d. 查找项目讨论群
# ---------------------------------------------------------------------------

def find_project_conversation(user_id, project_id):
    """查找指定用户已参与的、绑定到指定项目的群聊（用户可见性场景）。

    Returns:
        int | None: 找到的 conversation id，否则 None
    """
    try:
        rows = (
            db.session.query(ChatConversation)
            .join(ChatParticipant, ChatParticipant.conversation_id == ChatConversation.id)
            .filter(
                ChatParticipant.user_id == user_id,
                ChatConversation.is_deleted == False,
                ChatConversation.type == 'group',
                ChatConversation.sync_metadata.isnot(None),
            )
            .all()
        )
        for conv in rows:
            meta = _load_meta(conv)
            if meta.get('project_id') == project_id:
                return conv.id
        return None
    except Exception as e:
        logger.warning(f"查找项目讨论群失败 user={user_id} project={project_id}: {e}")
        return None


def find_any_project_conversation(project_id):
    """全局查找绑定到指定项目的群聊（不限定用户）—— 系统通知场景用。"""
    try:
        rows = (
            ChatConversation.query
            .filter(
                ChatConversation.is_deleted == False,
                ChatConversation.type == 'group',
                ChatConversation.sync_metadata.isnot(None),
            ).all()
        )
        for conv in rows:
            meta = _load_meta(conv)
            if meta.get('project_id') == project_id:
                return conv.id
        return None
    except Exception as e:
        logger.warning(f"全局查找项目群失败 project={project_id}: {e}")
        return None


# ---------------------------------------------------------------------------
# 11. 创建 AI 对话
# ---------------------------------------------------------------------------

def create_ai_conversation(user_id):
    """
    为用户创建一个新的 AI 对话。

    每次调用都会创建新的对话，支持多个 AI 对话并存。

    Args:
        user_id: 用户 ID

    Returns:
        dict: {'success': True, 'data': {'id': ..., 'type': 'ai', ...}}
    """
    try:
        return create_conversation(
            creator_id=user_id,
            participant_ids=[],
            conv_type='ai',
            name='AI 助手',
        )

    except Exception as e:
        logger.error(f"创建 AI 对话失败: {e}", exc_info=True)
        return {'success': False, 'message': f'创建 AI 对话失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 12. 删除对话
# ---------------------------------------------------------------------------

def delete_conversation(conversation_id, user_id):
    """
    软删除对话（对所有参与者不可见）。

    Args:
        conversation_id: 对话 ID
        user_id: 操作者用户 ID

    Returns:
        dict: {'success': True/False, 'message': ...}
    """
    try:
        conv = ChatConversation.query.get(conversation_id)
        if not conv:
            return {'success': False, 'message': '对话不存在'}

        # 验证操作者是参与者
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id, user_id=user_id
        ).first()
        if not participant:
            return {'success': False, 'message': '您不是该对话的参与者'}

        conv.is_deleted = True
        db.session.commit()

        logger.info(f"对话 {conversation_id} 已被用户 {user_id} 删除")
        return {'success': True, 'message': '对话已删除'}

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除对话失败: {e}", exc_info=True)
        return {'success': False, 'message': f'删除对话失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 13. 撤回消息
# ---------------------------------------------------------------------------

RECALL_TIME_LIMIT = 120  # 秒


def recall_message(message_id, user_id):
    """
    撤回消息（仅发送者，2 分钟内）。

    设置 is_deleted=True、deleted_at=now()，清空 content 和 file_url。

    Args:
        message_id: 消息 ID
        user_id: 操作者用户 ID

    Returns:
        dict: {'success': True/False, ...}
    """
    try:
        msg = ChatMessage.query.get(message_id)
        if not msg:
            return {'success': False, 'message': '消息不存在'}
        if msg.sender_id != user_id:
            return {'success': False, 'message': '只能撤回自己发送的消息'}
        if msg.is_deleted:
            return {'success': False, 'message': '消息已被撤回'}

        # 时间限制检查
        now = datetime.now(timezone.utc)
        created = msg.created_at
        # 确保时区一致
        if created.tzinfo is None:
            from datetime import timezone as tz
            created = created.replace(tzinfo=tz.utc)
        elapsed = (now - created).total_seconds()
        if elapsed > RECALL_TIME_LIMIT:
            return {'success': False, 'message': '超过 2 分钟，无法撤回'}

        msg.is_deleted = True
        msg.deleted_at = now
        msg.content = ''
        msg.file_url = None
        db.session.commit()

        logger.info(f"消息 {message_id} 已被用户 {user_id} 撤回")
        return {'success': True, 'message': '消息已撤回', 'data': {'id': message_id}}

    except Exception as e:
        db.session.rollback()
        logger.error(f"撤回消息失败: {e}", exc_info=True)
        return {'success': False, 'message': f'撤回消息失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 14. 转发消息
# ---------------------------------------------------------------------------

def forward_message(message_id, sender_id, target_conversation_ids, note=None):
    """
    将消息转发到一个或多个对话。

    复制原消息的内容（文本、附件信息）到目标对话。
    如果有留言(note)，会在转发消息后追加一条文本消息。

    Args:
        message_id: 要转发的消息 ID
        sender_id: 转发操作者的用户 ID
        target_conversation_ids: 目标对话 ID 列表
        note: 可选的留言文本

    Returns:
        dict: {'success': True, 'data': {'forwarded_count': N, 'conversation_ids': [...]}}
    """
    try:
        # 验证原消息存在
        original_msg = ChatMessage.query.get(message_id)
        if not original_msg:
            return {'success': False, 'message': '消息不存在'}
        if original_msg.is_deleted:
            return {'success': False, 'message': '消息已被撤回，无法转发'}

        # 验证操作者有权查看原消息（是原对话的参与者）
        src_participant = ChatParticipant.query.filter_by(
            conversation_id=original_msg.conversation_id,
            user_id=sender_id,
        ).first()
        if not src_participant:
            return {'success': False, 'message': '您无权转发此消息'}

        forwarded_ids = []

        for conv_id in target_conversation_ids:
            # 验证操作者是目标对话的参与者
            participant = ChatParticipant.query.filter_by(
                conversation_id=conv_id,
                user_id=sender_id,
            ).first()
            if not participant:
                continue

            # 创建转发消息（复制原消息内容）
            fwd_msg = ChatMessage(
                conversation_id=conv_id,
                sender_id=sender_id,
                content=original_msg.content,
                message_type=original_msg.message_type or 'text',
                file_url=original_msg.file_url,
                file_name=original_msg.file_name,
                file_size=original_msg.file_size,
                source_language=original_msg.source_language or 'zh',
            )
            db.session.add(fwd_msg)

            # 如果有留言，追加一条文本消息
            if note and note.strip():
                note_msg = ChatMessage(
                    conversation_id=conv_id,
                    sender_id=sender_id,
                    content=note.strip(),
                    source_language=detect_language(note),
                )
                db.session.add(note_msg)

            # 更新目标对话 updated_at 和发送者 last_read_at
            conv = ChatConversation.query.get(conv_id)
            if conv:
                conv.updated_at = datetime.now(timezone.utc)
            participant.last_read_at = datetime.now(timezone.utc)

            forwarded_ids.append(conv_id)

        db.session.commit()

        logger.info(
            f"消息 {message_id} 已被用户 {sender_id} 转发到 {len(forwarded_ids)} 个对话: {forwarded_ids}"
        )

        return {
            'success': True,
            'data': {
                'forwarded_count': len(forwarded_ids),
                'conversation_ids': forwarded_ids,
            },
            'message': f'成功转发到 {len(forwarded_ids)} 个对话',
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"转发消息失败: {e}", exc_info=True)
        return {'success': False, 'message': f'转发消息失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 14b. 分享文件管理器文件到对话
# ---------------------------------------------------------------------------

def share_files_to_conversations(sender_id, file_refs_with_libs, target_conversation_ids, note=None):
    """
    将文件管理器文件分享到一个或多个聊天对话。

    Args:
        sender_id: 发送者用户 ID
        file_refs_with_libs: list of (UserFileRef, FileLibrary) 元组
        target_conversation_ids: 目标对话 ID 列表
        note: 可选的留言文本

    Returns:
        dict: {'success': True, 'data': {'shared_count': N, 'conversation_ids': [...]}}
    """
    try:
        shared_ids = []

        for conv_id in target_conversation_ids:
            # 验证操作者是目标对话的参与者
            participant = ChatParticipant.query.filter_by(
                conversation_id=conv_id,
                user_id=sender_id,
            ).first()
            if not participant:
                continue

            # 为每个文件创建一条消息
            for ref, lib in file_refs_with_libs:
                # 根据 mime_type 判断消息类型
                mime = (lib.mime_type or '').lower()
                if mime.startswith('image/'):
                    msg_type = 'image'
                elif mime.startswith('video/'):
                    msg_type = 'video'
                else:
                    msg_type = 'file'

                msg = ChatMessage(
                    conversation_id=conv_id,
                    sender_id=sender_id,
                    content=None,
                    message_type=msg_type,
                    file_url=f'fm:{ref.id}',
                    file_name=ref.display_name,
                    file_size=lib.file_size,
                    source_language=detect_language(ref.display_name),
                )
                db.session.add(msg)

            # 如果有留言，追加一条文本消息
            if note and note.strip():
                note_msg = ChatMessage(
                    conversation_id=conv_id,
                    sender_id=sender_id,
                    content=note.strip(),
                    source_language=detect_language(note),
                )
                db.session.add(note_msg)

            # 更新目标对话 updated_at 和发送者 last_read_at
            conv = ChatConversation.query.get(conv_id)
            if conv:
                conv.updated_at = datetime.now(timezone.utc)
            participant.last_read_at = datetime.now(timezone.utc)

            shared_ids.append(conv_id)

        db.session.commit()

        logger.info(
            f"用户 {sender_id} 分享 {len(file_refs_with_libs)} 个文件到 {len(shared_ids)} 个对话: {shared_ids}"
        )

        return {
            'success': True,
            'data': {
                'shared_count': len(shared_ids),
                'conversation_ids': shared_ids,
            },
            'message': f'成功分享到 {len(shared_ids)} 个对话',
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"分享文件到对话失败: {e}", exc_info=True)
        return {'success': False, 'message': f'分享文件失败: {str(e)}'}


# ---------------------------------------------------------------------------
# 15. 发送卡片消息
# ---------------------------------------------------------------------------

def send_card_message(conversation_id, sender_id, message_type, card_data):
    """
    发送业务实体卡片消息。

    Args:
        conversation_id: 对话 ID
        sender_id: 发送者 ID
        message_type: 'customer_card' 或 'project_card'
        card_data: dict, 卡片数据（将序列化为 JSON 存入 content）

    Returns:
        dict: {'success': True, 'data': {...}}
    """
    import json

    try:
        # 验证参与者身份
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id,
            user_id=sender_id,
        ).first()
        if not participant:
            return {'success': False, 'message': '您不是该对话的参与者'}

        # 创建卡片消息
        message = ChatMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=json.dumps(card_data, ensure_ascii=False),
            message_type=message_type,
            source_language='zh',
        )
        db.session.add(message)

        # 更新对话时间戳 + 已读时间
        conv = ChatConversation.query.get(conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
        participant.last_read_at = datetime.now(timezone.utc)

        db.session.commit()

        # 返回消息数据
        sender = User.query.get(sender_id)
        return {
            'success': True,
            'data': {
                'id': message.id,
                'conversation_id': conversation_id,
                'sender_id': sender_id,
                'sender_name': (sender.real_name or sender.username) if sender else None,
                'content': message.content,
                'message_type': message_type,
                'created_at': _utc_iso(message.created_at),
            },
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"发送卡片消息失败: {e}", exc_info=True)
        return {'success': False, 'message': f'发送卡片消息失败: {str(e)}'}
