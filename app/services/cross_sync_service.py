# -*- coding: utf-8 -*-
"""
跨系统聊天消息同步服务

SG NAS → CN NAS 单向推送：
- SG 上的聊天消息/任务分配 → 推送到 CN 同邮箱用户的只读对话
- 通信走 Tailscale 内网
- CN 端接收后自动创建 "来自新加坡 PMA 的消息" 对话
"""
import json
import logging
import os
import threading
from datetime import datetime, timezone

from app import db
from app.models.chat import ChatConversation, ChatParticipant, ChatMessage, ChatTranslation
from app.models.user import User

logger = logging.getLogger(__name__)

# 默认对话名称
DEFAULT_SOURCE_LABEL = '新加坡 PMA'
CROSS_CONV_NAME_TEMPLATE = '来自{}的消息'


def is_cross_sync_enabled():
    """检查跨系统同步是否启用（发送端需要配置）"""
    return (
        os.environ.get('CROSS_SYNC_ENABLED', '').lower() == 'true'
        and os.environ.get('CROSS_SYNC_PEER_URL')
        and os.environ.get('CROSS_SYNC_API_KEY')
    )


def get_or_create_cross_system_conversation(user_id, source_label=None):
    """
    获取或创建跨系统对话。

    每个接收用户对每个来源有一个唯一的跨系统对话。

    Args:
        user_id: 接收者用户 ID
        source_label: 来源标签，如 '新加坡 PMA'

    Returns:
        ChatConversation 实例
    """
    label = source_label or DEFAULT_SOURCE_LABEL
    conv_name = CROSS_CONV_NAME_TEMPLATE.format(label)

    # 查找已有的跨系统对话
    existing = (
        ChatConversation.query
        .join(ChatParticipant, ChatParticipant.conversation_id == ChatConversation.id)
        .filter(
            ChatConversation.type == 'cross_system',
            ChatConversation.name == conv_name,
            ChatConversation.is_deleted == False,
            ChatParticipant.user_id == user_id,
        )
        .first()
    )
    if existing:
        return existing

    # 创建新的跨系统对话
    conv = ChatConversation(
        type='cross_system',
        name=conv_name,
        created_by=user_id,
    )
    db.session.add(conv)
    db.session.flush()

    participant = ChatParticipant(
        conversation_id=conv.id,
        user_id=user_id,
        role='member',
        last_read_at=datetime.now(timezone.utc),
    )
    db.session.add(participant)
    db.session.flush()

    logger.info(f"创建跨系统对话: conv_id={conv.id}, user_id={user_id}, name={conv_name}")
    return conv


def receive_message_from_peer(data):
    """
    接收来自对等端的推送消息（CN 端接收 SG 推送）。

    Args:
        data: dict with keys:
            - recipient_email: 接收者邮箱
            - sender_name: 发送者显示名称
            - content: 消息文本
            - msg_type: 'chat' 或 'task'
            - source_label: 来源标签（可选）

    Returns:
        dict: {'success': True/False, 'message': ...}
    """
    recipient_email = data.get('recipient_email', '').strip().lower()
    sender_name = data.get('sender_name', '未知用户')
    content = data.get('content', '')
    msg_type = data.get('msg_type', 'chat')
    source_label = data.get('source_label', DEFAULT_SOURCE_LABEL)
    source_lang = data.get('source_lang', 'en')

    if not recipient_email or not content:
        return {'success': False, 'message': '缺少必要字段: recipient_email, content'}

    # 按邮箱查找本地用户（排除 admin 和未激活用户）
    user = User.query.filter(
        db.func.lower(User.email) == recipient_email,
        User.username != 'admin',
        User._is_active == True,
    ).first()

    if not user:
        return {'success': False, 'message': f'未找到用户: {recipient_email}'}

    try:
        conv = get_or_create_cross_system_conversation(user.id, source_label)

        # 存储 sender_email 到 sync_metadata（仅首次写入）
        sender_email_in = data.get('sender_email', '').strip()
        if sender_email_in:
            metadata = json.loads(conv.sync_metadata or '{}')
            if 'peer_sender_email' not in metadata:
                metadata['peer_sender_email'] = sender_email_in
                conv.sync_metadata = json.dumps(metadata, ensure_ascii=False)

        # 构建 JSON 内容
        msg_content = json.dumps({
            'sender_name': sender_name,
            'text': content,
            'msg_type': msg_type,
        }, ensure_ascii=False)

        message = ChatMessage(
            conversation_id=conv.id,
            sender_id=None,  # 跨系统消息无本地发送者
            content=msg_content,
            message_type='cross_system',
            source_language=source_lang,
        )
        db.session.add(message)

        # 更新对话时间戳
        conv.updated_at = datetime.now(timezone.utc)
        db.session.flush()  # 获取 message.id，暂不提交（避免翻译前消息可见）

        # 翻译原始文本（在 commit 前加入 session，确保消息+翻译原子可见）
        _add_cross_system_translation(message.id, content, source_lang)

        db.session.commit()

        logger.info(
            f"跨系统消息接收成功: conv_id={conv.id}, recipient={recipient_email}, "
            f"sender={sender_name}, type={msg_type}"
        )

        return {'success': True, 'message': '消息接收成功'}

    except Exception as e:
        db.session.rollback()
        logger.error(f"接收跨系统消息失败: {e}", exc_info=True)
        return {'success': False, 'message': f'接收失败: {str(e)}'}


