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
from app.models.chat import ChatConversation, ChatParticipant, ChatMessage
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
            source_language='zh',
        )
        db.session.add(message)

        # 更新对话时间戳
        conv.updated_at = datetime.now(timezone.utc)
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
        db.session.commit()

        logger.info(f"私聊回复注入成功: conv_id={conv.id}, sender={sender_email}")
        return {'success': True, 'message': '回复注入成功'}
    except Exception as e:
        db.session.rollback()
        logger.error(f"私聊回复注入失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


def push_message_to_peer(recipient_email, sender_name, content, msg_type='chat', sender_email=None, reply_mode=False):
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
