# -*- coding: utf-8 -*-
"""
审批站内消息通知服务
提供审批流程的站内消息通知功能

推送策略：
- 审批人通知：不发送（审批人通过待审批列表查看）
- 审批结果通知：发送给提交人（审批通过/拒绝）
- 抄送通知：按配置发送（cc_enabled + cc_users）
"""

from flask import current_app
from app import db
from app.models.user import User
from app.models.message import Message
import logging

logger = logging.getLogger(__name__)


class ApprovalMessageService:
    """审批站内消息服务类"""

    @staticmethod
    def send_approval_notification(instance, step, action=None, comment=None,
                                   custom_context=None, notify_submitter=False,
                                   actual_approver=None):
        """
        发送审批站内消息通知

        接口与原 ApprovalEmailService.send_approval_notification 保持一致，便于替换

        Args:
            instance: 审批实例
            step: 当前审批步骤（字典格式，来自模板快照）
            action: 审批动作 ('approve', 'reject', None表示待审批)
            comment: 审批意见
            custom_context: 自定义上下文数据，用于不同业务模块的特殊信息
            notify_submitter: 是否发送给提交人（默认False，发送给审批人）
            actual_approver: 动态计算的审批人对象（优先使用，None时从快照读取）

        Returns:
            bool: 是否发送成功
        """
        try:
            sender_id = instance.created_by

            # 根据 notify_submitter 决定推送策略
            if notify_submitter:
                # 发送给提交人（审批结果通知：通过/拒绝）
                submitter = User.query.get(instance.created_by)
                if not submitter:
                    logger.warning(f"提交人不存在: instance_id={instance.id}")
                    return False

                success = ApprovalMessageService._send_single_notification(
                    sender_id, submitter.id, instance, action, comment, custom_context
                )
                return success
            else:
                # 审批人通知已取消，审批人通过待审批列表查看
                # 只处理抄送
                cc_enabled = step.get('cc_enabled') if isinstance(step, dict) else getattr(step, 'cc_enabled', False)
                cc_users = step.get('cc_users') if isinstance(step, dict) else getattr(step, 'cc_users', None)
                if cc_enabled and cc_users:
                    logger.info(f"处理抄送，抄送人数: {len(cc_users) if isinstance(cc_users, list) else 0}")
                    ApprovalMessageService._handle_cc_notifications(
                        sender_id, instance, action, comment, custom_context, cc_users
                    )
                return True

        except Exception as e:
            logger.error(f"发送审批通知消息失败: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _send_single_notification(sender_id, recipient_id, instance, action, comment, custom_context):
        """
        发送单个通知消息

        Args:
            sender_id: 发送者用户ID
            recipient_id: 收件人用户ID
            instance: 审批实例
            action: 审批动作
            comment: 审批意见
            custom_context: 自定义上下文

        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建消息
            msg = Message.create_approval_notification(
                sender_id=sender_id,
                recipient_id=recipient_id,
                instance=instance,
                action=action,
                comment=comment,
                custom_context=custom_context,
                is_cc=False
            )

            db.session.add(msg)
            # 不在这里commit，由调用者统一提交

            recipient = User.query.get(recipient_id)
            recipient_name = recipient.real_name or recipient.username if recipient else recipient_id
            logger.info(f"审批通知消息已创建: 收件人={recipient_name}, instance_id={instance.id}")

            return True

        except Exception as e:
            logger.error(f"发送单个通知消息失败: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _handle_cc_notifications(sender_id, instance, action, comment, custom_context, cc_users):
        """
        处理抄送通知

        Args:
            sender_id: 发送者用户ID
            instance: 审批实例
            action: 审批动作
            comment: 审批意见
            custom_context: 自定义上下文
            cc_users: 抄送用户ID列表
        """
        try:
            cc_user_ids = cc_users if isinstance(cc_users, list) else []

            for user_id in cc_user_ids:
                cc_user = User.query.get(user_id)
                if cc_user:
                    # 创建抄送消息
                    msg = Message.create_approval_notification(
                        sender_id=sender_id,
                        recipient_id=user_id,
                        instance=instance,
                        action=action,
                        comment=comment,
                        custom_context=custom_context,
                        is_cc=True
                    )
                    db.session.add(msg)
                    logger.info(f"审批抄送消息已创建: 收件人={cc_user.real_name or cc_user.username}")

        except Exception as e:
            logger.error(f"处理抄送通知失败: {str(e)}", exc_info=True)
