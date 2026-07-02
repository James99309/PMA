from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort, session, after_this_request
from flask_babel import gettext as _
from datetime import datetime, date, timedelta
from flask_login import login_required, current_user
from config import Config
from app import db, csrf
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.approval import ApprovalStatus
from app.decorators import permission_required, permission_required_with_approval_context
from app.utils.access_control import get_viewable_data, can_edit_data, get_accessible_data, can_change_project_owner, can_view_project
import logging
import re
from fuzzywuzzy import fuzz
from app.utils.text_similarity import calculate_chinese_similarity, is_similar_project_name
import uuid  # 使用内置的uuid模块替代bson.objectid
import pandas as pd
import json
from app.models.user import User
from app.models.quotation import Quotation
from app.models.expense import Expense, EXPENSE_CATEGORIES
from app.models.pricing_order import PricingOrder
from app.permissions import check_permission, Permissions
from werkzeug.utils import secure_filename
import os
from flask_wtf.csrf import CSRFProtect
from app.models.action import Action, ActionReply
from app.models.projectpm_stage_history import ProjectStageHistory  # 导入阶段历史记录模型
from app.utils.dictionary_helpers import project_type_label, project_stage_label, REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS, COMPANY_TYPE_LABELS, INDUSTRY_OPTIONS, get_industry_options, get_project_type_options, get_report_source_options, get_product_situation_options, get_project_stage_options, get_default_currency, get_currency_symbol, get_amount_unit_config, get_activity_status_options
from app.services.exchange_rate_service import exchange_rate_service
from app.utils.chinese_mapping_manager import mapping_manager
from sqlalchemy import or_, func, case
from sqlalchemy.orm import joinedload
from app.helpers.project_helpers import is_project_editable
from app.utils.activity_tracker import check_company_activity, update_active_status
from app.models.settings import SystemSettings
from zoneinfo import ZoneInfo
from app.utils.role_mappings import get_role_display_name
from flask import after_this_request
from app.utils.change_tracker import ChangeTracker
from app.utils.work_item_recorder import record_activity
from app.helpers.approval_helpers import get_object_approval_instance, get_available_templates
from app.utils.access_control import can_start_approval
from app.utils.query_filters import (
    extract_filter_params, apply_filters_to_query, extract_sort_params,
    extract_pagination_params, build_list_query, build_ajax_response
)
from app.models.prospect_project import ProspectProject

# ============================================================
# 项目管理筛选配置
# ============================================================
PROJECT_FILTER_CONFIG = {
    'search': {'type': 'ilike', 'fields': ['project_name', 'authorization_code']},
    'owner_id': {'type': 'exact', 'aliases': ['filter_owner_id']},
    'vendor_sales_manager_id': {'type': 'exact', 'aliases': ['filter_vendor_sales_manager_id']},
    'activity_status': {'type': 'exact'},
    'industry': {'type': 'exact'},
    'report_source': {'type': 'exact'},
    'current_stage': {'type': 'exact'},
    'project_type': {'type': 'exact'},
    'stage_not': {'handler': 'stage_not'},
    'has_authorization': {'handler': 'has_authorization'},
    'updated_this_month': {'handler': 'updated_this_month', 'aliases': ['business_update_filter']},
}

# 添加 ProjectRatingRecord 导入
try:
    from app.models.project_rating_record import ProjectRatingRecord
except ImportError:
    ProjectRatingRecord = None

csrf = CSRFProtect()

logger = logging.getLogger(__name__)

project = Blueprint('project', __name__)

@project.route('/api/companies/<company_type>')
@login_required
def api_companies_for_project(company_type):
    """API端点 - 为项目获取企业列表（移除权限等级过滤，仅过滤删除状态和企业角色）"""
    try:
        # 直接查询所有未删除的企业，不使用权限等级过滤
        query = Company.query.filter(Company.is_deleted == False)
        
        # 根据类型筛选企业
        type_mapping = {
            'user': ['user', 'end_user', 'customer'],
            'designer': ['designer', 'design_institute', 'consultant'],
            'contractor': ['contractor', 'general_contractor'],
            'integrator': ['integrator', 'system_integrator'],
            'dealer': ['dealer', 'distributor']
        }
        
        if company_type in type_mapping:
            company_types = type_mapping[company_type]
            query = query.filter(Company.company_type.in_(company_types))
        
        companies = query.all()  # 先获取所有企业，后面分组后再排序
        
        # 格式化返回数据，区分当前用户和其他用户的公司
        current_user_companies = []
        other_companies = []
        
        for company in companies:
            company_data = {
                'id': company.id,
                'name': company.company_name,
                'type': company.company_type,
                'owner_name': company.owner.real_name if company.owner else '未指定',
                'owner_id': company.owner_id,
                'is_readable': True,  # 移除权限检查，所有企业都可读
                'is_own': company.owner_id == current_user.id
            }
            
            # 分组：当前用户的公司优先
            if company.owner_id == current_user.id:
                current_user_companies.append(company_data)
            else:
                other_companies.append(company_data)
        
        # 对每个分组内部按企业名称排序
        current_user_companies.sort(key=lambda x: x['name'] or '')
        other_companies.sort(key=lambda x: x['name'] or '')
        
        # 组合结果：当前用户的公司在前，其他公司在后
        result = current_user_companies + other_companies
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取项目企业列表失败: {str(e)}")
        return jsonify([])

def get_company_list_by_type(company_type):
    """根据企业类型获取企业列表"""
    # 使用数据访问控制
    query = get_viewable_data(Company, current_user)
    return query.filter_by(company_type=company_type).order_by(Company.company_name).all()

@project.route('/')
@permission_required('project', 'view')
def list_projects():
    """旧 TW 项目列表 — 已重定向到 AT 风格列表"""
    return redirect(url_for('project.at_list_view', **request.args))

def _can_win_lock(p, user):
    """成功锁定权限:项目负责人 / 厂商销售负责人 / 项目负责人的部门经理 / admin"""
    if user.role == 'admin':
        return True
    if p.owner_id == user.id:
        return True
    if getattr(p, 'vendor_sales_manager_id', None) == user.id:
        return True
    if user.is_department_manager and p.owner and \
            (user.department or '') == (p.owner.department or '') and \
            (user.company_name or '') == (p.owner.company_name or ''):
        return True
    return False


