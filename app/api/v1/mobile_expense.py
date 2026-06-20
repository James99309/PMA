# -*- coding: utf-8 -*-
"""移动端报销单接口 — list / detail / CRUD / 明细 / 提交-召回-重提 / 审批流

业务模型: app.models.expense.Expense + ExpenseDetail
权限: 报销单特殊规则(详见 access_control L750-799), 不走数据归属机制
审批: 复用 app.helpers.approval_helpers (start/recall/resubmit)
"""
from datetime import datetime, date
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func as sa_func, and_, or_

from app import db
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.expense import Expense, ExpenseDetail, EXPENSE_CATEGORIES, EXPENSE_STATUS
from app.api.v1.utils import get_request_lang as _lang

# 科目/状态英文 label 统一收口到 app.helpers.expense_labels(唯一来源),此处不再各写一份
def _category_label(key):
    from app.helpers.expense_labels import expense_category_label
    return expense_category_label(key, _lang())

def _status_label_i18n(key):
    from app.helpers.expense_labels import expense_status_label
    return expense_status_label(key, _lang())
from app.utils.access_control import get_viewable_data
import logging

logger = logging.getLogger(__name__)


# ─── 序列化 helpers ─────────────────────────────────────────────────────

_STATUS_META = {
    'draft':              {'zh': '草稿',   'en': 'Draft',            'color': '#7A7570', 'bg': '#EFEAE2'},
    'pending':            {'zh': '审批中', 'en': 'Under approval',   'color': '#C77B22', 'bg': '#F9F1E6'},
    'approved':           {'zh': '已通过', 'en': 'Approved',         'color': '#2F7A4F', 'bg': '#E9F1EB'},
    'rejected':           {'zh': '已驳回', 'en': 'Rejected',         'color': '#B5453A', 'bg': '#F4E4E1'},
    'awaiting_payment':   {'zh': '待支付', 'en': 'Awaiting Payment', 'color': '#C77B22', 'bg': '#F9F1E6'},
    'paid':               {'zh': '已打款', 'en': 'Paid',             'color': '#3A6FB7', 'bg': '#E5EBF4'},
}


def _status_block(status: str) -> dict:
    meta = _STATUS_META.get(status)
    if not meta:
        return {'label': status, 'color': '#7A7570', 'bg': '#EFEAE2'}
    return {'label': meta[_lang()], 'color': meta['color'], 'bg': meta['bg']}


def _expense_summary(e: Expense) -> dict:
    """列表行数据。current_node 让前端在行尾显示 "当前: 票据审核"."""
    current_node = None
    if e.status == 'pending':
        try:
            from app.helpers.approval_helpers import get_object_approval_instance
            inst = get_object_approval_instance('expense', e.id)
            if inst:
                step_info = inst.get_current_step_info()
                if step_info:
                    current_node = step_info.get('step_name') or step_info.get('name')
        except Exception:
            pass

    return {
        'id': e.id,
        'expense_number': e.expense_number,
        'title': e.title,
        'subtitle': (e.description or '')[:40],
        'amount': e.total_amount or 0.0,
        'currency': e.currency or 'CNY',
        'status': e.status,
        'status_meta': _status_block(e.status),
        'apply_at': e.created_at.strftime('%Y-%m-%d') if e.created_at else None,
        'detail_count': e.detail_count,
        'current_node': current_node,
    }


def _normalize_invoice_images(images):
    """老报销单 invoice_images 的 url 是 web 会话路由 /storage/nas/invoice?path=...
    App 无 web session → 命中即 302 跳 web 登录页。 序列化时改写成 JWT 版 mobile
    端点 (不动 DB, 一次修好所有老单)。 新单已是 /api/v1/mobile/chat/file?... ,
    绝对 http(s) 链接(更老 Supabase 时代)保持原样。"""
    if not images:
        return images
    out = []
    for im in images:
        u = (im or {}).get('url') or ''
        if u.startswith('/storage/nas/invoice?path='):
            im = {**im, 'url': '/api/v1/mobile/expense/invoice-file?path='
                  + u.split('?path=', 1)[1]}
        out.append(im)
    return out


def _line_dict(d: ExpenseDetail) -> dict:
    cat_label = _category_label(d.expense_category)
    return {
        'id': d.id,
        'expense_date': d.expense_date.strftime('%Y-%m-%d') if d.expense_date else None,
        'expense_category': d.expense_category,
        'expense_category_label': cat_label,
        'description': d.description or '',
        'document_count': d.document_count or 1,
        'currency': d.currency or 'CNY',
        'invoice_amount': d.invoice_amount or 0.0,
        'current_amount': d.current_amount or 0.0,
        'exchange_rate': d.exchange_rate or 1.0,
        'invoice_images': _normalize_invoice_images(d.invoice_images_list),
    }


