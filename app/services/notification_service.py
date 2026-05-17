# -*- coding: utf-8 -*-
"""站内通知统一服务(鉴权无关)

历史上各视图内联手搓 `Message(...)`,web 与 mobile 行为易漂移。
本服务集中创建/入库 Message,web 路由与 mobile 端点都调它,
不再各处 new Message。失败只 log、不抛(与原 web 行为一致:通知失败
不应阻断主流程)。

注意:本服务只 add 到 session,**不 commit**——由调用的业务 service
在其事务里统一 commit,保证通知与主数据原子一致。
"""
import logging
import threading
from app import db

logger = logging.getLogger(__name__)


def _push(recipient_id, title, body, task_id=None):
    """站外 APNS 推送 — fire-and-forget,后台线程(仿 chat),不阻塞/不依赖
    事务提交。失败只 log。站内已读态由 Message.is_read 管,推送只负责叮一下。"""
    if not recipient_id:
        return
    try:
        from flask import current_app
        app = current_app._get_current_object()
    except Exception:
        return

    def _w():
        with app.app_context():
            try:
                from app.services.apns_service import send_push
                send_push(
                    user_ids=[recipient_id],
                    title=(title or '')[:80] or '任务通知',
                    body=(body or '')[:120],
                    data={'type': 'task', 'task_id': task_id} if task_id else None,
                )
            except Exception as e:
                logger.warning(f"task push 失败: {e}")
    try:
        threading.Thread(target=_w, daemon=True).start()
    except Exception as e:
        logger.warning(f"task push 线程启动失败: {e}")


def notify_task_assigned(actor_id, recipient_id, task):
    """任务指派/进入审核 → 通知接收人(站内 Message + 站外推送)。"""
    if not recipient_id or recipient_id == actor_id:
        return
    try:
        from app.models.message import Message
        msg = Message.create_task_assigned(
            sender_id=actor_id, recipient_id=recipient_id, task=task)
        db.session.add(msg)
        _push(recipient_id, msg.title, msg.content, getattr(task, 'id', None))
    except Exception as e:
        logger.warning(f"notify_task_assigned 失败: {e}")


def notify_task_completed(actor_id, recipient_id, task):
    """任务完成/审核结果 → 通知接收人(站内 Message + 站外推送)。"""
    if not recipient_id or recipient_id == actor_id:
        return
    try:
        from app.models.message import Message
        msg = Message.create_task_completed(
            sender_id=actor_id, recipient_id=recipient_id, task=task)
        db.session.add(msg)
        _push(recipient_id, msg.title, msg.content, getattr(task, 'id', None))
    except Exception as e:
        logger.warning(f"notify_task_completed 失败: {e}")


def notify_task_custom(actor_id, recipient_id, title, content,
                       obj_id, message_type='task_notification'):
    """自定义任务通知(如暂停)。原 web 在 pause 里内联 Message(...)。"""
    if not recipient_id:
        return
    try:
        from app.models.message import Message
        db.session.add(Message(
            sender_id=actor_id,
            recipient_id=recipient_id,
            message_type=message_type,
            title=title,
            content=content,
            related_object_type='task',
            related_object_id=obj_id,
        ))
    except Exception as e:
        logger.warning(f"notify_task_custom 失败: {e}")