@project.route('/at-api/<int:project_id>/win-lock', methods=['POST'])
@login_required
@permission_required('project', 'view')
def at_api_win_lock(project_id):
    """成功锁定(锁单预判):强制理由;签约阶段自动解除,亦可人为解除"""
    p = Project.query.get_or_404(project_id)
    if not _can_win_lock(p, current_user):
        return jsonify({'success': False, 'message': '仅项目负责人/厂商销售负责人/部门经理可锁定成功'}), 403
    if p.current_stage == 'signed':
        return jsonify({'success': False, 'message': '项目已签约,无需锁定'}), 400
    payload = request.get_json() or {}
    reason = (payload.get('reason') or '').strip()
    if not reason:
        return jsonify({'success': False, 'message': '请填写锁定理由'}), 400
    delivery_raw = (payload.get('delivery_forecast') or '').strip()
    if not delivery_raw:
        return jsonify({'success': False, 'message': '请填写预计交付日期'}), 400
    try:
        delivery_date = datetime.strptime(delivery_raw, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': '交付日期格式不正确'}), 400
    # 锁定必须关联报价单:无报价单的项目不可锁;多报价单需指明锁定哪一单
    from app.models.quotation import Quotation as _Q
    proj_quotes = _Q.query.filter_by(project_id=p.id).order_by(_Q.created_at.desc()).all()
    if not proj_quotes:
        return jsonify({'success': False, 'message': '该项目尚无报价单,无法锁定成功'}), 400
    qid = payload.get('quotation_id')
    if len(proj_quotes) == 1 and not qid:
        lock_q = proj_quotes[0]
    else:
        lock_q = next((q for q in proj_quotes if q.id == qid), None)
        if not lock_q:
            return jsonify({'success': False, 'message': '请选择锁定的报价单'}), 400
    # 改为「提交审核」:不直接锁定,创建审批实例,通过回调才真正 win_locked
    approver_id = payload.get('approver_id')
    # 未指定 → 若唯一在职候选则自动指定(多数业务线只有1人,无需手选);多个才要求选
    if not approver_id:
        from app.helpers.project_hold_helpers import resolve_win_lock_candidates
        _cands, _cerr = resolve_win_lock_candidates(p, exclude_user_id=current_user.id)
        _cands = list(_cands or [])
        if len(_cands) == 1:
            approver_id = _cands[0].id
        elif len(_cands) == 0:
            return jsonify({'success': False, 'message': _cerr or '未找到可用审核人'}), 400
        else:
            return jsonify({'success': False, 'message': '存在多个可选审核人，请选择'}), 400
    try:
        from app.helpers.project_hold_helpers import submit_win_lock
        inst, err = submit_win_lock(p, reason, current_user.id, approver_id,
                                    lock_q.id, delivery_date)
        if err:
            return jsonify({'success': False, 'message': err}), 400
        return jsonify({'success': True, 'message': '已提交成功锁定审核，待审核通过后生效'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'提交成功锁定审核失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500


@project.route('/at-api/<int:project_id>/win-lock-candidates')
@login_required
@permission_required('project', 'view')
def at_api_win_lock_candidates(project_id):
    """成功锁定审核人候选(供前端弹窗强制选择)。"""
    p = Project.query.get_or_404(project_id)
    if not _can_win_lock(p, current_user):
        return jsonify({'success': False, 'message': '无权限'}), 403
    from app.helpers.project_hold_helpers import resolve_win_lock_candidates
    cands, err = resolve_win_lock_candidates(p, exclude_user_id=current_user.id)
    if err:
        return jsonify({'success': False, 'message': err}), 400
    out = [{'id': u.id, 'name': u.real_name or u.username, 'role': u.role}
           for u in (cands or [])]
    if not out:
        return jsonify({'success': False, 'message': '没有可指定的审核人(可选人均为您本人或缺位)'}), 400
    return jsonify({'success': True, 'candidates': out})


@project.route('/at-api/<int:project_id>/win-unlock', methods=['POST'])
@login_required
@permission_required('project', 'view')
def at_api_win_unlock(project_id):
    """人为解除成功锁定(权限同锁定)"""
    p = Project.query.get_or_404(project_id)
    if not _can_win_lock(p, current_user):
        return jsonify({'success': False, 'message': '仅项目负责人/厂商销售负责人/部门经理可解除'}), 403
    if not p.win_locked:
        return jsonify({'success': False, 'message': '该项目未处于锁定成功状态'}), 400
    try:
        from app.utils.change_tracker import ChangeTracker
        old_values = {'win_locked': True, 'win_lock_reason': p.win_lock_reason}
        p.win_locked = False
        p.win_lock_reason = None
        p.win_locked_by = None
        p.win_locked_at = None
        p.win_locked_quotation_id = None
        p.win_locked_amount = None
        db.session.commit()
        try:
            ChangeTracker.log_update(p, old_values, {'win_locked': False, 'win_lock_reason': None})
        except Exception:
            pass
        return jsonify({'success': True, 'message': '已解除锁定'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'解除成功锁定失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500


@project.route('/at-api/<int:project_id>/fail-attribution', methods=['POST'])
@login_required
@permission_required('project', 'view')
def at_api_fail_attribution(project_id):
    """CEO 对已失败项目补录责任认定(个人因素为主/团队管理失责),输入内容作为 CEO 认定评语。仅 CEO 有效。"""
    if current_user.role != 'ceo':
        return jsonify({'success': False, 'message': '仅总经理(CEO)可补录责任认定'}), 403
    p = Project.query.get_or_404(project_id)
    if (p.current_stage or '') != 'lost':
        return jsonify({'success': False, 'message': '仅失败项目可补录责任认定'}), 400
    data = request.get_json(silent=True) or {}
    # 个人因素 / 团队管理失责 可同时成立(非二选一) → 接受列表;兼容旧单值 attribution
    attrs = data.get('attributions')
    if not attrs and data.get('attribution'):
        attrs = [data.get('attribution')]
    attrs = [a for a in (attrs or []) if a in ('owner_fault', 'mgmt_fault')]
    comment = (data.get('comment') or '').strip()
    if not attrs:
        return jsonify({'success': False, 'message': '请至少选择一种责任类型'}), 400
    if not comment:
        return jsonify({'success': False, 'message': '请填写认定评语'}), 400
    try:
        from datetime import datetime as _dt
        for a in attrs:
            setattr(p, f'fail_{a}', True)
        # 评语直接存到项目(不依赖审批实例 — 直接置失败、无审批流的项目也能展示)
        p.fail_attribution_note = comment
        p.fail_attribution_by = current_user.id
        p.fail_attribution_at = _dt.now()
        db.session.commit()
        return jsonify({'success': True, 'message': '责任认定已补录'})
    except Exception as e:
        db.session.rollback()
        logger.error(f'补录责任认定失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500


@project.route('/<int:project_id>/at_view')
@login_required
@permission_required('project', 'view')
def at_view_project(project_id):
    """AT 风格项目详情页"""
    from app.utils.related_data import RelatedDataService
    from app.models.action import Action
    from app.models.project_customer_association import ProjectCustomerAssociation
    from app.models.customer import Company

    p = Project.query.get_or_404(project_id)
    if not can_view_project(current_user, p):
        from flask import abort
        abort(403)

    related = RelatedDataService.fetch_all('project', project_id, current_user, limit=5)

    # 关联客户(双向多对多)— 返回 [(company, association_id)] 供模板移除按钮用
    _assoc_rows = db.session.query(
        Company, ProjectCustomerAssociation.id
    ).join(
        ProjectCustomerAssociation, ProjectCustomerAssociation.company_id == Company.id
    ).filter(
        ProjectCustomerAssociation.project_id == project_id,
        Company.is_deleted == False,
    ).all()
    # 给 Company 实例挂一个轻量属性 _assoc_id 方便模板取,不改模型
    associated_companies = []
    for _c, _aid in _assoc_rows:
        _c._assoc_id = _aid
        associated_companies.append(_c)

    # 项目跟进
    actions = get_viewable_data(Action, current_user,
        [Action.project_id == project_id]
    ).order_by(Action.created_at.desc()).limit(20).all()

    from app.utils.lockable import can_edit_with_lock
    from app.utils.access_control import can_delete_project
    perms = {
        # can_edit 同时考虑权限和锁定:被审批锁定的项目非 admin 不能编辑
        'can_edit':          can_edit_with_lock(p, current_user),
        'can_delete':        can_delete_project(current_user, p),
        'can_change_owner':  can_change_project_owner(current_user, p),
        'can_create_action': True,
    }

    # ─── 阶段进度条 stages 数组 ───
    # 9 阶段:发现 → 植入 → 标前 → 标中 → 中标 → 批价 → 签约;旁支:失败 / 搁置
    from app.models.projectpm_stage_history import ProjectStageHistory
    _stage_order = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed']
    from flask_babel import gettext as _sg
    _stage_labels = {'discover':_sg('发现'),'embed':_sg('植入'),'pre_tender':_sg('标前'),'tendering':_sg('标中'),
                     'awarded':_sg('中标'),'quoted':_sg('批价'),'signed':_sg('签约'),'lost':_sg('失败'),'paused':_sg('搁置')}
    # 阶段图标 — 移植自 TW 项目阶段(Material Symbols);AT 阶段条 icon_set='material' 渲染
    _stage_icons  = {'discover':'travel_explore','embed':'biotech','pre_tender':'manage_search',
                     'tendering':'gavel','awarded':'emoji_events','quoted':'payments','signed':'handshake'}
    _history = ProjectStageHistory.query.filter_by(project_id=project_id)\
        .order_by(ProjectStageHistory.change_date.asc(), ProjectStageHistory.id.asc()).all()
    # 每个阶段的进入时间(以 to_stage 为准,首次进入)
    _enter_date = {}
    for h in _history:
        if h.to_stage not in _enter_date:
            _enter_date[h.to_stage] = h.change_date.strftime('%Y-%m-%d') if h.change_date else ''
    cur = p.current_stage or 'discover'
    # 失败/搁置 → 把 current 落在历史中最后一个正常阶段,其余为 future,在 cur 节点单独高亮异常态
    _abnormal = cur in ('lost', 'paused')
    last_normal = None
    if _abnormal:
        for h in reversed(_history):
            if h.from_stage in _stage_order:
                last_normal = h.from_stage; break
        last_normal = last_normal or 'discover'
    stages = []
    reached = True
    for s in _stage_order:
        if _abnormal:
            if s == last_normal:
                status = 'current'; reached = False
            elif reached:
                status = 'done'
            else:
                status = 'future'
        else:
            if s == cur:
                status = 'current'; reached = False
            elif reached:
                status = 'done'
            else:
                status = 'future'
        stages.append({
            'key':    s,
            'label':  _stage_labels[s],
            'icon':   _stage_icons.get(s, 'check'),
            'status': status,
            'date':   _enter_date.get(s, ''),
            'attachments': [],
        })

    # 共享用户
    from app.models.user import User as _U
    shared_users = []
    if p.share_enabled and p.shared_with_users:
        shared_users = _U.query.filter(_U.id.in_(p.shared_with_users)).all()

    # 共享设置 modal 需要的用户树(perms.can_edit 时才传)
    shareable_users_tree = None
    if perms.get('can_edit'):
        from app.utils.sharing import get_shareable_users_tree
        try:
            shareable_users_tree = get_shareable_users_tree(current_user, 'project')
        except Exception:
            shareable_users_tree = []

    # 项目审批 — 跟采购订单同范式:_impl 纯函数 + thin wrapper
    approval = None
    try:
        from app.helpers.at_project_helpers import build_approval_data as _build_project_approval
        _flow_result = _get_project_approval_flow_impl(project_id)
        if isinstance(_flow_result, tuple):
            _flow_result = _flow_result[0]
        if _flow_result and _flow_result.get('success') and _flow_result.get('has_approval'):
            approval = _build_project_approval(p, _flow_result)
    except Exception as _appr_err:
        current_app.logger.warning(f"构造项目审批流数据失败: {_appr_err}")

    # 是否可提交报备审批(admin / owner / vendor_sales_manager)
    can_submit_approval = (
        current_user.role == 'admin'
        or p.owner_id == current_user.id
        or (p.vendor_sales_manager_id and p.vendor_sales_manager_id == current_user.id)
    )

    # ─── 失败/搁置审核(project_hold) chip + 发起入口上下文 ───
    from app.helpers.project_hold_helpers import get_pending_hold_instance
    _hold_inst = get_pending_hold_instance(project_id)
    hold_pending = _hold_inst is not None
    hold_target = (_hold_inst.template_snapshot or {}).get('hold_target') if _hold_inst else None
    # 发起权限与后端 request_project_hold / 成功锁定对齐(_can_win_lock):
    # 项目负责人 / 厂商销售负责人 / 项目负责人的部门经理 / admin;正常阶段且无进行中 hold
    can_request_hold = (
        _can_win_lock(p, current_user)
        and not _abnormal
        and not hold_pending
    )

    # ─── 失败项目:展示已通过的失败审批理由 + 责任认定(审批通过后 chip 消失,这里补全可见)───
    fail_approval = None
    if cur == 'lost':
        try:
            from app.models.approval import ApprovalInstance, ApprovalStatus, ApprovalRecord
            from app.models.user import User as _U
            _fi = (ApprovalInstance.query
                   .filter(ApprovalInstance.object_type == 'project_hold',
                           ApprovalInstance.object_id == project_id,
                           ApprovalInstance.status == ApprovalStatus.APPROVED)
                   .order_by(ApprovalInstance.started_at.desc()).first())
            if _fi and (_fi.template_snapshot or {}).get('hold_target') == 'lost':
                _snap = _fi.template_snapshot or {}
                _initor = _U.query.get(_snap.get('hold_initiator_id')) if _snap.get('hold_initiator_id') else None
                _recs = (ApprovalRecord.query.filter_by(instance_id=_fi.id)
                         .order_by(ApprovalRecord.timestamp.asc()).all())
                _rlist = []
                for _r in _recs:
                    if _r.action == 'skipped':
                        continue
                    _ru = _U.query.get(_r.approver_id) if _r.approver_id else None
                    _rlist.append({
                        'name': (_ru.real_name or _ru.username) if _ru else '—',
                        'action': _r.action,
                        'comment': _r.comment or '',
                        'time': _r.timestamp.strftime('%Y-%m-%d %H:%M') if _r.timestamp else '',
                    })
                fail_approval = {
                    'reason': _snap.get('hold_reason') or '',
                    'initiator': (_initor.real_name or _initor.username) if _initor else '',
                    'records': _rlist,
                }
        except Exception as _fa_err:
            current_app.logger.warning(f"加载失败审批信息失败: {_fa_err}")

    # CEO 补录的责任认定评语(存项目自身,不依赖审批实例)
    fail_attribution = None
    if cur == 'lost' and getattr(p, 'fail_attribution_note', None):
        _ab = User.query.get(p.fail_attribution_by) if p.fail_attribution_by else None
        fail_attribution = {
            'note': p.fail_attribution_note,
            'by': (_ab.real_name or _ab.username) if _ab else '',
            'at': p.fail_attribution_at.strftime('%Y-%m-%d %H:%M') if p.fail_attribution_at else '',
        }

    # 项目附件:补全上传人姓名(新文件已存 uploaded_by_name,旧文件按 uploaded_by 反查)
    project_attachments = []
    try:
        _raw = p.attachments_list
        # 附件按创建人隔离(与图纸统一口径):创建人 / 厂商 / 上级 / 角色(方案·产品经理) / admin。
        # 老数据(无 uploaded_by)归项目负责人名义。(能到详情页=已过 can_view_project)
        from app.models.user import Affiliation
        _aff_owner_ids = {aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=current_user.id).all()}
        _att_full = (current_user.role in ('admin', 'solution_manager', 'product_manager')
                     or getattr(p, 'vendor_sales_manager_id', None) == current_user.id)
        _uids = {a.get('uploaded_by') for a in _raw if a.get('uploaded_by')}
        _umap = {}
        if _uids:
            from app.models.user import User as _U
            for _u in _U.query.filter(_U.id.in_(_uids)).all():
                _umap[_u.id] = _u.real_name or _u.username
        for a in _raw:
            _uid = a.get('uploaded_by') or p.owner_id   # 老数据归项目负责人
            if not (_att_full or _uid == current_user.id or _uid in _aff_owner_ids):
                continue
            a = dict(a)
            a['uploader'] = a.get('uploaded_by_name') or _umap.get(a.get('uploaded_by')) or ''
            project_attachments.append(a)
    except Exception as _att_err:
        current_app.logger.warning(f"加载项目附件失败: {_att_err}")
        project_attachments = []

    # 项目系统图(系统设计卡;复用 system_diagram 模块,只读加载)
    try:
        from app.models.system_diagram import SystemDiagram
        from app.views.system_diagram import _can_view_diagram
        _all_dg = (SystemDiagram.query
                   .filter_by(project_id=p.id, is_deleted=False)
                   .order_by(SystemDiagram.updated_at.desc()).all())
        # 逐图按统一口径过滤(创建人/厂商/上级/角色),不再"能看项目就全看"
        project_diagrams = [d for d in _all_dg if _can_view_diagram(d)]
    except Exception as _dg_err:
        current_app.logger.warning(f"加载项目系统图失败: {_dg_err}")
        project_diagrams = []

    _win_locker = User.query.get(p.win_locked_by) if p.win_locked_by else None
    from app.models.quotation import Quotation as _Q
    _lock_quotes = [{'id': q.id, 'number': q.quotation_number,
                     'amount': float(q.amount or 0), 'currency': q.currency or 'CNY'}
                    for q in _Q.query.filter_by(project_id=p.id).order_by(_Q.created_at.desc()).all()]
    _locked_q = next((q for q in _lock_quotes if q['id'] == p.win_locked_quotation_id), None)

    # 成功锁定审核:进行中实例(徽章橙) + 审核人候选(弹窗强制选)
    from app.helpers.project_hold_helpers import get_pending_win_lock_instance, resolve_win_lock_candidates
    from app.utils.role_mappings import get_role_display_name
    # 审核中:用 AT 通用审批组件(at_approval_dropdown)就地展示流程,流程数据由 /project/api/win-lock/<id>/flow 提供
    win_lock_pending = bool(get_pending_win_lock_instance(p.id))
    win_lock_candidates = []
    if _can_win_lock(p, current_user) and not p.win_locked and not win_lock_pending:
        _cands, _cerr = resolve_win_lock_candidates(p, exclude_user_id=current_user.id)
        if _cands:
            win_lock_candidates = [{'id': u.id, 'name': u.real_name or u.username,
                                    'role_label': get_role_display_name(u.role)}
                                   for u in _cands]
    return render_template('project/at_view.html',
                           project=p,
                           can_win_lock=_can_win_lock(p, current_user),
                           win_locker_name=(_win_locker.real_name or _win_locker.username) if _win_locker else '',
                           lock_quotations=_lock_quotes,
                           locked_quotation=_locked_q,
                           related=related,
                           companies=associated_companies,
                           actions=actions,
                           perms=perms,
                           stages=stages,
                           abnormal_status=cur if _abnormal else None,
                           abnormal_label=_stage_labels.get(cur) if _abnormal else None,
                           shared_users=shared_users,
                           shareable_users_tree=shareable_users_tree,
                           approval=approval,
                           can_submit_approval=can_submit_approval,
                           hold_pending=hold_pending,
                           hold_target=hold_target,
                           can_request_hold=can_request_hold,
                           fail_approval=fail_approval,
                           fail_attribution=fail_attribution,
                           win_lock_pending=win_lock_pending,
                           win_lock_candidates=win_lock_candidates,
                           recover_stage=(last_normal if _abnormal else None),
                           project_attachments=project_attachments,
                           project_diagrams=project_diagrams)


@project.route('/at_list')
@login_required
@permission_required('project', 'view')
def at_list_view():
    """AT 风格项目列表"""
    from sqlalchemy import or_
    page = max(int(request.args.get('page', 1)), 1)
    per_page = 30
    tab = request.args.get('tab', 'all')
    search = request.args.get('search', '').strip()
    # 多选:同名多个 query 参数(阶段维度已由 tab 表达,这里不再重复筛选)
    owner_values = [v for v in request.args.getlist('owner') if v.strip()]
    ptype_values = [v for v in request.args.getlist('ptype') if v.strip()]
    vsm_values = [v for v in request.args.getlist('vsm') if v.strip()]  # 厂商销售负责人(多选)

    base = get_viewable_data(Project, current_user).filter(Project.is_deleted == False)

    # ── 筛选选项(基于可见数据 → 天然含权限+归属);能看到他人数据才显示筛选 ──
    from app.utils.dictionary_helpers import project_type_label
    from app.utils.access_control import build_owner_filter_options
    _owner_ids = [r[0] for r in base.with_entities(Project.owner_id).distinct().all() if r[0]]
    show_filter = any(oid != current_user.id for oid in _owner_ids)
    owner_options = build_owner_filter_options(_owner_ids)
    type_options = [(t, project_type_label(t)) for t in sorted(
        {x[0] for x in base.with_entities(Project.project_type).distinct().all() if x[0]})]
    # 厂商销售负责人筛选选项(可见数据中出现过的)
    _vsm_ids = [r[0] for r in base.with_entities(Project.vendor_sales_manager_id).distinct().all() if r[0]]
    vsm_options = build_owner_filter_options(_vsm_ids)

    # ── 应用筛选(多选 → IN)──
    _owner_ids_sel = [int(v) for v in owner_values if v.isdigit()]
    if _owner_ids_sel:
        base = base.filter(Project.owner_id.in_(_owner_ids_sel))
    if ptype_values:
        base = base.filter(Project.project_type.in_(ptype_values))
    _vsm_ids_sel = [int(v) for v in vsm_values if v.isdigit()]
    if _vsm_ids_sel:
        base = base.filter(Project.vendor_sales_manager_id.in_(_vsm_ids_sel))

    # tab → current_stage
    TAB_STAGE_MAP = {
        'discover':   ['discover'],
        'embed':      ['embed'],
        'pre_tender': ['pre_tender'],
        'quoted':     ['quoted'],
        'tendering':  ['tendering'],
        'awarded':    ['awarded'],
        'signed':     ['signed'],            # 签约(独立 tab)
        'closed':     ['lost', 'paused'],
    }
    # 「全部」排除 搁置/失败/签约(只看进行中管道);NULL 阶段仍计入
    _EXCLUDE_FROM_ALL = ['paused', 'lost', 'signed']
    _all_filter = or_(Project.current_stage.is_(None),
                      Project.current_stage.notin_(_EXCLUDE_FROM_ALL))

    tab_counts = {'all': base.filter(_all_filter).count()}
    for k, stages in TAB_STAGE_MAP.items():
        tab_counts[k] = base.filter(Project.current_stage.in_(stages)).count()
    # 锁定成功(锁单预判)tab:跨阶段标记,签约自动解除
    # 锁定成功:win_locked 且未签约(签约后锁单预判已兑现,与列表 🏆 徽章口径一致)
    tab_counts['win_locked'] = base.filter(Project.win_locked.is_(True), Project.current_stage != 'signed').count()

    q = base
    if tab in TAB_STAGE_MAP:
        q = q.filter(Project.current_stage.in_(TAB_STAGE_MAP[tab]))
    elif tab == 'win_locked':
        q = q.filter(Project.win_locked.is_(True), Project.current_stage != 'signed')
    else:  # 全部:排除 搁置/失败/签约
        q = q.filter(_all_filter)

    if search:
        like = f'%{search}%'
        q = q.filter(or_(
            Project.project_name.ilike(like),
            Project.authorization_code.ilike(like),
        ))

    # 当前 tab+筛选下的报价总额(全量,非仅当页)。
    # 跨币种(SG: MYR/SGD/USD)用 MultiCurrencyAggregationService 按行换算到实例默认币种
    # (ovs=USD / sp8d=CNY),与仪表盘漏斗同一套口径;sp8d 全 CNY 时为无损相加。
    from app.services.multi_currency_aggregation import MultiCurrencyAggregationService
    tab_total_amount = MultiCurrencyAggregationService.sum_converted(
        q, Project.quotation_customer, Project.quotation_currency
    )

    # 列排序(可点击表头):白名单字段,NULL 值排最后,id 兜底保证稳定次序
    from app.utils.query_filters import extract_sort_params
    from sqlalchemy import nullslast
    _SORT_COLS = {
        'created_at': Project.created_at, 'updated_at': Project.updated_at,
        'delivery_forecast': Project.delivery_forecast,
        'quotation_customer': Project.quotation_customer,
    }
    sort_field, sort_order = extract_sort_params(
        request.args, default_sort='updated_at', default_order='desc',
        allowed_fields=list(_SORT_COLS.keys()))
    _col = _SORT_COLS[sort_field]
    _ordered = _col.desc() if sort_order == 'desc' else _col.asc()
    pagination = q.order_by(nullslast(_ordered), Project.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False,
    )

    # 当页中"成功锁定审核中"的项目(徽章橙;批量查避免 N+1)
    win_lock_pending_ids = set()
    try:
        from app.models.approval import ApprovalInstance, ApprovalStatus
        _pg_ids = [pp.id for pp in pagination.items]
        if _pg_ids:
            win_lock_pending_ids = {
                r[0] for r in db.session.query(ApprovalInstance.object_id).filter(
                    ApprovalInstance.object_type == 'project_win_lock',
                    ApprovalInstance.status == ApprovalStatus.PENDING,
                    ApprovalInstance.object_id.in_(_pg_ids),
                ).all()}
    except Exception as _wlp_err:
        logger.warning(f"批量查成功锁定审核中状态失败: {_wlp_err}")

    # 当页各项目「最新报价单」的确认状态(金额着色:confirmed→绿/reconfirm→橘;批量避免 N+1)
    quote_confirm_status = {}
    try:
        from app.models.quotation import Quotation
        from sqlalchemy import func as _qf
        _pg_ids2 = [pp.id for pp in pagination.items]
        if _pg_ids2:
            _latest = db.session.query(
                Quotation.project_id, _qf.max(Quotation.id).label('mid')
            ).filter(Quotation.project_id.in_(_pg_ids2)).group_by(Quotation.project_id).subquery()
            for pid, st in db.session.query(
                Quotation.project_id, Quotation.confirmation_badge_status
            ).join(_latest, Quotation.id == _latest.c.mid).all():
                quote_confirm_status[pid] = st
    except Exception as _qcs_err:
        logger.warning(f"批量查报价单确认状态失败: {_qcs_err}")

    # 非空查询参数(供 tab/分页链接保留筛选+搜索状态;多选 → 列表值)
    list_qs = {}
    if search:
        list_qs['search'] = search
    if owner_values:
        list_qs['owner'] = owner_values
    if ptype_values:
        list_qs['ptype'] = ptype_values
    if vsm_values:
        list_qs['vsm'] = vsm_values

    # 未跟进天数(当前页批量;排除 签约/暂停/失败;≥20 天才标识)
    overdue_days = {}
    try:
        from sqlalchemy import func as _f
        from app.models.action import Action
        from app.models.projectpm_stage_history import ProjectStageHistory
        from datetime import datetime as _dt, date as _date
        _page_ids = [pp.id for pp in pagination.items
                     if pp.current_stage not in ('signed', 'paused', 'lost')]
        if _page_ids:
            _last_act = dict(db.session.query(Action.project_id, _f.max(Action.date))
                             .filter(Action.project_id.in_(_page_ids))
                             .group_by(Action.project_id).all())
            _no_act = [pid for pid in _page_ids if pid not in _last_act]
            _since = {}
            if _no_act:
                _since = dict(db.session.query(ProjectStageHistory.project_id,
                                               _f.max(ProjectStageHistory.change_date))
                              .filter(ProjectStageHistory.project_id.in_(_no_act))
                              .group_by(ProjectStageHistory.project_id).all())
            _today, _now = _date.today(), _dt.now()
            for pp in pagination.items:
                if pp.id not in _page_ids:
                    continue
                _ld = _last_act.get(pp.id)
                if _ld:
                    _days = (_today - _ld).days
                else:
                    _b = _since.get(pp.id) or pp.created_at
                    _days = (_now - _b).days if _b else None
                if _days is not None and _days >= 20:
                    overdue_days[pp.id] = _days
    except Exception as _oe:
        logger.warning(f'overdue calc err: {_oe}')

    from app.helpers.quality_score import project_quality_scores
    quality_scores = project_quality_scores([p.id for p in pagination.items])

    return render_template('project/at_list.html',
                           projects=pagination.items,
                           sort_field=sort_field,
                           sort_order=sort_order,
                           overdue_days=overdue_days,
                           quote_confirm_status=quote_confirm_status,
                           quality_scores=quality_scores,
                           pagination=pagination,
                           tab_counts=tab_counts,
                           current_tab=tab,
                           search=search,
                           show_filter=show_filter,
                           owner_options=owner_options,
                           owner_values=owner_values,
                           type_options=type_options,
                           ptype_values=ptype_values,
                           vsm_options=vsm_options,
                           vsm_values=vsm_values,
                           win_lock_pending_ids=win_lock_pending_ids,
                           tab_total_amount=tab_total_amount,
                           list_qs=list_qs)




@project.route('/view/<int:project_id>')
@permission_required_with_approval_context('project', 'view')
def view_project(project_id):
    """旧 TW 项目详情 — 已重定向到 AT 风格详情"""
    return redirect(url_for('project.at_view_project', project_id=project_id))

@project.route('/add', methods=['GET', 'POST'])
@permission_required('project', 'create')
def add_project():
    if request.method == 'POST':
        try:
            # 验证必填字段
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/add.html', **get_project_form_data())
            # 报备日期不再强制要求，将在授权批准后自动设置
            # if not request.form.get('report_time'):
            #     flash('报备日期不能为空', 'danger')
            #     return render_template('project/add.html', **get_project_form_data())
            # 当前阶段不在创建页面显示，默认设为'discover'阶段
            # if not request.form.get('current_stage'):
            #     flash('当前阶段不能为空', 'danger')
            #     return render_template('project/add.html', **get_project_form_data())
            if not request.form.get('industry'):
                flash('项目行业不能为空', 'danger')
                return render_template('project/add.html', **get_project_form_data())
            
            # 解析日期 - 只有在授权批准后才设置报备日期，创建时不设置
            report_time = None  # 初始创建时不设置报备日期
            # if request.form.get('report_time'):
            #     report_time = datetime.strptime(request.form['report_time'], '%Y-%m-%d').date()
                
            delivery_forecast = None
            if request.form.get('delivery_forecast'):
                delivery_forecast = datetime.strptime(request.form['delivery_forecast'], '%Y-%m-%d').date()
            
            # 获取项目类型
            from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS
            project_type = request.form.get('project_type', '').strip()
            if not project_type:
                project_type = None
            elif project_type not in PROJECT_TYPE_LABELS:
                # 反查中文 label 对应的 key
                reverse_lookup = {v['zh']: k for k, v in PROJECT_TYPE_LABELS.items()}
                project_type = reverse_lookup.get(project_type, None)
            # 如果 project_type 是合法英文 key，则保留原样

            # 不再自动生成授权编号，授权编号必须通过申请流程获得
            authorization_code = None
            
            # 报价字段设置为无效，不处理
            quotation_customer = None
            
            # 自动设置销售负责人
            vendor_sales_manager_id = request.form.get('vendor_sales_manager_id')
            
            # 如果厂商销售负责人字段为空，默认将拥有人账户作为内容
            if not vendor_sales_manager_id and current_user.is_vendor_user():
                vendor_sales_manager_id = current_user.id
            
            project = Project(
                project_name=request.form['project_name'],
                report_time=report_time,
                report_source=request.form.get('report_source'),
                product_situation=request.form.get('product_situation'),
                delivery_forecast=delivery_forecast,
                current_stage='discover',  # 默认从发现阶段开始
                stage_description=request.form.get('stage_description'),
                authorization_code=authorization_code,
                project_type=project_type,
                quotation_customer=quotation_customer,
                industry=request.form.get('industry'),  # 添加行业字段
                created_by=current_user.id,  # 设置创建人（不可变）
                owner_id=current_user.id,  # 设置当前负责人（可修改）
                vendor_sales_manager_id=vendor_sales_manager_id  # 设置厂商销售负责人
            )
            
            db.session.add(project)

            # 发放积分：新建项目（flush 确保 project.id 已生成）
            try:
                from app.services.points_service import award_points
                db.session.flush()
                award_points(
                    user_id=current_user.id,
                    behavior_code='project_create',
                    source_type='project',
                    source_id=project.id,
                    context=project.project_name
                )
            except Exception as pts_err:
                logger.warning(f"发放项目创建积分失败: {pts_err}")

            db.session.commit()

            # 记录创建历史
            try:
                ChangeTracker.log_create(project)
            except Exception as track_err:
                logger.warning(f"记录项目创建历史失败: {str(track_err)}")

            # 记录工作项
            record_activity('create', 'project', project.project_name, current_user,
                project_id=project.id,
                start_time_str=request.form.get('page_open_time'),
                description=f'创建项目 {project.project_name}')

            # 新增：每次保存后自动刷新活跃度
            update_active_status(project)
            
            # 项目保存后触发评分重新计算
            try:
                from app.models.project_scoring import ProjectScoringEngine
                ProjectScoringEngine.calculate_project_score(project.id, commit=True)
                current_app.logger.info(f"项目 {project.project_name} 更新后评分已重新计算")
            except Exception as score_err:
                current_app.logger.warning(f"项目更新后评分重新计算失败: {str(score_err)}")

            # 如果来自潜在项目，标记已转化
            from_prospect_id = request.form.get('from_prospect_id', type=int)
            if from_prospect_id:
                try:
                    prospect = ProspectProject.query.get(from_prospect_id)
                    if prospect and not prospect.is_deleted:
                        prospect.converted_project_id = project.id
                        db.session.commit()
                except Exception as pe:
                    logger.warning(f"标记潜在项目转化失败: {pe}")

            flash('项目添加成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存项目失败: {str(e)}", exc_info=True)
            flash(f'保存失败：{str(e)}', 'danger')
            return render_template('project/add.html', **get_project_form_data())
    
    # 从潜在项目预填
    prospect_prefill = {}
    from_prospect_id = request.args.get('from_prospect', type=int)
    if from_prospect_id:
        prospect = ProspectProject.query.filter_by(id=from_prospect_id, is_deleted=False).first()
        if prospect:
            prospect_prefill['project_name'] = prospect.project_name
            prospect_prefill['industry'] = prospect.industry or ''
            # 找建设单位作为 end_user 参考
            owner_sh = prospect.stakeholders.filter_by(stakeholder_type='owner').first()
            if owner_sh:
                prospect_prefill['owner_company'] = owner_sh.company_name

    return render_template(
        'project/add.html',
        from_prospect_id=from_prospect_id,
        prospect_prefill=prospect_prefill,
        **get_project_form_data()
    )

# 辅助函数，获取公司数据
def get_company_data():
    company_query = get_viewable_data(Company, current_user)
    return {
        key: company_query.filter_by(company_type=key).all()
        for key in COMPANY_TYPE_LABELS.keys()
    }

# 新的项目表单数据逻辑函数
def get_project_form_data():
    """获取项目表单需要的数据（创建和编辑通用）"""
    return {
        'PRODUCT_SITUATION_OPTIONS': get_product_situation_options(),
        'REPORT_SOURCE_OPTIONS': get_report_source_options(),
        'PROJECT_TYPE_OPTIONS': get_project_type_options(),
        'PROJECT_STAGE_OPTIONS': get_project_stage_options(),
        'INDUSTRY_OPTIONS': get_industry_options(),
        **get_company_data()
    }


# ─── AT 风格新建项目模态 — 选项列表 + 创建 API ───
@project.route('/api/form-options', methods=['GET'])
@login_required
def api_project_form_options():
    """返回 AT 新建项目 modal 用的下拉选项(标准格式 [{code, label}])。

    厂商销售下拉走 vendor-sales-manager-selector.js 自己的 API,不在此处。
    """
    def _norm(opts):
        # opts 形如 [('code','中文')] 或 [{'code':..,'label':..}]
        out = []
        for o in (opts or []):
            if isinstance(o, dict):
                out.append({'code': o.get('code') or o.get('key') or '',
                            'label': o.get('label') or o.get('value') or ''})
            elif isinstance(o, (list, tuple)) and len(o) >= 2:
                out.append({'code': o[0], 'label': o[1]})
        return out
    from app.helpers.project_helpers import forced_project_type_for, can_edit_project_type
    return jsonify({
        'success': True,
        'project_types':       _norm(get_project_type_options()),
        'industries':          _norm(get_industry_options()),
        'report_sources':      _norm(get_report_source_options()),
        'product_situations':  _norm(get_product_situation_options()),
        # 项目类型按角色锁定: 创建态锁定角色的强制类型(null=可自由选);
        # 编辑态是否可改类型(仅 admin/business_admin)
        'forced_project_type':  forced_project_type_for(current_user),
        'can_edit_project_type': can_edit_project_type(current_user),
    })


@project.route('/api/at-create', methods=['POST'])
@login_required
@permission_required('project', 'create')
def api_at_create_project():
    """AT 新建项目 API — JSON 输入/输出,创建后返回 project_id 让前端跳详情。

    复用 add_project 的字段处理逻辑(report_time 自动留空 / project_type 反查
    中文标签 / vendor_sales_manager 默认厂商用户自填)。
    """
    from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS
    data = request.get_json() or {}

    project_name = (data.get('project_name') or '').strip()
    if not project_name:
        return jsonify({'success': False, 'message': '项目名称不能为空'}), 400

    industry = (data.get('industry') or '').strip()
    if not industry:
        return jsonify({'success': False, 'message': '项目行业不能为空'}), 400

    description = (data.get('stage_description') or '').strip()
    if not description:
        return jsonify({'success': False, 'message': '项目描述不能为空'}), 400

    # 项目类型:接受英文 key,也兼容中文 label 反查(对齐 add_project)
    project_type = (data.get('project_type') or '').strip()
    if project_type and project_type not in PROJECT_TYPE_LABELS:
        reverse_lookup = {v['zh']: k for k, v in PROJECT_TYPE_LABELS.items()}
        project_type = reverse_lookup.get(project_type) or ''
    # 角色锁定: 锁定角色强制按角色定类型(忽略前端传值,即便为空也强制填上)
    from app.helpers.project_helpers import resolve_create_project_type
    project_type = resolve_create_project_type(current_user, project_type)
    if not project_type:
        return jsonify({'success': False, 'message': '项目类型不能为空'}), 400
    if project_type not in PROJECT_TYPE_LABELS:
        return jsonify({'success': False, 'message': '项目类型无效'}), 400

    report_source = (data.get('report_source') or '').strip() or None

    # 报备时间:创建时**故意不落库**(对齐 TW 行为)— 正式报备时间由授权批准
    # 流程设置;UI 默认显示今天仅供参考,即使用户填了也不写
    report_time = None

    delivery_forecast = None
    df_str = (data.get('delivery_forecast') or '').strip()
    if df_str:
        try:
            delivery_forecast = datetime.strptime(df_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # 厂商销售负责人:为空时,如当前用户是厂商用户自填
    vendor_sales_manager_id = data.get('vendor_sales_manager_id') or None
    if not vendor_sales_manager_id and current_user.is_vendor_user():
        vendor_sales_manager_id = current_user.id
    if vendor_sales_manager_id:
        try:
            vendor_sales_manager_id = int(vendor_sales_manager_id)
        except (TypeError, ValueError):
            vendor_sales_manager_id = None

    try:
        # 地址字段(可选)— AddressPicker 会把结构化数据回写到这些字段
        _addr_lat = data.get('latitude')
        _addr_lng = data.get('longitude')
        try:
            _addr_lat = float(_addr_lat) if _addr_lat not in (None, '', 'null') else None
        except (TypeError, ValueError):
            _addr_lat = None
        try:
            _addr_lng = float(_addr_lng) if _addr_lng not in (None, '', 'null') else None
        except (TypeError, ValueError):
            _addr_lng = None

        new_project = Project(
            project_name=project_name,
            report_time=report_time,
            report_source=report_source,
            product_situation=(data.get('product_situation') or None),
            delivery_forecast=delivery_forecast,
            current_stage='discover',
            stage_description=description,
            authorization_code=None,
            project_type=project_type,
            industry=industry,
            quotation_customer=None,
            created_by=current_user.id,
            owner_id=current_user.id,
            vendor_sales_manager_id=vendor_sales_manager_id,
            # 地址(可选)
            address=(data.get('address') or '').strip() or None,
            country=(data.get('country') or '').strip() or None,
            region=(data.get('region') or '').strip() or None,
            city=(data.get('city') or '').strip() or None,
            latitude=_addr_lat,
            longitude=_addr_lng,
        )
        db.session.add(new_project)

        # 发放积分
        try:
            from app.services.points_service import award_points
            db.session.flush()
            award_points(
                user_id=current_user.id,
                behavior_code='project_create',
                source_type='project',
                source_id=new_project.id,
                context=new_project.project_name
            )
        except Exception as pts_err:
            logger.warning(f"发放项目创建积分失败: {pts_err}")

        db.session.commit()

        # 如果调用方传了 pre_associate_company_id(从客户详情新建),自动建客户关联
        _pre_company = data.get('pre_associate_company_id')
        if _pre_company:
            try:
                _pre_company = int(_pre_company)
                from app.services.project_customer_link_service import add_link
                add_link(current_user, new_project.id, _pre_company)
                db.session.commit()
            except Exception as e:
                logger.warning(f"自动关联客户失败 project={new_project.id} company={_pre_company}: {e}")
                db.session.rollback()

        # 创建历史 + 活动记录(失败不阻塞)
        try:
            ChangeTracker.log_create(new_project)
        except Exception as e:
            logger.warning(f"记录项目创建历史失败: {e}")
        try:
            record_activity('create', 'project', new_project.project_name, current_user,
                project_id=new_project.id,
                description=f'创建项目 {new_project.project_name}')
        except Exception as e:
            logger.warning(f"记录创建活动失败: {e}")

        return jsonify({
            'success': True,
            'project_id': new_project.id,
            'message': '项目已创建',
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"AT 新建项目失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


# ─── AT 编辑项目 — 加载数据 ───
@project.route('/api/<int:project_id>/at-data', methods=['GET'])
@login_required
def api_at_project_data(project_id):
    """返回 AT 编辑模态需要的项目数据(含 readonly 字段供展示)。"""
    p = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not p:
        return jsonify({'success': False, 'message': '项目不存在'}), 404
    if not can_view_project(current_user, p):
        return jsonify({'success': False, 'message': '无权访问该项目'}), 403

    # 当前阶段中文标签
    try:
        _stage_label = project_stage_label(p.current_stage) if p.current_stage else ''
    except Exception:
        _stage_label = p.current_stage or ''

    owner_name = ''
    if p.owner:
        owner_name = p.owner.real_name or p.owner.username

    return jsonify({
        'success': True,
        'data': {
            'id': p.id,
            'project_name':            p.project_name,
            'project_type':            p.project_type or '',
            'industry':                p.industry or '',
            'report_source':           p.report_source or '',
            'product_situation':       p.product_situation or '',
            'vendor_sales_manager_id': p.vendor_sales_manager_id,
            'report_time':             p.report_time.strftime('%Y-%m-%d') if p.report_time else '',
            'delivery_forecast':       p.delivery_forecast.strftime('%Y-%m-%d') if p.delivery_forecast else '',
            'stage_description':       p.stage_description or '',
            'address':                 p.address or '',
            'country':                 p.country or '',
            'region':                  p.region or '',
            'city':                    p.city or '',
            'latitude':                p.latitude,
            'longitude':               p.longitude,
            # 只读字段
            'authorization_code':      p.authorization_code or '',
            'current_stage':           p.current_stage or '',
            'current_stage_label':     _stage_label,
            'owner_name':              owner_name,
        }
    })


# ─── AT 编辑项目 — 提交更新 ───
@project.route('/api/<int:project_id>/at-update', methods=['POST'])
@login_required
def api_at_update_project(project_id):
    """AT 编辑模态提交 — 白名单更新,readonly 字段(report_time/authorization_code/
    current_stage/owner_id)忽略不写。"""
    from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS

    p = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not p:
        return jsonify({'success': False, 'message': '项目不存在'}), 404
    if not can_edit_data(p, current_user):
        return jsonify({'success': False, 'message': '无权编辑该项目'}), 403
    if p.is_locked and current_user.role != 'admin':
        return jsonify({'success': False, 'message': '项目已锁定,无法编辑'}), 403

    data = request.get_json() or {}

    # 必填校验
    project_name = (data.get('project_name') or '').strip()
    if not project_name:
        return jsonify({'success': False, 'message': '项目名称不能为空'}), 400
    industry = (data.get('industry') or '').strip()
    if not industry:
        return jsonify({'success': False, 'message': '项目行业不能为空'}), 400
    description = (data.get('stage_description') or '').strip()
    if not description:
        return jsonify({'success': False, 'message': '项目描述不能为空'}), 400

    project_type = (data.get('project_type') or '').strip()
    if project_type and project_type not in PROJECT_TYPE_LABELS:
        reverse_lookup = {v['zh']: k for k, v in PROJECT_TYPE_LABELS.items()}
        project_type = reverse_lookup.get(project_type) or ''
    # 编辑期类型修改权: 仅 admin/business_admin 可改, 其余忽略前端值保持原类型
    from app.helpers.project_helpers import resolve_update_project_type
    project_type = resolve_update_project_type(current_user, p.project_type, project_type)
    if not project_type:
        return jsonify({'success': False, 'message': '项目类型不能为空'}), 400
    if project_type not in PROJECT_TYPE_LABELS:
        return jsonify({'success': False, 'message': '项目类型无效'}), 400

    delivery_forecast = None
    df_str = (data.get('delivery_forecast') or '').strip()
    if df_str:
        try:
            delivery_forecast = datetime.strptime(df_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    vendor_sales_manager_id = data.get('vendor_sales_manager_id') or None
    if vendor_sales_manager_id:
        try:
            vendor_sales_manager_id = int(vendor_sales_manager_id)
        except (TypeError, ValueError):
            vendor_sales_manager_id = None

    # 地址相关
    _lat = data.get('latitude'); _lng = data.get('longitude')
    try:
        _lat = float(_lat) if _lat not in (None, '', 'null') else None
    except (TypeError, ValueError):
        _lat = None
    try:
        _lng = float(_lng) if _lng not in (None, '', 'null') else None
    except (TypeError, ValueError):
        _lng = None

    try:
        # 白名单 — 显式写允许修改的字段;readonly 字段(report_time/authorization_code/
        # current_stage/owner_id)即便前端传了也不写
        p.project_name           = project_name
        p.project_type           = project_type
        p.industry               = industry
        p.report_source          = (data.get('report_source') or '').strip() or None
        p.product_situation      = (data.get('product_situation') or '').strip() or None
        p.vendor_sales_manager_id = vendor_sales_manager_id
        p.delivery_forecast      = delivery_forecast
        p.stage_description      = description
        p.address                = (data.get('address') or '').strip() or None
        p.country                = (data.get('country') or '').strip() or None
        p.region                 = (data.get('region') or '').strip() or None
        p.city                   = (data.get('city') or '').strip() or None
        p.latitude               = _lat
        p.longitude              = _lng
        p.updated_at             = datetime.now()
        db.session.commit()

        # 变更历史(失败不阻塞)
        try:
            ChangeTracker.log_update(p)
        except Exception as e:
            logger.warning(f"记录项目更新历史失败: {e}")

        return jsonify({'success': True, 'project_id': p.id, 'message': '项目已更新'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"AT 更新项目失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500

# 新的编辑项目后台逻辑函数
def get_edit_project_data():
    """获取编辑项目需要的数据"""
    return get_project_form_data()

@project.route('/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以编辑自己的项目
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)

    # 使用统一的数据权限检查（包含数据归属逻辑）
    if not can_edit_data(project, current_user):
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试编辑无权限的项目: {project_id} (所有者: {project.owner_id})")
        flash('您没有权限编辑此项目', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查项目是否被锁定
    from app.helpers.project_helpers import is_project_editable
    is_editable, lock_reason = is_project_editable(project_id, current_user.id)
    if not is_editable and current_user.role != 'admin':
        flash(f'项目已被锁定，无法编辑: {lock_reason}', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    if request.method == 'POST':
        # 在修改前捕获旧值用于变更跟踪
        from app.utils.change_tracker import ChangeTracker
        old_values = ChangeTracker.capture_old_values(project)

        try:
            # 必填项校验
            if not request.form.get('project_name'):
                flash('项目名称不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            # 报备日期不在编辑页面显示，不需要验证
            # 当前阶段不在编辑页面显示，不需要验证
            # if not request.form.get('current_stage'):
            #     flash('当前阶段不能为空', 'danger')
            #     return render_template('project/edit.html', project=project, **get_edit_project_data())
            if not request.form.get('industry'):
                flash('项目行业不能为空', 'danger')
                return render_template('project/edit.html', project=project, **get_edit_project_data())
            # 报备日期不在编辑页面显示，不需要解析，保持原有值不变
            # 解析出货预测日期
            if request.form.get('delivery_forecast'):
                project.delivery_forecast = datetime.strptime(request.form['delivery_forecast'], '%Y-%m-%d').date()
            else:
                project.delivery_forecast = None
            # 更新项目信息
            project.project_name = request.form['project_name']
            project.report_source = request.form.get('report_source')
            project.product_situation = request.form.get('product_situation')
            project.industry = request.form.get('industry')  # 添加行业字段更新
            
            # 当前阶段不在编辑页面显示，不需要更新，保持原值
            old_stage = project.current_stage
            new_stage = project.current_stage  # 保持不变
            # 客户关联字段已从编辑表单中移除，在项目详情页单独管理
            project.stage_description = request.form.get('stage_description')
            
            # 更新销售负责人字段
            vendor_sales_manager_id = request.form.get('vendor_sales_manager_id')
            
            # 如果厂商销售负责人字段为空，默认将拥有人账户作为内容
            if not vendor_sales_manager_id and project.owner and project.owner.is_vendor_user():
                vendor_sales_manager_id = project.owner_id
            
            if vendor_sales_manager_id:
                project.vendor_sales_manager_id = int(vendor_sales_manager_id) if vendor_sales_manager_id != '' else None
            
            # 更新项目类型 - 只接受英文键
            new_project_type = request.form.get('project_type', 'normal')

            # 验证项目类型有效性
            if new_project_type not in ['normal', 'channel_follow', 'sales_focus', 'sales_key', 'business_opportunity']:
                new_project_type = 'normal'
            if new_project_type != project.project_type:
                project.project_type = new_project_type
            
            # 更新项目共享设置
            from app.utils.sharing import SharingService
            SharingService.update_sharing_from_request(project, current_user, 'project')
            
            db.session.commit()
            
            # 记录变更历史
            try:
                new_values = ChangeTracker.get_new_values(project, old_values.keys())
                ChangeTracker.log_update(project, old_values, new_values)
            except Exception as track_err:
                logger.warning(f"记录项目变更历史失败: {str(track_err)}")
            
            # 新增：每次保存后自动刷新活跃度（必须在commit之后调用）
            try:
                logger.info(f"项目编辑保存后更新活跃状态: 项目 ID {project.id}, 名称: {project.project_name}")
                logger.info(f"更新前活跃状态: {project.is_active}, 更新时间: {project.updated_at}")
                update_active_status(project, commit=True)
                # 重新查询项目以获取最新状态
                db.session.refresh(project)
                logger.info(f"更新后活跃状态: {project.is_active}")
            except Exception as activity_err:
                logger.error(f"更新项目活跃状态失败: {str(activity_err)}")
            
            # 项目保存后触发评分重新计算
            try:
                from app.models.project_scoring import ProjectScoringEngine
                ProjectScoringEngine.calculate_project_score(project.id, commit=True)
                current_app.logger.info(f"项目 {project.project_name} 更新后评分已重新计算")
            except Exception as score_err:
                current_app.logger.warning(f"项目更新后评分重新计算失败: {str(score_err)}")

            flash('项目信息已更新！', 'success')
            return redirect(url_for('project.view_project', project_id=project.id))
        except Exception as e:
            import sqlalchemy
            db.session.rollback()
            # 详细日志
            logger.error(f"编辑项目保存异常，表单内容: {dict(request.form)}，异常类型: {type(e).__name__}, 信息: {str(e)}")
            if isinstance(e, sqlalchemy.exc.InvalidRequestError) and 'closed' in str(e).lower():
                flash('保存失败：数据库会话已关闭，请刷新页面后重试。如多次出现请联系管理员。', 'danger')
            else:
                flash(f'保存失败：{type(e).__name__}: {str(e)}', 'danger')
    
    # GET请求：返回编辑页面
    return render_template(
        'project/edit.html',
        project=project,
        **get_edit_project_data()
    )

@project.route('/api/check_delete_dependencies/<int:project_id>', methods=['GET'])
@login_required
def check_delete_dependencies(project_id):
    """检查项目删除前的关联数据"""
    from app.models.approval import ApprovalInstance

    proj = Project.query.get_or_404(project_id)

    # 使用统一的数据权限检查
    if not can_edit_data(proj, current_user):
        return jsonify({'success': False, 'message': '您没有权限删除此项目'}), 403

    dependencies = {
        'quotations': [],      # 报价单（可删除）
        'pricing_orders': [],  # 批价单（不可删除，带锁）
        'actions': [],         # 跟进记录（可删除）
        'approvals': []        # 审批实例（可删除）
    }

    # 1. 收集报价单
    quotations = Quotation.query.filter_by(project_id=project_id).all()
    quotation_ids = [q.id for q in quotations]
    for q in quotations:
        dependencies['quotations'].append({
            'id': q.id,
            'name': q.quotation_number or f'报价单#{q.id}',
            'deletable': True
        })

    # 2. 收集批价单（通过报价单关联）
    if quotation_ids:
        pricing_orders = PricingOrder.query.filter(PricingOrder.quotation_id.in_(quotation_ids)).all()
        for po in pricing_orders:
            dependencies['pricing_orders'].append({
                'id': po.id,
                'name': po.order_number or f'批价单#{po.id}',
                'deletable': False  # 批价单不可删除
            })

    # 3. 收集跟进记录
    actions = Action.query.filter_by(project_id=project_id).all()
    for a in actions:
        dependencies['actions'].append({
            'id': a.id,
            'name': f'跟进记录#{a.id}',
            'deletable': True
        })

    # 4. 收集项目审批实例
    project_approvals = ApprovalInstance.query.filter_by(
        object_type='project',
        object_id=project_id
    ).all()
    for ap in project_approvals:
        dependencies['approvals'].append({
            'id': ap.id,
            'name': f'项目审批#{ap.id}',
            'deletable': True
        })

    # 5. 收集报价单审批实例
    if quotation_ids:
        quotation_approvals = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'quotation',
            ApprovalInstance.object_id.in_(quotation_ids)
        ).all()
        for ap in quotation_approvals:
            dependencies['approvals'].append({
                'id': ap.id,
                'name': f'报价单审批#{ap.id}',
                'deletable': True
            })

    has_pricing_orders = len(dependencies['pricing_orders']) > 0

    return jsonify({
        'success': True,
        'can_delete': not has_pricing_orders,
        'block_reason': '存在批价单，无法删除项目。请先删除或转移批价单。' if has_pricing_orders else None,
        'project_name': proj.project_name,
        'dependencies': dependencies,
        'summary': {
            'total_count': sum(len(v) for v in dependencies.values()),
            'blocked_count': len(dependencies['pricing_orders'])
        }
    })


@project.route('/delete/<int:project_id>', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以删除自己的项目数据
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)

    # 使用统一的数据权限检查（包含数据归属逻辑）
    if not can_edit_data(project, current_user):
        logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_user.role}) 尝试删除无权限的项目: {project_id} (所有者: {project.owner_id})")

        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '您没有权限删除此项目'
            }), 403

        flash('您没有权限删除此项目', 'danger')
        return redirect(url_for('project.list_projects'))
    
    try:
        # === 关联数据清理开始 ===

        # 0. 先获取报价单 IDs
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project_id).all()
        quotation_ids = [q.id for q in quotations]

        # 1. 检查是否存在批价单 - 如果存在，阻止删除
        from app.models.pricing_order import PricingOrder
        if quotation_ids:
            pricing_orders_count = PricingOrder.query.filter(PricingOrder.quotation_id.in_(quotation_ids)).count()
            if pricing_orders_count > 0:
                error_msg = '无法删除项目：存在关联的批价单。请先删除或转移批价单后再删除项目。'
                logger.warning(f"用户 {current_user.username} 尝试删除项目 {project_id}，但存在 {pricing_orders_count} 个关联批价单")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_msg}), 400
                flash(error_msg, 'danger')
                return redirect(url_for('project.view_project', project_id=project_id))

        # 2. 删除项目关联的所有报价单
        if quotations:
            for quotation in quotations:
                db.session.delete(quotation)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotations)} 个报价单")
        
        # 2. 删除项目关联的所有阶段历史记录
        from app.models.projectpm_stage_history import ProjectStageHistory
        stage_histories = ProjectStageHistory.query.filter_by(project_id=project_id).all()
        if stage_histories:
            for history in stage_histories:
                db.session.delete(history)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(stage_histories)} 个阶段历史记录")
        
        # 3. 删除项目跟进记录和回复 (新增)
        from app.models.action import Action, ActionReply
        project_actions = Action.query.filter_by(project_id=project_id).all()
        if project_actions:
            action_reply_count = 0
            for action in project_actions:
                # 统计回复数量
                replies = ActionReply.query.filter_by(action_id=action.id).all()
                action_reply_count += len(replies)
                # ActionReply已通过cascade='all, delete-orphan'自动删除
                db.session.delete(action)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_actions)} 个跟进记录和 {action_reply_count} 个回复")
        
        # 4. 删除项目审批实例和记录 (新增)
        from app.models.approval import ApprovalInstance, ApprovalRecord
        project_approvals = ApprovalInstance.query.filter_by(
            object_type='project', 
            object_id=project_id
        ).all()
        if project_approvals:
            approval_record_count = 0
            for approval in project_approvals:
                # 统计审批记录数量
                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                approval_record_count += len(records)
                # ApprovalRecord已通过cascade="all, delete-orphan"自动删除
                db.session.delete(approval)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(project_approvals)} 个项目审批实例和 {approval_record_count} 个审批记录")
        
        # 5. 删除关联报价单的审批实例
        if quotation_ids:
            quotation_approvals = ApprovalInstance.query.filter(
                ApprovalInstance.object_type == 'quotation',
                ApprovalInstance.object_id.in_(quotation_ids)
            ).all()
            if quotation_approvals:
                quotation_approval_record_count = 0
                for approval in quotation_approvals:
                    # 统计审批记录数量
                    records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                    quotation_approval_record_count += len(records)
                    db.session.delete(approval)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotation_approvals)} 个报价单审批实例和 {quotation_approval_record_count} 个审批记录")

        # 6. 删除项目关联的评分记录
        try:
            from app.models.project_scoring import ProjectScoringRecord, ProjectTotalScore
            
            # 删除评分记录
            scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
            if scoring_records:
                for record in scoring_records:
                    db.session.delete(record)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(scoring_records)} 个项目评分记录")
            
            # 删除总评分记录
            total_scores = ProjectTotalScore.query.filter_by(project_id=project_id).all()
            if total_scores:
                for score in total_scores:
                    db.session.delete(score)
                logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(total_scores)} 个项目总分记录")
                    
        except ImportError:
            # 如果新评分系统模块不存在，跳过
            logger.info("项目评分系统模块不存在，跳过评分记录清理")
        
        # 7. 删除旧的评分记录
        try:
            if ProjectRatingRecord:
                old_rating_records = ProjectRatingRecord.query.filter_by(project_id=project_id).all()
                if old_rating_records:
                    for record in old_rating_records:
                        db.session.delete(record)
                    logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(old_rating_records)} 个旧版评分记录")
        except Exception:
            # 如果评分系统模块处理失败，跳过
            logger.info("旧版评分系统模块处理失败，跳过")

        # 8. 删除项目-客户关联记录
        from app.models.project_customer_association import ProjectCustomerAssociation
        associations = ProjectCustomerAssociation.query.filter_by(project_id=project_id).all()
        if associations:
            for association in associations:
                db.session.delete(association)
            logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(associations)} 个客户关联")

        # === 关联数据清理结束 ===

        # 9. 最后删除项目
        # 记录删除历史（在实际删除前记录）
        try:
            ChangeTracker.log_delete(project)
        except Exception as track_err:
            logger.warning(f"记录项目删除历史失败: {str(track_err)}")
        
        db.session.delete(project)
        db.session.commit()
        
        logger.info(f"项目 {project_id} ({project.project_name}) 及其所有关联数据删除成功")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '项目删除成功！'
            })
        flash('项目删除成功！', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除项目 {project_id} 失败: {str(e)}")
        
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'删除失败：{str(e)}'
            }), 500
            
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('project.list_projects'))

