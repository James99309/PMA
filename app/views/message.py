# -*- coding: utf-8 -*-
"""
站内消息模块 - 视图层

提供消息面板所需的 API 接口
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from flask_babel import gettext as _

logger = logging.getLogger(__name__)

from app import db
from app.models.message import Message
from app.models.announcement import AnnouncementRead, Announcement
from app.helpers.approval_helpers import get_user_pending_approvals, get_pending_approval_count


message = Blueprint('message', __name__, url_prefix='/message')


@message.route('/api/panel-data', methods=['GET'])
@login_required
def get_panel_data():
    """获取消息面板数据（日志@消息 + 审批通知 + 待审批记录）"""
    try:
        # 1. 获取日志@消息（未读优先，最多20条）
        unread_messages = Message.get_unread_messages(current_user.id, limit=20)

        # 计算权限：是否可以查看他人日历
        from app.permissions import is_admin_or_ceo
        can_view_all = is_admin_or_ceo()
        is_dept_manager = getattr(current_user, 'is_department_manager', False)

        mention_list = []
        for msg in unread_messages:
            # 跳过审批消息（由后面单独处理，避免重复添加）
            if msg.message_type in ['approval_approved', 'approval_rejected', 'approval_cc']:
                continue

            msg_dict = msg.to_dict()

            # 判断是否可以查看发送者的日历
            can_view = False
            if msg.related_object_type == 'worklog':
                if can_view_all:
                    can_view = True
                elif is_dept_manager:
                    # 部门负责人只能查看同部门成员
                    from app.models.user import User
                    sender = db.session.get(User, msg.sender_id)
                    if sender and sender.department == current_user.department:
                        can_view = True
            elif msg.related_object_type == 'workitem':
                # 行程类消息（共享、取消、完成等），用户自己收到的通知，可以查看自己的日历
                can_view = True

            msg_dict['can_view_calendar'] = can_view
            mention_list.append(msg_dict)

        # 1.5 获取审批通知消息（结果通知 + 抄送，未读）
        approval_messages = Message.query.filter(
            Message.recipient_id == current_user.id,
            Message.is_read == False,
            Message.message_type.in_(['approval_approved', 'approval_rejected', 'approval_cc'])
        ).order_by(Message.created_at.desc()).limit(20).all()

        for msg in approval_messages:
            msg_dict = msg.to_dict()
            # 添加详情页 URL
            msg_dict['detail_url'] = _get_approval_detail_url(
                msg.related_object_type,
                msg.related_object_id
            )
            msg_dict['can_view_calendar'] = False  # 审批消息不跳转日历
            mention_list.append(msg_dict)

        # 2. 获取用户的未读公告，混入 mention_list（与@消息一致：已读即消失）
        announcement_records = AnnouncementRead.query.filter(
            AnnouncementRead.user_id == current_user.id,
            AnnouncementRead.is_read == False
        ).join(Announcement).filter(
            Announcement.status == 'published',
            Announcement.is_deleted == False
        ).order_by(Announcement.published_at.desc()).limit(20).all()

        logger.info(f"[消息面板] 用户 {current_user.id} 公告记录数: {len(announcement_records)}")

        for record in announcement_records:
            ann = record.announcement
            mention_list.append({
                'id': f'ann_{record.id}',
                'title': ann.title,
                'content': ann.content,  # 显示完整内容
                'message_type': f'announcement_{ann.announcement_type}',
                'is_read': record.is_read,
                'created_at': ann.published_at.isoformat() if ann.published_at else None,
                'sender_name': ann.creator.real_name if ann.creator else None,
                'can_view_calendar': False,
                'related_object_type': 'announcement',
                'related_object_id': ann.id
            })

        # 按优先级排序：worklog_submitted 优先级最低，排在最后；其余按时间倒序
        LOW_PRIORITY_TYPES = {'worklog_submitted'}
        mention_list.sort(
            key=lambda x: (
                1 if x.get('message_type') in LOW_PRIORITY_TYPES else 0,
                -(datetime.fromisoformat(x['created_at']).timestamp() if x.get('created_at') else 0)
            )
        )

        # 3. 获取待审批记录（实时查询）
        pending_approvals = get_user_pending_approvals(current_user.id, page=1, per_page=20)
        approval_list = []

        for instance in pending_approvals.items:
            approval_info = {
                'id': instance.id,
                'object_type': instance.object_type,
                'object_id': instance.object_id,
                'object_name': _get_object_name(instance),
                'status': instance.status.value if hasattr(instance.status, 'value') else str(instance.status),
                'created_at': instance.started_at.isoformat() if instance.started_at else None,
                'detail_url': _get_detail_url(instance)
            }
            approval_list.append(approval_info)

        # 4. 获取待办任务（产品确认等）— pending + 最近24h已确认
        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        from sqlalchemy.orm import joinedload as jl
        from datetime import timedelta
        cutoff = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None) - timedelta(hours=24)

        todo_tasks = QuotationConfirmationTask.query.options(
            jl(QuotationConfirmationTask.quotation),
            jl(QuotationConfirmationTask.requester)
        ).filter(
            QuotationConfirmationTask.assignee_id == current_user.id,
            db.or_(
                QuotationConfirmationTask.status == 'pending',
                db.and_(
                    QuotationConfirmationTask.status == 'confirmed',
                    QuotationConfirmationTask.confirmed_at >= cutoff
                )
            )
        ).order_by(
            # pending 排在 confirmed 前面
            db.case(
                (QuotationConfirmationTask.status == 'pending', 0),
                else_=1
            ),
            QuotationConfirmationTask.created_at.desc()
        ).limit(20).all()

        todo_list = []
        pending_todo_count = 0
        for task in todo_tasks:
            qt = task.quotation
            todo_list.append({
                'id': task.id,
                'type': 'product_confirmation',
                'status': task.status,
                'title': f'产品确认: {qt.quotation_number if qt else ""}',
                'message': task.message or '',
                'requester_name': (task.requester.real_name or task.requester.username) if task.requester else '',
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'detail_url': url_for('quotation.view_quotation', id=task.quotation_id) if qt else '#',
                'quotation_id': task.quotation_id
            })
            if task.status == 'pending':
                pending_todo_count += 1

        # 4.5 获取通用任务 — pending/in_progress + 最近24h已完成
        from app.models.task import Task as GeneralTask
        general_tasks = GeneralTask.query.filter(
            db.or_(GeneralTask.assignee_id == current_user.id, GeneralTask.creator_id == current_user.id),
            GeneralTask.is_deleted == False,
            db.or_(
                GeneralTask.status.in_(['pending', 'in_progress']),
                db.and_(
                    GeneralTask.status == 'completed',
                    GeneralTask.completed_at >= cutoff
                )
            )
        ).order_by(
            db.case(
                (GeneralTask.status.in_(['pending', 'in_progress']), 0),
                else_=1
            ),
            GeneralTask.due_date.asc().nullslast(),
            GeneralTask.created_at.desc()
        ).limit(20).all()

        for gt in general_tasks:
            todo_list.append({
                'id': f'gt_{gt.id}',
                'type': 'general_task',
                'status': 'confirmed' if gt.status == 'completed' else gt.status,
                'title': gt.title,
                'message': gt.description or '',
                'requester_name': (gt.creator.real_name or gt.creator.username) if gt.creator else '',
                'due_date': gt.due_date.isoformat() if gt.due_date else None,
                'created_at': gt.created_at.isoformat() if gt.created_at else None,
                'detail_url': '#',
                'task_id': gt.id,
                'priority': gt.priority,
            })
            if gt.status in ('pending', 'in_progress'):
                pending_todo_count += 1

        # 4.6 获取待审批的访问请求
        from app.models.access_request import AccessRequest
        access_requests = AccessRequest.query.filter_by(
            approver_id=current_user.id, status='pending'
        ).order_by(AccessRequest.created_at.desc()).all()

        for req in access_requests:
            entity_label = '客户' if req.entity_type == 'customer' else '项目'
            todo_list.append({
                'id': f'access_req_{req.id}',
                'type': 'access_request',
                'status': 'pending',
                'title': f'{req.requester.real_name or req.requester.username} 请求访问{entity_label}',
                'message': req.request_message or '',
                'requester_name': req.requester.real_name or req.requester.username if req.requester else '',
                'due_date': None,
                'created_at': req.created_at.isoformat() if req.created_at else None,
                'detail_url': '#',
                'request_id': req.id,
                'entity_type': req.entity_type,
                'entity_id': req.entity_id,
            })
            pending_todo_count += 1

        # 4.7 获取待审核的知识库晋升申请（只看分配给自己的）
        from app.models.knowledge import KnowledgePromotionRequest
        promotion_requests = KnowledgePromotionRequest.query.filter_by(
            assigned_to=current_user.id, status='pending'
        ).order_by(KnowledgePromotionRequest.created_at.desc()).all()

        for pr in promotion_requests:
            scope_labels = {'personal': '个人', 'department': '部门', 'company': '公司', 'system': '系统'}
            todo_list.append({
                'id': f'wiki_promo_{pr.id}',
                'type': 'wiki_promotion',
                'status': 'pending',
                'title': f'知识晋升: {pr.article.title if pr.article else ""}',
                'message': pr.request_note or '',
                'requester_name': (pr.requester.real_name or pr.requester.username) if pr.requester else '',
                'due_date': None,
                'created_at': pr.created_at.isoformat() if pr.created_at else None,
                'detail_url': f'/wiki?promote={pr.id}',
                'promotion_request_id': pr.id,
                'article_id': pr.article_id,
                'from_scope': pr.from_scope,
                'to_scope': pr.to_scope,
                'to_scope_label': scope_labels.get(pr.to_scope, pr.to_scope),
            })
            pending_todo_count += 1

        # 4.8 获取待确认的里程碑会审（分配给自己的）
        from app.models.subtask import MilestoneReviewer, SubTask
        milestone_reviews = MilestoneReviewer.query.join(
            SubTask, MilestoneReviewer.subtask_id == SubTask.id
        ).join(
            GeneralTask, SubTask.task_id == GeneralTask.id
        ).filter(
            MilestoneReviewer.reviewer_id == current_user.id,
            MilestoneReviewer.status == 'pending',
            SubTask.is_deleted == False,
            GeneralTask.is_deleted == False,
        ).order_by(MilestoneReviewer.created_at.desc()).all()

        for mr in milestone_reviews:
            st = mr.subtask
            t = st.task if st else None
            task_title = t.title if t else ''
            todo_list.append({
                'id': f'milestone_{mr.id}',
                'type': 'milestone_confirmation',
                'status': 'pending',
                'title': f'里程碑确认: {st.title}',
                'message': f'任务「{task_title}」的节点「{st.title}」已完成，请确认',
                'requester_name': (st.assignee.real_name or st.assignee.username) if st and st.assignee else '',
                'due_date': st.due_date.isoformat() if st and st.due_date else None,
                'created_at': mr.created_at.isoformat() if mr.created_at else None,
                'detail_url': f'/task/management?task_id={t.id}&subtask_id={st.id}' if t and st else '#',
                'task_id': t.id if t else None,
                'subtask_id': st.id if st else None,
            })
            pending_todo_count += 1

        # 4.85 获取待审核的任务（作为审计人）
        from app.models.task import TaskReviewer
        task_reviews = TaskReviewer.query.join(
            GeneralTask, TaskReviewer.task_id == GeneralTask.id
        ).filter(
            TaskReviewer.reviewer_id == current_user.id,
            TaskReviewer.status == 'pending',
            GeneralTask.is_deleted == False,
            GeneralTask.review_status == 'pending_review',
        ).order_by(TaskReviewer.created_at.desc()).all()

        for tr in task_reviews:
            t = tr.task
            todo_list.append({
                'id': f'task_review_{tr.id}',
                'type': 'task_review',
                'status': 'pending',
                'title': f'任务审核: {t.title}',
                'message': f'任务「{t.title}」已完成，请审核',
                'requester_name': (t.assignee.real_name or t.assignee.username) if t and t.assignee else '',
                'due_date': t.due_date.isoformat() if t and t.due_date else None,
                'created_at': tr.created_at.isoformat() if tr.created_at else None,
                'detail_url': f'/task/management?task_id={t.id}',
                'task_id': t.id,
            })
            pending_todo_count += 1

        # 4.9 混合排序：pending/in_progress 在前，confirmed/completed 在后，各组内按创建时间倒序
        def todo_sort_key(item):
            s = item.get('status', '')
            is_done = 1 if s in ('confirmed', 'completed') else 0
            return (is_done, -(datetime.fromisoformat(item['created_at']).timestamp() if item.get('created_at') else 0))
        todo_list.sort(key=todo_sort_key)

        # 5. 计算总未读数（消息 + 公告）
        unread_mention_count = Message.get_unread_count(current_user.id)
        unread_announcement_count = AnnouncementRead.get_unread_count(current_user.id)
        # 直接使用实际查询结果的总数，避免缓存导致数量与列表不一致
        pending_approval_count = pending_approvals.total
        # @我标签的未读数 = 消息未读 + 公告未读
        total_mentions_unread = unread_mention_count + unread_announcement_count

        return jsonify({
            'success': True,
            'data': {
                'mentions': mention_list,
                'approvals': approval_list,
                'todos': todo_list,
                'counts': {
                    'unread_mentions': total_mentions_unread,
                    'pending_approvals': pending_approval_count,
                    'pending_todos': pending_todo_count,
                    'total': total_mentions_unread + pending_approval_count + pending_todo_count
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@message.route('/api/mark-read', methods=['POST'])
@login_required
def mark_read():
    """标记消息为已读"""
    try:
        data = request.get_json() or {}
        message_ids = data.get('message_ids', [])

        Message.mark_as_read(message_ids, current_user.id)

        return jsonify({
            'success': True,
            'message': _('已标记为已读')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@message.route('/api/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """获取未读消息数量（轻量接口，用于徽章显示）"""
    try:
        unread_mention_count = Message.get_unread_count(current_user.id)
        unread_announcement_count = AnnouncementRead.get_unread_count(current_user.id)
        pending_approval_count = get_pending_approval_count(current_user.id)
        # @我标签未读 = 消息 + 公告
        total_mentions_unread = unread_mention_count + unread_announcement_count

        # 待办任务数（产品确认 + 通用任务）
        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        pending_todo_count = QuotationConfirmationTask.query.filter_by(
            assignee_id=current_user.id,
            status='pending'
        ).count()

        from app.models.task import Task as GeneralTask
        pending_todo_count += GeneralTask.query.filter(
            GeneralTask.assignee_id == current_user.id,
            GeneralTask.is_deleted == False,
            GeneralTask.status.in_(['pending', 'in_progress'])
        ).count()

        # 访问请求待审批
        from app.models.access_request import AccessRequest
        pending_todo_count += AccessRequest.query.filter_by(
            approver_id=current_user.id, status='pending'
        ).count()

        # Wiki 晋升待审核
        try:
            from app.models.knowledge import KnowledgePromotionRequest
            pending_todo_count += KnowledgePromotionRequest.query.filter_by(
                assigned_to=current_user.id, status='pending'
            ).count()
        except Exception:
            pass

        return jsonify({
            'success': True,
            'data': {
                'unread_mentions': total_mentions_unread,
                'pending_approvals': pending_approval_count,
                'pending_todos': pending_todo_count,
                'total': total_mentions_unread + pending_approval_count + pending_todo_count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@message.route('/api/has-unread', methods=['GET'])
@login_required
def has_unread():
    """检查是否有未读消息（用于登录后自动弹出判断）"""
    try:
        unread_mention_count = Message.get_unread_count(current_user.id)
        unread_announcement_count = AnnouncementRead.get_unread_count(current_user.id)
        pending_approval_count = get_pending_approval_count(current_user.id)

        from app.models.quotation_confirmation_task import QuotationConfirmationTask
        pending_todo_count = QuotationConfirmationTask.query.filter_by(
            assignee_id=current_user.id,
            status='pending'
        ).count()

        from app.models.task import Task as GeneralTask
        pending_todo_count += GeneralTask.query.filter(
            GeneralTask.assignee_id == current_user.id,
            GeneralTask.is_deleted == False,
            GeneralTask.status.in_(['pending', 'in_progress'])
        ).count()

        # 访问请求待审批
        from app.models.access_request import AccessRequest
        pending_todo_count += AccessRequest.query.filter_by(
            approver_id=current_user.id, status='pending'
        ).count()

        # Wiki 晋升待审核
        try:
            from app.models.knowledge import KnowledgePromotionRequest
            pending_todo_count += KnowledgePromotionRequest.query.filter_by(
                assigned_to=current_user.id, status='pending'
            ).count()
        except Exception:
            pass

        total = unread_mention_count + unread_announcement_count + pending_approval_count + pending_todo_count
        has_unread_flag = total > 0

        return jsonify({
            'success': True,
            'has_unread': has_unread_flag,
            'total': total
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def _get_object_name(instance):
    """获取审批对象名称"""
    try:
        if instance.object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(instance.object_id)
            return obj.project_name if obj else f'项目#{instance.object_id}'
        elif instance.object_type == 'expense':
            from app.models.expense import Expense
            obj = Expense.query.get(instance.object_id)
            return obj.expense_number if obj else f'报销单#{instance.object_id}'
        elif instance.object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(instance.object_id)
            return obj.quotation_number if obj else f'报价单#{instance.object_id}'
        elif instance.object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            obj = PricingOrder.query.get(instance.object_id)
            return obj.order_number if obj else f'批价单#{instance.object_id}'
        elif instance.object_type == 'purchase_order':
            from app.models.inventory import PurchaseOrder
            obj = PurchaseOrder.query.get(instance.object_id)
            return obj.order_number if obj else f'采购订单#{instance.object_id}'
        elif instance.object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.get(instance.object_id)
            return obj.name if obj else f'客户#{instance.object_id}'
        elif instance.object_type == 'rd_product':
            from app.models.dev_product import DevProduct
            obj = DevProduct.query.get(instance.object_id)
            return obj.name if obj else f'研发产品#{instance.object_id}'
        else:
            return f'{instance.object_type}#{instance.object_id}'
    except Exception:
        return f'{instance.object_type}#{instance.object_id}'


def _get_detail_url(instance):
    """获取审批对象详情页URL（从审批实例）"""
    return _get_approval_detail_url(instance.object_type, instance.object_id)


def _get_approval_detail_url(object_type, object_id):
    """获取审批对象详情页URL（从对象类型和ID）"""
    try:
        if object_type == 'project':
            return url_for('project.view_project', project_id=object_id)
        elif object_type == 'expense':
            return url_for('expense.expense_detail', id=object_id)
        elif object_type == 'quotation':
            return url_for('quotation.view_quotation', id=object_id)
        elif object_type == 'pricing_order':
            return url_for('pricing_order.list_pricing_orders') + f'?open={object_id}'
        elif object_type == 'purchase_order':
            return url_for('purchase_order.detail_view', order_id=object_id)
        elif object_type == 'customer':
            return url_for('customer.view_company', company_id=object_id)
        elif object_type == 'rd_product':
            # 研发产品蓝图已停用，返回空链接
            return '#'
        else:
            return '#'
    except Exception:
        return '#'