def _approval_flow_nodes(expense_id: int, current_user_id=None) -> list:
    """构造 UI 期望的 flow node 数组(变长, 与模板一致)。

    Shape:
        [{ node, user, state, at, remark?, can_recall? }, ...]

    state ∈ {'done', 'current', 'pending'}
    current_user_id: 用于在 current 节点附 can_recall 标志(仅创建人/admin 可召回).
    """
    try:
        from app.helpers.approval_helpers import (
            get_object_approval_instance, get_step_actual_approver, can_recall_approval
        )
        from app.models.approval import ApprovalRecord, ApprovalStatus
    except Exception:
        return []

    inst = get_object_approval_instance('expense', expense_id)
    if not inst:
        return []

    steps = inst.get_steps() or []
    if not steps:
        return []

    can_recall = bool(
        current_user_id
        and can_recall_approval('expense', expense_id, current_user_id)
    )

    records = ApprovalRecord.query.filter_by(instance_id=inst.id) \
        .order_by(ApprovalRecord.timestamp.asc() if hasattr(ApprovalRecord, 'timestamp') else ApprovalRecord.id.asc()) \
        .all()
    # 按 step_id (或 step_order) 索引最新一条记录
    step_record = {}
    for r in records:
        key = getattr(r, 'step_id', None) or getattr(r, 'step_order', None)
        if key is not None:
            step_record[key] = r

    current_step_value = inst.current_step
    is_finished = inst.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)
    nodes = []
    for s in steps:
        step_id = s.get('step_id')
        step_order = s.get('step_order')
        step_name = s.get('step_name') or s.get('name') or f'步骤{step_order}'

        # 判定 state
        record = step_record.get(step_id) or step_record.get(step_order)
        if record:
            action = (getattr(record, 'action', '') or '').lower()
            if action in ('reject', 'rejected'):
                state = 'rejected'
            elif action == 'skipped':
                state = 'skipped'  # 跳过步可见 (审计透明), 移动端与 web 一致
            else:
                state = 'done'
        elif (current_step_value == step_id or current_step_value == step_order) and not is_finished:
            state = 'current'
        else:
            state = 'pending'

        # 处理人姓名
        try:
            approver = get_step_actual_approver(s, inst)
            user_name = (approver.real_name or approver.username) if approver else (s.get('approver_name') or '')
        except Exception:
            user_name = s.get('approver_name') or ''

        node = {
            'node': step_name,
            'user': user_name or '—',
            'state': state,
            'at': record.timestamp.strftime('%Y-%m-%d %H:%M')
                  if record and getattr(record, 'timestamp', None) else None,
        }
        if record and getattr(record, 'comment', None):
            node['remark'] = record.comment
        if state == 'current' and can_recall:
            node['can_recall'] = True
        nodes.append(node)
    return nodes


def _expense_detail_dict(e: Expense, with_flow: bool = True, current_user_id=None) -> dict:
    owner = e.owner
    attributed = e.attributed_to
    customer = e.customer
    project = e.project
    return {
        'id': e.id,
        'expense_number': e.expense_number,
        'title': e.title,
        'description': e.description or '',
        'currency': e.currency or 'CNY',
        'total_amount': e.total_amount or 0.0,
        'status': e.status,
        'status_meta': _status_block(e.status),
        'is_locked': bool(e.is_locked),
        'created_at': e.created_at.strftime('%Y-%m-%d %H:%M') if e.created_at else None,
        'updated_at': e.updated_at.strftime('%Y-%m-%d %H:%M') if e.updated_at else None,
        'owner': {
            'id': owner.id,
            'name': owner.real_name or owner.username,
            'department': getattr(owner, 'department', '') or '',
        } if owner else None,
        'attributed_to': {
            'id': attributed.id,
            'name': attributed.real_name or attributed.username,
        } if attributed else None,
        'customer': {
            'id': customer.id,
            'name': customer.company_name,
            'code': getattr(customer, 'company_code', '') or '',
        } if customer else None,
        'project': {
            'id': project.id,
            'name': project.project_name,
            'code': getattr(project, 'project_code', '') or '',
        } if project else None,
        'approval_notes': e.approval_notes or '',
        'lines': [_line_dict(d) for d in e.details],
        'flow': _approval_flow_nodes(e.id, current_user_id=current_user_id) if with_flow else None,
    }


# ─── 列表 ───────────────────────────────────────────────────────────────

