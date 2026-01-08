#!/usr/bin/env python3
"""
解决方案经理站内消息通知助手函数
"""

from app.models.user import User
import logging

logger = logging.getLogger(__name__)


def send_quotation_internal_message(quotation, sender_id, action_type='created'):
    """
    发送报价单相关的站内消息给解决方案经理

    Args:
        quotation: Quotation 对象
        sender_id: 发送者用户ID（当前操作用户）
        action_type: 'created' 或 'updated'

    Returns:
        int: 成功发送的消息数量
    """
    from app.extensions import db
    from app.models.message import Message

    try:
        # 查找需要通知的解决方案经理
        # 注意：is_active 是 property，实际数据库列是 _is_active
        solution_managers = User.query.filter(
            User.role.in_(['solution_manager', 'solution']),
            User._is_active == True,
            User.id != sender_id  # 不通知自己
        ).all()

        # 获取发送者信息
        sender = User.query.get(sender_id)
        sender_company = sender.company_name if sender else None

        # 筛选：厂商的解决方案经理 或 同公司的解决方案经理
        recipients = []
        for sm in solution_managers:
            # 厂商的解决方案经理
            if sm.is_vendor_user():
                recipients.append(sm)
            # 同公司的解决方案经理
            elif sender_company and sm.company_name == sender_company:
                recipients.append(sm)

        # 去重并发送消息
        recipient_ids = list(set(sm.id for sm in recipients))

        if not recipient_ids:
            logger.info("没有符合条件的解决方案经理需要通知")
            return 0

        # 选择对应的消息创建方法
        create_method = (Message.create_quotation_created
                        if action_type == 'created'
                        else Message.create_quotation_updated)

        for recipient_id in recipient_ids:
            msg = create_method(
                sender_id=sender_id,
                recipient_id=recipient_id,
                quotation=quotation
            )
            db.session.add(msg)

        db.session.commit()
        logger.info(f"报价单{action_type}消息已发送给 {len(recipient_ids)} 位解决方案经理")
        return len(recipient_ids)

    except Exception as e:
        logger.error(f"发送报价单站内消息失败: {str(e)}")
        return 0
