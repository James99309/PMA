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
        User.is_active == True,
    ).first()

    if not user:
        return {'success': False, 'message': f'未找到用户: {recipient_email}'}

    try:
        conv = get_or_create_cross_system_conversation(user.id, source_label)

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


def push_message_to_peer(recipient_email, sender_name, content, msg_type='chat'):
    """
    异步推送消息到对等端（SG → CN）。

    在后台线程中执行，不阻塞发送者操作。

    Args:
        recipient_email: 接收者邮箱
        sender_name: 发送者显示名称
        content: 消息文本
        msg_type: 'chat' 或 'task'
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
                },
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                timeout=15,
            )
            if resp.status_code == 200:
                logger.info(f"跨系统推送成功: {recipient_email}, type={msg_type}")
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