def receive_private_reply_from_peer(data):
    """接收 CN 私聊回复，注入到 SG 原有私聊对话"""
    sender_email = data.get('sender_email', '').strip().lower()
    recipient_email = data.get('recipient_email', '').strip().lower()
    content = data.get('content', '')

    if not sender_email or not recipient_email or not content:
        return {'success': False, 'message': '缺少必要字段: sender_email, recipient_email, content'}

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
        db.session.flush()  # 获取 message.id，不提交

        # 翻译（SG=en 时翻译 zh→en），commit 前加入 session
        _add_cross_system_translation(message.id, content, 'zh')

        db.session.commit()

        logger.info(f"私聊回复注入成功: conv_id={conv.id}, sender={sender_email}")

        return {'success': True, 'message': '回复注入成功'}
    except Exception as e:
        db.session.rollback()
        logger.error(f"私聊回复注入失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


def push_message_to_peer(recipient_email, sender_name, content, msg_type='chat', sender_email=None, reply_mode=False, source_lang='en'):
    """
    异步推送消息到对等端（SG → CN）。

    在后台线程中执行，不阻塞发送者操作。

    Args:
        recipient_email: 接收者邮箱
        sender_name: 发送者显示名称
        content: 消息文本
        msg_type: 'chat' 或 'task' 或 'reply'
        sender_email: 发送者邮箱（用于对端回复路由）
        reply_mode: True 表示这是一条私聊回复（对端注入到原私聊对话）
    """
    if not is_cross_sync_enabled():
        return

    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    source_label = os.environ.get('CROSS_SYNC_SELF_LABEL', DEFAULT_SOURCE_LABEL)

    def _do_push():
        import requests
        try:
            resp = requests.post(
                f'{peer_url}/cross-sync/push',
                json={
                    'recipient_email': recipient_email,
                    'sender_name': sender_name,
                    'content': content,
                    'msg_type': msg_type,
                    'source_label': source_label,
                    'sender_email': sender_email or '',
                    'reply_mode': reply_mode,
                    'source_lang': source_lang,
                },
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                timeout=15,
            )
            if resp.status_code == 200:
                logger.info(f"跨系统推送成功: {recipient_email}, type={msg_type}, reply_mode={reply_mode}")
            else:
                logger.warning(f"跨系统推送失败: status={resp.status_code}, body={resp.text[:200]}")
        except Exception as e:
            logger.warning(f"跨系统推送异常: {e}")

    thread = threading.Thread(target=_do_push, daemon=True)
    thread.start()


def push_group_to_peer(sg_group_id, group_name, sender_name, sender_email, content, recipient_emails):
    """异步推送 SG 群消息到 CN（触发 CN 创建/更新镜像群）"""
    if not is_cross_sync_enabled():
        return
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    if not peer_url:
        return

    # 检测实际文本语言，避免把中文消息标记为 'en'
    actual_source_lang = _detect_text_lang(content)

    def _do_push():
        import requests
        try:
            resp = requests.post(
                f'{peer_url}/cross-sync/push-group',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                json={
                    'sg_group_id': sg_group_id,
                    'group_name': group_name,
                    'sender_name': sender_name,
                    'sender_email': sender_email,
                    'content': content,
                    'recipient_emails': recipient_emails,
                    'source_lang': actual_source_lang,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info(f"群聊跨系统推送成功: sg_group_id={sg_group_id}")
            else:
                logger.warning(f"群聊跨系统推送失败: status={resp.status_code}, body={resp.text[:200]}")
        except Exception as e:
            logger.warning(f"群聊跨系统推送异常: {e}")

    threading.Thread(target=_do_push, daemon=True).start()


def push_group_reply_to_peer(sg_group_id, sender_email, sender_name, content):
    """异步推送 CN 镜像群回复到 SG 原群"""
    if not is_cross_sync_enabled():
        return
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    if not peer_url:
        return

    def _do_push():
        import requests
        try:
            resp = requests.post(
                f'{peer_url}/cross-sync/push-group',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                json={
                    'sg_group_id': sg_group_id,
                    'sender_email': sender_email,
                    'sender_name': sender_name,
                    'content': content,
                    'reply_mode': True,
                },
                timeout=10,
            )
            if resp.status_code != 200:
                logger.warning(f"群聊回复推送失败: status={resp.status_code}, body={resp.text[:200]}")
        except Exception as e:
            logger.warning(f"群聊回复推送异常: {e}")

    threading.Thread(target=_do_push, daemon=True).start()


def receive_group_message_from_peer(data):
    """接收 SG 群消息，在 CN 创建/更新镜像群并写入消息"""
    sg_group_id = data.get('sg_group_id')
    group_name = data.get('group_name', '群聊')
    sender_name = data.get('sender_name', '未知 [SG]')
    content = data.get('content', '')
    recipient_emails = [e.lower() for e in data.get('recipient_emails', [])]
    source_lang = data.get('source_lang', 'en')

    if not sg_group_id or not content or not recipient_emails:
        return {'success': False, 'message': '缺少必要字段: sg_group_id, content, recipient_emails'}

    local_users = User.query.filter(
        db.func.lower(User.email).in_(recipient_emails),
        User._is_active == True,
    ).all()

    if not local_users:
        return {'success': False, 'message': f'CN 无对应用户: {recipient_emails}'}

    try:
        # 查找现有镜像群
        mirror_conv = None
        candidates = ChatConversation.query.filter(
            ChatConversation.type == 'cross_system_group',
            ChatConversation.is_deleted == False,
            ChatConversation.sync_metadata.isnot(None),
        ).all()
        for c in candidates:
            meta = json.loads(c.sync_metadata or '{}')
            if meta.get('peer_group_id') == sg_group_id:
                mirror_conv = c
                break

        # 首次：创建镜像群
        if not mirror_conv:
            mirror_conv = ChatConversation(
                type='cross_system_group',
                name=f'{group_name} · SG PMA',
                created_by=local_users[0].id,
                sync_metadata=json.dumps({'peer_group_id': sg_group_id}, ensure_ascii=False),
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

        # 写入消息
        msg_content = json.dumps({
            'sender_name': sender_name,
            'text': content,
            'msg_type': 'chat',
        }, ensure_ascii=False)

        message = ChatMessage(
            conversation_id=mirror_conv.id,
            sender_id=None,
            content=msg_content,
            message_type='cross_system',
            source_language=source_lang,
        )
        db.session.add(message)
        mirror_conv.updated_at = datetime.now(timezone.utc)
        db.session.flush()  # 获取 message.id，不提交

        # 翻译原始文本（commit 前加入 session）
        _add_cross_system_translation(message.id, content, source_lang)

        db.session.commit()

        logger.info(f"群聊消息写入成功: conv_id={mirror_conv.id}, sender={sender_name}")

        return {'success': True}

    except Exception as e:
        db.session.rollback()
        logger.error(f"接收群聊消息失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


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

    sender = User.query.filter(
        db.func.lower(User.email) == sender_email,
        User._is_active == True,
    ).first()

    try:
        if sender:
            message = ChatMessage(
                conversation_id=conv.id,
                sender_id=sender.id,
                content=content,
                message_type='text',
                source_language='zh',
            )
        else:
            message = ChatMessage(
                conversation_id=conv.id,
                sender_id=None,
                content=json.dumps({'sender_name': f'{sender_name} [CN]', 'text': content}, ensure_ascii=False),
                message_type='cross_system',
                source_language='zh',
            )
        db.session.add(message)
        conv.updated_at = datetime.now(timezone.utc)
        db.session.flush()  # 获取 message.id，不提交

        # 翻译（SG=en 时翻译 zh→en），commit 前加入 session
        _add_cross_system_translation(message.id, content, 'zh')

        db.session.commit()

        logger.info(f"群聊回复注入成功: conv_id={sg_group_id}, sender={sender_email}")

        return {'success': True}
    except Exception as e:
        db.session.rollback()
        logger.error(f"群聊回复注入失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


def _get_system_lang():
    """根据 PMA_DB_TYPE 返回本系统语言（sp8d → zh，ovs → en）"""
    db_type = os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', '')
    return 'en' if db_type == 'ovs' else 'zh'


def _detect_text_lang(text):
    """简单语言检测：含 CJK 字符返回 'zh'，否则 'en'。"""
    if not text:
        return 'en'
    for ch in text:
        if '一' <= ch <= '鿿':
            return 'zh'
    return 'en'


def _add_cross_system_translation(message_id, original_text, source_lang):
    """为跨系统消息添加翻译到 session（不 commit，由调用方提交）。
    翻译规则：实际文本语言与本系统语言不同时才翻译（en→zh 或 zh→en）。
    调用方必须在此函数之前 flush() 以获取 message_id，之后再 commit()。
    """
    system_lang = _get_system_lang()
    # 以实际文本语言为准（忽略发送方可能传错的 source_lang）
    actual_lang = _detect_text_lang(original_text)
    if actual_lang == system_lang:
        return  # 文本已是本系统语言，无需翻译

    try:
        from app.services.chat_translation_service import translate_text
        translated = translate_text(original_text, actual_lang, system_lang)
        if translated:
            db.session.add(ChatTranslation(
                message_id=message_id,
                target_language=system_lang,
                translated_content=translated,
            ))
            logger.info(f"跨系统消息翻译完成: msg_id={message_id}, {actual_lang}→{system_lang}")
    except Exception as e:
        logger.warning(f"跨系统消息翻译失败: {e}")


def push_task_to_peer(assignee_email, creator_name, task_title, due_date_str=None):
    """
    推送任务分配通知到对等端。

    Args:
        assignee_email: 被指派人邮箱
        creator_name: 创建者名称
        task_title: 任务标题
        due_date_str: 截止日期字符串（可选）
    """
    due_info = f'，截止 {due_date_str}' if due_date_str else ''
    content = f'给你分配了任务「{task_title}」{due_info}'
    push_message_to_peer(assignee_email, creator_name, content, msg_type='task')


def fetch_peer_procurement_demands():
    """
    从对端 NAS 拉取待采购需求（同步调用，用于需求池聚合）。

    Returns:
        list: 需求列表，每项包含 order_number, product_name, remaining_to_procure 等
              失败时返回空列表
    """
    if not is_cross_sync_enabled():
        return []

    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')

    import requests
    try:
        resp = requests.get(
            f'{peer_url}/cross-sync/procurement-demands',
            headers={'X-API-Key': api_key},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get('demands', [])
        else:
            logger.warning(f"拉取对端需求失败: status={resp.status_code}")
            return []
    except Exception as e:
        logger.warning(f"拉取对端需求异常: {e}")
        return []


def notify_peer_refresh_cache():
    """通知对等端刷新物化视图缓存（CN 分类变更后调用，异步不阻塞）"""
    if not is_cross_sync_enabled():
        return

    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')

    def _do_refresh():
        import requests
        try:
            resp = requests.post(
                f'{peer_url}/cross-sync/refresh-cache',
                json={},
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                timeout=30,
            )
            if resp.status_code == 200:
                logger.info('通知对等端刷新缓存成功')
            else:
                logger.warning(f'通知对等端刷新缓存失败: status={resp.status_code}')
        except Exception as e:
            logger.warning(f'通知对等端刷新缓存异常: {e}')

    thread = threading.Thread(target=_do_refresh, daemon=True)
    thread.start()


def sync_display_order_to_peer(category_code, subcategory_code):
    """将指定子分类的产品排序数据推送到对等端（异步不阻塞）"""
    if not is_cross_sync_enabled():
        return

    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')

    from app.models.product_display_order import ProductDisplayOrder
    rows = ProductDisplayOrder.query.filter_by(
        category_code=category_code,
        subcategory_code=subcategory_code
    ).order_by(ProductDisplayOrder.model_order).all()

    payload = {
        'category_code': category_code,
        'subcategory_code': subcategory_code,
        'items': [r.to_dict() for r in rows]
    }

    def _do_sync():
        import requests
        try:
            resp = requests.post(
                f'{peer_url}/cross-sync/sync-display-order',
                json=payload,
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                timeout=30,
            )
            if resp.status_code == 200:
                logger.info(f'产品排序同步成功: {category_code}{subcategory_code}')
            else:
                logger.warning(f'产品排序同步失败: status={resp.status_code}, body={resp.text[:200]}')
        except Exception as e:
            logger.warning(f'产品排序同步异常: {e}')

    thread = threading.Thread(target=_do_sync, daemon=True)
    thread.start()


# ═══ 跨实例「双真实账号」绑定 + KPI 合并:同步 GET 对端(2026-06-30)═══════════
def fetch_peer_users(q='', limit=50):
    """GET 对端真实账号列表(供 CN 绑定 UI 下拉)。失败返回 []。"""
    if not is_cross_sync_enabled():
        return []
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    import requests
    try:
        resp = requests.get(
            f'{peer_url}/cross-sync/list-users',
            params={'q': q or '', 'limit': limit},
            headers={'X-API-Key': api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            return (resp.json() or {}).get('data', []) or []
        logger.warning(f'fetch_peer_users 失败 status={resp.status_code} body={resp.text[:200]}')
    except Exception as e:
        logger.warning(f'fetch_peer_users 异常: {e}')
    return []


def fetch_peer_user(peer_id):
    """GET 对端单个真实账号(按 id)。用于绑定名快照缺失时自愈回填。
       返回 dict(id/username/name/role/...) 或 None。"""
    if not is_cross_sync_enabled() or not peer_id:
        return None
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    import requests
    try:
        resp = requests.get(
            f'{peer_url}/cross-sync/list-users',
            params={'id': peer_id, 'limit': 1},
            headers={'X-API-Key': api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            rows = (resp.json() or {}).get('data', []) or []
            # 防御:对端必须返回 id 精确匹配的那一条;若对端旧版忽略 id 参数(返回搜索结果),
            # 则 id 不匹配 → 丢弃,避免回填错误姓名。
            for r in rows:
                if str(r.get('id')) == str(peer_id):
                    return r
            return None
        logger.warning(f'fetch_peer_user 失败 status={resp.status_code} body={resp.text[:200]}')
    except Exception as e:
        logger.warning(f'fetch_peer_user 异常: {e}')
    return None


def fetch_peer_kpi_actuals(peer_user_id, start_iso, end_iso, metrics=None):
    """GET 对端某用户本期各 KPI 指标实际值(Phase 2 合并用)。
       返回完整 payload {self_system, self_currency, data:{code:{...}}} 或 None
       (对端不可达时,调用方降级为仅本地,不影响本端考核)。
       metrics: 可选 list[str],只取这些指标(减负载);None=全量。"""
    if not is_cross_sync_enabled() or not peer_user_id:
        return None
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL', '').rstrip('/')
    api_key = os.environ.get('CROSS_SYNC_API_KEY', '')
    import requests
    params = {'user_id': peer_user_id, 'start': start_iso, 'end': end_iso}
    if metrics:
        params['metrics'] = ','.join(metrics)
    try:
        resp = requests.get(
            f'{peer_url}/cross-sync/kpi-actuals',
            params=params,
            headers={'X-API-Key': api_key},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json() or None
        logger.warning(f'fetch_peer_kpi_actuals 失败 status={resp.status_code} body={resp.text[:200]}')
    except Exception as e:
        logger.warning(f'fetch_peer_kpi_actuals 异常: {e}')
    return None