@api_v1_bp.route('/mobile/expense', methods=['GET'])
@jwt_required()
def mobile_expense_list():
    """报销单列表 + hero 汇总(本月已申报/审批中笔数).

    Query params:
        search   — 标题模糊
        status   — 状态过滤(可选)
        page / per_page
        scope    — 'mine' (默认) / 'all' 走 access_control
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    scope = request.args.get('scope', 'mine').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))

    if scope == 'mine':
        # 我自己提交的(申请人视角)
        query = Expense.query.filter(Expense.is_deleted == False, Expense.owner_id == user_id)
    else:
        query = get_viewable_data(Expense, user)

    if search:
        query = query.filter(Expense.title.ilike(f'%{search}%'))
    if status_filter:
        query = query.filter(Expense.status == status_filter)

    # ── hero 汇总:本月已申报金额 + 审批中笔数 ──
    today = date.today()
    month_start = today.replace(day=1)
    base_for_summary = query  # 当前过滤条件下的总集

    month_total = base_for_summary.with_entities(sa_func.sum(Expense.total_amount)).filter(
        Expense.created_at >= month_start
    ).scalar() or 0.0

    pending_count = base_for_summary.filter(Expense.status == 'pending').count()
    total_count = base_for_summary.count()

    pagination = query.order_by(Expense.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return api_response(success=True, data={
        'items': [_expense_summary(e) for e in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'summary': {
            'month_total': float(month_total),
            'pending_count': pending_count,
            'total_count': total_count,
            'currency': user.settlement_currency or 'CNY',  # 汇总按用户结算货币展示
        },
    })


# ─── 详情 ───────────────────────────────────────────────────────────────

def _load_visible_expense(expense_id: int, user) -> Expense:
    # 按报销特殊权限筛选
    return get_viewable_data(Expense, user).filter(Expense.id == expense_id).first()


@api_v1_bp.route('/mobile/expense/<int:expense_id>', methods=['GET'])
@jwt_required()
def mobile_expense_detail(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        # 也许是当前审批人? 走审批人路径
        try:
            from app.helpers.approval_helpers import is_current_approver
            if is_current_approver('expense', expense_id, user_id):
                e = Expense.query.filter(Expense.id == expense_id, Expense.is_deleted == False).first()
        except Exception:
            pass
    if not e:
        return api_response(success=False, code=404, message='报销单不存在或无权限')

    data = _expense_detail_dict(e, with_flow=True, current_user_id=user_id)
    # 控制信息: 提交/召回/重提按钮可见性
    try:
        from app.helpers.approval_helpers import can_recall_approval, can_resubmit_approval
        data['control'] = {
            'can_submit': e.status in ('draft', 'rejected') and e.owner_id == user_id,
            'can_recall': can_recall_approval('expense', expense_id, user_id),
            'can_resubmit': can_resubmit_approval('expense', expense_id, user_id),
            'can_edit': e.status in ('draft', 'rejected') and e.owner_id == user_id,
            'can_delete': e.status == 'draft' and e.owner_id == user_id,
        }
    except Exception:
        data['control'] = {
            'can_submit': e.status == 'draft' and e.owner_id == user_id,
            'can_recall': False, 'can_resubmit': False,
            'can_edit': e.status == 'draft' and e.owner_id == user_id,
            'can_delete': e.status == 'draft' and e.owner_id == user_id,
        }
    return api_response(success=True, data=data)


# ─── 创建草稿 ───────────────────────────────────────────────────────────

@api_v1_bp.route('/mobile/expense', methods=['POST'])
@jwt_required()
def mobile_expense_create():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    # A: 手输描述保存即归一区域语言(SG→en), 草稿立刻英文, 无需提交/等待
    description = _normalize_region_text((data.get('description') or '').strip())
    # 不再同步调 AI 生成 title — 改由前端 fire-and-forget 调 /auto-title 异步生成
    # title 留空也允许; 列表/详情展示时前端用「未命名报销」占位

    # 默认货币: 用户结算货币 → 系统 region 默认 (sp8d=CNY / ovs=USD)
    from config import Config
    default_currency = (user.settlement_currency or Config.DEFAULT_CURRENCY or 'CNY')
    e = Expense(
        title=title,
        description=description,
        currency=data.get('currency') or default_currency,
        customer_id=data.get('customer_id'),
        contact_id=data.get('contact_id'),
        project_id=data.get('project_id'),
        owner_id=user_id,
        status='draft',
    )
    # 归属人默认 = 申请人自己; 跟 web 行为对齐, 关联客户/项目不再自动改归属人。
    # 若 mobile 后续加"归属其他人"UI, 前端传 attributed_to_id 即可。
    e.attributed_to_id = data.get('attributed_to_id') or user_id
    db.session.add(e)
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense create error: {exc}')
        return api_response(success=False, code=500, message='创建失败')

    return api_response(success=True, data=_expense_detail_dict(e, with_flow=False, current_user_id=user_id))


# ─── 更新主表(草稿/驳回态) ──────────────────────────────────────────────

@api_v1_bp.route('/mobile/expense/<int:expense_id>', methods=['PUT'])
@jwt_required()
def mobile_expense_update(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在或无权限')
    if e.owner_id != user_id:
        return api_response(success=False, code=403, message='只有创建人可以修改')
    if e.status not in ('draft', 'rejected'):
        return api_response(success=False, code=400, message='当前状态不可编辑')

    data = request.get_json() or {}
    if 'title' in data:
        e.title = (data['title'] or '').strip()
    if 'description' in data:
        new_desc = (data['description'] or '').strip()
        # A: 仅当描述非空且真改了才归一(避免每次 PUT 重复调 AI)
        if new_desc and new_desc != (e.description or ''):
            new_desc = _normalize_region_text(new_desc)
        e.description = new_desc
    # 不再同步调 AI; 前端会在保存成功后异步调 /auto-title 生成
    # 报销币种创建后锁定(按用户 settlement_currency), 不允许切换 — 静默忽略 currency 字段
    for k in ('customer_id', 'contact_id', 'project_id'):
        if k in data:
            setattr(e, k, data[k] or None)

    # 归属人: 跟 web 对齐, 关联客户/项目不再自动改; 前端显式传才改, 否则保持原值或落回 owner
    if 'attributed_to_id' in data:
        e.attributed_to_id = data.get('attributed_to_id') or e.owner_id
    elif not e.attributed_to_id:
        e.attributed_to_id = e.owner_id
    e.calculate_total_amount()

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense update error: {exc}')
        return api_response(success=False, code=500, message='保存失败')

    return api_response(success=True, data=_expense_detail_dict(e, with_flow=False, current_user_id=user_id))


# ─── 删除(草稿) ─────────────────────────────────────────────────────────

@api_v1_bp.route('/mobile/expense/<int:expense_id>', methods=['DELETE'])
@jwt_required()
def mobile_expense_delete(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在或无权限')
    if e.owner_id != user_id:
        return api_response(success=False, code=403, message='只有创建人可以删除')
    if e.status != 'draft':
        return api_response(success=False, code=400, message='只有草稿可以删除')

    e.is_deleted = True
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense delete error: {exc}')
        return api_response(success=False, code=500, message='删除失败')
    return api_response(success=True, message='已删除')


# ─── 明细 CRUD ──────────────────────────────────────────────────────────

def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        try:
            return datetime.strptime(s, '%Y/%m/%d').date()
        except ValueError:
            return None


@api_v1_bp.route('/mobile/expense/<int:expense_id>/lines', methods=['POST'])
@jwt_required()
def mobile_expense_add_line(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')
    if e.owner_id != user_id:
        return api_response(success=False, code=403, message='只有创建人可以加明细')
    if e.status not in ('draft', 'rejected'):
        return api_response(success=False, code=400, message='当前状态不可加明细')

    data = request.get_json() or {}
    expense_date = _parse_date(data.get('expense_date')) or date.today()
    invoice_amount = float(data.get('invoice_amount') or 0)
    line_currency = data.get('currency') or e.currency
    invoice_images = data.get('invoice_images') or []

    d = ExpenseDetail(
        expense_id=e.id,
        expense_date=expense_date,
        expense_category=data.get('expense_category') or 'other',
        description=_normalize_region_text((data.get('description') or '').strip()),
        document_count=int(data.get('document_count') or 1),
        currency=line_currency,
        invoice_amount=invoice_amount,
        amount=invoice_amount,  # 向后兼容
    )
    if invoice_images:
        import json as _json
        d.invoice_images = _json.dumps(invoice_images)

    db.session.add(d)
    db.session.flush()  # 拿 id; 触发 expense 关系
    d.expense = e  # 让 _recalculate_current_amount 能拿到 expense.currency
    d._recalculate_current_amount()

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense add line error: {exc}')
        return api_response(success=False, code=500, message='加明细失败')

    e.calculate_total_amount()
    db.session.commit()
    return api_response(success=True, data=_line_dict(d))


@api_v1_bp.route('/mobile/expense/<int:expense_id>/lines/<int:line_id>', methods=['PUT'])
@jwt_required()
def mobile_expense_update_line(expense_id, line_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')
    if e.owner_id != user_id:
        return api_response(success=False, code=403, message='只有创建人可以改明细')
    if e.status not in ('draft', 'rejected'):
        return api_response(success=False, code=400, message='当前状态不可改明细')

    d = ExpenseDetail.query.filter_by(id=line_id, expense_id=expense_id).first()
    if not d:
        return api_response(success=False, code=404, message='明细不存在')

    data = request.get_json() or {}
    if 'expense_date' in data:
        parsed = _parse_date(data['expense_date'])
        if parsed:
            d.expense_date = parsed
    if 'expense_category' in data:
        d.expense_category = data['expense_category']
    if 'description' in data:
        s = (data['description'] or '').strip()
        # A: 仅当明细描述非空且真改了才归一
        if s and s != (d.description or ''):
            d.description = _normalize_region_text(s)
        else:
            d.description = s
    if 'document_count' in data:
        d.document_count = int(data['document_count'] or 1)
    if 'invoice_amount' in data:
        d.invoice_amount = float(data['invoice_amount'] or 0)
        d.amount = d.invoice_amount
    if 'currency' in data and data['currency']:
        d.currency = data['currency']
    if 'invoice_images' in data:
        import json as _json
        d.invoice_images = _json.dumps(data['invoice_images']) if data['invoice_images'] else None

    d._recalculate_current_amount()

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense update line error: {exc}')
        return api_response(success=False, code=500, message='保存失败')

    e.calculate_total_amount()
    db.session.commit()
    return api_response(success=True, data=_line_dict(d))


@api_v1_bp.route('/mobile/expense/<int:expense_id>/lines/<int:line_id>', methods=['DELETE'])
@jwt_required()
def mobile_expense_delete_line(expense_id, line_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')
    if e.owner_id != user_id:
        return api_response(success=False, code=403, message='只有创建人可以删明细')
    if e.status not in ('draft', 'rejected'):
        return api_response(success=False, code=400, message='当前状态不可删明细')

    d = ExpenseDetail.query.filter_by(id=line_id, expense_id=expense_id).first()
    if not d:
        return api_response(success=False, code=404, message='明细不存在')

    db.session.delete(d)
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense delete line error: {exc}')
        return api_response(success=False, code=500, message='删除失败')

    e.calculate_total_amount()
    db.session.commit()
    return api_response(success=True, message='已删除')


# ─── 提交 / 召回 / 重提 ─────────────────────────────────────────────────

@api_v1_bp.route('/mobile/expense/<int:expense_id>/submit', methods=['POST'])
@jwt_required()
def mobile_expense_submit(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')
    if e.owner_id != user_id:
        return api_response(success=False, code=403, message='只有创建人可以提交')
    if e.status not in ('draft', 'rejected'):
        return api_response(success=False, code=400, message='当前状态不可提交')
    if not e.details:
        return api_response(success=False, code=400, message='请先添加至少一条明细')

    data = request.get_json() or {}
    template_id = data.get('template_id')
    if not template_id:
        from app.models.approval import ApprovalProcessTemplate
        tpl = ApprovalProcessTemplate.query.filter_by(object_type='expense', is_active=True).first()
        if not tpl:
            return api_response(success=False, code=400, message='未找到可用的报销审批模板')
        template_id = tpl.id

    try:
        from app.helpers.approval_helpers import start_approval_process
        result = start_approval_process(
            object_type='expense',
            object_id=expense_id,
            template_id=template_id,
            user_id=user_id,
            auto_commit=False,
        )
        if not result or (isinstance(result, dict) and not result.get('success')):
            db.session.rollback()
            msg = (result or {}).get('message', '提交失败') if isinstance(result, dict) else '提交失败'
            return api_response(success=False, code=400, message=msg)
        e.status = 'pending'
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense submit error: {exc}')
        return api_response(success=False, code=500, message='提交失败')

    # 提交时同步归一(SG→en/CN→zh): 多数已在保存时(A)归一, 这里 CJK 闸只兜
    # 残留中文, 正常情况近 0 调用、不卡提交; 完成后响应即带最终文案
    _translate_expense_sync(expense_id)
    return api_response(success=True, data=_expense_detail_dict(e, with_flow=True, current_user_id=user_id))


def _normalize_region_text(text):
    """把用户手输自由文本同步归一成区域系统语言(SG→en / CN→zh)。

    保存时(A)调用 → 草稿一保存就是区域语言, detail 立刻显示, 无需提交/等待。
    空/纯空白原样返回; CN 纯中文走 translate_to 内部短路零成本;
    失败返回原文(绝不丢用户输入)。
    """
    if not text or not str(text).strip():
        return text
    try:
        from app.services.translation_service import (
            translate_to, normalize_lang_for_region,
        )
        return translate_to(str(text).strip(), normalize_lang_for_region())
    except Exception as e:
        logger.warning(f'normalize region text 失败: {e}')
        return text


def _translate_expense_sync(expense_id):
    """把 expense 的 title / description / 各明细描述归一成区域系统语言。

    同步执行(供异步 worker 调用, 也便于单测)。已是目标语言由
    translate_to 内部原样返回; 任何异常只 log, 绝不影响调用方。
    """
    try:
        from app.services.translation_service import (
            translate_to, normalize_lang_for_region, has_cjk,
        )
        target = normalize_lang_for_region()

        # CJK 闸: en 目标时保存(A)已归一, 仅对"仍含中文"的字段调 AI →
        # 正常提交近 0 次调用、不卡; zh 目标交给 translate_to 内部短路
        def _need(txt):
            return bool(txt) and (target != 'en' or has_cjk(txt))

        ex = Expense.query.get(expense_id)
        if not ex:
            return
        changed = False
        if _need(ex.title):
            t = translate_to(ex.title, target)
            if t and t != ex.title:
                ex.title = t
                changed = True
        if _need(ex.description):
            d = translate_to(ex.description, target)
            if d and d != ex.description:
                ex.description = d
                changed = True
        for det in (ex.details or []):
            if _need(det.description):
                nd = translate_to(det.description, target)
                if nd and nd != det.description:
                    det.description = nd
                    changed = True
        if changed:
            db.session.commit()
    except Exception as e:
        logger.warning(f'expense translate hook 失败 (id={expense_id}): {e}')
        try:
            db.session.rollback()
        except Exception:
            pass


@api_v1_bp.route('/mobile/expense/<int:expense_id>/recall', methods=['POST'])
@jwt_required()
def mobile_expense_recall(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = Expense.query.filter(Expense.id == expense_id, Expense.is_deleted == False).first()
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')

    try:
        from app.helpers.approval_helpers import recall_approval, can_recall_approval
        if not can_recall_approval('expense', expense_id, user_id):
            return api_response(success=False, code=403, message='当前状态不可召回')
        data = request.get_json() or {}
        result = recall_approval('expense', expense_id, user_id, reason=data.get('reason'))
        if not result or (isinstance(result, dict) and not result.get('success')):
            return api_response(success=False, code=400, message=(result or {}).get('message', '召回失败'))
        # 召回成功 → 状态回到 draft; mobile UI 没归属人选项, 顺手把残留的 attributed_to_id 重置到 owner,
        # 避免之前的 bug 数据(自动归属客户 owner)在重提时再走错流程
        e.status = 'draft'
        if e.attributed_to_id != e.owner_id:
            logger.info(f'recall: 重置 expense {e.id} attributed_to_id {e.attributed_to_id} -> {e.owner_id}')
            e.attributed_to_id = e.owner_id
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense recall error: {exc}')
        return api_response(success=False, code=500, message='召回失败')

    return api_response(success=True, data=_expense_detail_dict(e, with_flow=True, current_user_id=user_id))


@api_v1_bp.route('/mobile/expense/<int:expense_id>/resubmit', methods=['POST'])
@jwt_required()
def mobile_expense_resubmit(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')

    try:
        from app.helpers.approval_helpers import resubmit_approval, can_resubmit_approval
        if not can_resubmit_approval('expense', expense_id, user_id):
            return api_response(success=False, code=403, message='当前状态不可重提')
        result = resubmit_approval('expense', expense_id, user_id)
        if not result or (isinstance(result, dict) and not result.get('success')):
            return api_response(success=False, code=400, message=(result or {}).get('message', '重提失败'))
        e.status = 'pending'
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'mobile expense resubmit error: {exc}')
        return api_response(success=False, code=500, message='重提失败')

    return api_response(success=True, data=_expense_detail_dict(e, with_flow=True, current_user_id=user_id))


# ─── AI 异步生成标题 ─────────────────────────────────────────────────
@api_v1_bp.route('/mobile/expense/<int:expense_id>/auto-title', methods=['POST'])
@jwt_required()
def mobile_expense_auto_title(expense_id):
    """根据 description 用 AI 生成标题. 前端在保存草稿后 fire-and-forget 调用,
    用户不需要等待 — 即使本接口返回慢, 也不会阻塞用户操作.
    仅当 title 为空且 description 非空时才生成。"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')
    if e.owner_id != user_id:
        return api_response(success=False, code=403, message='只有创建人可以生成')
    if e.status not in ('draft', 'rejected'):
        return api_response(success=False, code=400, message='当前状态不可编辑')

    if (e.title or '').strip():
        return api_response(success=True, data={'title': e.title, 'changed': False})
    if not (e.description or '').strip():
        return api_response(success=True, data={'title': '', 'changed': False})

    try:
        from app.services.expense_title_generator import generate_title
        new_title = generate_title(e.description, fallback='', lang=_lang())
    except Exception as exc:
        logger.warning(f'auto-title generate failed: {exc}')
        return api_response(success=False, code=500, message='AI 生成失败')

    if not new_title:
        return api_response(success=True, data={'title': '', 'changed': False})

    e.title = new_title
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'auto-title commit failed: {exc}')
        return api_response(success=False, code=500, message='保存失败')

    return api_response(success=True, data={'title': new_title, 'changed': True})


