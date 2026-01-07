# -*- coding: utf-8 -*-
"""
站内消息模块 - 视图层

提供消息面板所需的 API 接口
"""
import logging
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

        # 按时间倒序排列混合列表
        mention_list.sort(key=lambda x: x.get('created_at') or '', reverse=True)

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

        # 4. 计算总未读数（消息 + 公告）
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
                'counts': {
                    'unread_mentions': total_mentions_unread,
                    'pending_approvals': pending_approval_count,
                    'total': total_mentions_unread + pending_approval_count
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

        return jsonify({
            'success': True,
            'data': {
                'unread_mentions': total_mentions_unread,
                'pending_approvals': pending_approval_count,
                'total': total_mentions_unread + pending_approval_count
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

        total = unread_mention_count + unread_announcement_count + pending_approval_count
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
            return url_for('project.view_project', project_id=object_id, tw=1)
        elif object_type == 'expense':
            return url_for('expense.expense_detail', id=object_id)
        elif object_type == 'quotation':
            return url_for('quotation.view_quotation', id=object_id, tw=1)
        elif object_type == 'pricing_order':
            return url_for('pricing_order.edit_pricing_order', order_id=object_id)
        elif object_type == 'purchase_order':
            return url_for('inventory.order_detail', id=object_id)
        elif object_type == 'customer':
            return url_for('customer.view_company', company_id=object_id)
        elif object_type == 'rd_product':
            # 研发产品蓝图已停用，返回空链接
            return '#'
        else:
            return '#'
    except Exception:
        return '#'