@project.route('/apply_authorization/<int:project_id>', methods=['POST'])
@login_required
def apply_authorization(project_id):
    """申请项目授权编号"""
    project = Project.query.get_or_404(project_id)
    
    # 检查权限 - 项目拥有者、厂商负责人或管理员可以申请
    if (current_user.id != project.owner_id and 
        current_user.id != project.vendor_sales_manager_id and 
        current_user.role != 'admin'):
        flash('您没有权限申请此项目的授权编号', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查项目当前状态
    if project.authorization_code:
        flash('此项目已有授权编号，无需重复申请', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    if project.authorization_status == 'pending':
        flash('此项目已经提交申请，正在审批中', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查项目类型是否填写
    if not project.project_type or project.project_type.strip() == '':
        flash('项目类型未填写，无法提交授权编号申请。请先完善项目信息。', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 更新项目状态为申请中
    apply_note = request.form.get('apply_note', '')
    project.authorization_status = 'pending'
    project.feedback = f"申请备注: {apply_note}" if apply_note else None
    
    try:
        db.session.commit()
        # 记录日志
        logger.info(f"用户 {current_user.username} 申请了项目 {project.project_name} 的授权编号")
        flash('授权编号申请已提交，等待审批', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"申请授权编号失败: {str(e)}")
        flash('申请提交失败，请稍后重试', 'danger')
    
    return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/check_similar_projects', methods=['POST'])
def check_similar_projects():
    """检查是否有类似的项目名称"""
    data = request.get_json()
    project_name = data.get('project_name', '')
    exclude_id = data.get('exclude_id', None)
    
    if not project_name:
        return jsonify({'similar_projects': []})
    
    # 使用SQLAlchemy查询而非MongoDB
    query = Project.query.filter(Project.authorization_status != 'rejected')
    
    if exclude_id:
        try:
            exclude_id = int(exclude_id)
            query = query.filter(Project.id != exclude_id)
        except Exception:
            pass
    
    projects = query.all()
    similar_projects = []
    
    for project in projects:
        # 使用优化后的中文相似度比较函数
        is_similar, similarity = is_similar_project_name(
            project_name, 
            project.project_name, 
            threshold=50,  # 使用较低的阈值捕获更多潜在相似项目
            debug=True
        )
        
        if is_similar:
            similar_projects.append({
                'name': project.project_name,
                'authorization_code': project.authorization_code,
                'owner_name': project.owner.username if project.owner else "未知",
                'status': project.authorization_status,
                'similarity': similarity
            })
    
    # 按相似度降序排序
    similar_projects.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({'similar_projects': similar_projects})

@project.route('/projects/approve_authorization/<int:project_id>', methods=['POST'])
@login_required
def approve_authorization(project_id):
    """批准项目授权编号申请"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 获取最新的用户信息（确保角色是最新的）
        from app.models.user import User
        current_db_user = User.query.get(current_user.id)
        
        # 检查用户权限
        # 项目授权批准权限检查 - 使用权限配置系统
        # 注：授权批准权限通过 project 模块的 edit 权限控制
        # - 系统级(system)权限可以批准所有项目
        # - 使用 content_filters 限制可批准的项目类型
        # 例如：渠道经理配置 content_filters = {"project_type": ["channel_follow"]}
        can_approve = False

        # 管理员可以批准所有项目授权申请
        from app.permissions import is_admin_or_ceo
        if is_admin_or_ceo():
            can_approve = True
        elif current_db_user.has_permission('project', 'edit'):
            permission_level = current_db_user.get_permission_level('project')
            if permission_level == 'system':
                # 系统级权限：可以批准所有项目
                can_approve = True
            else:
                # 检查 content_filters 是否允许该项目类型
                permission = current_db_user.get_permission_config('project')
                if permission and hasattr(permission, 'content_filters') and permission.content_filters:
                    allowed_types = permission.content_filters.get('project_type', [])
                    if project.project_type in allowed_types:
                        can_approve = True
                else:
                    # 无 content_filters 限制时，有编辑权限即可批准
                    can_approve = True

        if not can_approve:
            logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_db_user.role}) 尝试批准无权限的项目: {project_id} (类型: {project.project_type})")
            flash('您没有权限批准此类项目的授权申请', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))

        # 如果项目状态不是待授权，则不能批准
        if project.authorization_code:
            flash('此项目已有授权编号，无需审批', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        if project.authorization_status != 'pending':
            flash('此项目未提交授权申请或已被处理', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 获取审批备注
        approval_note = request.form.get('approval_note', '')
        
        # 生成授权编号 - 先将英文类型映射为中文
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        project_type_for_code = project_type_label(project.project_type, lang_code)
        authorization_code = Project.generate_authorization_code(project_type_for_code)
        
        if not authorization_code:
            flash('无法为此类型的项目生成授权编号', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新项目
        project.authorization_code = authorization_code
        project.authorization_status = None  # 清除pending状态
        project.feedback = approval_note if approval_note else None
        
        # 授权批准后自动设置报备日期为当前日期
        from datetime import date
        project.report_time = date.today()
        
        # 同步更新所有关联报价单的project_stage和project_type
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = project.current_stage
            q.project_type = project.project_type
        
        try:
            db.session.commit()
            # 记录日志
            logger.info(f"用户 {current_user.username} 批准了项目 {project.project_name} 的授权编号申请，编号为 {authorization_code}")
            flash(f'授权申请已批准，授权编号为: {authorization_code}', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"批准授权编号失败: {str(e)}")
            flash('批准申请失败，请稍后重试', 'danger')
        
        return redirect(url_for('project.view_project', project_id=project_id))
    except Exception as e:
        flash(f'批准授权失败：{str(e)}', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/reject_authorization/<int:project_id>', methods=['POST'])
@login_required
def reject_authorization(project_id):
    """拒绝项目授权申请"""
    try:
        project = Project.query.get_or_404(project_id)
        feedback = request.form.get('feedback', '')
        
        # 获取最新的用户信息（确保角色是最新的）
        from app.models.user import User
        current_db_user = User.query.get(current_user.id)
        
        # 检查用户权限
        # 项目授权拒绝权限检查 - 使用权限配置系统
        # 注：授权拒绝权限通过 project 模块的 edit 权限控制
        # - 系统级(system)权限可以拒绝所有项目
        # - 使用 content_filters 限制可拒绝的项目类型
        can_reject = False

        # 管理员可以拒绝所有项目授权申请
        from app.permissions import is_admin_or_ceo
        if is_admin_or_ceo():
            can_reject = True
        elif current_db_user.has_permission('project', 'edit'):
            permission_level = current_db_user.get_permission_level('project')
            if permission_level == 'system':
                # 系统级权限：可以拒绝所有项目
                can_reject = True
            else:
                # 检查 content_filters 是否允许该项目类型
                permission = current_db_user.get_permission_config('project')
                if permission and hasattr(permission, 'content_filters') and permission.content_filters:
                    allowed_types = permission.content_filters.get('project_type', [])
                    if project.project_type in allowed_types:
                        can_reject = True
                else:
                    # 无 content_filters 限制时，有编辑权限即可拒绝
                    can_reject = True

        if not can_reject:
            logger.warning(f"用户 {current_user.username} (ID: {current_user.id}, 角色: {current_db_user.role}) 尝试拒绝无权限的项目: {project_id} (类型: {project.project_type})")
            flash('您没有权限拒绝此类项目的授权申请', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))

        # 如果项目状态不是待授权，则不能拒绝
        if project.authorization_status != 'pending':
            flash('此项目未提交授权申请或已被处理', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新项目状态
        project.authorization_status = 'rejected'
        project.feedback = feedback
        
        try:
            db.session.commit()
            # 记录日志
            logger.info(f"用户 {current_user.username} 驳回了项目 {project.project_name} 的授权编号申请")
            flash('授权申请已驳回', 'warning')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"驳回授权编号失败: {str(e)}")
            flash('操作失败，请稍后重试', 'danger')
        
        return redirect(url_for('project.view_project', project_id=project_id))
    except Exception as e:
        flash(f'驳回授权失败：{str(e)}', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/revoke_authorization/<int:project_id>', methods=['POST'])
@login_required
def revoke_authorization(project_id):
    """撤回项目授权申请"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 检查权限 - 只有项目拥有者或管理员可以撤回
        if current_user.id != project.owner_id and current_user.role != 'admin':
            flash('您没有权限撤回此项目的授权申请', 'danger')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 检查项目当前状态，只有pending状态的可以撤回
        if project.authorization_status != 'pending':
            flash('此项目未在审批中，无法撤回申请', 'warning')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 获取撤回原因
        revoke_reason = request.form.get('revoke_reason', '')
        
        # 更新项目状态，清除pending状态
        project.authorization_status = None
        project.feedback = f"申请已撤回。原因: {revoke_reason}" if revoke_reason else "申请已撤回"
        
        try:
            db.session.commit()
            # 记录日志
            logger.info(f"用户 {current_user.username} 撤回了项目 {project.project_name} 的授权编号申请")
            flash('授权申请已成功撤回', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"撤回授权申请失败: {str(e)}")
            flash('撤回申请失败，请稍后重试', 'danger')
        
        return redirect(url_for('project.view_project', project_id=project_id))
    except Exception as e:
        flash(f'撤回授权申请失败：{str(e)}', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

@project.route('/api/batch-delete', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以删除自己的项目数据
@csrf.exempt
def batch_delete_projects():
    """批量删除项目"""
    try:
        data = request.get_json()
        if not data or 'project_ids' not in data or not data['project_ids']:
            return jsonify({
                'success': False,
                'message': '请选择要删除的项目'
            })
        
        project_ids = data['project_ids']
        result = {
            'success': True,
            'deleted': 0,
            'failed': 0,
            'failure_reasons': []
        }
        
        # 导入 Quotation 模型
        from app.models.quotation import Quotation
        
        for project_id in project_ids:
            try:
                project = Project.query.get(project_id)
                if not project:
                    result['failed'] += 1
                    result['failure_reasons'].append(f'ID为{project_id}的项目不存在')
                    continue
                
                # 检查权限
                if not can_edit_data(project, current_user):
                    result['failed'] += 1
                    result['failure_reasons'].append(f'您没有权限删除 "{project.project_name}" 项目')
                    continue
                
                # 先删除关联的报价单
                quotations = Quotation.query.filter_by(project_id=project_id).all()
                if quotations:
                    for quotation in quotations:
                        db.session.delete(quotation)
                    
                    logger.info(f"删除项目 {project_id} 前，已删除关联的 {len(quotations)} 个报价单")
                
                # 删除关联的阶段历史记录
                from app.models.projectpm_stage_history import ProjectStageHistory
                stage_histories = ProjectStageHistory.query.filter_by(project_id=project_id).all()
                if stage_histories:
                    for history in stage_histories:
                        db.session.delete(history)
                
                # 删除项目关联的评分记录
                try:
                    from app.models.project_scoring import ProjectScoringRecord, ProjectTotalScore
                    
                    # 删除评分记录
                    scoring_records = ProjectScoringRecord.query.filter_by(project_id=project_id).all()
                    if scoring_records:
                        for record in scoring_records:
                            db.session.delete(record)
                    
                    # 删除总评分记录
                    total_scores = ProjectTotalScore.query.filter_by(project_id=project_id).all()
                    if total_scores:
                        for score in total_scores:
                            db.session.delete(score)
                            
                except ImportError:
                    # 如果新评分系统模块不存在，跳过
                    pass
                
                # 删除旧的评分记录
                try:
                    if ProjectRatingRecord:
                        old_rating_records = ProjectRatingRecord.query.filter_by(project_id=project_id).all()
                        if old_rating_records:
                            for record in old_rating_records:
                                db.session.delete(record)
                except Exception:
                    # 如果评分系统模块处理失败，跳过
                    pass

                # 删除项目-客户关联记录
                from app.models.project_customer_association import ProjectCustomerAssociation
                associations = ProjectCustomerAssociation.query.filter_by(project_id=project_id).all()
                if associations:
                    for association in associations:
                        db.session.delete(association)

                # 最后删除项目
                # 记录删除历史（在实际删除前记录）
                try:
                    ChangeTracker.log_delete(project)
                except Exception as track_err:
                    logger.warning(f"记录项目删除历史失败: {str(track_err)}")
                
                db.session.delete(project)
                result['deleted'] += 1
                
                # 记录日志
                logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 删除了项目 {project.project_name} (ID: {project_id})")
                
            except Exception as e:
                db.session.rollback()
                result['failed'] += 1
                result['failure_reasons'].append(f'删除 ID为{project_id} 的项目时出错: {str(e)}')
                logger.error(f"删除项目 {project_id} 失败: {str(e)}")
        
        db.session.commit()
        
        if result['deleted'] > 0:
            result['message'] = f'成功删除 {result["deleted"]} 个项目' + (f'，{result["failed"]} 个项目删除失败' if result['failed'] > 0 else '')
        else:
            result['success'] = False
            result['message'] = '所有项目删除失败'
        
        return jsonify(result)
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量删除项目失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        })

def update_project_stage_business_logic(project_id, new_stage, current_user_id):
    """
    业务逻辑函数：更新项目阶段并处理批价单创建
    供测试脚本和其他业务逻辑调用
    """
    try:
        from app.models.user import User
        user = User.query.get(current_user_id)
        if not user:
            return {'error': '用户不存在'}
        
        # 查询项目
        project = Project.query.get(project_id)
        if not project:
            return {'error': '项目不存在'}
        
        old_stage = project.current_stage
        
        # 检查从批价到签约的流程 - 严格控制，只有批价单审批通过才能推进
        if new_stage == 'signed' and old_stage == 'quoted':
            from app.models.quotation import Quotation
            from app.models.pricing_order import PricingOrder
            
            # 获取项目的最新报价单
            latest_quotation = Quotation.query.filter_by(project_id=project_id).order_by(
                Quotation.created_at.desc()
            ).first()
            
            if not latest_quotation:
                return {'error': '项目未找到相关报价单，无法推进到签约阶段。请先创建报价单。'}
            
            # 检查报价单是否有审核标记
            has_approval = (
                latest_quotation.approval_status and
                latest_quotation.approval_status != 'pending' and
                latest_quotation.approval_status != 'rejected' and
                latest_quotation.approved_stages
            )

            # 签约口径=批价单终审:不再卡报价单 approval_status(批价单是报价单下游,已审批通过即代表商务认可)。
            # 原「报价单未审核」拦截已移除——只要批价单已通过即可进签约(下方仍校验批价单 + 授权编号)。
            _ = has_approval  # 计算保留但不拦截
            
            # 检查是否已存在批价单且已审批通过
            existing_pricing_order = PricingOrder.query.filter_by(
                project_id=project_id,
                quotation_id=latest_quotation.id
            ).first()
            
            if not existing_pricing_order:
                return {'error': f'项目尚未创建批价单，无法推进到签约阶段。请先创建并完成批价单审批流程。'}
            
            # 检查批价单是否已审批通过
            if existing_pricing_order.status != 'approved':
                return {'error': f'批价单 {existing_pricing_order.order_number} 尚未审批通过（当前状态：{existing_pricing_order.status_label["zh"]}），无法推进到签约阶段。请先完成批价单审批流程。'}
            
            # 检查项目是否有授权编号
            if not project.authorization_code:
                return {'error': f'批价单 {existing_pricing_order.order_number} 已审批通过，但项目缺少授权编号，无法推进到签约阶段。请先申请项目授权编号。'}
        
        # 更新项目阶段
        project.current_stage = new_stage

        # 成功锁定只在「中标待签约」窗口有效:签约(兑现)或任何其它阶段变更(回退/撤销)都应解除
        if getattr(project, 'win_locked', False) and new_stage != old_stage:
            project.win_locked = False
            project.win_lock_reason = None
            project.win_locked_by = None
            project.win_locked_at = None
            project.win_locked_quotation_id = None
            project.win_locked_amount = None

        # 创建阶段历史记录
        try:
            from app.models.projectpm_stage_history import ProjectStageHistory
            ProjectStageHistory.add_history_record(
                project_id=project.id,
                from_stage=old_stage,
                to_stage=new_stage,
                change_date=datetime.now(),
                remarks=f"业务逻辑推进: {user.username}",
                commit=False  # 不在方法内部提交，与主事务一同提交
            )
        except Exception as history_err:
            # 历史记录失败不应阻塞主流程
            pass
        
        db.session.commit()

        # 阶段切换 → 给项目讨论群推送结构化"阶段推进卡"（不阻断主业务）
        try:
            import json as _json
            from app.services import chat_service as _cs
            from app.utils.dictionary_helpers import project_stage_label
            conv_id = _cs.find_any_project_conversation(project_id)
            if conv_id and old_stage != new_stage:
                from_label = project_stage_label(old_stage) if old_stage else '未设置'
                to_label = project_stage_label(new_stage) if new_stage else '未设置'
                actor = user.real_name or user.username or '系统'
                payload = _json.dumps({
                    'from_stage_label': from_label,
                    'to_stage_label': to_label,
                    'by_name': actor,
                    'by_initial': actor[0] if actor else '?',
                }, ensure_ascii=False)
                _cs.send_system_message(conv_id, payload, message_type='stage_advance')
        except Exception as _hook_err:
            # 通知失败不影响主业务
            pass

        return {
            'success': True,
            'project_id': project_id,
            'old_stage': old_stage,
            'new_stage': new_stage,
            'message': '项目阶段更新成功'
        }

    except Exception as e:
        db.session.rollback()
        return {'error': f'更新项目阶段失败: {str(e)}'}

@project.route('/api/update_stage', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;真授权由函数内 owner/vendor/admin 判断(支持负责人操作自己项目)
def update_project_stage():
    """
    更新项目阶段
    用于项目阶段可视化进度条组件调用
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
            
        project_id = data.get('project_id')
        new_stage = data.get('current_stage')
        remarks = data.get('remarks', '')  # 可选的备注参数

        if not project_id or not new_stage:
            return jsonify({'success': False, 'message': '项目ID和阶段不能为空'}), 400
        
        # 如果传入的是中文阶段名称，转换为英文key
        if new_stage not in PROJECT_STAGE_LABELS:
            # 反查中文名称对应的英文key
            reverse_lookup = {v['zh']: k for k, v in PROJECT_STAGE_LABELS.items()}
            new_stage_key = reverse_lookup.get(new_stage, new_stage)
            if new_stage_key != new_stage:
                current_app.logger.info(f"阶段名称转换: {new_stage} -> {new_stage_key}")
                new_stage = new_stage_key
        
        # 查询项目 - 使用 with_for_update() 锁定行，防止并发更新
        try:
            project = db.session.query(Project).with_for_update().filter(Project.id == project_id).first()
            if not project:
                return jsonify({'success': False, 'message': '项目不存在'}), 404
                
            # 设置跳过自动历史记录的标志，因为我们会手动添加
            project._skip_history_recording = True
        except Exception as e:
            current_app.logger.error(f"查询项目时发生错误: {str(e)}")
            return jsonify({'success': False, 'message': f'查询错误: {str(e)}'}), 500
        
        # 检查项目是否被锁定
        from app.helpers.project_helpers import is_project_editable
        is_editable, lock_reason = is_project_editable(project_id, current_user.id)
        from app.permissions import is_admin_or_ceo
        if not is_editable and not is_admin_or_ceo():
            return jsonify({'success': False, 'message': f'项目已被锁定，无法推进阶段: {lock_reason}'}), 403
            
        # 检查权限
        allowed = False
        if is_admin_or_ceo():
            allowed = True
        elif project.owner_id == current_user.id:
            allowed = True
        elif project.vendor_sales_manager_id == current_user.id:
            # 厂商负责人享有与拥有人同等权限
            allowed = True
        else:
            allowed_user_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
            if project.owner_id in allowed_user_ids:
                allowed = True
        # 签约阶段加固：已签约项目不允许任何阶段变更（包括管理员）
        if project.current_stage == 'signed':
            return jsonify({'success': False, 'message': '已签约项目不允许变更阶段'}), 403
            
        # 防止将项目从任何阶段切换到搁置或失败（如果曾经签约过）
        if new_stage in ['paused', 'lost']:
            # 检查是否曾经有签约历史记录
            has_signed_history = ProjectStageHistory.query.filter(
                ProjectStageHistory.project_id == project_id,
                ProjectStageHistory.to_stage == 'signed'
            ).first()
            
            if has_signed_history:
                stage_name_map = {'paused': '搁置', 'lost': '失败'}
                return jsonify({
                    'success': False, 
                    'message': f'该项目曾经签约，不允许切换到{stage_name_map[new_stage]}状态'
                }), 403
        if not allowed:
            return jsonify({'success': False, 'message': '您没有权限修改此项目'}), 403
            
        # **新增: 签约阶段检测逻辑（批价流程）**
        old_stage = project.current_stage
        pricing_flow_info = None
        should_block_progress = False

        if new_stage == 'signed' and old_stage == 'quoted':
            # ⚠️ 禁止从"批价"阶段手动推进到"签约"阶段
            # 签约阶段必须通过批价单审批流程自动推进（见 pricing_order_service.py::complete_approval）
            return jsonify({
                'success': False,
                'message': '签约阶段需通过批价单审批流程自动推进'
            }), 400

            # 从批价阶段推进到签约阶段，检查批价流程状态
            
            # 获取项目的最新报价单
            latest_quotation = Quotation.query.filter_by(project_id=project_id).order_by(
                Quotation.created_at.desc()
            ).first()
            
            if not latest_quotation:
                # 无报价单，阻止推进
                should_block_progress = True
                pricing_flow_info = {
                    'has_quotation': False,
                    'has_pricing_order': False,
                    'message': '项目未找到相关报价单，无法推进到签约阶段。请先创建报价单。',
                    'action_required': 'create_quotation'
                }
            else:
                # 检查报价单是否有审核标记
                has_approval = (
                    latest_quotation.approval_status and
                    latest_quotation.approval_status != 'pending' and
                    latest_quotation.approval_status != 'rejected' and
                    latest_quotation.approved_stages
                )
                
                if not has_approval:
                    # 报价单没有审核标记，阻止推进
                    should_block_progress = True
                    pricing_flow_info = {
                        'has_quotation': True,
                        'has_approval': False,
                        'quotation_number': latest_quotation.quotation_number,
                        'message': f'报价单 {latest_quotation.quotation_number} 尚未完成审核，无法推进到签约阶段。请先完成报价单审核流程。',
                        'action_required': 'complete_quotation_approval',
                        'quotation_id': latest_quotation.id
                    }
                else:
                    # 有报价单且有审核标记，检查是否已存在批价单
                    existing_pricing_order = PricingOrder.query.filter_by(
                        project_id=project_id,
                        quotation_id=latest_quotation.id
                    ).first()
                    
                    if existing_pricing_order:
                        # 已存在批价单，检查审批状态
                        if existing_pricing_order.status == 'approved':
                            # 检查项目是否有授权编号
                            if not project.authorization_code:
                                # 批价单已通过但项目无授权编号，阻止推进
                                should_block_progress = True
                                pricing_flow_info = {
                                    'has_quotation': True,
                                    'has_approval': True,
                                    'has_pricing_order': True,
                                    'has_authorization': False,
                                    'quotation_number': latest_quotation.quotation_number,
                                    'pricing_order_number': existing_pricing_order.order_number,
                                    'pricing_order_status': existing_pricing_order.status,
                                    'message': f'批价单 {existing_pricing_order.order_number} 已审批通过，但项目缺少授权编号，无法推进到签约阶段。请先申请项目授权编号。',
                                    'action_required': 'apply_authorization',
                                    'project_id': project.id
                                }
                            else:
                                # 批价单已审批通过且有授权编号，可以推进到签约
                                pricing_flow_info = {
                                    'has_quotation': True,
                                    'has_approval': True,
                                    'has_pricing_order': True,
                                    'has_authorization': True,
                                    'quotation_number': latest_quotation.quotation_number,
                                    'pricing_order_number': existing_pricing_order.order_number,
                                    'pricing_order_status': existing_pricing_order.status,
                                    'authorization_code': project.authorization_code,
                                    'message': f'批价单 {existing_pricing_order.order_number} 已审批通过，项目授权编号 {project.authorization_code}，项目可以推进到签约阶段。',
                                    'action_required': 'view_pricing_order',
                                    'pricing_order_id': existing_pricing_order.id
                                }
                        else:
                            # 批价单存在但未审批通过，阻止推进
                            should_block_progress = True
                            pricing_flow_info = {
                                'has_quotation': True,
                                'has_approval': True,
                                'has_pricing_order': True,
                                'quotation_number': latest_quotation.quotation_number,
                                'pricing_order_number': existing_pricing_order.order_number,
                                'pricing_order_status': existing_pricing_order.status,
                                'message': f'批价单 {existing_pricing_order.order_number} 尚未审批通过（当前状态：{existing_pricing_order.status_label["zh"]}），无法推进到签约阶段。请先完成批价单审批流程。',
                                'action_required': 'view_pricing_order',
                                'pricing_order_id': existing_pricing_order.id
                            }
                    else:
                        # 有报价单有审核但无批价单，阻止推进并提示创建
                        should_block_progress = True
                        pricing_flow_info = {
                            'has_quotation': True,
                            'has_approval': True,
                            'has_pricing_order': False,
                            'quotation_number': latest_quotation.quotation_number,
                            'message': f'项目尚未创建批价单，无法推进到签约阶段。请先创建并完成批价单审批流程。',
                            'action_required': 'create_pricing_order',
                            'quotation_id': latest_quotation.id
                        }
        
        # 如果需要阻止推进，回滚到原阶段
        if should_block_progress:
            return jsonify({
                'success': False, 
                'message': pricing_flow_info['message'],
                'pricing_flow': pricing_flow_info,
                'current_stage': old_stage  # 保持原阶段
            }), 400
        
        # 更新项目阶段
        project.current_stage = new_stage

        # 成功锁定只在「中标待签约」窗口有效:签约(兑现)或任何其它阶段变更(回退/撤销)都应解除
        if getattr(project, 'win_locked', False) and new_stage != old_stage:
            project.win_locked = False
            project.win_lock_reason = None
            project.win_locked_by = None
            project.win_locked_at = None
            project.win_locked_quotation_id = None
            project.win_locked_amount = None

        # 如果项目推进到签约阶段，自动锁定项目
        if new_stage == 'signed' and not project.is_locked:
            project.is_locked = True
            project.locked_reason = _('项目已签约，自动锁定')
            project.locked_by = current_user.id
            project.locked_at = datetime.now()
            current_app.logger.info(f'项目 {project.project_name} (ID: {project.id}) 由于签约自动锁定')

        # 在一个事务中同时保存项目更新和阶段历史
        try:
            current_app.logger.info(f"开始为项目ID={project.id}创建阶段历史记录: {old_stage} -> {new_stage}")
            
            # 创建阶段历史记录但不提交
            ProjectStageHistory.add_history_record(
                project_id=project.id,
                from_stage=old_stage,
                to_stage=new_stage,
                change_date=datetime.now(),
                remarks=remarks if remarks else f"API推进: {current_user.username}",
                commit=False  # 不在方法内部提交，与主事务一同提交
            )
            current_app.logger.info(f"阶段历史记录已创建，准备提交事务")

            # 提交所有更改（让SQLAlchemy自动更新updated_at字段）
            db.session.commit()
            current_app.logger.info(f"数据库事务已提交")

            # 发放积分：项目阶段向前推进
            try:
                from app.services.points_service import award_points
                _forward_stages = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed']
                _old_idx = _forward_stages.index(old_stage) if old_stage in _forward_stages else -1
                _new_idx = _forward_stages.index(new_stage) if new_stage in _forward_stages else -1
                if _new_idx > _old_idx >= 0:
                    from datetime import date as _date
                    award_points(
                        user_id=project.owner_id or current_user.id,
                        behavior_code='project_stage_advance',
                        source_type='project',
                        source_id=f'{project.id}_{_date.today().isoformat()}',
                        memo=f'推进项目[{project.project_name}]阶段: {old_stage} → {new_stage}'
                    )
                    db.session.commit()
            except Exception as pts_err:
                current_app.logger.warning(f"发放项目阶段推进积分失败: {pts_err}")

            # 在提交后更新项目活跃度（使用最新的updated_at时间）
            current_app.logger.info(f"开始更新项目活跃度状态")
            update_active_status(project, commit=True)
            current_app.logger.info(f"项目ID={project.id}的阶段从{old_stage}更新为{new_stage}，历史记录已添加")

            # 记录工作项
            record_activity('advance_stage', 'project', project.project_name, current_user,
                project_id=project.id, description=f'项目推进 {project.project_name}')

            # 提交后再单独重新计算项目评分（避免事务冲突）
            @after_this_request
            def calculate_score(response):
                try:
                    # 在请求完成后计算评分，使用独立事务
                    from app.models.project_scoring import ProjectScoringEngine
                    ProjectScoringEngine.calculate_project_score(project.id, commit=True)
                    current_app.logger.info(f"项目ID={project.id}阶段推进后评分已重新计算")
                except Exception as score_err:
                    current_app.logger.warning(f"重新计算项目评分失败: {str(score_err)}")
                return response
            
            # 验证更新是否生效
            db.session.refresh(project)
            if project.current_stage != new_stage:
                current_app.logger.error(f"项目阶段推进后数据库未更新: 项目ID={project.id}, 期望={new_stage}, 实际={project.current_stage}")
                return jsonify({'success': False, 'message': '数据库更新失败，请联系管理员'}), 500

            # 构建响应数据
            response_data = {
                'success': True, 
                'message': '项目阶段已更新',
                'data': {
                    'project_id': project.id,
                    'current_stage': project.current_stage,
                    'old_stage': old_stage
                }
            }
            
            # 如果有批价流程信息，添加到响应中
            if pricing_flow_info:
                response_data['pricing_flow'] = pricing_flow_info
            
            return jsonify(response_data), 200
            
        except Exception as db_err:
            import traceback
            db_error_traceback = traceback.format_exc()
            db.session.rollback()
            current_app.logger.error(f"提交阶段更新到数据库失败: {str(db_err)}")
            current_app.logger.error(f"数据库错误堆栈:\n{db_error_traceback}")
            return jsonify({
                'success': False, 
                'message': f'数据库错误: {str(db_err)}',
                'error_details': db_error_traceback if current_app.debug else None
            }), 500
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        current_app.logger.error(f"更新项目阶段出错: {str(e)}")
        current_app.logger.error(f"错误堆栈:\n{error_traceback}")
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'服务器错误: {str(e)}',
            'error_details': error_traceback if current_app.debug else None
        }), 500

@project.route('/add_action/<int:project_id>', methods=['GET', 'POST'])
@login_required
def add_action_for_project(project_id):
    """为项目添加行动记录"""
    project = Project.query.get_or_404(project_id)
    
    # 从关联表查找项目相关的所有企业（与项目详情逻辑一致）
    from app.models.project_customer_association import ProjectCustomerAssociation

    # 获取活跃的客户关联
    associations = ProjectCustomerAssociation.get_active_associations(project_id)

    # 🔥 权限过滤：厂商负责人可以选择所有关联客户，其他用户需要客户权限
    if current_user.role == 'admin' or (hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == current_user.id):
        # 管理员和厂商负责人：可以选择所有关联客户
        filtered_associations = associations
    else:
        # 其他用户：只保留有权限查看的客户
        from app.utils.access_control import can_view_company
        filtered_associations = [
            assoc for assoc in associations
            if assoc.company and can_view_company(current_user, assoc.company)
        ]

    # 构建客户列表
    related_companies = []
    related_companies_dict = {}
    customer_associations = []  # 包含类型信息的关联列表

    for assoc in filtered_associations:
        company = assoc.company
        if company.id not in related_companies_dict:
            related_companies.append(company)
            related_companies_dict[company.id] = company
        # 添加到包含类型信息的列表（可能有重复公司但不同角色）
        customer_associations.append({
            'company': company,
            'customer_type': assoc.customer_type
        })
    
    # 获取默认选择的企业ID和锁定状态
    default_company_id = request.args.get('company_id')
    locked_company = request.args.get('locked') == 'true'  # 检查是否锁定客户
    selected_company = None
    company_contacts = []
    
    if default_company_id and default_company_id.isdigit():
        selected_company = Company.query.filter_by(id=int(default_company_id), is_deleted=False).first()
        if selected_company:
            company_contacts = Contact.query.filter_by(company_id=selected_company.id).all()
    elif related_companies:
        # 如果没有指定企业，默认选择第一个相关企业
        selected_company = related_companies[0]
        company_contacts = Contact.query.filter_by(company_id=selected_company.id).all()
    
    if request.method == 'POST':
        contact_id = request.form.get('contact_id')
        communication = request.form.get('communication')
        date = request.form.get('date')
        company_id = request.form.get('company_id')
        
        if not communication or not date:
            flash('请填写沟通情况和日期', 'danger')
        else:
            action = Action(
                date=datetime.strptime(date, '%Y-%m-%d'),
                contact_id=contact_id if contact_id else None,
                company_id=company_id if company_id else None,
                project_id=project_id,
                communication=communication,
                owner_id=current_user.id,
                is_shared='is_shared' in request.form  # 默认为False（如果未选中checkbox）
            )
            db.session.add(action)
            db.session.commit()

            # 记录日历工作项
            record_activity('create', 'action', project.project_name, current_user,
                customer_id=int(company_id) if company_id and company_id.isdigit() else None,
                project_id=project_id, description=action.communication)

            # 新增：每次添加行动记录后自动刷新项目活跃度和更新时间
            project.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
            update_active_status(project, commit=False)
            db.session.commit()
            # 如果关联了客户，更新客户活跃状态
            if company_id and company_id.isdigit():
                check_company_activity(company_id=int(company_id), days_threshold=1)
            try:
                from app.services.points_service import award_points
                from datetime import date as _date
                award_points(user_id=current_user.id, behavior_code='action_record_create',
                             source_type='action_project',
                             source_id=f'project_{project_id}_{current_user.id}_{_date.today().isoformat()}',
                             context=project.project_name)
                db.session.commit()
            except Exception as _pts_err:
                current_app.logger.warning(f'action_record_create积分发放失败: {_pts_err}')
            flash('行动记录添加成功！', 'success')
            return redirect(url_for('project.view_project', project_id=project_id))
    
    return render_template('project/add_action.html',
                           project=project,
                           related_companies=related_companies,
                           customer_associations=customer_associations,
                           selected_company=selected_company,
                           company_contacts=company_contacts,
                           locked_company=locked_company)

@project.route('/api/<int:project_id>/add_action', methods=['POST'])
@login_required
def api_add_action_for_project(project_id):
    """AJAX 添加跟进记录 API(项目场景)— 对齐 customer/api/<id>/add_action 接口"""
    try:
        p = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()
        data = request.get_json() or {}
        communication = (data.get('communication') or '').strip()
        date_str      = (data.get('date') or '').strip()
        company_id    = data.get('company_id')
        contact_id    = data.get('contact_id')
        is_shared     = data.get('is_shared', True)

        if not communication:
            return jsonify({'success': False, 'message': '请填写沟通情况'}), 400
        if not date_str:
            return jsonify({'success': False, 'message': '请选择日期'}), 400
        try:
            action_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': '日期格式无效'}), 400

        action = Action(
            date=action_date,
            project_id=project_id,
            company_id=int(company_id) if company_id else None,
            contact_id=int(contact_id) if contact_id else None,
            communication=communication,
            owner_id=current_user.id,
            is_shared=bool(is_shared),
        )
        db.session.add(action)
        db.session.commit()

        record_activity('create', 'action', p.project_name, current_user,
            project_id=project_id,
            customer_id=int(company_id) if company_id else None,
            description=action.communication)

        # 刷新项目活跃度
        try:
            p.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
            update_active_status(p, commit=False)
            db.session.commit()
        except Exception as e:
            logger.warning(f"刷新项目活跃度失败: {e}")
        if company_id:
            try:
                check_company_activity(company_id=int(company_id), days_threshold=1)
            except Exception as e:
                logger.warning(f"刷新客户活跃度失败: {e}")

        return jsonify({'success': True, 'message': '跟进记录已添加', 'action_id': action.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加项目跟进记录失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@project.route('/api/get_company_contacts/<int:company_id>', methods=['GET'])
@permission_required('customer', 'view')
def get_company_contacts(company_id):
    """获取企业联系人API"""
    try:
        company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
        contacts = Contact.query.filter_by(company_id=company_id).all()
        
        result = [{
            'id': contact.id,
            'name': contact.name,
            'position': contact.position or '',
            'phone': contact.phone or '',
            'email': contact.email or ''
        } for contact in contacts]
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"获取企业联系人失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取企业联系人失败: {str(e)}'
        }), 500


@project.route('/api/<int:project_id>/add_action', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;记录级授权见下(认归属,支持负责人/dealer 为自己项目加跟进)
def api_add_action(project_id):
    """AJAX添加行动记录API"""
    try:
        project_obj = Project.query.get_or_404(project_id)
        # 记录级授权:能编辑该项目者(负责人/厂商/公司级等)才可加跟进
        if not can_edit_data(project_obj, current_user):
            return jsonify({'success': False, 'message': _('您没有权限为此项目添加跟进记录')}), 403

        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

        communication = data.get('communication', '').strip()
        date_str = data.get('date', '')
        company_id = data.get('company_id')
        contact_id = data.get('contact_id')
        is_shared = data.get('is_shared', True)

        # 验证必填字段
        if not communication:
            return jsonify({'success': False, 'message': _('请填写沟通情况')}), 400
        if not date_str:
            return jsonify({'success': False, 'message': _('请选择日期')}), 400

        # 解析日期
        try:
            action_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'message': _('日期格式无效')}), 400

        # 创建行动记录
        action = Action(
            date=action_date,
            contact_id=int(contact_id) if contact_id else None,
            company_id=int(company_id) if company_id else None,
            project_id=project_id,
            communication=communication,
            owner_id=current_user.id,
            is_shared=is_shared
        )
        db.session.add(action)
        db.session.commit()

        # 记录日历工作项
        record_activity('create', 'action', project_obj.project_name, current_user,
            customer_id=int(company_id) if company_id else None,
            project_id=project_id, description=action.communication)

        # 更新项目活跃度和更新时间
        project_obj.updated_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
        update_active_status(project_obj, commit=False)
        db.session.commit()

        # 如果关联了客户，更新客户活跃状态
        if company_id:
            check_company_activity(company_id=int(company_id), days_threshold=1)

        try:
            from app.services.points_service import award_points
            from datetime import date as _date
            award_points(user_id=current_user.id, behavior_code='action_record_create',
                         source_type='action_project',
                         source_id=f'project_{project_id}_{current_user.id}_{_date.today().isoformat()}',
                         context=project_obj.project_name)
            db.session.commit()
        except Exception as _pts_err:
            current_app.logger.warning(f'action_record_create积分发放失败: {_pts_err}')

        # 构建返回数据
        owner_name = current_user.real_name or current_user.username
        result = {
            'id': action.id,
            'date': action.date.isoformat() if action.date else '',
            'communication': action.communication,
            'owner_name': owner_name,
            'owner_id': action.owner_id,
            'company_name': action.company.company_name if action.company else None,
            'contact_name': action.contact.name if action.contact else None
        }

        return jsonify({
            'success': True,
            'message': _('行动记录添加成功'),
            'data': result
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"添加行动记录失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'{_("添加行动记录失败")}: {str(e)}'
        }), 500


# 获取行动记录的所有回复（树形结构）
@project.route('/action/<int:action_id>/replies')
@login_required
@permission_required('customer', 'view')
def get_action_replies(action_id):
    action = Action.query.get_or_404(action_id)
    replies = ActionReply.query.filter_by(action_id=action_id, parent_reply_id=None).order_by(ActionReply.created_at.asc()).all()
    def build_tree(reply):
        # 返回 ISO 格式带 UTC 标记，前端可正确转换为本地时间
        created_at_iso = reply.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if reply.created_at else ''
        return {
            'id': reply.id,
            'content': reply.content,
            'owner': reply.owner.real_name or reply.owner.username,
            'owner_id': reply.owner_id,
            'created_at': created_at_iso,
            'can_delete': (current_user.id == reply.owner_id or current_user.role == 'admin'),
            'children': [build_tree(child) for child in reply.children]
        }
    return jsonify([build_tree(r) for r in replies])

# 添加回复
@project.route('/action/<int:action_id>/reply', methods=['POST'])
@login_required
@permission_required('customer', 'view')
def add_action_reply(action_id):
    action = Action.query.get_or_404(action_id)
    data = request.get_json()
    content = data.get('content', '').strip()
    parent_reply_id = data.get('parent_reply_id')
    if not content:
        return jsonify({'success': False, 'message': '回复内容不能为空'}), 400
    reply = ActionReply(
        action_id=action_id,
        parent_reply_id=parent_reply_id,
        content=content,
        owner_id=current_user.id
    )
    db.session.add(reply)
    db.session.commit()
    return jsonify({'success': True})

@project.route('/<int:project_id>/change_owner', methods=['POST'])
@permission_required('project', 'edit')
def change_project_owner(project_id):
    project = Project.query.get_or_404(project_id)
    if not can_change_project_owner(current_user, project):
        flash('您没有权限修改该项目的拥有人', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

    # 检查项目是否被锁定
    from app.helpers.project_helpers import is_project_editable
    is_editable, lock_reason = is_project_editable(project_id, current_user.id)
    if not is_editable and current_user.role != 'admin':
        flash(f'项目已被锁定，无法修改拥有人: {lock_reason}', 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    new_owner_id = request.form.get('new_owner_id', type=int)
    if not new_owner_id:
        flash('请选择新的拥有人', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

    from app.models.user import User
    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        flash('新拥有人不存在', 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))
    
    # 检查新拥有人是否是厂商企业账户
    is_vendor_company = new_owner.is_vendor_user()
    
    # 处理厂商销售负责人设置（保持原有值或设置新值）
    vendor_sales_manager_id = project.vendor_sales_manager_id  # 保持原有值
    
    if not is_vendor_company:
        # 如果新拥有人不是厂商企业账户，允许可选设置厂商销售负责人
        form_vendor_id = request.form.get('vendor_sales_manager_id', type=int)
        
        # 如果用户指定了新的厂商销售负责人，需要验证其有效性
        if form_vendor_id:
            vendor_sales_manager = User.query.get(form_vendor_id)
            if not vendor_sales_manager:
                flash('厂商销售负责人不存在', 'danger')
                return redirect(url_for('project.view_project', project_id=project_id))

            if not vendor_sales_manager.is_vendor_user():
                flash('厂商销售负责人必须是厂商企业账户', 'danger')
                return redirect(url_for('project.view_project', project_id=project_id))
            
            # 验证通过，更新为新的厂商销售负责人
            vendor_sales_manager_id = form_vendor_id
        # 如果没有指定新的厂商销售负责人，保持原有值（已在上面设置）
    else:
        # 如果新拥有人是厂商企业账户，自动设置为厂商销售负责人
        vendor_sales_manager_id = new_owner_id
    
    # 记录旧值用于ChangeLog
    old_owner_id = project.owner_id
    old_owner = User.query.get(old_owner_id) if old_owner_id else None

    # 更新项目拥有人和厂商销售负责人
    project.owner_id = new_owner_id
    project.vendor_sales_manager_id = vendor_sales_manager_id

    # 注意：不再自动更新关联报价单的owner_id
    # 报价单的owner_id保持为原创建人，以保留历史记录和绩效统计准确性
    # 这与批价单、行动记录、客户等模块的行为保持一致

    # 记录owner_id变更到ChangeLog
    if old_owner_id != new_owner_id:
        from app.models.change_log import ChangeLog
        ChangeLog.log_update(
            module_name='project',
            table_name='projects',
            record_id=project.id,
            field_name='owner_id',
            old_value=old_owner.real_name or old_owner.username if old_owner else '无',
            new_value=new_owner.real_name or new_owner.username,
            user_id=current_user.id,
            user_name=current_user.real_name or current_user.username,
            description=f'项目负责人从 {old_owner.real_name if old_owner else "无"} 变更为 {new_owner.real_name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

    db.session.commit()

    # 构建成功消息
    success_msg = '项目拥有人已更新'
    if vendor_sales_manager_id and vendor_sales_manager_id != new_owner_id:
        vendor_manager = User.query.get(vendor_sales_manager_id)
        success_msg += f'，厂商销售负责人已设置为 {vendor_manager.real_name or vendor_manager.username}'
    
    flash(success_msg, 'success')
    # 保持 tw 参数，返回 Tailwind 版本页面
    return redirect(url_for('project.view_project', project_id=project_id))


@project.route('/<int:project_id>/change_vendor_sales_manager', methods=['POST'])
@permission_required('project', 'edit')
def change_vendor_sales_manager(project_id):
    """修改项目厂商销售负责人"""
    project = Project.query.get_or_404(project_id)
    if not can_change_project_owner(current_user, project):
        flash(_('您没有权限修改该项目的厂商销售负责人'), 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

    # 检查项目是否被锁定
    from app.helpers.project_helpers import is_project_editable
    is_editable, lock_reason = is_project_editable(project_id, current_user.id)
    if not is_editable and current_user.role != 'admin':
        flash(_('项目已被锁定，无法修改厂商销售负责人: %(reason)s', reason=lock_reason), 'warning')
        return redirect(url_for('project.view_project', project_id=project_id))

    vendor_sales_manager_id = request.form.get('vendor_sales_manager_id', type=int)
    if not vendor_sales_manager_id:
        flash(_('请选择厂商销售负责人'), 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

    from app.models.user import User
    vendor_sales_manager = User.query.get(vendor_sales_manager_id)
    if not vendor_sales_manager:
        flash(_('厂商销售负责人不存在'), 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

    # 验证是否为厂商用户
    if not vendor_sales_manager.is_vendor_user():
        flash(_('厂商销售负责人必须是厂商企业账户'), 'danger')
        return redirect(url_for('project.view_project', project_id=project_id))

    # 记录旧值用于ChangeLog
    old_vendor_id = project.vendor_sales_manager_id
    old_vendor = User.query.get(old_vendor_id) if old_vendor_id else None

    # 更新厂商销售负责人
    project.vendor_sales_manager_id = vendor_sales_manager_id

    # 记录变更到ChangeLog
    if old_vendor_id != vendor_sales_manager_id:
        from app.models.change_log import ChangeLog
        ChangeLog.log_update(
            module_name='project',
            table_name='projects',
            record_id=project.id,
            field_name='vendor_sales_manager_id',
            old_value=old_vendor.real_name or old_vendor.username if old_vendor else '无',
            new_value=vendor_sales_manager.real_name or vendor_sales_manager.username,
            user_id=current_user.id,
            user_name=current_user.real_name or current_user.username,
            description=f'厂商销售负责人从 {old_vendor.real_name if old_vendor else "无"} 变更为 {vendor_sales_manager.real_name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

    db.session.commit()
    flash(_('厂商销售负责人已更新为 %(name)s', name=vendor_sales_manager.real_name or vendor_sales_manager.username), 'success')
    # 保持 tw 参数，返回 Tailwind 版本页面
    return redirect(url_for('project.view_project', project_id=project_id))


@project.route('/action/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
@permission_required('customer', 'view')
def delete_action_reply(reply_id):
    from app.models.action import ActionReply
    reply = ActionReply.query.get_or_404(reply_id)
    if reply.owner_id != current_user.id and current_user.role != 'admin':
        return jsonify({'success': False, 'message': '无权删除此回复'}), 403
    db.session.delete(reply)
    db.session.commit()
    return jsonify({'success': True})

@project.route('/api/project/<int:project_id>', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_project_api(project_id):
    """获取项目详情API"""
    project = Project.query.get_or_404(project_id)

    return jsonify({
        'id': project.id,
        'project_name': project.project_name,
        'current_stage': project.current_stage,
        'project_type': project.project_type,
        'owner_id': project.owner_id,
        'owner_name': project.owner.username if project.owner else None
    })

@project.route('/api/users', methods=['GET'])
@login_required
@permission_required('project', 'view')  # 读接口(取用户列表),view 即可
def get_users_api():
    """获取用户列表API，用于销售负责人选择"""
    user_type = request.args.get('type', 'all')  # vendor, dealer, all
    
    try:
        from app.models.user import User
        from app.models.dictionary import Dictionary

        if user_type == 'vendor':
            # 获取厂商用户：company_name 在 Dictionary 中标记为 is_vendor=True
            vendor_companies = db.session.query(Dictionary.value).filter(
                Dictionary.type == 'company',
                Dictionary.is_active == True,
                Dictionary.is_vendor == True
            ).subquery()
            users = User.query.filter(
                User.company_name.isnot(None),
                User.company_name.in_(db.session.query(vendor_companies))
            ).all()
        elif user_type == 'dealer':
            # 获取代理商用户：company_name 不在厂商列表中
            vendor_company_names = db.session.query(Dictionary.value).filter(
                Dictionary.type == 'company',
                Dictionary.is_active == True,
                Dictionary.is_vendor == True
            )
            users = User.query.filter(
                or_(
                    User.company_name.is_(None),
                    ~User.company_name.in_(vendor_company_names)
                )
            ).all()
        else:
            # 获取所有用户
            users = User.query.all()
        
        users_data = []
        for user in users:
            # 获取真实姓名，如果没有则使用用户名
            display_name = user.real_name if hasattr(user, 'real_name') and user.real_name else user.username
            # 获取角色的中文显示名
            role_display = get_role_display_name(user.role) if user.role else '未知角色'
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'real_name': display_name,
                'company_name': user.company_name,
                'role': user.role,
                'role_display': role_display,
                'display_text': f"{display_name} ({role_display})"  # 用于前端显示的组合文本
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        current_app.logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500 

@project.route('/api/project/<int:project_id>/latest-quotation', methods=['GET'])
@login_required
@permission_required('project', 'view')
def get_project_latest_quotation_api(project_id):
    """获取项目最新报价信息"""
    try:
        project = Project.query.get_or_404(project_id)

        # 获取最新报价
        latest_quotation = Quotation.query.filter_by(project_id=project_id).order_by(Quotation.created_at.desc()).first()
        
        if latest_quotation:
            return jsonify({
                'success': True,
                'data': {
                    'id': latest_quotation.id,
                    'quotation_number': latest_quotation.quotation_number,
                    'amount': latest_quotation.amount,
                    'created_at': latest_quotation.created_at.strftime('%Y-%m-%d %H:%M:%S') if latest_quotation.created_at else None,
                    'owner': {
                        'id': latest_quotation.owner.id if latest_quotation.owner else None,
                        'name': latest_quotation.owner.real_name or latest_quotation.owner.username if latest_quotation.owner else None
                    }
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': None,
                'message': '暂无报价记录'
            })
            
    except Exception as e:
        logger.error(f"获取项目最新报价失败: {str(e)}")
        return jsonify({'success': False, 'message': '获取报价信息失败'}), 500

# 项目评分相关API端点已迁移到新的评分系统
# 请使用 app/views/project_scoring_api.py 中的新API

def _get_project_owner_options(current_user):
    """获取项目拥有人筛选选项 - 只查询实际存在的拥有者"""
    try:
        # 获取当前用户可见的项目中的所有拥有者ID
        unique_owner_ids_query = get_viewable_data(Project, current_user)\
            .filter(Project.owner_id.isnot(None))\
            .with_entities(Project.owner_id.distinct())
        
        unique_owner_ids = {row[0] for row in unique_owner_ids_query.all()}
        
        if not unique_owner_ids:
            return []
        
        # 只查询需要的用户，避免加载所有用户
        # 移除活跃状态过滤，确保所有实际拥有项目的用户都出现在筛选选项中
        available_users = User.query.filter(
            User.id.in_(unique_owner_ids)
        ).order_by(User.real_name, User.username).all()
        
        return [
            {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
            for user in available_users
        ]
        
    except Exception as e:
        current_app.logger.error(f"获取项目拥有人选项失败: {e}")
        return []

def _format_currency_amount(amount, currency_symbol=None):
    """格式化金额，添加千位分隔符"""
    # 如果没有传入货币符号，使用当前语言的默认货币符号
    if currency_symbol is None:
        from app.utils.dictionary_helpers import get_default_currency, get_currency_symbol
        default_currency = get_default_currency()
        currency_symbol = get_currency_symbol(default_currency)

    try:
        # 保留两位小数
        formatted = f"{amount:.2f}"
        # 分割整数和小数部分
        parts = formatted.split('.')
        # 为整数部分添加千位分隔符
        parts[0] = f"{int(parts[0]):,}"
        # 重新组合
        return f"{currency_symbol}{'.'.join(parts)}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"

def _create_stage_card(stage_key, title, icon, stage_stats, currency_symbol, color):
    """创建阶段统计卡片配置（使用传递的currency_symbol）"""
    stage_data = stage_stats.get(stage_key, {'count': 0, 'amount': 0})

    # 使用系统货币配置的金额单位（与语言设置解耦）
    amount_unit = Config.AMOUNT_UNIT

    return {
        'id': stage_key,
        'title': _(title),
        'icon': icon,
        'value': stage_data['count'],
        'amount': round(stage_data['amount'] / Config.AMOUNT_DIVISOR, 2),  # 使用系统配置的除数转换
        'unit': _('个'),
        'amount_unit': amount_unit,  # 使用系统货币配置的单位
        'currency_symbol': currency_symbol,  # 添加货币符号
        'color': color,
        'clickable': True,  # 启用点击筛选功能
        'click_params': {'current_stage': stage_key},  # 点击时筛选对应阶段
        'data_key': stage_key
    }

def _get_vendor_manager_options(current_user):
    """获取厂商负责人筛选选项 - 只查询实际存在的负责人"""
    try:
        # 获取当前用户可见的项目中的所有厂商负责人ID
        unique_manager_ids_query = get_viewable_data(Project, current_user)\
            .filter(Project.vendor_sales_manager_id.isnot(None))\
            .with_entities(Project.vendor_sales_manager_id.distinct())
        
        unique_manager_ids = {row[0] for row in unique_manager_ids_query.all()}
        
        if not unique_manager_ids:
            return []
        
        # 只查询需要的用户，避免加载所有用户
        # 移除活跃状态过滤，确保所有实际负责项目的用户都出现在筛选选项中
        available_managers = User.query.filter(
            User.id.in_(unique_manager_ids)
        ).order_by(User.real_name, User.username).all()
        
        return [
            {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
            for user in available_managers
        ]
        
    except Exception as e:
        current_app.logger.error(f"获取厂商负责人选项失败: {e}")
        return []

def _calculate_stage_stats_fast(projects):
    """快速计算项目阶段统计（基于当前显示的项目）"""
    stage_stats = {}
    # 定义所有可能的阶段
    all_stages = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']

    # 初始化所有阶段计数和金额为0
    for stage in all_stages:
        stage_stats[stage] = {'count': 0, 'amount': 0}

    # 快速统计（无汇率转换）
    for project in projects:
        stage = project.current_stage
        if stage in stage_stats:
            stage_stats[stage]['count'] += 1
            stage_stats[stage]['amount'] += project.quotation_customer or 0

    return stage_stats


def _apply_filters_to_query(query, current_user, search=None, owner_id=None, vendor_sales_manager_id=None,
                           activity_status=None, industry=None, report_source=None, current_stage=None, project_type=None):
    """将筛选条件应用到查询对象，复用现有筛选逻辑"""
    from sqlalchemy import or_

    # 应用搜索条件
    if search:
        query = query.filter(
            or_(
                Project.project_name.ilike(f'%{search}%'),
                Project.authorization_code.ilike(f'%{search}%')
            )
        )

    # 应用筛选条件
    if owner_id:
        query = query.filter(Project.owner_id == owner_id)

    if vendor_sales_manager_id:
        query = query.filter(Project.vendor_sales_manager_id == vendor_sales_manager_id)

    if activity_status:
        query = query.filter(Project.activity_status == activity_status)

    if industry:
        query = query.filter(Project.industry == industry)

    if report_source:
        query = query.filter(Project.report_source == report_source)

    if project_type:
        query = query.filter(Project.project_type == project_type)

    if current_stage:
        query = query.filter(Project.current_stage == current_stage)

    return query


def get_full_project_stats(base_query, target_currency=None):
    """使用数据库聚合查询获取完整项目统计数据"""
    from sqlalchemy import func, case
    from app import db
    from app.services.exchange_rate_service import exchange_rate_service

    # 默认使用系统货币
    if target_currency is None:
        target_currency = Config.DEFAULT_CURRENCY

    try:
        # 1. 基础统计（count 类）- 数据库聚合
        base_stats = base_query.with_entities(
            func.count(Project.id).label('total_count'),
            func.sum(case(
                (Project.activity_status.in_(['highly_active', 'active', 'normal']), 1), else_=0
            )).label('active_count'),
            func.sum(case(
                (Project.activity_status.in_(['to_follow', 'dormant', 'churned']), 1), else_=0
            )).label('inactive_count'),
        ).first()

        # 2. 跨货币聚合 - 使用 MultiCurrencyAggregationService 动态换算
        # Project.quotation_customer 存的是**最新一张报价单的原金额**（不换算）
        # Project.quotation_currency 存的是**原货币**
        # 跨项目统计时需要按货币分组 + 动态换算到 target_currency
        from app.services.multi_currency_aggregation import MultiCurrencyAggregationService

        total_converted_amount = MultiCurrencyAggregationService.sum_converted(
            base_query, Project.quotation_customer, Project.quotation_currency,
            target_currency=target_currency
        )

        # 3. 按阶段分组的跨货币聚合
        stage_amount_map = MultiCurrencyAggregationService.sum_converted_by_group(
            base_query, Project.quotation_customer, Project.quotation_currency,
            Project.current_stage, target_currency=target_currency
        )

        # 4. 阶段计数（count 不涉及货币）
        stage_counts_raw = base_query.with_entities(
            Project.current_stage,
            func.count(Project.id).label('count')
        ).group_by(Project.current_stage).all()

        # 5. 合并阶段统计数据
        all_stages = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']
        stage_stats = {stage: {'count': 0, 'amount': 0} for stage in all_stages}
        for stage, count in stage_counts_raw:
            if stage in stage_stats:
                stage_stats[stage]['count'] = count or 0
                stage_stats[stage]['amount'] = stage_amount_map.get(stage, 0.0)

        result = {
            'total_count': base_stats.total_count or 0,
            'active_count': base_stats.active_count or 0,
            'inactive_count': base_stats.inactive_count or 0,
            'total_value': total_converted_amount,
            'stage_stats': stage_stats
        }

        return result

    except Exception as e:
        current_app.logger.error(f"获取完整项目统计失败: {str(e)}")
        # 返回默认值避免页面错误
        default_result = {
            'total_count': 0,
            'active_count': 0,
            'inactive_count': 0,
            'total_value': 0,
            'stage_stats': {stage: {'count': 0, 'amount': 0} for stage in ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']}
        }
        return default_result

def _format_stats_for_ajax(full_stats):
    """将get_full_project_stats的输出格式化为AJAX接口需要的格式"""
    stage_stats = full_stats.get('stage_stats', {})

    return {
        'total': full_stats.get('total_count', 0),
        'total_amount': round(full_stats.get('total_value', 0) / 10000, 2),
        'discover': stage_stats.get('discover', {'count': 0})['count'],
        'discover_amount': round(stage_stats.get('discover', {'amount': 0})['amount'] / 10000, 2),
        'embed': stage_stats.get('embed', {'count': 0})['count'],
        'embed_amount': round(stage_stats.get('embed', {'amount': 0})['amount'] / 10000, 2),
        'pre_tender': stage_stats.get('pre_tender', {'count': 0})['count'],
        'pre_tender_amount': round(stage_stats.get('pre_tender', {'amount': 0})['amount'] / 10000, 2),
        'tendering': stage_stats.get('tendering', {'count': 0})['count'],
        'tendering_amount': round(stage_stats.get('tendering', {'amount': 0})['amount'] / 10000, 2),
        'awarded': stage_stats.get('awarded', {'count': 0})['count'],
        'awarded_amount': round(stage_stats.get('awarded', {'amount': 0})['amount'] / 10000, 2),
        'quoted': stage_stats.get('quoted', {'count': 0})['count'],
        'quoted_amount': round(stage_stats.get('quoted', {'amount': 0})['amount'] / 10000, 2),
        'signed': stage_stats.get('signed', {'count': 0})['count'],
        'signed_amount': round(stage_stats.get('signed', {'amount': 0})['amount'] / 10000, 2),
        'lost': stage_stats.get('lost', {'count': 0})['count'],
        'lost_amount': round(stage_stats.get('lost', {'amount': 0})['amount'] / 10000, 2),
        'paused': stage_stats.get('paused', {'count': 0})['count'],
        'paused_amount': round(stage_stats.get('paused', {'amount': 0})['amount'] / 10000, 2),
    }




@project.route('/<int:project_id>/api/update-sharing', methods=['POST'])
@login_required
def api_update_project_sharing(project_id):
    """AT 共享设置提交(项目)— JSON 入参 {share_enabled, shared_with_users:[id,...]}"""
    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()
    from app.utils.sharing import SharingService
    if not SharingService.can_edit_sharing_settings(current_user, project, 'project'):
        return jsonify({'success': False, 'message': '您没有权限编辑此项目的共享设置'}), 403
    data = request.get_json() or {}
    try:
        if hasattr(project, 'share_enabled'):
            project.share_enabled = bool(data.get('share_enabled'))
        if hasattr(project, 'shared_with_users'):
            ids = data.get('shared_with_users') or []
            project.shared_with_users = sorted(set(int(x) for x in ids if str(x).isdigit()))
        db.session.commit()
        return jsonify({'success': True, 'message': '共享设置已更新'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新项目共享设置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@project.route('/update_project_sharing/<int:project_id>', methods=['POST'])
@login_required
@permission_required('project', 'view')
def update_project_sharing(project_id):
    """更新项目共享设置"""
    try:
        project_obj = Project.query.get_or_404(project_id)
        
        # 检查用户是否有权限编辑项目共享设置
        from app.utils.sharing import SharingService
        if not SharingService.can_edit_sharing_settings(current_user, project_obj, 'project'):
            flash(_('您没有权限编辑此项目的共享设置'), 'error')
            return redirect(url_for('project.view_project', project_id=project_id))
        
        # 更新共享设置
        if SharingService.update_sharing_from_request(project_obj, current_user, 'project'):
            db.session.commit()
            flash(_('项目共享设置已更新'), 'success')
            logger.info(f"用户 {current_user.username} 更新了项目 {project_obj.project_name} (ID: {project_id}) 的共享设置")
        else:
            flash(_('更新共享设置失败'), 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(_('更新共享设置时发生错误'), 'error')
        logger.error(f"更新项目共享设置失败: {e}")
    
    return redirect(url_for('project.view_project', project_id=project_id))

# ===== 项目-客户关联管理API =====
# 注：客户搜索API已统一使用 /api/export-helpers/customers/search
# 该端点支持权限过滤、空搜索和点击展开功能

@project.route('/api/customer_associations/<int:project_id>')
@permission_required('project', 'view')  
def get_customer_associations(project_id):
    """获取项目的客户关联列表"""
    try:
        from app.models.project_customer_association import ProjectCustomerAssociation

        # 获取项目对象（用于后续厂商负责人判断）
        project_obj = Project.query.get_or_404(project_id)

        # 获取活跃的客户关联
        associations = ProjectCustomerAssociation.get_active_associations(project_id)

        # 🔥 权限过滤：厂商负责人可以查看所有关联客户，其他用户需要客户权限
        if current_user.role == 'admin' or (hasattr(project_obj, 'vendor_sales_manager_id') and project_obj.vendor_sales_manager_id == current_user.id):
            # 管理员和厂商负责人：查看所有关联客户
            filtered_associations = associations
        else:
            # 其他用户：只保留有权限查看的客户
            from app.utils.access_control import can_view_company
            filtered_associations = [
                assoc for assoc in associations
                if assoc.company and can_view_company(current_user, assoc.company)
            ]

        associations_data = []

        for assoc in filtered_associations:
            company = assoc.company

            # 检查是否可以移除此关联
            # 严格遵循"谁关联谁删除"原则
            can_remove = False
            
            # 只有管理员有完全权限
            if current_user.role == 'admin':
                can_remove = True
            # 只有创建者可以移除自己创建的关联
            elif (hasattr(assoc, 'created_by') and
                  assoc.created_by == current_user.id):
                can_remove = True
            
            # 获取拥有者信息，用于正确显示徽章
            owner_info = None
            if company.owner:
                owner_info = {
                    'real_name': company.owner.real_name,
                    'username': company.owner.username,
                    'is_vendor_user': company.owner.is_vendor_user()
                }
            
            # 获取创建者信息（安全处理）
            created_by_name = None
            created_by_is_vendor = False
            try:
                if hasattr(assoc, 'creator') and assoc.creator:
                    created_by_name = assoc.creator.real_name or assoc.creator.username
                    created_by_is_vendor = assoc.creator.is_vendor_user()
            except Exception as e:
                # 如果creator字段不存在或查询失败，使用created_by字段
                logger.debug(f"获取创建者信息失败: {e}")
                if hasattr(assoc, 'created_by') and assoc.created_by:
                    try:
                        from app.models.user import User
                        creator_user = User.query.get(assoc.created_by)
                        if creator_user:
                            created_by_name = creator_user.real_name or creator_user.username
                            created_by_is_vendor = creator_user.is_vendor_user()
                    except Exception as e2:
                        logger.debug(f"查询创建者用户失败: {e2}")
                        created_by_name = f"用户#{assoc.created_by}" if hasattr(assoc, 'created_by') else None

            associations_data.append({
                'id': assoc.id,
                'company_id': assoc.company_id,
                'company_name': company.company_name,
                'customer_type': assoc.customer_type,
                'customer_type_label': assoc.customer_type_label,
                'company_type': company.company_type,
                'owner_name': company.owner.real_name if company.owner else None,
                'owner_info': owner_info,
                'is_active': company.owner.is_active if company.owner else False,
                'can_remove': can_remove,
                'can_view_customer': True,  # 已过滤，用户必然有查看权限
                'created_by': assoc.created_by,
                'created_by_name': created_by_name,
                'created_by_is_vendor': created_by_is_vendor,
                'created_at': assoc.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'associations': associations_data
        })
        
    except Exception as e:
        logger.error(f"获取项目客户关联失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取客户关联失败，请重试'
        }), 500

@project.route('/api/add_customer_association', methods=['POST'])
@permission_required('project', 'view')
def add_customer_association():
    """添加项目-客户关联（薄壳，调 project_customer_link_service）"""
    from app.services.project_customer_link_service import add_link, LinkError
    try:
        data = request.get_json() or {}
        add_link(current_user, data.get('project_id'), data.get('company_id'))
        db.session.commit()
        return jsonify({'success': True, 'message': '客户关联添加成功'})
    except LinkError as e:
        return jsonify({'success': False, 'message': e.message}), e.status
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加客户关联失败: {e}")
        return jsonify({
            'success': False,
            'message': '添加客户关联失败，请重试'
        }), 500

@project.route('/api/remove_customer_association/<int:association_id>', methods=['POST'])
@permission_required('project', 'view')
def remove_customer_association(association_id):
    """移除项目-客户关联（薄壳，调 project_customer_link_service）"""
    from app.services.project_customer_link_service import remove_link, LinkError
    try:
        remove_link(current_user, association_id)
        db.session.commit()
        return jsonify({'success': True, 'message': '关联已移除'})
    except LinkError as e:
        return jsonify({'success': False, 'message': e.message}), e.status
    except Exception as e:
        db.session.rollback()
        logger.error(f"移除客户关联失败: {e}")
        return jsonify({
            'success': False,
            'message': '移除客户关联失败，请重试'
        }), 500

@project.route('/api/customer_associations/<int:project_id>/render')
@permission_required('project', 'view')
def render_customer_associations_list(project_id):
    """渲染项目客户关联列表的通用组件HTML"""
    from flask import render_template
    from app.models.project_customer_association import ProjectCustomerAssociation
    
    try:
        # 获取项目对象（用于后续权限判断）
        project_obj = Project.query.get_or_404(project_id)

        # 获取客户关联数据
        associations = ProjectCustomerAssociation.get_active_associations(project_id)
        
        # 准备数据供模板使用
        association_data = []
        for association in associations:
            company = association.company
            owner = company.owner if company else None
            
            can_remove = ((current_user.role == 'admin' or 
                          current_user.id == project_obj.owner_id) and 
                         (not project_obj.is_locked or current_user.role == 'admin'))
            
            # 检查当前用户是否有权限查看此客户
            from app.utils.access_control import can_view_company
            can_view_customer = can_view_company(current_user, company) if company else False
            
            association_data.append({
                'id': association.id,
                'company_id': company.id,
                'company_name': company.company_name,
                'customer_type_label': dict(ProjectCustomerAssociation.CUSTOMER_TYPE_CHOICES).get(
                    association.customer_type, association.customer_type
                ),
                'owner_name': owner.real_name if owner else None,
                'is_active': bool(owner.is_active) if owner else False,
                'can_remove': can_remove,
                'can_view_customer': can_view_customer,
                'company': company  # 为模板权限检查提供company对象
            })
        
        # 使用专门的模板渲染客户关联列表
        
        rendered_html = render_template(
            'project/customer_associations_list.html',
            associations=association_data
        )
        
        return jsonify({
            'success': True,
            'html': rendered_html
        })
        
    except Exception as e:
        logger.error(f"渲染客户关联列表失败: {e}")
        return jsonify({
            'success': False,
            'message': '渲染客户关联列表失败，请重试'
        }), 500


# ==================== 报价单管理API ====================

@project.route('/api/quotations/<int:project_id>')
@permission_required('project', 'view')
def get_quotations_list(project_id):
    """获取项目的报价单列表（带权限过滤）"""
    try:
        from app.models.quotation import Quotation
        from app.models.customer import Company

        # 获取项目对象（确保项目存在）
        project_obj = Project.query.get_or_404(project_id)

        # 查询项目的报价单（两步过滤：先获取所有，再逐个检查权限）
        all_quotations = Quotation.query.filter_by(
            project_id=project_id
        ).order_by(Quotation.updated_at.desc()).all()

        # 通过 can_view_quotation 逐个检查权限
        from app.utils.access_control import can_view_quotation
        quotations = [q for q in all_quotations if can_view_quotation(current_user, q)]

        # 准备返回数据
        quotations_data = []
        for quot in quotations:
            # 获取关联客户信息
            customer_name = None
            company_id = None
            if quot.customer_id:
                company = quot.customer  # 直接使用关系
                if company:
                    customer_name = company.company_name
                    company_id = company.id

            # 获取创建者信息
            owner_name = None
            is_vendor = False
            if quot.owner:
                owner_name = quot.owner.real_name if quot.owner.real_name else quot.owner.username
                is_vendor = quot.owner.is_vendor_user()

            # 检查是否可以删除（只有创建人可以删除）
            is_owner = (quot.owner_id == current_user.id)

            quotations_data.append({
                'id': quot.id,
                'quotation_number': quot.quotation_number,
                'amount': quot.amount or 0,
                'currency': quot.currency or 'CNY',
                'currency_symbol': quot.currency_symbol,
                'customer_name': customer_name or '未关联客户',
                'company_id': company_id,
                'owner_id': quot.owner_id,
                'owner_name': owner_name or '未知',
                'is_vendor': is_vendor,
                'created_at': quot.created_at.strftime('%Y-%m-%d') if quot.created_at else '',
                'updated_at': quot.updated_at.strftime('%Y-%m-%d %H:%M') if quot.updated_at else '',
                'is_owner': is_owner,
                'can_delete': is_owner or current_user.role == 'admin',
                # 确认徽章字段
                'confirmation_badge_status': quot.confirmation_badge_status,
                'confirmed_by': quot.confirmed_by,
                'confirmed_at': quot.confirmed_at.strftime('%Y-%m-%d %H:%M:%S') if quot.confirmed_at else None
            })

        return jsonify({
            'success': True,
            'quotations': quotations_data,
            'total_amount': sum([q['amount'] for q in quotations_data]),
            'count': len(quotations_data)
        })

    except Exception as e:
        logger.error(f"获取报价单列表失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取报价单列表失败，请重试'
        }), 500


@project.route('/api/pricing_orders/<int:project_id>')
@permission_required('project', 'view')
def get_pricing_orders_list(project_id):
    """获取项目的批价单列表（带权限过滤）"""
    try:
        from app.models.pricing_order import PricingOrder

        # 获取项目对象（确保项目存在）
        project_obj = Project.query.get_or_404(project_id)

        # 查询项目的批价单（两步过滤：先获取所有，再逐个检查权限）
        all_pricing_orders = PricingOrder.query.filter_by(
            project_id=project_id
        ).order_by(PricingOrder.created_at.desc()).all()

        # 通过 can_view_pricing_order 逐个检查权限
        from app.utils.access_control import can_view_pricing_order
        pricing_orders = [po for po in all_pricing_orders if can_view_pricing_order(current_user, po)]

        pricing_orders_data = []
        for po in pricing_orders:
            # 经销商名称 - 安全处理
            dealer_name = '无'
            if po.dealer:
                try:
                    dealer_name = po.dealer.company_name or '无'
                except Exception as e:
                    logger.warning(f"获取经销商名称失败 (批价单ID: {po.id}): {e}")
                    dealer_name = '无'

            # 创建人名称 - 安全处理
            creator_name = '未知'
            if po.creator:
                try:
                    creator_name = po.creator.real_name or '未知'
                except Exception as e:
                    logger.warning(f"获取创建人名称失败 (批价单ID: {po.id}): {e}")
                    creator_name = '未知'

            # 获取状态标签（展开字典以便JSON序列化）
            status_label = po.status_label

            pricing_orders_data.append({
                'id': po.id,
                'order_number': po.order_number,
                'dealer_id': po.dealer_id,
                'dealer_name': dealer_name,
                'pricing_total_amount': po.pricing_total_amount or 0,
                'currency': po.currency or 'CNY',
                'currency_symbol': po.currency_symbol,
                'creator_name': creator_name,
                'is_vendor': po.creator.is_vendor_user() if po.creator else False,
                'status': po.status,
                'status_label': {
                    'zh': status_label['zh'],
                    'en': status_label['en'],
                    'color': status_label['color']
                },
                'created_at': po.created_at.strftime('%Y-%m-%d') if po.created_at else ''
            })

        return jsonify({
            'success': True,
            'pricing_orders': pricing_orders_data,
            'count': len(pricing_orders_data)
        })

    except Exception as e:
        logger.error(f"获取批价单列表失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取批价单列表失败，请重试'
        }), 500


@project.route('/api/remove_quotation/<int:quotation_id>', methods=['POST'])
@permission_required('project', 'view')
def remove_quotation(quotation_id):
    """删除报价单"""
    try:
        from app.models.quotation import Quotation

        # 获取报价单
        quotation = Quotation.query.get_or_404(quotation_id)

        # 验证删除权限：只有创建人或管理员可以删除
        if quotation.owner_id != current_user.id and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': '您只能删除自己创建的报价单'
            }), 403

        # 删除报价单
        db.session.delete(quotation)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '报价单删除成功'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除报价单失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除报价单失败: {str(e)}'
        }), 500


@project.route('/api/customer_associations/<int:project_id>/search')
@permission_required('project', 'view')
def search_project_customers_for_quotation(project_id):
    """搜索项目关联的客户（用于报价单创建时的客户选择）"""
    try:
        from app.models.project_customer_association import ProjectCustomerAssociation
        from app.models.customer import Company

        keyword = request.args.get('keyword', '').strip()
        saved_customer_id = request.args.get('saved_customer_id', type=int)  # 已保存的客户ID

        # 获取项目对象（确保项目存在）
        project_obj = Project.query.get_or_404(project_id)

        # 获取项目的客户关联
        associations = ProjectCustomerAssociation.get_active_associations(project_id)

        # 只保留用户有权限查看的客户
        from app.utils.access_control import can_view_company
        filtered_companies = []
        for assoc in associations:
            if assoc.company and can_view_company(current_user, assoc.company):
                filtered_companies.append(assoc.company)

        # ⚠️ 特殊处理: 如果提供了saved_customer_id,确保已保存的客户在结果中
        # 编辑报价单时,用户应该能看到报价单已关联的客户,即使该客户不在项目关联中
        if saved_customer_id:
            # 检查已保存的客户是否已在列表中
            if not any(c.id == saved_customer_id for c in filtered_companies):
                # 尝试加载该客户并插入到列表开头
                saved_customer = Company.query.get(saved_customer_id)
                if saved_customer:
                    filtered_companies.insert(0, saved_customer)

        # 关键词过滤
        if keyword:
            filtered_companies = [
                c for c in filtered_companies
                if keyword.lower() in c.company_name.lower()
            ]

        # 返回格式化数据（与标准客户搜索API格式一致）
        results = []
        for company in filtered_companies[:10]:  # 限制返回10个结果
            # 获取主要联系人 - 通过查询Contact表
            from app.models.customer import Contact
            primary_contact = Contact.query.filter_by(
                company_id=company.id,
                is_primary=True
            ).first()

            results.append({
                'id': company.id,
                'company_name': company.company_name,
                'contact_person': primary_contact.name if primary_contact else None,
                'phone': primary_contact.phone if primary_contact else None,
                'owner_name': company.owner.real_name if company.owner else None,
                'industry': company.industry if hasattr(company, 'industry') else None
            })

        return jsonify({
            'success': True,
            'results': results  # 修改字段名为results以匹配前端期望
        })

    except Exception as e:
        logger.error(f"搜索项目关联客户失败: {e}")
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        }), 500


@project.route('/<int:project_id>/start_approval', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以启动自己项目的审批
def start_project_approval(project_id):
    """启动项目审批流程"""
    try:
        project_obj = Project.query.get_or_404(project_id)

        # 使用统一的数据权限检查（包含数据归属逻辑）
        if not can_edit_data(project_obj, current_user):
            return jsonify({
                'success': False,
                'message': '您没有权限提交此项目的审批'
            }), 403
        
        # 检查项目类型是否填写
        if not project_obj.project_type or project_obj.project_type.strip() == '':
            return jsonify({
                'success': False,
                'message': '项目类型未填写，无法提交审批。请先完善项目信息。'
            }), 400
        
        # 检查是否已经有进行中的审批
        from app.helpers.approval_helpers import get_object_approval_instance
        existing_approval = get_object_approval_instance('project', project_id)
        if existing_approval and existing_approval.status == 'pending':
            return jsonify({
                'success': False,
                'message': '此项目已有进行中的审批流程'
            }), 400
        
        # 获取可用的审批模板
        from app.helpers.approval_helpers import get_available_templates
        templates = get_available_templates('project')
        if not templates:
            return jsonify({
                'success': False,
                'message': '未找到可用的项目审批模板，请联系管理员配置'
            }), 400
        
        # 使用第一个可用模板（通常是"测试流程分支"）
        template = templates[0]
        
        # 启动审批流程（使用 auto_commit=False 确保与项目状态更新在同一事务中）
        from app.helpers.approval_helpers import start_approval_process
        approval_instance = start_approval_process(
            object_type='project',
            object_id=project_id,
            template_id=template.id,
            user_id=current_user.id,
            auto_commit=False
        )

        if approval_instance:
            # 更新项目状态为待审批
            project_obj.status = 'pending'
            db.session.commit()
            logging.info(f"项目 {project_id} 审批流程启动成功，审批实例ID: {approval_instance.id}")
            return jsonify({
                'success': True,
                'message': '项目审批已提交成功',
                'approval_instance_id': approval_instance.id
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': '启动审批流程失败，请检查项目状态或联系管理员'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"启动项目审批失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'系统错误: {str(e)}'
        }), 500


# ==================== 订单审批系统风格的项目审批API端点 ====================

@project.route('/api/approval/<int:project_id>/templates')
@login_required
@permission_required('project', 'view')
def get_project_approval_templates(project_id):
    """获取项目审批模板列表"""
    try:
        # 检查项目访问权限
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 获取项目类型的审批模板
        from app.models.approval import ApprovalProcessTemplate
        templates = ApprovalProcessTemplate.query.filter_by(
            object_type='project',
            is_active=True
        ).order_by(ApprovalProcessTemplate.name).all()
        
        template_list = []
        for template in templates:
            template_list.append({
                'id': template.id,
                'name': template.name,
                'description': template.description or '',
                'total_steps': len(template.steps)
            })
        
        return jsonify({
            'success': True,
            'templates': template_list
        })
    except Exception as e:
        logging.error(f"获取项目审批模板失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取失败：{str(e)}'})


@project.route('/api/approval/<int:project_id>/preview-authorization', methods=['POST'])
@login_required
@permission_required('project', 'view')
def preview_project_authorization(project_id):
    """预览项目授权编码"""
    try:
        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 获取当前审批实例和步骤
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance('project', project_id)
        if not approval_instance:
            return jsonify({
                'success': False,
                'message': '项目暂无审批流程'
            })
        
        # 🔥 修复：使用 get_current_step_info() 获取步骤信息（支持动态步骤）
        current_step = approval_instance.get_current_step_info()
        if not current_step:
            return jsonify({
                'success': False,
                'message': '未找到当前审批步骤'
            })

        # 获取步骤属性（兼容字典和对象）
        step_action_type = current_step.get('action_type') if isinstance(current_step, dict) else current_step.action_type
        step_branch_condition = current_step.get('branch_condition') if isinstance(current_step, dict) else current_step.branch_condition

        # 检查是否为授权步骤（简化版本）
        is_auth_step = False
        if step_action_type == 'authorization':
            is_auth_step = True
        elif step_action_type == 'branch_decision' and step_branch_condition:
            try:
                import json
                branch_condition = step_branch_condition
                if isinstance(branch_condition, str):
                    branch_condition = json.loads(branch_condition)

                field_name = branch_condition.get('field')
                if field_name:
                    field_value = getattr(project_obj, field_name, None)
                    conditions = branch_condition.get('conditions', [])
                    for condition in conditions:
                        if ((condition.get('operator') == 'equals' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'in' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'contains' and condition.get('value') in str(field_value))):
                            is_auth_step = 'authorization' in condition.get('action', '')
                            break
            except Exception as e:
                logging.error(f"检查分支授权步骤失败: {e}")

        if not is_auth_step:
            return jsonify({
                'success': False,
                'message': '当前步骤不是授权步骤'
            })

        # 获取匹配的分支授权动作
        branch_action = None
        if step_action_type == 'branch_decision' and step_branch_condition:
            try:
                import json
                branch_condition = step_branch_condition
                if isinstance(branch_condition, str):
                    branch_condition = json.loads(branch_condition)
                
                field_name = branch_condition.get('field')
                if field_name:
                    field_value = getattr(project_obj, field_name, None)
                    conditions = branch_condition.get('conditions', [])
                    for condition in conditions:
                        if ((condition.get('operator') == 'equals' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'in' and field_value == condition.get('value')) or
                            (condition.get('operator') == 'contains' and condition.get('value') in str(field_value))):
                            branch_action = condition.get('action')
                            break
            except Exception as e:
                logging.error(f"解析分支条件失败: {e}")
        
        # 使用重构后的授权处理函数（预览模式）
        from app.helpers.approval_helpers import _handle_project_authorization
        preview_code = _handle_project_authorization(
            approval_instance, 
            project_obj.project_type, 
            preview_only=True, 
            branch_action=branch_action
        )
        
        return jsonify({
            'success': True,
            'authorization_code': preview_code,
            'message': f'通过审批后将授予授权编码：{preview_code}'
        })
        
    except Exception as e:
        logging.error(f"预览授权编码失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'预览失败：{str(e)}'
        }), 500


@project.route('/api/approval/<int:project_id>/submit', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以提交自己项目的审批
def submit_project_approval_standard(project_id):
    """提交项目审批 - 标准化API"""
    try:
        logging.info(f"提交项目审批请求: project_id={project_id}, user_id={current_user.id}")

        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            logging.warning(f"项目不存在或无权限访问: project_id={project_id}")
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404

        logging.info(f"项目当前状态: status={project_obj.status}, is_locked={project_obj.is_locked}")

        # 检查项目状态（None 或空字符串视为 draft）
        effective_status = project_obj.status or 'draft'
        if effective_status not in ['draft', 'rejected']:
            logging.warning(f"项目状态不允许提交审批: status={project_obj.status}")
            return jsonify({
                'success': False,
                'message': '只有草稿或被拒绝状态的项目才能提交审批'
            })

        # 使用统一的数据权限检查（包含数据归属逻辑）
        if not can_edit_data(project_obj, current_user):
            logging.warning(f"无编辑权限: project_id={project_id}, user_id={current_user.id}")
            return jsonify({
                'success': False,
                'message': '只有项目创建人可以提交审批'
            }), 403
        
        # 业务线路由发起(2026-06-13):渠道→渠道经理/服务→服务经理/其余→营销总监
        # (缺位跳级)→ 总经理;模板由代码 get-or-create,忽略前端 template_id
        from app.helpers.project_hold_helpers import submit_project_report_approval
        approval_instance, _rep_err = submit_project_report_approval(project_obj, current_user.id)
        if not approval_instance and _rep_err:
            return jsonify({'success': False, 'message': _rep_err}), 400

        if approval_instance:
            # 更新项目状态为待审批
            project_obj.status = 'pending'
            db.session.add(project_obj)
            # 统一提交：审批实例创建 + 项目状态更新
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '项目审批已提交',
                'approval_instance_id': approval_instance.id
            })
        else:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': '启动审批流程失败'
            }), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"提交项目审批失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'提交失败：{str(e)}'
        }), 500


def _get_project_approval_flow_impl(project_id, object_type='project'):
    """
    项目审批流原始数据获取 — 纯函数,返回 dict 而非 Flask Response。

    object_type:'project'(报备审批,默认) 或 'project_hold'(失败/搁置审核)。
    两者共用同一套流程构建逻辑,只是审批实例命名空间不同。

    跟 `purchase_order_routes._get_approval_flow_impl` 对齐范式,供:
      • `get_project_approval_flow` endpoint(thin jsonify wrapper)
      • `at_view_project` 视图(同步预渲染审批卡,无需 fetch)

    返回字段(已对齐 at_approval_helpers.build_approval_data 期望):
      {
        'success': bool,
        'has_approval': bool,
        'approval_flow': {status, stages, instance_id, started_at, can_approve, ...},
        'control_info': {can_approve, can_recall, can_resubmit, ...},   # 字段位置对齐 PO
      }
    """
    try:
        # 检查项目访问权限 - 优先检查是否为项目审批人
        from app.helpers.approval_helpers import is_current_approver
        is_approver = is_current_approver(object_type, project_id, current_user.id)
        
        if is_approver:
            # 如果是当前审批人，直接获取项目（绕过常规权限检查）
            project_obj = Project.query.filter_by(id=project_id).first()
        else:
            # 否则使用常规权限检查
            viewable_projects = get_viewable_data(Project, current_user)
            project_obj = viewable_projects.filter_by(id=project_id).first()
            
        if not project_obj:
            return ({'success': False, 'message': '项目不存在或无权限访问'}, 404)

        # 获取审批实例
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance(object_type, project_id)

        if not approval_instance:
            return {'success': True, 'has_approval': False, 'message': '项目暂无审批流程'}

        # 获取审批流程数据 - 使用与报销相同的格式
        from app.helpers.approval_helpers import can_recall_approval, can_resubmit_approval
        from app.models.approval import ApprovalRecord, ApprovalStep

        # 获取审批步骤（从模板获取）
        steps = approval_instance.get_steps()
        if not steps:
            return {'success': False, 'message': '审批流程配置错误'}
        
        # 获取已有的审批记录
        records = ApprovalRecord.query.filter_by(
            instance_id=approval_instance.id
        ).order_by(ApprovalRecord.timestamp.asc()).all()
        
        # 构建审批阶段数据
        stages_data = []
        current_step_value = approval_instance.current_step
        matched_step_order = None

        # 先尝试用 step_order 匹配
        for step in steps:
            if step.get('step_order') == current_step_value:
                matched_step_order = current_step_value
                break

        # 如果 step_order 匹配不到，尝试用 step_id 匹配
        if matched_step_order is None:
            for step in steps:
                if step.get('step_id') == current_step_value:
                    matched_step_order = step.get('step_order')
                    break

        current_step_order = matched_step_order

        # 预评估执行条件：对尚未到达的步骤检查条件，不满足条件的不显示
        from app.helpers.approval_helpers import get_step_actual_approver, _check_step_execution_condition
        target_object_for_condition = project_obj

        for i, step in enumerate(steps):
            # 确定审批人
            actual_approver = get_step_actual_approver(step, approval_instance)

            # 获取这个步骤的审批记录
            step_records = []
            if step.get('step_id'):
                step_records = [r for r in records if r.step_id == step['step_id']]

            # 兜底：模板快照模式（动态生成的step_id写入记录时为NULL）
            if not step_records and records:
                approve_records = [r for r in records if r.action in ('approve', 'reject')]
                if approve_records and all(r.step_id is None for r in approve_records):
                    step_order = step.get('step_order', i + 1)
                    if step_order <= len(approve_records):
                        step_records = [approve_records[step_order - 1]]

            # 对尚未到达的步骤，评估执行条件，不满足条件的不显示
            if not step_records and step['step_order'] != current_step_order:
                exec_condition = step.get('execution_condition')
                if exec_condition and isinstance(exec_condition, dict):
                    should_execute = _check_step_execution_condition(step, target_object_for_condition)
                    if should_execute is False:
                        continue

            stage_data = {
                'id': step['step_id'],
                'stage_name': step['step_name'],
                'stage_order': step['step_order'],
                'approver_name': actual_approver.real_name if actual_approver else '待确定',
                'approver_id': actual_approver.id if actual_approver else None,
                'status': 'pending',
                'completed_time': None,
                'comment': None,
                'action': None,
                'arrived_at': None,
                'can_approve': False
            }

            # 处理审批记录
            if step_records:
                latest_record = step_records[-1]
                if latest_record.action == 'skipped':
                    # 已跳过的步骤也不显示
                    continue
                else:
                    stage_data.update({
                        'status': 'approved' if latest_record.action == 'approve' else 'rejected',
                        'completed_time': latest_record.timestamp.isoformat(),
                        'comment': latest_record.comment,
                        'action': latest_record.action,
                        'arrived_at': latest_record.timestamp.isoformat()
                    })
            elif step['step_order'] == current_step_order:
                stage_data['status'] = 'current'
                stage_data['can_approve'] = (actual_approver and actual_approver.id == current_user.id)
            elif current_step_order and step['step_order'] < current_step_order:
                stage_data['status'] = 'approved'

            stages_data.append(stage_data)
        
        # 获取实际状态
        from app.models.approval import ApprovalStatus
        actual_status = approval_instance.status.value if hasattr(approval_instance.status, 'value') else str(approval_instance.status).lower()
        
        # 检查是否被召回
        last_record = records[-1] if records else None
        if last_record and last_record.action == 'recall':
            actual_status = 'recalled'
        
        _can_approve = any(stage.get('can_approve', False) for stage in stages_data)
        _can_recall = can_recall_approval(object_type, project_id, current_user.id)
        _can_resubmit = can_resubmit_approval(object_type, project_id, current_user.id)
        return {
            'success': True,
            'has_approval': True,
            'approval_flow': {
                'instance_id': approval_instance.id,
                'stages': stages_data,
                'current_stage': current_step_order,
                'can_approve': _can_approve,    # 保留旧位置(向后兼容老前端)
                'status': actual_status,
                'can_recall': _can_recall,
                'can_resubmit': _can_resubmit,
                'is_creator': approval_instance.created_by == current_user.id,
                'creator_id': approval_instance.created_by,
                'started_at': approval_instance.started_at.strftime('%Y-%m-%d %H:%M') if approval_instance.started_at else None
            },
            # 对齐 PO 范式:control_info 顶层独立字段(at_approval_helpers.build_approval_data 期望位置)
            'control_info': {
                'can_approve':  _can_approve,
                'can_recall':   _can_recall,
                'can_resubmit': _can_resubmit,
            },
        }
    except Exception as e:
        logging.error(f"获取项目审批流程失败：{str(e)}")
        return ({'success': False, 'message': f'获取失败：{str(e)}'}, 500)


@project.route('/api/approval/<int:project_id>/flow')
@login_required
@permission_required('project', 'view')
def get_project_approval_flow(project_id):
    """获取项目审批流程数据 — thin jsonify wrapper(对齐 PO 范式)"""
    result = _get_project_approval_flow_impl(project_id)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@project.route('/api/approval/<int:project_id>/recall', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;真授权由函数内 created_by/admin 判断
def recall_project_approval(project_id):
    """召回项目审批"""
    try:
        logging.info(f"项目召回请求: project_id={project_id}, user_id={current_user.id}")
        
        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project_obj = viewable_projects.filter_by(id=project_id).first()
        if not project_obj:
            logging.warning(f"项目不存在或无权限访问: project_id={project_id}")
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404
        
        # 获取审批实例
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance('project', project_id)
        
        if not approval_instance:
            logging.warning(f"项目没有审批流程: project_id={project_id}")
            return jsonify({
                'success': False,
                'message': '项目没有审批流程'
            }), 400
        
        logging.info(f"审批实例状态: instance_id={approval_instance.id}, status={approval_instance.status}, created_by={approval_instance.created_by}")
        
        # 检查召回权限：发起人或管理员可以召回
        if approval_instance.created_by != current_user.id and current_user.role != 'admin':
            logging.warning(f"召回权限检查失败: created_by={approval_instance.created_by}, current_user={current_user.id}, role={current_user.role}")
            return jsonify({
                'success': False,
                'message': '只有审批发起人或管理员可以召回'
            }), 403
        
        if approval_instance.status != ApprovalStatus.PENDING:
            logging.warning(f"审批状态不正确: status={approval_instance.status}, 期望状态=ApprovalStatus.PENDING")
            return jsonify({
                'success': False,
                'message': '只有进行中的审批可以召回'
            }), 400
        
        # 执行召回
        from app.helpers.approval_helpers import recall_approval_process
        success, message = recall_approval_process('project', project_id, current_user.id)

        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
    except Exception as e:
        db.session.rollback()
        logging.error(f"召回项目审批失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'召回失败：{str(e)}'
        }), 500


@project.route('/api/approval/<int:project_id>/resubmit', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;真授权由函数内 _can_win_lock(认归属)
def resubmit_project_approval(project_id):
    """重新提交项目审批"""
    try:
        # 重新提交实际上就是提交审批，所以直接调用提交接口
        return submit_project_approval_standard(project_id)
    except Exception as e:
        logging.error(f"重新提交项目审批失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'重新提交失败：{str(e)}'
        }), 500


# ─────────────────────────────────────────────────────────────────────────────
# 项目失败/搁置审核 (object_type='project_hold') —— gated 审批,部门经理→总经理
# ─────────────────────────────────────────────────────────────────────────────

@project.route('/api/hold/<int:project_id>/request', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;真授权由函数内 _can_win_lock(认归属,支持负责人/dealer 发起)
def request_project_hold(project_id):
    """发起项目失败/搁置审核(申请)。body: {target: 'lost'|'paused', reason: str}"""
    try:
        viewable = get_viewable_data(Project, current_user)
        project_obj = viewable.filter_by(id=project_id).first()
        if not project_obj:
            return jsonify({'success': False, 'message': '项目不存在或无权限访问'}), 404

        # 发起权限与「成功锁定」对齐(单一口径):项目负责人 / 厂商销售负责人 / 项目负责人的部门经理 / admin
        if not _can_win_lock(project_obj, current_user):
            return jsonify({'success': False, 'message': '只有项目负责人/厂商销售负责人/部门经理/管理员可发起失败/搁置审核'}), 403

        data = request.get_json(silent=True) or {}
        target = data.get('target')
        reason = data.get('reason', '')

        from app.helpers.project_hold_helpers import submit_project_hold, HOLD_TARGETS
        instance, err = submit_project_hold(project_obj, target, reason, current_user.id)
        if err:
            return jsonify({'success': False, 'message': err}), 400
        return jsonify({'success': True,
                        'message': f'已提交{HOLD_TARGETS.get(target, "")}审核，等待部门经理 / 总经理审批',
                        'instance_id': instance.id})
    except Exception as e:
        db.session.rollback()
        logging.error(f"发起项目失败/搁置审核失败：{str(e)}")
        return jsonify({'success': False, 'message': f'发起失败：{str(e)}'}), 500


@project.route('/api/hold/<int:project_id>/flow')
@login_required
@permission_required('project', 'view')
def get_project_hold_flow(project_id):
    """获取项目失败/搁置审核流程 — 复用通用构建 + 前置「发起申请」节点(含发起人理由)。"""
    result = _get_project_approval_flow_impl(project_id, object_type='project_hold')
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]

    # 前置「发起申请」节点:展示发起人 + 强制理由
    if result.get('success') and result.get('has_approval') and result.get('approval_flow'):
        try:
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.user import User as _U
            inst = get_object_approval_instance('project_hold', project_id, include_rejected=True)
            snap = (inst.template_snapshot or {}) if inst else {}
            initiator = _U.query.get(snap.get('hold_initiator_id')) if snap.get('hold_initiator_id') else None
            started = inst.started_at.isoformat() if inst and inst.started_at else None
            origin_node = {
                'id': 'initiator', 'stage_name': '发起申请', 'stage_order': 0,
                'approver_name': (initiator.real_name or initiator.username) if initiator else '发起人',
                'approver_id': initiator.id if initiator else None,
                'status': 'approved', 'completed_time': started,
                'comment': snap.get('hold_reason') or '', 'action': 'submit',
                'arrived_at': started, 'can_approve': False,
            }
            result['approval_flow'].setdefault('stages', [])
            result['approval_flow']['stages'].insert(0, origin_node)
        except Exception as _e:
            logging.warning(f"前置发起节点失败: {_e}")
    return jsonify(result)


@project.route('/api/hold/<int:project_id>/editable-fields')
@login_required
@permission_required('project', 'view')
def get_project_hold_editable_fields(project_id):
    """失败/搁置审核无「审核修改」场景,返回空字段(供下拉组件并发拉取)。"""
    return jsonify({'success': True, 'fields': [], 'editable_fields': []})


@project.route('/api/hold/<int:project_id>/recall', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;真授权由函数内 created_by/admin 判断
def recall_project_hold(project_id):
    """撤回进行中的失败/搁置审核(仅发起人或管理员)。"""
    try:
        from app.helpers.approval_helpers import get_object_approval_instance, recall_approval_process
        inst = get_object_approval_instance('project_hold', project_id)
        if not inst:
            return jsonify({'success': False, 'message': '没有进行中的失败/搁置审核'}), 400
        if inst.created_by != current_user.id and current_user.role != 'admin':
            return jsonify({'success': False, 'message': '只有发起人或管理员可撤回'}), 403
        if inst.status != ApprovalStatus.PENDING:
            return jsonify({'success': False, 'message': '只有进行中的审核可撤回'}), 400
        success, message = recall_approval_process('project_hold', project_id, current_user.id)
        return jsonify({'success': success, 'message': message}), (200 if success else 500)
    except Exception as e:
        db.session.rollback()
        logging.error(f"撤回失败/搁置审核失败：{str(e)}")
        return jsonify({'success': False, 'message': f'撤回失败：{str(e)}'}), 500


@project.route('/api/win-lock/<int:project_id>/flow')
@login_required
@permission_required('project', 'view')
def get_project_win_lock_flow(project_id):
    """获取项目成功锁定审核流程 — 复用通用构建 + 前置「发起申请」节点(含发起人理由)。"""
    result = _get_project_approval_flow_impl(project_id, object_type='project_win_lock')
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]

    # 前置「发起申请」节点:展示发起人 + 锁定理由
    if result.get('success') and result.get('has_approval') and result.get('approval_flow'):
        try:
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.user import User as _U
            inst = get_object_approval_instance('project_win_lock', project_id, include_rejected=True)
            snap = (inst.template_snapshot or {}) if inst else {}
            initiator = _U.query.get(snap.get('wl_initiator_id')) if snap.get('wl_initiator_id') else None
            started = inst.started_at.isoformat() if inst and inst.started_at else None
            origin_node = {
                'id': 'initiator', 'stage_name': '发起申请', 'stage_order': 0,
                'approver_name': (initiator.real_name or initiator.username) if initiator else '发起人',
                'approver_id': initiator.id if initiator else None,
                'status': 'approved', 'completed_time': started,
                'comment': snap.get('wl_reason') or '', 'action': 'submit',
                'arrived_at': started, 'can_approve': False,
            }
            result['approval_flow'].setdefault('stages', [])
            result['approval_flow']['stages'].insert(0, origin_node)
        except Exception as _e:
            logging.warning(f"前置发起节点失败(win-lock): {_e}")
    return jsonify(result)


@project.route('/api/win-lock/<int:project_id>/editable-fields')
@login_required
@permission_required('project', 'view')
def get_project_win_lock_editable_fields(project_id):
    """成功锁定审核无「审核修改」场景,返回空字段(供下拉组件并发拉取)。"""
    return jsonify({'success': True, 'fields': [], 'editable_fields': []})


@project.route('/api/win-lock/<int:project_id>/recall', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;真授权由函数内 created_by/admin 判断
def recall_project_win_lock(project_id):
    """撤回进行中的成功锁定审核(仅发起人或管理员)。"""
    try:
        from app.helpers.approval_helpers import get_object_approval_instance, recall_approval_process
        inst = get_object_approval_instance('project_win_lock', project_id)
        if not inst:
            return jsonify({'success': False, 'message': '没有进行中的成功锁定审核'}), 400
        if inst.created_by != current_user.id and current_user.role != 'admin':
            return jsonify({'success': False, 'message': '只有发起人或管理员可撤回'}), 403
        if inst.status != ApprovalStatus.PENDING:
            return jsonify({'success': False, 'message': '只有进行中的审核可撤回'}), 400
        success, message = recall_approval_process('project_win_lock', project_id, current_user.id)
        return jsonify({'success': success, 'message': message}), (200 if success else 500)
    except Exception as e:
        db.session.rollback()
        logging.error(f"撤回成功锁定审核失败：{str(e)}")
        return jsonify({'success': False, 'message': f'撤回失败：{str(e)}'}), 500


@project.route('/<int:project_id>/generate_authorization', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器 - 创建者可以为自己的项目生成授权编号
def generate_authorization_code(project_id):
    """审批通过后生成项目授权编号"""
    try:
        # 获取项目
        viewable_projects = get_viewable_data(Project, current_user)
        project = viewable_projects.filter_by(id=project_id).first()
        if not project:
            return jsonify({
                'success': False,
                'message': '项目不存在或无权限访问'
            }), 404

        # 使用统一的数据权限检查（包含数据归属逻辑）
        if not can_edit_data(project, current_user):
            return jsonify({
                'success': False,
                'message': '只有项目创建人可以生成授权编号'
            }), 403
        
        # 检查是否已有授权编号
        if project.authorization_code and project.authorization_code.strip():
            return jsonify({
                'success': False,
                'message': '项目已有授权编号，无需重复生成'
            }), 400
        
        # 检查审批状态
        from app.helpers.approval_helpers import get_object_approval_instance
        approval_instance = get_object_approval_instance('project', project_id)
        
        if not approval_instance or approval_instance.status != 'approved':
            return jsonify({
                'success': False,
                'message': '只有审批通过的项目才能生成授权编号'
            }), 400
        
        # 生成授权编号
        from app.helpers.authorization_helpers import generate_project_authorization_code
        authorization_code = generate_project_authorization_code(project)
        
        if authorization_code:
            project.authorization_code = authorization_code
            project.authorization_status = 'approved'
            project.authorization_date = datetime.now()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '授权编号生成成功',
                'authorization_code': authorization_code
            })
        else:
            return jsonify({
                'success': False,
                'message': '授权编号生成失败'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"生成授权编号失败：{str(e)}")
        return jsonify({
            'success': False,
            'message': f'生成失败：{str(e)}'
        }), 500


# ============================================================
# 项目表单API端点 - 用于创建和编辑项目
# ============================================================

@project.route('/api/options', methods=['GET'])
@login_required
@permission_required('project', 'view')
def api_get_project_options():
    """API端点 - 获取项目表单选项"""
    try:
        # 获取项目类型选项
        project_types = [
            {'value': k, 'label': v}
            for k, v in get_project_type_options()
        ]
        
        # 获取行业选项
        industries = [
            {'value': k, 'label': v}
            for k, v in get_industry_options()
        ]
        
        # 获取报备源选项
        report_sources = [
            {'value': k, 'label': v}
            for k, v in get_report_source_options()
        ]
        
        # 获取产品情况选项
        product_situations = [
            {'value': k, 'label': v}
            for k, v in get_product_situation_options()
        ]
        
        # 获取用户列表（用于项目负责人和厂商销售负责人）
        users = User.query.filter_by(is_active=True).order_by(User.real_name).all()
        user_options = [
            {'value': str(user.id), 'label': user.real_name or user.username}
            for user in users
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'project_types': project_types,
                'industries': industries,
                'report_sources': report_sources,
                'product_situations': product_situations,
                'users': user_options
            }
        })
    except Exception as e:
        logger.error(f"获取项目表单选项失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@project.route('/api/create', methods=['POST'])
@login_required
@permission_required('project', 'create')
def api_create_project():
    """API端点 - 创建新项目"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': _('无效的请求数据')}), 400
        
        # 验证必填字段
        required_fields = ['project_name', 'project_type', 'report_time', 'report_source']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': _('请填写所有必填字段')}), 400
        
        # 检查项目名称是否已存在
        existing = Project.query.filter_by(project_name=data.get('project_name')).first()
        if existing:
            return jsonify({'success': False, 'message': _('项目名称已存在')}), 400
        
        # 转换日期字段
        report_time = None
        if data.get('report_time'):
            try:
                report_time = datetime.strptime(data.get('report_time'), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': _('报备时间格式不正确')}), 400
        
        delivery_forecast = None
        if data.get('delivery_forecast'):
            try:
                delivery_forecast = datetime.strptime(data.get('delivery_forecast'), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': _('出货时间格式不正确')}), 400
        
        # 创建新项目
        new_project = Project(
            project_name=data.get('project_name'),
            project_type=data.get('project_type'),
            industry=data.get('industry', ''),
            report_time=report_time,
            delivery_forecast=delivery_forecast,
            report_source=data.get('report_source'),
            product_situation=data.get('product_situation', ''),
            # 地址相关字段
            address=data.get('address', ''),
            country=data.get('country', ''),
            region=data.get('region', ''),
            city=data.get('city', ''),
            owner_id=current_user.id,
            vendor_sales_manager_id=current_user.id if current_user.is_vendor_user() else None,
            authorization_code=data.get('authorization_code', ''),
            stage_description=data.get('stage_description', ''),
            created_by=current_user.id,
            status='draft',
            current_stage='discover'  # 默认阶段为"发现"
        )
        
        db.session.add(new_project)

        # 发放积分：新建项目（flush 确保 new_project.id 已生成）
        try:
            from app.services.points_service import award_points
            db.session.flush()
            award_points(
                user_id=current_user.id,
                behavior_code='project_create',
                source_type='project',
                source_id=new_project.id,
                context=new_project.project_name
            )
        except Exception as pts_err:
            logger.warning(f"发放项目创建积分失败: {pts_err}")

        db.session.commit()

        # 记录创建历史
        try:
            ChangeTracker.log_create(new_project)
        except Exception as track_err:
            logger.warning(f"记录项目创建历史失败: {str(track_err)}")

        # 记录工作项
        data = request.get_json() or {}
        record_activity('create', 'project', new_project.project_name, current_user,
            project_id=new_project.id,
            start_time_str=data.get('page_open_time'),
            description=f'创建项目 {new_project.project_name}')

        return jsonify({
            'success': True,
            'message': _('项目创建成功'),
            'data': {
                'id': new_project.id,
                'project_name': new_project.project_name
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建项目失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@project.route('/api/<int:project_id>/update', methods=['POST'])
@login_required
@permission_required('project', 'view')  # 粗闸=模块访问;真授权由函数内 can_edit_data(认归属,支持负责人编辑自己项目)
def api_update_project(project_id):
    """API端点 - 更新项目数据"""
    try:
        proj = Project.query.filter_by(id=project_id).first()
        if not proj:
            return jsonify({'success': False, 'message': _('项目不存在')}), 404
        
        # 检查编辑权限
        if not can_edit_data(proj, current_user):
            return jsonify({'success': False, 'message': _('您没有权限编辑此项目')}), 403
        
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': _('无效的请求数据')}), 400
        
        # 捕获修改前的值
        old_values = ChangeTracker.capture_old_values(proj)
        
        # 允许更新的字段
        allowed_fields = ['project_name', 'project_type', 'industry', 'report_source',
                         'product_situation', 'authorization_code', 'stage_description',
                         'address', 'country', 'region', 'city']
        
        for field in allowed_fields:
            if field in data:
                if field in ['owner_id', 'vendor_sales_manager_id']:
                    # ID字段需要转换为整数
                    setattr(proj, field, int(data[field]) if data[field] else None)
                else:
                    setattr(proj, field, data[field])
        
        # 处理日期字段
        if 'report_time' in data and data['report_time']:
            try:
                proj.report_time = datetime.strptime(data['report_time'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': _('报备时间格式不正确')}), 400
        
        if 'delivery_forecast' in data and data['delivery_forecast']:
            try:
                proj.delivery_forecast = datetime.strptime(data['delivery_forecast'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'message': _('出货时间格式不正确')}), 400
        
        # 检测项目名称是否变更（用于触发 AI 调研）
        project_name_changed = old_values.get('project_name') and old_values['project_name'] != proj.project_name

        db.session.commit()

        # 记录修改历史
        try:
            ChangeTracker.log_update(proj, old_values)
        except Exception as track_err:
            logger.warning(f"记录项目修改历史失败: {str(track_err)}")

        return jsonify({
            'success': True,
            'message': _('项目更新成功')
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新项目失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@project.route('/api/<int:project_id>', methods=['GET'])
@login_required
@permission_required('project', 'view')
def api_get_project_data(project_id):
    """API端点 - 获取项目数据（用于编辑表单）"""
    try:
        proj = Project.query.filter_by(id=project_id).first()
        if not proj:
            return jsonify({'success': False, 'message': _('项目不存在')}), 404
        
        # 检查查看权限
        if not can_view_project(current_user, proj):
            return jsonify({'success': False, 'message': _('您没有权限查看此项目')}), 403
        
        return jsonify({
            'success': True,
            'data': {
                'id': proj.id,
                'project_name': proj.project_name,
                'project_type': proj.project_type or '',
                'industry': proj.industry or '',
                'report_time': proj.report_time.strftime('%Y-%m-%d') if proj.report_time else '',
                'delivery_forecast': proj.delivery_forecast.strftime('%Y-%m-%d') if proj.delivery_forecast else '',
                'report_source': proj.report_source or '',
                'product_situation': proj.product_situation or '',
                'owner_id': str(proj.owner_id) if proj.owner_id else '',
                'vendor_sales_manager_id': str(proj.vendor_sales_manager_id) if proj.vendor_sales_manager_id else '',
                'authorization_code': proj.authorization_code or '',
                'stage_description': proj.stage_description or '',
                'address': proj.address or '',
                'country': proj.country or '',
                'region': proj.region or '',
                'city': proj.city or ''
            }
        })
    except Exception as e:
        logger.error(f"获取项目数据失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@project.route('/api/search', methods=['GET'])
@login_required
@permission_required('project', 'view')
def api_search_projects():
    """API端点 - 搜索项目（用于名称查重）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        
        if not keyword:
            return jsonify({'results': []})
        
        # 搜索相似项目名称
        projects = Project.query.filter(
            Project.project_name.ilike(f'%{keyword}%')
        ).limit(10).all()
        
        results = [{
            'id': p.id,
            'project_name': p.project_name,
            'authorization_code': p.authorization_code or '',
            'owner_name': p.owner.real_name if p.owner else None
        } for p in projects]
        
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"搜索项目失败: {str(e)}")
        return jsonify({'results': []}), 500


@project.route('/api/<int:project_id>/ai-research', methods=['GET'])
@login_required
@permission_required('project', 'view')
def api_get_project_ai_research(project_id):
    """获取项目 AI 调研状态和数据（权限由装饰器控制）"""
    try:
        proj = Project.query.filter_by(id=project_id).first()
        if not proj:
            return jsonify({'success': False, 'message': _('项目不存在')}), 404

        from app.services.ai_research_service import AIResearchService
        result = AIResearchService.get_project_status(project_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"获取项目AI调研数据失败: {str(e)}")
        return jsonify({'success': False, 'status': 'error', 'error': str(e)}), 500


@project.route('/api/<int:project_id>/ai-research/retry', methods=['POST'])
@login_required
@permission_required('project', 'view')
def api_retry_project_ai_research(project_id):
    """手动重试项目 AI 调研（权限由装饰器控制）"""
    try:
        proj = Project.query.filter_by(id=project_id).first()
        if not proj:
            return jsonify({'success': False, 'message': _('项目不存在')}), 404

        from app.services.ai_research_service import AIResearchService
        AIResearchService.trigger_project_research(project_id)
        return jsonify({'success': True, 'message': _('已触发 AI 调研')})

    except Exception as e:
        logger.error(f"重试项目AI调研失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@project.route('/api/<int:project_id>/ai-research/confirm', methods=['POST'])
@login_required
@permission_required('project', 'view')
def api_confirm_project_ai_research(project_id):
    """用户确认候选项目名后继续调研"""
    proj = Project.query.filter_by(id=project_id).first_or_404()
    data = request.get_json() or {}
    confirmed_name = data.get('confirmed_name') or proj.project_name

    from app.services.ai_research_service import AIResearchService
    AIResearchService.continue_project_with_candidate(project_id, confirmed_name)
    return jsonify({'success': True, 'message': _('已启动调研')})


@project.route('/api/similar-projects')
@login_required
@permission_required('project', 'view')
def similar_projects_api():
    """实时相似项目查询，全库查重，按权限区分显示"""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []})

    try:
        projects = (Project.query
                    .filter(Project.is_deleted == False)
                    .options(joinedload(Project.owner))
                    .all())

        results = []
        for p in projects:
            is_sim, score = is_similar_project_name(q, p.project_name)
            if not is_sim:
                continue
            viewable = can_view_project(current_user, p)
            owner_name = ''
            if not viewable and p.owner:
                owner_name = p.owner.real_name or p.owner.username
            results.append({
                'id': p.id,
                'name': p.project_name,
                'score': round(score / 100, 2),
                'viewable': viewable,
                'url': url_for('project.view_project', project_id=p.id) if viewable else '',
                'owner_name': owner_name,
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        return jsonify({'results': results[:6]})
    except Exception as e:
        current_app.logger.error(f'[similar_projects_api] 查询失败: {e}', exc_info=True)
        return jsonify({'results': []})


@project.route('/api/ai-enrich', methods=['POST'])
@login_required
@permission_required('project', 'create')
def ai_enrich_project():
    """AI 回填：Tavily 搜索 + Claude Haiku 解析项目信息"""
    data = request.get_json(silent=True) or {}
    project_name = (data.get('project_name') or '').strip()
    if not project_name:
        return jsonify({'success': False, 'message': '请输入项目名称'}), 400
    project_name = project_name[:200].replace('\n', ' ').replace('\r', ' ')

    is_en = current_app.config.get('IS_OVS', False)
    tavily_key = os.environ.get('TAVILY_API_KEY', '').strip()
    if not tavily_key:
        return jsonify({'success': False, 'message': '未配置 TAVILY_API_KEY'}), 500

    search_query = (
        f'{project_name} construction project owner location'
        if is_en else
        f'{project_name} 工程项目 招标 建设 业主 地址'
    )
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_key)
        search_result = client.search(
            query=search_query,
            search_depth='basic',
            max_results=5,
            include_answer=True,
        )
        snippets = '\n'.join(
            f"- {r.get('title', '')}: {(r.get('content', '') or '')[:300]}"
            for r in search_result.get('results', [])
        )
        answer = search_result.get('answer', '') or ''
        search_text = f"Answer: {answer}\n\nSnippets:\n{snippets}"
    except Exception as e:
        current_app.logger.error(f'[ai_enrich_project] Tavily 搜索失败: {e}')
        return jsonify({'success': False, 'message': f'Tavily 搜索失败: {e}'}), 500

    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not anthropic_key:
        return jsonify({'success': False, 'message': '未配置 ANTHROPIC_API_KEY'}), 500

    industry_opts = (
        'manufacturing / datacenter / energy / technology / government / healthcare / '
        'finance / real_estate / education / retail / transportation / hospitality / '
        'shipbuilding / semiconductor / chemical / tunnel_underground / other'
    )
    if is_en:
        json_schema = (
            '{\n'
            '  "official_names": ["official project name 1", "official project name 2"],\n'
            '  "address": "project location address (street level if possible)",\n'
            '  "country": "country name (e.g. China / Singapore)",\n'
            f'  "industry": "pick the best matching key from: {industry_opts}",\n'
            '  "description": "project background in under 100 words (project type, owner, scale)"\n'
            '}\n\n'
            'Return JSON only, no other text.'
        )
        prompt = (
            f'Based on the following search results, extract structured information about the project "{project_name}".\n\n'
            f'Search results:\n{search_text}\n\n'
            f'Return a JSON object with the following fields (use empty string for unknown fields):\n{json_schema}'
        )
    else:
        json_schema = (
            '{\n'
            '  "official_names": ["项目正式名称候选1", "项目正式名称候选2"],\n'
            '  "address": "项目所在地址（尽量精确到街道/路名/门牌号；无具体地址时写到城市/区县）",\n'
            '  "country": "国家（英文，如 China / Singapore）",\n'
            f'  "industry": "从以下选项中选最匹配的 key，只返回 key：{industry_opts}",\n'
            '  "description": "100字以内的项目背景简介（工程类型、业主单位、建设规模等）"\n'
            '}\n\n'
            '只返回 JSON，不要任何其他文字。'
        )
        prompt = (
            f'根据以下搜索结果，提取关于工程项目「{project_name}」的结构化信息。\n\n'
            f'搜索结果：\n{search_text}\n\n'
            f'请以 JSON 格式返回，字段如下（无法确定的字段返回空字符串）：\n{json_schema}'
        )

    try:
        import anthropic as _anthropic
        from app.utils.dictionary_helpers import INDUSTRY_LABELS
        claude = _anthropic.Anthropic(api_key=anthropic_key)
        msg = claude.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=512,
            messages=[{'role': 'user', 'content': prompt}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```\s*$', '', raw)
        parsed = json.loads(raw.strip())
    except Exception as e:
        current_app.logger.error(f'[ai_enrich_project] Claude 解析失败: {e}')
        return jsonify({'success': False, 'message': 'AI 解析失败，请稍后重试'}), 500

    industry_key = parsed.get('industry') or ''
    lang = 'en' if is_en else 'zh'
    return jsonify({
        'success': True,
        'official_names': parsed.get('official_names') or [],
        'address': parsed.get('address') or '',
        'country': parsed.get('country') or '',
        'industry': industry_key,
        'industry_label': INDUSTRY_LABELS.get(industry_key, {}).get(lang, ''),
        'description': parsed.get('description') or '',
    })