# ─── 审批流单独取(避免每次详情都拉全量) ────────────────────────────────

@api_v1_bp.route('/mobile/expense/<int:expense_id>/flow', methods=['GET'])
@jwt_required()
def mobile_expense_flow(expense_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    e = _load_visible_expense(expense_id, user)
    if not e:
        # 当前审批人也允许看
        try:
            from app.helpers.approval_helpers import is_current_approver
            if not is_current_approver('expense', expense_id, user_id):
                return api_response(success=False, code=404, message='报销单不存在或无权限')
        except Exception:
            return api_response(success=False, code=404, message='报销单不存在或无权限')

    return api_response(success=True, data={
        'flow': _approval_flow_nodes(expense_id, current_user_id=user_id),
    })


# ─── 参考数据(科目/状态枚举) ────────────────────────────────────────────

@api_v1_bp.route('/mobile/expense/categories', methods=['GET'])
@jwt_required()
def mobile_expense_categories():
    return api_response(success=True, data={
        'categories': [{'key': k, 'label': _category_label(k)} for k, _ in EXPENSE_CATEGORIES],
        'statuses': [{'key': k, 'label': _status_label_i18n(k), **_status_block(k)} for k, _ in EXPENSE_STATUS],
    })


@api_v1_bp.route('/mobile/expense/attributed-to-candidates', methods=['GET'])
@jwt_required()
def mobile_expense_attributed_candidates():
    """归属人候选 = 当前用户同公司所有 active 账户(自己排最前). 与 web 端 /expense/api/users/same-company 同口径."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    try:
        from app.views.expense import _get_same_company_users_data
        return api_response(success=True, data=_get_same_company_users_data(user))
    except Exception as e:
        logger.error(f'mobile attributed-to-candidates error: {e}', exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 货币 + 实时汇率(以 CNY 为基准) ─────────────────────────────────────

# 设计稿 EX_CURRENCIES 完整 9 货币列表(含符号与显示名), foreign→CNY 方向
_EX_CURRENCIES = [
    {'code': 'CNY', 'label': '人民币',          'symbol': '¥',   'fallback_rate': 1.0000},
    {'code': 'USD', 'label': '美元',            'symbol': '$',   'fallback_rate': 7.2400},
    {'code': 'HKD', 'label': '港币',            'symbol': 'HK$', 'fallback_rate': 0.9300},
    {'code': 'TWD', 'label': '台币',            'symbol': 'NT$', 'fallback_rate': 0.2240},
    {'code': 'SGD', 'label': '新加坡元',        'symbol': 'S$',  'fallback_rate': 5.4000},
    {'code': 'MYR', 'label': '马来西亚林吉特', 'symbol': 'RM',  'fallback_rate': 1.6200},
    {'code': 'IDR', 'label': '印尼盾',          'symbol': 'Rp',  'fallback_rate': 0.0005},
    {'code': 'THB', 'label': '泰铢',            'symbol': '฿',   'fallback_rate': 0.2050},
    {'code': 'VND', 'label': '越南盾',          'symbol': '₫',   'fallback_rate': 0.0003},
]

# 英文 label 映射 (SG/en 用) — 同 _category_label / _status_label_i18n 模式
_EXPENSE_CURRENCY_EN = {
    'CNY': 'Chinese Yuan',
    'USD': 'US Dollar',
    'HKD': 'Hong Kong Dollar',
    'TWD': 'Taiwan Dollar',
    'SGD': 'Singapore Dollar',
    'MYR': 'Malaysian Ringgit',
    'IDR': 'Indonesian Rupiah',
    'THB': 'Thai Baht',
    'VND': 'Vietnamese Dong',
}


@api_v1_bp.route('/mobile/expense/currencies', methods=['GET'])
@jwt_required()
def mobile_expense_currencies():
    """返回 9 货币 + 当前 foreign→CNY 汇率(走 ExchangeRateService, 不在覆盖列表的用 fallback)."""
    rates_map = {'CNY': 1.0}
    try:
        from app.services.exchange_rate_service import exchange_rate_service
        # foreign→CNY: 先拿 base=CNY 的 rates(返回 CNY→foreign), 取倒数
        cny_to_foreign = exchange_rate_service.get_exchange_rates('CNY') or {}
        for code, c2f in cny_to_foreign.items():
            if c2f and c2f > 0:
                rates_map[code] = 1.0 / c2f
    except Exception as e:
        logger.warning(f'mobile expense currencies fetch rates fail: {e}')

    en = (_lang() == 'en')
    items = []
    for c in _EX_CURRENCIES:
        rate = rates_map.get(c['code'], c['fallback_rate'])
        items.append({
            'code': c['code'],
            'label': _EXPENSE_CURRENCY_EN.get(c['code'], c['label']) if en else c['label'],
            'symbol': c['symbol'],
            'rate': round(rate, 6),
        })
    return api_response(success=True, data={'currencies': items, 'base': 'CNY'})


@api_v1_bp.route('/mobile/expense/exchange-rate', methods=['GET'])
@jwt_required()
def mobile_expense_exchange_rate():
    """单次查询 from→to 汇率, OCR confirm 页 lock 字段用."""
    from_ccy = (request.args.get('from') or '').strip().upper()
    to_ccy = (request.args.get('to') or '').strip().upper()
    if not from_ccy or not to_ccy:
        return api_response(success=False, code=400, message='from / to 参数必填')

    try:
        from app.services.exchange_rate_service import exchange_rate_service
        rate = exchange_rate_service.get_exchange_rate(from_ccy, to_ccy)
    except Exception as e:
        logger.warning(f'mobile expense exchange-rate fail: {e}')
        rate = 1.0
    return api_response(success=True, data={
        'from': from_ccy, 'to': to_ccy, 'rate': round(rate or 1.0, 6),
    })


# ─── 发票上传 + OCR ─────────────────────────────────────────────────────

@api_v1_bp.route('/mobile/expense/upload-invoice', methods=['POST'])
@jwt_required()
def mobile_expense_upload_invoice():
    """multipart 上传发票图 → 存 NAS + 调 expense_invoice_ocr → 返回 OCR 字段.

    返回 data: {file_url, fields: {seller, invoice_no, date, currency,
                invoice_amount, tax_amount, category, description, confidence},
                ocr_json}
    前端拿到 fields 后填充 ReceiptConfirm 页, 用户确认后 POST 到 /lines.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    from app.services.expense_invoice_ocr import extract_invoice
    from app.api.v1.utils import handle_image_ocr_upload
    _req_lang = _lang()  # SG→en: description 直接出英文(确认页一开始即英文)
    success, payload, code, message = handle_image_ocr_upload(
        request.files.get('file'),
        owner_id=user_id,
        business_type='expense_invoice',
        ocr_fn=lambda blob: extract_invoice(blob, lang=_req_lang),
        default_filename='invoice.jpg',
    )
    return api_response(success=success, code=code, message=message, data=payload)


@api_v1_bp.route('/mobile/expense/invoice-file', methods=['GET'])
def mobile_expense_invoice_file():
    """老报销单发票文件 JWT 代理。

    老 url /storage/nas/invoice?path=... 是 @login_required web 路由, App 无
    session → 302 跳 web 登录页。 _line_dict 已把老 url 改写指向此端点; 鉴权
    同 chat/file (Authorization header 或 ?token=, 供 <img>/Browser 直连),
    取文件复用 storage.py 同款解析, 与 web 路由结果完全一致。
    """
    from flask import Response
    from flask_jwt_extended import decode_token
    from urllib.parse import unquote
    token = request.headers.get('Authorization', '').replace('Bearer ', '') \
        or request.args.get('token', '')
    if not token:
        return api_response(success=False, code=401, message="缺少 token")
    try:
        decode_token(token)
    except Exception:
        return api_response(success=False, code=401, message="token 无效")
    file_path = unquote(request.args.get('path', ''))
    if (not file_path or '/../' in file_path or file_path.startswith('../')
            or file_path.endswith('/..') or file_path.startswith('/')):
        return api_response(success=False, code=400, message="非法路径")
    from app.views.storage import _get_file_with_fallback, _get_content_type
    data, _src = _get_file_with_fallback(file_path, 'invoice')
    if not data:
        return api_response(success=False, code=404, message="文件不存在")
    fname = file_path.split('/')[-1]
    return Response(data, mimetype=_get_content_type(file_path), headers={
        'Cache-Control': 'private, max-age=3600',
        'Content-Disposition': f'inline; filename="{fname}"',
    })
