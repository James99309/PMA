# -*- coding: utf-8 -*-
"""
站内消息模型 - 用于存储日志@消息等站内通知

Message: 站内消息记录
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Index

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class Message(db.Model):
    """站内消息模型"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)

    # 消息类型: worklog_mention(日志@), approval_reminder(审批提醒) 等
    message_type = Column(String(50), nullable=False, index=True)

    # 发送者和接收者
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')

    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

    # 消息内容
    title = Column(String(200), nullable=False)      # 消息标题
    content = Column(Text)                           # 消息内容预览

    # 关联对象（如日志ID、项目ID等）
    related_object_type = Column(String(50))         # 'worklog', 'project', 'expense' 等
    related_object_id = Column(Integer)              # 关联对象ID

    # 元数据（存储额外信息，如日志日期等）
    # 注意：不能使用 metadata 作为字段名，因为它是 SQLAlchemy 的保留字
    extra_data = Column('metadata', JSON, default=dict)

    # 状态
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime)

    # 系统字段
    created_at = Column(DateTime, default=get_local_time, index=True)

    # 索引：用于快速查询未读消息
    __table_args__ = (
        Index('ix_messages_recipient_unread', 'recipient_id', 'is_read'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'message_type': self.message_type,
            'sender_id': self.sender_id,
            'sender_name': self.sender.real_name or self.sender.username if self.sender else None,
            'recipient_id': self.recipient_id,
            'title': self.title,
            'content': self.content,
            'related_object_type': self.related_object_type,
            'related_object_id': self.related_object_id,
            'metadata': self.extra_data or {},
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def get_unread_count(cls, user_id):
        """获取用户未读消息数量"""
        from datetime import timedelta
        expiry_cutoff = datetime.utcnow() - timedelta(days=3)

        return cls.query.filter(
            cls.recipient_id == user_id,
            cls.is_read == False,
            # 行程类通知3天过期，其他类型不过期
            db.or_(
                ~cls.message_type.like('workitem_%'),
                cls.created_at >= expiry_cutoff
            )
        ).count()

    @classmethod
    def get_unread_messages(cls, user_id, limit=50):
        """获取用户未读消息列表"""
        from datetime import timedelta
        expiry_cutoff = datetime.utcnow() - timedelta(days=3)

        return cls.query.filter(
            cls.recipient_id == user_id,
            cls.is_read == False,
            # 行程类通知3天过期，其他类型不过期
            db.or_(
                ~cls.message_type.like('workitem_%'),
                cls.created_at >= expiry_cutoff
            )
        ).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_all_messages(cls, user_id, limit=50):
        """获取用户所有消息列表（包括已读）"""
        return cls.query.filter(
            cls.recipient_id == user_id
        ).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def create_worklog_mention(cls, sender_id, recipient_id, worklog):
        """创建日志@消息

        Args:
            sender_id: 发送者用户ID（日志作者）
            recipient_id: 接收者用户ID（被@的用户）
            worklog: WorkLog 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        # 截取内容预览（最多100字符）
        content_preview = ''
        if worklog.additional_notes:
            # 移除 mention 标记，只保留纯文本预览
            import re
            clean_text = re.sub(r'[@#%]\[([^\]|]+)\|[^\]]+\]', r'\1', worklog.additional_notes)
            content_preview = clean_text[:100] + ('...' if len(clean_text) > 100 else '')

        return cls(
            message_type='worklog_mention',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 在日志中@了你',
            content=content_preview,
            related_object_type='worklog',
            related_object_id=worklog.id,
            extra_data={
                'log_date': worklog.log_date.isoformat() if worklog.log_date else None,
                'log_type': worklog.log_type,
                'owner_id': worklog.owner_id  # 日志所有者ID
            }
        )

    @classmethod
    def mark_as_read(cls, message_ids, user_id):
        """批量标记消息为已读

        Args:
            message_ids: 消息ID列表，为空则标记所有未读消息
            user_id: 用户ID
        """
        now = get_local_time()

        if not message_ids:
            # 标记所有未读消息为已读
            cls.query.filter(
                cls.recipient_id == user_id,
                cls.is_read == False
            ).update({
                'is_read': True,
                'read_at': now
            })
        else:
            # 标记指定消息为已读
            cls.query.filter(
                cls.id.in_(message_ids),
                cls.recipient_id == user_id
            ).update({
                'is_read': True,
                'read_at': now
            }, synchronize_session=False)

        db.session.commit()

    @classmethod
    def create_meeting_invite(cls, sender_id, recipient_id, recording):
        """会议旁听邀请通知

        Args:
            sender_id: 发起录音的人
            recipient_id: 被邀请旁听的人
            recording: MeetingRecording 对象
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        return cls(
            message_type='meeting_invite',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 邀请你旁听会议',
            content=(recording.title or '')[:100],
            related_object_type='meeting_recording',
            related_object_id=recording.id,
            extra_data={
                'meeting_time': recording.meeting_time.isoformat() if recording.meeting_time else None,
            }
        )

    @classmethod
    def create_workitem_shared(cls, sender_id, recipient_id, work_item):
        """创建行程共享通知

        Args:
            sender_id: 发送者用户ID（行程创建者）
            recipient_id: 接收者用户ID（被共享的用户）
            work_item: WorkItem 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        # 内容预览：行程标题
        content_preview = work_item.title[:100] if work_item.title else ''

        return cls(
            message_type='workitem_shared',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 与你共享了行程',
            content=content_preview,
            related_object_type='workitem',
            related_object_id=work_item.id,
            extra_data={
                'planned_date': work_item.planned_date.isoformat() if work_item.planned_date else None,
                'work_type': work_item.work_type
            }
        )

    @classmethod
    def create_workitem_cancelled(cls, sender_id, recipient_id, work_item):
        """创建行程取消通知

        Args:
            sender_id: 发送者用户ID（行程创建者）
            recipient_id: 接收者用户ID（被共享的用户）
            work_item: WorkItem 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = work_item.title[:100] if work_item.title else ''

        return cls(
            message_type='workitem_cancelled',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 取消了行程',
            content=content_preview,
            related_object_type='workitem',
            related_object_id=work_item.id,
            extra_data={
                'planned_date': work_item.planned_date.isoformat() if work_item.planned_date else None,
                'work_type': work_item.work_type
            }
        )

    @classmethod
    def create_workitem_completed(cls, sender_id, recipient_id, work_item):
        """创建行程完成通知

        Args:
            sender_id: 发送者用户ID（行程创建者）
            recipient_id: 接收者用户ID（被共享的用户）
            work_item: WorkItem 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = work_item.title[:100] if work_item.title else ''

        return cls(
            message_type='workitem_completed',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 完成了行程',
            content=content_preview,
            related_object_type='workitem',
            related_object_id=work_item.id,
            extra_data={
                'planned_date': work_item.planned_date.isoformat() if work_item.planned_date else None,
                'work_type': work_item.work_type
            }
        )

    @classmethod
    def create_workitem_time_changed(cls, sender_id, recipient_id, work_item, old_date, new_date):
        """创建行程时间变更通知

        Args:
            sender_id: 发送者用户ID（行程创建者）
            recipient_id: 接收者用户ID（被共享的用户）
            work_item: WorkItem 对象
            old_date: 原日期
            new_date: 新日期

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = work_item.title[:100] if work_item.title else ''

        return cls(
            message_type='workitem_time_changed',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 修改了行程时间',
            content=content_preview,
            related_object_type='workitem',
            related_object_id=work_item.id,
            extra_data={
                'planned_date': new_date.isoformat() if new_date else None,
                'old_date': old_date.isoformat() if old_date else None,
                'work_type': work_item.work_type
            }
        )

    @classmethod
    def create_workitem_unshared(cls, sender_id, recipient_id, work_item):
        """创建行程取消共享通知（被移除）

        Args:
            sender_id: 发送者用户ID（行程创建者）
            recipient_id: 接收者用户ID（被移除的用户）
            work_item: WorkItem 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = work_item.title[:100] if work_item.title else ''

        return cls(
            message_type='workitem_unshared',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 将你从行程中移除',
            content=content_preview,
            related_object_type='workitem',
            related_object_id=work_item.id,
            extra_data={
                'planned_date': work_item.planned_date.isoformat() if work_item.planned_date else None,
                'work_type': work_item.work_type
            }
        )

    @classmethod
    def create_workitem_invalidated(cls, sender_id, recipient_id, work_item):
        """创建行程作废通知

        Args:
            sender_id: 发送者用户ID（行程创建者）
            recipient_id: 接收者用户ID（被共享的用户）
            work_item: WorkItem 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = work_item.title[:100] if work_item.title else ''

        return cls(
            message_type='workitem_invalidated',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 作废了行程',
            content=content_preview,
            related_object_type='workitem',
            related_object_id=work_item.id,
            extra_data={
                'planned_date': work_item.planned_date.isoformat() if work_item.planned_date else None,
                'work_type': work_item.work_type
            }
        )

    @classmethod
    def create_worklog_submitted(cls, sender_id, recipient_id, worklog):
        """创建日志提交通知

        Args:
            sender_id: 发送者用户ID（日志作者）
            recipient_id: 接收者用户ID（领导）
            worklog: WorkLog 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        # 截取内容预览
        content_preview = ''
        if worklog.additional_notes:
            import re
            clean_text = re.sub(r'[@#%]\[([^\]|]+)\|[^\]]+\]', r'\1', worklog.additional_notes)
            content_preview = clean_text[:100] + ('...' if len(clean_text) > 100 else '')

        return cls(
            message_type='worklog_submitted',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 提交了工作日志',
            content=content_preview,
            related_object_type='worklog',
            related_object_id=worklog.id,
            extra_data={
                'log_date': worklog.log_date.isoformat() if worklog.log_date else None,
                'log_type': worklog.log_type,
                'owner_id': worklog.owner_id  # 日志所有者ID
            }
        )

    # ========== 审批通知相关方法 ==========

    @classmethod
    def create_approval_notification(cls, sender_id, recipient_id, instance, action=None,
                                     comment=None, custom_context=None, is_cc=False):
        """创建审批通知消息

        Args:
            sender_id: 发送者用户ID（提交人或审批人）
            recipient_id: 接收者用户ID（审批人或提交人）
            instance: ApprovalInstance 审批实例
            action: 审批动作 ('approve', 'reject', None表示待审批)
            comment: 审批意见
            custom_context: 自定义上下文（业务编号、金额等）
            is_cc: 是否为抄送消息

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '系统'

        # 获取动作文本
        action_value = action.value if hasattr(action, 'value') else action
        action_map = {
            'approve': '已通过',
            'reject': '已拒绝',
            'recall': '已召回',
            None: '待审批'
        }
        action_text = action_map.get(action_value, '处理中')

        # 获取对象类型中文名
        object_map = {
            'quotation': '报价单',
            'order': '订单',
            'project': '项目',
            'expense': '报销单',
            'pricing_order': '批价单',
            'settlement_order': '结算单',
        }
        object_name = object_map.get(instance.object_type, instance.object_type)

        # 获取业务编号
        if custom_context and 'business_number' in custom_context:
            object_identifier = custom_context['business_number']
        else:
            object_identifier = f"#{instance.object_id}"

        # 确定消息类型
        if is_cc:
            message_type = 'approval_cc'
            title = f'[抄送] {object_name} {object_identifier} {action_text}'
        elif action_value == 'approve':
            message_type = 'approval_approved'
            title = f'{object_name} {object_identifier} 审批已通过'
        elif action_value == 'reject':
            message_type = 'approval_rejected'
            title = f'{object_name} {object_identifier} 审批被拒绝'
        else:
            message_type = 'approval_pending'
            title = f'{object_name} {object_identifier} 待您审批'

        # 构建内容预览
        content_parts = []
        if custom_context:
            if custom_context.get('object_title'):
                content_parts.append(f"主题: {custom_context['object_title']}")
            if custom_context.get('total_amount'):
                content_parts.append(f"金额: {custom_context['total_amount']}")
        if comment:
            content_parts.append(f"意见: {comment[:50]}{'...' if len(comment) > 50 else ''}")
        content_preview = ' | '.join(content_parts) if content_parts else f"由 {sender_name} 提交"

        return cls(
            message_type=message_type,
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=title,
            content=content_preview,
            related_object_type=instance.object_type,
            related_object_id=instance.object_id,
            extra_data={
                'instance_id': instance.id,
                'action': action_value,
                'business_number': custom_context.get('business_number') if custom_context else None,
                'object_title': custom_context.get('object_title') if custom_context else None,
                'is_cc': is_cc
            }
        )

    # ========== 报价单通知相关方法 ==========

    @classmethod
    def create_quotation_created(cls, sender_id, recipient_id, quotation):
        """创建报价单新建通知消息

        Args:
            sender_id: 发送者用户ID（报价单创建人）
            recipient_id: 接收者用户ID（解决方案经理）
            quotation: Quotation 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        # 获取项目名称
        project_name = quotation.project.project_name if quotation.project else '未知项目'

        # 格式化金额
        amount_str = f"{quotation.amount:,.2f}" if quotation.amount else '0.00'

        return cls(
            message_type='quotation_created',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 创建了报价单 {quotation.quotation_number}',
            content=f'项目: {project_name}，金额: {amount_str}',
            related_object_type='quotation',
            related_object_id=quotation.id,
            extra_data={
                'quotation_number': quotation.quotation_number,
                'project_id': quotation.project_id,
                'project_name': project_name,
                'amount': float(quotation.amount) if quotation.amount else 0
            }
        )

    @classmethod
    def create_quotation_updated(cls, sender_id, recipient_id, quotation):
        """创建报价单修改通知消息

        Args:
            sender_id: 发送者用户ID（报价单修改人）
            recipient_id: 接收者用户ID（解决方案经理）
            quotation: Quotation 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        # 获取项目名称
        project_name = quotation.project.project_name if quotation.project else '未知项目'

        # 格式化金额
        amount_str = f"{quotation.amount:,.2f}" if quotation.amount else '0.00'

        return cls(
            message_type='quotation_updated',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 修改了报价单 {quotation.quotation_number}',
            content=f'项目: {project_name}，金额: {amount_str}',
            related_object_type='quotation',
            related_object_id=quotation.id,
            extra_data={
                'quotation_number': quotation.quotation_number,
                'project_id': quotation.project_id,
                'project_name': project_name,
                'amount': float(quotation.amount) if quotation.amount else 0
            }
        )

    # ========== 产品确认任务通知相关方法 ==========

    @classmethod
    def create_confirmation_request(cls, sender_id, recipient_id, quotation, message_text=None):
        """创建产品确认请求通知

        Args:
            sender_id: 发送者用户ID（销售/发起人）
            recipient_id: 接收者用户ID（PM/SE）
            quotation: Quotation 对象
            message_text: 自定义消息文本

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = message_text[:100] if message_text else f'报价单 {quotation.quotation_number}'

        return cls(
            message_type='confirmation_request',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 请求你确认产品选型',
            content=content_preview,
            related_object_type='quotation',
            related_object_id=quotation.id,
            extra_data={
                'quotation_number': quotation.quotation_number,
                'project_id': quotation.project_id,
                'task_type': 'product_confirmation'
            }
        )

    @classmethod
    def create_confirmation_completed(cls, sender_id, recipient_id, quotation):
        """创建产品确认完成通知（通知发起人）

        Args:
            sender_id: 系统或最后确认人ID
            recipient_id: 接收者用户ID（发起人/销售）
            quotation: Quotation 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        return cls(
            message_type='confirmation_completed',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'报价单 {quotation.quotation_number} 产品确认已完成',
            content='所有指派人已完成产品选型确认',
            related_object_type='quotation',
            related_object_id=quotation.id,
            extra_data={
                'quotation_number': quotation.quotation_number,
                'task_type': 'product_confirmation'
            }
        )

    # ========== 日志评论通知相关方法 ==========

    # ========== 通用任务通知相关方法 ==========

    @classmethod
    def create_task_assigned(cls, sender_id, recipient_id, task):
        """创建任务指派通知

        Args:
            sender_id: 发送者用户ID（任务创建人）
            recipient_id: 接收者用户ID（被指派人）
            task: Task 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = task.title[:100] if task.title else ''

        return cls(
            message_type='task_assigned',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 给你分配了任务',
            content=content_preview,
            related_object_type='task',
            related_object_id=task.id,
            extra_data={
                'task_id': task.id,
                'priority': task.priority,
                'due_date': task.due_date.isoformat() if task.due_date else None
            }
        )

    @classmethod
    def create_task_completed(cls, sender_id, recipient_id, task):
        """创建任务完成通知

        Args:
            sender_id: 发送者用户ID（被指派人/完成人）
            recipient_id: 接收者用户ID（任务创建人）
            task: Task 对象

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        content_preview = task.title[:100] if task.title else ''

        return cls(
            message_type='task_completed',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 完成了任务',
            content=content_preview,
            related_object_type='task',
            related_object_id=task.id,
            extra_data={
                'task_id': task.id,
                'priority': task.priority,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            }
        )

    @classmethod
    def create_worklog_comment(cls, sender_id, recipient_id, worklog, comment_content):
        """创建日志评论通知

        Args:
            sender_id: 发送者用户ID（评论者）
            recipient_id: 接收者用户ID（日志作者）
            worklog: WorkLog 对象
            comment_content: 评论内容（用于预览）

        Returns:
            Message: 创建的消息对象（未提交到数据库）
        """
        from app.models.user import User
        sender = db.session.get(User, sender_id)
        sender_name = sender.real_name or sender.username if sender else '未知用户'

        # 截取评论内容预览（最多100字符）
        content_preview = comment_content[:100] + ('...' if len(comment_content) > 100 else '')

        return cls(
            message_type='worklog_comment',
            sender_id=sender_id,
            recipient_id=recipient_id,
            title=f'{sender_name} 评论了你的日志',
            content=content_preview,
            related_object_type='worklog',
            related_object_id=worklog.id,
            extra_data={
                'log_date': worklog.log_date.isoformat() if worklog.log_date else None,
                'log_type': worklog.log_type,
                'owner_id': worklog.owner_id  # 日志所有者ID，用于前端正确显示日志
            }
        )
