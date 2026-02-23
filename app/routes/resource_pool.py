# -*- coding: utf-8 -*-
"""
资源池 API — 跨权限搜索 + 请求访问 + 审批共享
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from flask_babel import gettext as _

from app import db
from app.models.access_request import AccessRequest
from app.models.customer import Company
from app.models.project import Project
from app.models.user import User, Affiliation
from app.models.message import Message
from app.utils.dictionary_helpers import company_type_label, industry_label, project_type_label, project_stage_label

logger = logging.getLogger(__name__)

resource_pool_bp = Blueprint('resource_pool', __name__, url_prefix='/api/v1/resource-pool')


def _get_local_time():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


def _find_approver(entity):
    """确定审批人：归属人激活则用归属人，否则向上找商务经理"""
    owner = entity.owner if hasattr(entity, 'owner') else None

    if owner and getattr(owner, 'is_active', False):
        return owner

    # 归属人未激活 → 通过 Affiliation 找上级
    if owner:
        aff = Affiliation.query.filter_by(owner_id=owner.id).first()
        if aff and aff.viewer and aff.viewer.is_active:
            return aff.viewer

        # 同公司的 business_admin
        if owner.company_name:
            bm = User.query.filter_by(
                company_name=owner.company_name,
                role='business_admin',
            ).filter(User._is_active == True).first()
            if bm:
                return bm

    # 兜底: admin
    return User.query.filter_by(role='admin').filter(User._is_active == True).first()


@resource_pool_bp.route('/request-access', methods=['POST'])
@login_required
def request_access():
    """提交访问请求"""
    try:
        data = request.get_json() or {}
        entity_type = data.get('entity_type')  # customer | project
        entity_id = data.get('entity_id')
        message_text = data.get('message', '')
        requested_options = data.get('requested_options')

        if entity_type not in ('customer', 'project') or not entity_id:
            return jsonify({'success': False, 'message': _('参数错误')}), 400

        # 查找实体
        if entity_type == 'customer':
            entity = Company.query.get(entity_id)
        else:
            entity = Project.query.get(entity_id)

        if not entity:
            return jsonify({'success': False, 'message': _('资源不存在')}), 404

        # 防重复
        existing = AccessRequest.query.filter_by(
            requester_id=current_user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            status='pending'
        ).first()
        if existing:
            return jsonify({'success': False, 'message': _('已有待处理的请求')}), 400

        # 确定审批人
        approver = _find_approver(entity)
        if not approver:
            return jsonify({'success': False, 'message': _('找不到审批人，请联系管理员')}), 500

        # 不能给自己发请求
        if approver.id == current_user.id:
            return jsonify({'success': False, 'message': _('您已拥有该资源的访问权限')}), 400

        # 创建请求
        req = AccessRequest(
            requester_id=current_user.id,
            approver_id=approver.id,
            entity_type=entity_type,
            entity_id=entity_id,
            status='pending',
            request_message=message_text,
            requested_options=requested_options,
            created_at=_get_local_time()
        )
        db.session.add(req)

        # 发送消息通知
        entity_label = _('客户') if entity_type == 'customer' else _('项目')
        requester_name = current_user.real_name or current_user.username
        msg = Message(
            message_type='access_request',
            sender_id=current_user.id,
            recipient_id=approver.id,
            title=f'{requester_name} {_("请求访问")}{entity_label}',
            content=message_text[:100] if message_text else '',
            related_object_type='access_request',
            related_object_id=0,  # 将在 flush 后更新
            extra_data={
                'entity_type': entity_type,
                'entity_id': entity_id,
            }
        )
        db.session.add(msg)
        db.session.flush()  # 获取 req.id
        msg.related_object_id = req.id

        db.session.commit()
        return jsonify({'success': True, 'message': _('请求已发送')})

    except Exception as e:
        db.session.rollback()
        logger.error(f'request_access error: {e}', exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@resource_pool_bp.route('/request/<int:request_id>', methods=['GET'])
@login_required
def get_request_detail(request_id):
    """获取请求详情（审批人使用）"""
    try:
        req = AccessRequest.query.get_or_404(request_id)

        # 只有审批人或请求人可以查看
        if req.approver_id != current_user.id and req.requester_id != current_user.id:
            return jsonify({'success': False, 'message': _('无权查看')}), 403

        # 获取实体信息（审批人可以看到完整信息）
        entity_info = {}
        if req.entity_type == 'customer':
            company = Company.query.get(req.entity_id)
            if company:
                entity_info = {
                    'name': company.company_name,
                    'type': company_type_label(company.company_type) if company.company_type else '',
                    'industry': industry_label(company.industry) if company.industry else '',
                    'owner_name': (company.owner.real_name or company.owner.username) if company.owner else '',
                }
        else:
            project = Project.query.get(req.entity_id)
            if project:
                entity_info = {
                    'name': project.project_name,
                    'type': project_type_label(project.project_type) if project.project_type else '',
                    'stage': project_stage_label(project.current_stage) if project.current_stage else '',
                    'owner_name': (project.owner.real_name or project.owner.username) if project.owner else '',
                }

        result = req.to_dict()
        result['entity_info'] = entity_info
        result['requester_department'] = req.requester.department if req.requester else ''

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f'get_request_detail error: {e}', exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@resource_pool_bp.route('/resolve-access', methods=['POST'])
@login_required
def resolve_access():
    """审批请求（通过/拒绝）"""
    try:
        data = request.get_json() or {}
        request_id = data.get('request_id')
        action = data.get('action')  # approve | reject
        share_options = data.get('share_options', {})

        if not request_id or action not in ('approve', 'reject'):
            return jsonify({'success': False, 'message': _('参数错误')}), 400

        req = AccessRequest.query.get_or_404(request_id)

        # 验证审批人
        if req.approver_id != current_user.id:
            return jsonify({'success': False, 'message': _('无权操作')}), 403

        if req.status != 'pending':
            return jsonify({'success': False, 'message': _('该请求已处理')}), 400

        now = _get_local_time()
        approver_name = current_user.real_name or current_user.username

        if action == 'approve':
            req.status = 'approved'
            req.share_options = share_options
            req.resolved_at = now

            # 自动添加共享
            if req.entity_type == 'customer':
                company = Company.query.get(req.entity_id)
                if company:
                    company.share_enabled = True
                    company.add_shared_user(req.requester_id)

                    # 如果勾选了项目共享，或勾选了报价单（报价单权限依赖项目共享）
                    if share_options.get('projects') or share_options.get('quotations'):
                        from app.models.project_customer_association import ProjectCustomerAssociation
                        assocs = ProjectCustomerAssociation.query.filter_by(company_id=company.id).all()
                        for assoc in assocs:
                            proj = Project.query.get(assoc.project_id)
                            if proj:
                                proj.share_enabled = True
                                proj.add_shared_user(req.requester_id)

            elif req.entity_type == 'project':
                project = Project.query.get(req.entity_id)
                if project:
                    project.share_enabled = True
                    project.add_shared_user(req.requester_id)

            # 通知请求者 — 已通过
            msg = Message(
                message_type='access_request_result',
                sender_id=current_user.id,
                recipient_id=req.requester_id,
                title=_('访问请求已通过'),
                content=f'{approver_name} {_("已批准您的访问请求")}',
                related_object_type='access_request',
                related_object_id=req.id,
                extra_data={
                    'approved': True,
                    'entity_type': req.entity_type,
                    'entity_id': req.entity_id,
                    'share_options': share_options,
                }
            )
            db.session.add(msg)

        else:
            req.status = 'rejected'
            req.resolved_at = now

            # 通知请求者 — 已拒绝
            msg = Message(
                message_type='access_request_result',
                sender_id=current_user.id,
                recipient_id=req.requester_id,
                title=_('访问请求被拒绝'),
                content=f'{approver_name} {_("拒绝了您的访问请求")}',
                related_object_type='access_request',
                related_object_id=req.id,
                extra_data={
                    'approved': False,
                    'entity_type': req.entity_type,
                    'entity_id': req.entity_id,
                }
            )
            db.session.add(msg)

        db.session.commit()
        return jsonify({'success': True, 'message': _('操作成功')})

    except Exception as e:
        db.session.rollback()
        logger.error(f'resolve_access error: {e}', exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
