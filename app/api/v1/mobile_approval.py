from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.approval import ApprovalInstance, ApprovalStatus
from app import db
import logging

logger = logging.getLogger(__name__)

OBJECT_TYPE_LABEL = {
    'project': '项目', 'quotation': '报价单', 'expense': '报销单',
    'pricing_order': '批价单', 'purchase_order': '采购单',
    # 项目子审批(object_id 即项目 id) → 归到「项目」, 具体动作由 current_step_name 体现
    'project_win_lock': '项目', 'project_hold': '项目',
}

# 视作项目处理的 object_type(名称取项目名 / 摘要走项目分支)
_PROJECT_FAMILY = ('project', 'project_win_lock', 'project_hold')


def _get_pending_instances_for_user(user_id):
    """获取当前用户待审批的 ApprovalInstance 列表（复用 helpers 中的逻辑）"""
    from app.helpers.approval_helpers import get_step_actual_approver
    instances = ApprovalInstance.query.filter(
        ApprovalInstance.status == ApprovalStatus.PENDING
    ).all()
    result = []
    for inst in instances:
        try:
            step_info = inst.get_current_step_info()
            if not step_info:
                continue
            approver = get_step_actual_approver(step_info, inst)
            if approver and approver.id == user_id:
                result.append(inst)
        except Exception as e:
            logger.error(f"mobile approval check instance {inst.id}: {e}")
    return result


def _instance_to_dict(inst):
    submitter = User.query.get(inst.created_by) if inst.created_by else None

    # 当前步骤名称(不是数字, 给 UI 显示 chip 用)
    current_step_name = ''
    try:
        step_info = inst.get_current_step_info()
        if step_info:
            current_step_name = step_info.get('step_name') or step_info.get('name') or ''
    except Exception:
        pass

    # 业务对象关联信息(单号/客户/项目/明细数/金额) — 列表行展示用
    biz = _get_object_summary(inst.object_type, inst.object_id)

    return {
        'id': inst.id,
        'object_type': inst.object_type,
        'object_type_label': OBJECT_TYPE_LABEL.get(inst.object_type, inst.object_type),
        'object_id': inst.object_id,
        'object_name': _get_object_name(inst.object_type, inst.object_id),
        'current_step': inst.current_step,
        'current_step_name': current_step_name,
        'submitted_by_name': submitter.real_name or submitter.username if submitter else '',
        'created_at': inst.started_at.isoformat() if inst.started_at else None,
        # 业务字段(可空)
        'expense_number': biz.get('expense_number'),
        'customer_name': biz.get('customer_name'),
        'project_name': biz.get('project_name'),
        'detail_count': biz.get('detail_count'),
        'amount': biz.get('amount'),
        'currency': biz.get('currency'),
    }


def _get_object_summary(object_type, object_id):
    """业务对象汇总 — 列表行展示用(轻量), 不带明细."""
    try:
        if object_type == 'expense':
            from app.models.expense import Expense
            e = Expense.query.get(object_id)
            if not e:
                return {}
            return {
                'expense_number': e.expense_number,
                'customer_name': e.customer.company_name if e.customer else None,
                'project_name': e.project.project_name if e.project else None,
                'detail_count': len(e.details),
                'amount': float(e.total_amount or 0),
                'currency': e.currency or 'CNY',
            }
        if object_type in _PROJECT_FAMILY:
            from app.models.project import Project
            from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS, PROJECT_TYPE_LABELS
            p = Project.query.get(object_id)
            if not p:
                return {}
            owner = getattr(p, 'owner', None)
            stage_zh = PROJECT_STAGE_LABELS.get(p.current_stage, {}).get('zh', p.current_stage)
            type_zh = PROJECT_TYPE_LABELS.get(getattr(p, 'project_type', ''), {}).get('zh', getattr(p, 'project_type', '') or '')
            return {
                'expense_number': None,
                'project_code': getattr(p, 'project_code', '') or '',
                'project_name': p.project_name,
                'customer_name': p.customer.company_name if getattr(p, 'customer', None) else '',
                'owner_name': (owner.real_name or owner.username) if owner else '',
                'current_stage': p.current_stage,
                'stage_label': stage_zh,                       # 中文映射(发现/嵌入/招标中等)
                'project_type': getattr(p, 'project_type', '') or '',
                'project_type_label': type_zh,                 # 中文映射(销售重点/渠道跟进等)
                'authorization_status': getattr(p, 'authorization_status', '') or '',
                'amount': float(p.quotation_customer or 0) / 10000 if getattr(p, 'quotation_customer', None) else None,
                'currency': getattr(p, 'currency', 'CNY') or 'CNY',
                'detail_count': None,
            }
        if object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            po = PricingOrder.query.get(object_id)
            if not po:
                return {}
            return {
                'expense_number': po.order_number,
                'project_name': po.project.project_name if getattr(po, 'project', None) else '',
                'customer_name': po.project.customer.company_name if (getattr(po, 'project', None) and getattr(po.project, 'customer', None)) else '',
                'dealer_name': po.dealer.company_name if getattr(po, 'dealer', None) else '',
                'amount': float(po.pricing_total_amount or 0),
                'currency': getattr(po, 'currency', 'CNY') or 'CNY',
                'detail_count': None,
            }
        if object_type == 'quotation':
            from app.models.quotation import Quotation
            q = Quotation.query.get(object_id)
            if not q:
                return {}
            return {
                'expense_number': q.quotation_number,
                'project_name': q.project.project_name if getattr(q, 'project', None) else '',
                'customer_name': q.customer.company_name if getattr(q, 'customer', None) else '',
                'amount': float(q.amount or 0),
                'currency': getattr(q, 'currency', 'CNY') or 'CNY',
                'detail_count': None,
            }
    except Exception:
        pass
    return {}


def _get_object_name(object_type, object_id):
    try:
        if object_type in _PROJECT_FAMILY:
            from app.models.project import Project
            obj = Project.query.get(object_id)
            return obj.project_name if obj else f'项目#{object_id}'  # 含 win_lock/hold 子审批,object_id 即项目 id
        if object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
            return obj.quotation_number if obj else f'报价#{object_id}'
        if object_type == 'expense':
            from app.models.expense import Expense
            obj = Expense.query.get(object_id)
            return obj.title if obj else f'报销#{object_id}'
        if object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            obj = PricingOrder.query.get(object_id)
            return obj.order_number if obj else f'批价单#{object_id}'
    except Exception:
        pass
    return f'{object_type}#{object_id}'


@api_v1_bp.route('/mobile/approval/pending', methods=['GET'])
@jwt_required()
def mobile_approval_pending():
    """获取当前用户待审批列表"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    instances = _get_pending_instances_for_user(user_id)
    return api_response(success=True, data={
        'items': [_instance_to_dict(i) for i in instances],
        'total': len(instances),
    })


@api_v1_bp.route('/mobile/approval/<int:instance_id>/action', methods=['POST'])
@jwt_required()
def mobile_approval_action(instance_id):
    """执行审批操作：approve / reject"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    data = request.get_json() or {}
    action = data.get('action')
    comment = data.get('comment', '').strip()

    if action not in ('approve', 'reject'):
        return api_response(success=False, code=400, message="action 必须为 approve 或 reject")

    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return api_response(success=False, code=404, message="审批实例不存在或已处理")

    # 确认当前用户是该步骤审批人
    from app.helpers.approval_helpers import get_step_actual_approver
    step_info = instance.get_current_step_info()
    if not step_info:
        return api_response(success=False, code=400, message="审批步骤信息异常")

    actual_approver = get_step_actual_approver(step_info, instance)
    if not actual_approver or actual_approver.id != user_id:
        return api_response(success=False, code=403, message="您不是此步骤的审批人")

    try:
        # 注意: web 端用的是 process_approval (返回 bool, 内部自己 commit)
        # P1 写错成 process_approval_action 导致一直走 except 返回"操作失败"
        from app.helpers.approval_helpers import process_approval

        # 项目审批的分支决策步骤需要 project_type 路由审批人
        kwargs = {'user_id': user_id}
        if instance.object_type == 'project':
            try:
                from app.models.project import Project
                p = Project.query.get(instance.object_id)
                if p and getattr(p, 'project_type', None):
                    kwargs['project_type'] = p.project_type
            except Exception:
                pass

        success = process_approval(
            instance_id,
            action,
            comment or ('同意' if action == 'approve' else '驳回'),
            **kwargs,
        )
        if success:
            return api_response(success=True, message="审批操作成功")
        return api_response(success=False, code=400, message='操作失败')
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile approval action error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=f"操作失败: {str(e)[:80]}")


@api_v1_bp.route('/mobile/approval/<int:instance_id>/edit-line/<int:line_id>', methods=['PATCH'])
@jwt_required()
def mobile_approval_edit_line(instance_id, line_id):
    """审批人编辑报销明细字段(仅当前步骤 editable_fields 白名单内字段).

    用例: 财务审核步骤配 editable_fields=['exchange_rate'], 审批人发现汇率
    识别有误时不需要驳回, 直接在审批界面改完再点同意。

    Body: {field_name: new_value, ...} 仅 editable_fields 内的字段会被处理。
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    inst = ApprovalInstance.query.get(instance_id)
    if not inst or inst.status != ApprovalStatus.PENDING:
        return api_response(success=False, code=404, message='审批实例不存在或已结束')
    if inst.object_type != 'expense':
        return api_response(success=False, code=400, message='仅报销审批支持明细编辑')

    # 必须是当前审批人
    from app.helpers.approval_helpers import get_step_actual_approver
    step_info = inst.get_current_step_info()
    if not step_info:
        return api_response(success=False, code=400, message='审批步骤异常')
    approver = get_step_actual_approver(step_info, inst)
    if not approver or approver.id != user_id:
        return api_response(success=False, code=403, message='您不是当前步骤审批人')

    editable_fields = step_info.get('editable_fields') or []
    if not editable_fields:
        return api_response(success=False, code=400, message='当前步骤未配置可编辑字段')

    from app.models.expense import Expense, ExpenseDetail
    e = Expense.query.get(inst.object_id)
    if not e:
        return api_response(success=False, code=404, message='报销单不存在')
    line = ExpenseDetail.query.filter_by(id=line_id, expense_id=e.id).first()
    if not line:
        return api_response(success=False, code=404, message='明细不存在')

    data = request.get_json() or {}
    # 仅处理 editable_fields 白名单内的字段
    ALLOWED = {'exchange_rate', 'invoice_amount', 'current_amount', 'expense_category',
               'expense_date', 'description', 'document_count', 'currency'}
    changed = []
    for k, v in data.items():
        if k not in editable_fields or k not in ALLOWED:
            continue  # 静默忽略未授权字段
        try:
            if k in ('exchange_rate', 'invoice_amount', 'current_amount'):
                setattr(line, k, round(float(v), 4 if k == 'exchange_rate' else 2))
            elif k == 'expense_date':
                from app.api.v1.mobile_expense import _parse_date
                line.expense_date = _parse_date(v) or line.expense_date
            elif k == 'document_count':
                line.document_count = int(v)
            else:
                setattr(line, k, str(v).strip() if v is not None else None)
            changed.append(k)
        except (ValueError, TypeError) as exc:
            logger.warning(f'edit-line invalid value for {k}: {exc}')

    if not changed:
        return api_response(success=False, code=400, message='没有可保存的修改')

    # 改了汇率/发票金额时, 重算 current_amount(若 current_amount 不在 editable_fields)
    if ('exchange_rate' in changed or 'invoice_amount' in changed) and 'current_amount' not in changed:
        line.current_amount = round((line.invoice_amount or 0) * (line.exchange_rate or 1), 2)
    line.amount = line.current_amount  # 向后兼容字段

    e.calculate_total_amount()
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f'edit-line commit failed: {exc}')
        return api_response(success=False, code=500, message='保存失败')

    return api_response(success=True, data={
        'line_id': line.id,
        'changed_fields': changed,
        'invoice_amount': float(line.invoice_amount or 0),
        'current_amount': float(line.current_amount or 0),
        'exchange_rate': float(line.exchange_rate or 1.0),
        'expense_total': float(e.total_amount or 0),
    })


@api_v1_bp.route('/mobile/approval/history', methods=['GET'])
@jwt_required()
def mobile_approval_history():
    """获取当前用户已处理的审批历史（最近50条）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    from app.models.approval import ApprovalRecord
    records = (
        ApprovalRecord.query
        .filter(ApprovalRecord.approver_id == user_id)
        .order_by(ApprovalRecord.timestamp.desc())
        .limit(50)
        .all()
    )

    items = []
    for r in records:
        instance = ApprovalInstance.query.get(r.instance_id) if hasattr(r, 'instance_id') else None
        items.append({
            'id': r.id,
            'instance_id': r.instance_id,
            'action': r.action,
            'comment': r.comment,
            'object_type': instance.object_type if instance else '',
            'object_type_label': OBJECT_TYPE_LABEL.get(instance.object_type, '') if instance else '',
            'object_id': instance.object_id if instance else None,
            'object_name': _get_object_name(instance.object_type, instance.object_id) if instance else '',
            'created_at': r.timestamp.isoformat() if r.timestamp else None,
        })

    return api_response(success=True, data={'items': items, 'total': len(items)})


@api_v1_bp.route('/mobile/approval/cc', methods=['GET'])
@jwt_required()
def mobile_approval_cc():
    """抄送给我列表 — schema 暂不支持 CC, 返回空让 UI 三段一致."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    return api_response(success=True, data={'items': [], 'total': 0})


# ─── 审批详情(审批人视角): 业务对象 + 申请人画像 + 流程 ──────────────────

def _approval_flow_for_instance(inst, current_user_id=None):
    """同 mobile_expense._approval_flow_nodes 但用 instance 作输入(避免循环 import)。
    current_user_id: 用于在 current 节点附 can_recall 标志(仅创建人/admin 可召回)。
    """
    try:
        from app.helpers.approval_helpers import get_step_actual_approver, can_recall_approval
        from app.models.approval import ApprovalRecord, ApprovalStatus
    except Exception:
        return []
    can_recall = bool(
        current_user_id
        and can_recall_approval(inst.object_type, inst.object_id, current_user_id)
    )

    steps = inst.get_steps() or []
    if not steps:
        return []

    records = ApprovalRecord.query.filter_by(instance_id=inst.id) \
        .order_by(ApprovalRecord.timestamp.asc()).all()
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
        record = step_record.get(step_id) or step_record.get(step_order)
        if record:
            action = (getattr(record, 'action', '') or '').lower()
            state = 'rejected' if action in ('reject', 'rejected') else 'done'
        elif (current_step_value == step_id or current_step_value == step_order) and not is_finished:
            state = 'current'
        else:
            state = 'pending'
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


def _applicant_stats(submitter_id, object_type):
    """申请人画像: 本月业务量统计, 按 object_type 切换数据源.

    返回 {'text': '本月报销 1 笔 · 平均 ¥837.06'} 或 None.
    单位约定: expense 元 / project 万 / pricing_order/quotation 取自记录 currency.
    """
    if not submitter_id or not object_type:
        return None
    try:
        from datetime import date
        from sqlalchemy import func as sa_func
        month_start = date.today().replace(day=1)

        if object_type == 'expense':
            from app.models.expense import Expense
            q = Expense.query.filter(
                Expense.is_deleted == False,
                Expense.owner_id == submitter_id,
                Expense.created_at >= month_start,
            )
            cnt = q.count()
            if cnt == 0:
                return {'text': '本月还未提交报销'}
            avg = q.with_entities(sa_func.coalesce(sa_func.avg(Expense.total_amount), 0.0)).scalar() or 0.0
            return {'text': f'本月报销 {cnt} 笔 · 平均 ¥{float(avg):.2f}'}

        if object_type == 'project':
            from app.models.project import Project
            q = Project.query.filter(
                Project.is_deleted == False,
                Project.owner_id == submitter_id,
                Project.created_at >= month_start,
            )
            cnt = q.count()
            if cnt == 0:
                return {'text': '本月还未新建项目'}
            total = q.with_entities(sa_func.coalesce(sa_func.sum(Project.amount), 0.0)).scalar() or 0.0
            return {'text': f'本月新建 {cnt} 个项目 · 累计预计 ¥{float(total):,.0f} 万'}

        if object_type == 'pricing_order':
            try:
                from app.models.pricing_order import PricingOrder
                q = PricingOrder.query.filter(
                    PricingOrder.is_deleted == False,
                    PricingOrder.owner_id == submitter_id,
                    PricingOrder.created_at >= month_start,
                )
                cnt = q.count()
                if cnt == 0:
                    return {'text': '本月还未提交批价'}
                return {'text': f'本月批价 {cnt} 单'}
            except Exception:
                return None

        if object_type == 'quotation':
            try:
                from app.models.quotation import Quotation
                q = Quotation.query.filter(
                    Quotation.is_deleted == False,
                    Quotation.owner_id == submitter_id,
                    Quotation.created_at >= month_start,
                )
                cnt = q.count()
                if cnt == 0:
                    return {'text': '本月还未提交报价'}
                return {'text': f'本月报价 {cnt} 单'}
            except Exception:
                return None

        return None
    except Exception:
        return None


def _expense_summary_for_approval(expense_id):
    try:
        from app.models.expense import Expense, EXPENSE_CATEGORIES
        category_label_map = dict(EXPENSE_CATEGORIES)  # {'meals': '餐费', ...}
        e = Expense.query.get(expense_id)
        if not e:
            return None
        return {
            'id': e.id,
            'expense_number': e.expense_number,
            'title': e.title,
            'description': (e.description or '')[:200],
            'currency': e.currency,
            'total_amount': float(e.total_amount or 0),
            'detail_count': len(e.details),
            'customer_name': e.customer.company_name if e.customer else '',
            'project_name': e.project.project_name if e.project else '',
            'lines': [
                {
                    'id': d.id,
                    'category': d.expense_category,  # enum key (meals/fuel/...)
                    'category_label': category_label_map.get(d.expense_category, d.expense_category),  # 中文(餐费/油费/...)
                    # 兼容: 跟 mobile_expense._line_dict 字段名对齐, 让 ApprovalDetail 可复用 ExLineDetailSheet
                    'expense_category': d.expense_category,
                    'expense_category_label': category_label_map.get(d.expense_category, d.expense_category),
                    'expense_date': d.expense_date.strftime('%Y-%m-%d') if d.expense_date else None,
                    'description': d.description,
                    'document_count': d.document_count or 1,
                    'currency': d.currency,
                    'invoice_amount': d.invoice_amount,
                    'current_amount': d.current_amount,
                    'exchange_rate': d.exchange_rate,
                    'invoice_images': d.invoice_images_list,
                }
                for d in e.details
            ],
        }
    except Exception:
        return None


def _pricing_order_summary_for_approval(po_id):
    """批价单详情 — 给审批人看. 关键: 项目/客户/经销商/批价金额/折扣率"""
    try:
        from app.models.pricing_order import PricingOrder
        po = PricingOrder.query.get(po_id)
        if not po:
            return None
        creator = getattr(po, 'creator', None)
        return {
            'id': po.id,
            'object_kind': 'pricing_order',
            'order_number': po.order_number,
            'title': po.order_number,
            'project_name': po.project.project_name if getattr(po, 'project', None) else '',
            'project_id': getattr(po, 'project_id', None),
            'customer_name': po.project.customer.company_name if (getattr(po, 'project', None) and getattr(po.project, 'customer', None)) else '',
            'quotation_number': po.quotation.quotation_number if getattr(po, 'quotation', None) else '',
            'dealer_name': po.dealer.company_name if getattr(po, 'dealer', None) else '',
            'distributor_name': po.distributor.company_name if getattr(po, 'distributor', None) else '',
            'is_direct_contract': bool(getattr(po, 'is_direct_contract', False)),
            'is_factory_pickup': bool(getattr(po, 'is_factory_pickup', False)),
            'approval_flow_type': getattr(po, 'approval_flow_type', '') or '',
            'creator_name': (creator.real_name or creator.username) if creator else '',
            'pricing_total_amount': float(po.pricing_total_amount or 0),
            'pricing_total_discount_rate': float(po.pricing_total_discount_rate or 1),
            'settlement_total_amount': float(po.settlement_total_amount or 0),
            'settlement_total_discount_rate': float(po.settlement_total_discount_rate or 1),
            'currency': getattr(po, 'currency', 'CNY') or 'CNY',
            'notes': (getattr(po, 'notes', '') or '')[:300],
            'created_at': po.created_at.strftime('%Y-%m-%d') if getattr(po, 'created_at', None) else None,
            # 给前端用 .lines 守卫的统一字段
            'lines': [],
            'detail_count': len(po.pricing_details) if hasattr(po, 'pricing_details') else 0,
            'total_amount': float(po.pricing_total_amount or 0),
        }
    except Exception as e:
        logger.warning(f'_pricing_order_summary_for_approval error: {e}')
        return None


def _quotation_summary_for_approval(q_id):
    """报价单详情 — 给审批人看. 关键: 项目/客户/金额/阶段/类型"""
    try:
        from app.models.quotation import Quotation
        q = Quotation.query.get(q_id)
        if not q:
            return None
        owner = getattr(q, 'owner', None)
        return {
            'id': q.id,
            'object_kind': 'quotation',
            'quotation_number': q.quotation_number,
            'title': q.quotation_number,
            'project_name': q.project.project_name if getattr(q, 'project', None) else '',
            'customer_name': q.customer.company_name if getattr(q, 'customer', None) else '',
            'contact_name': q.contact.name if getattr(q, 'contact', None) else '',
            'owner_name': (owner.real_name or owner.username) if owner else '',
            'project_stage': getattr(q, 'project_stage', '') or '',
            'project_type': getattr(q, 'project_type', '') or '',
            'amount': float(q.amount or 0),
            'currency': getattr(q, 'currency', 'CNY') or 'CNY',
            'implant_total_amount': float(q.implant_total_amount or 0),
            'notes': (getattr(q, 'notes', '') or '')[:300],
            'created_at': q.created_at.strftime('%Y-%m-%d') if getattr(q, 'created_at', None) else None,
            'lines': [],
            'detail_count': 0,
            'total_amount': float(q.amount or 0),
        }
    except Exception as e:
        logger.warning(f'_quotation_summary_for_approval error: {e}')
        return None


_INDUSTRY_LABELS = {
    'manufacturing': '制造业', 'healthcare': '医疗健康', 'finance': '金融',
    'retail': '零售', 'logistics': '物流', 'energy': '能源',
    'tech': '科技', 'education': '教育', 'government': '政府',
    'real_estate': '房地产', 'tourism': '旅游', 'agriculture': '农业',
    'other': '其他',
}


def _project_summary_for_approval(project_id):
    """项目详情 — 给审批人看. 关键字段: 项目名/客户/阶段/金额/类型/授权码"""
    try:
        from app.models.project import Project
        from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS, PROJECT_TYPE_LABELS, AUTHORIZATION_STATUS_LABELS
        p = Project.query.get(project_id)
        if not p:
            return None
        owner = getattr(p, 'owner', None)
        sales_mgr = getattr(p, 'vendor_sales_manager', None)
        # 中文映射(避免显示 'discover'/'sales_focus' 这种 enum key)
        stage_zh = PROJECT_STAGE_LABELS.get(p.current_stage, {}).get('zh', p.current_stage or '')
        type_zh = PROJECT_TYPE_LABELS.get(getattr(p, 'project_type', ''), {}).get('zh', getattr(p, 'project_type', '') or '')
        auth_zh = AUTHORIZATION_STATUS_LABELS.get(getattr(p, 'authorization_status', '') or '', {}).get('zh', getattr(p, 'authorization_status', '') or '')
        industry_zh = _INDUSTRY_LABELS.get(getattr(p, 'industry', ''), getattr(p, 'industry', '') or '')

        return {
            'id': p.id,
            'object_kind': 'project',
            'project_code': getattr(p, 'project_code', '') or '',
            'project_name': p.project_name,
            'title': p.project_name,
            'description': (getattr(p, 'description', '') or '')[:300],
            'customer_name': p.customer.company_name if getattr(p, 'customer', None) else '',
            'customer_id': getattr(p, 'customer_id', None),
            'owner_name': (owner.real_name or owner.username) if owner else '',
            'sales_manager_name': (sales_mgr.real_name or sales_mgr.username) if sales_mgr else '',
            'industry': getattr(p, 'industry', '') or '',
            'industry_label': industry_zh,
            'city': getattr(p, 'city', '') or '',
            'region': getattr(p, 'region', '') or '',
            'current_stage': p.current_stage,
            'stage_label': stage_zh,                       # 例: 'discover' → '发现'
            'project_type': getattr(p, 'project_type', '') or '',  # 给后端 process_approval 用
            'project_type_label': type_zh,                 # 例: 'sales_focus' → '销售重点'
            'authorization_status': getattr(p, 'authorization_status', '') or '',
            'authorization_status_label': auth_zh,         # 例: 'pending' → '审批中'
            'authorization_code': getattr(p, 'authorization_code', '') or '',
            'amount': float(p.quotation_customer or 0) / 10000 if getattr(p, 'quotation_customer', None) else 0,
            'currency': getattr(p, 'currency', 'CNY') or 'CNY',
            'created_at': p.created_at.strftime('%Y-%m-%d') if getattr(p, 'created_at', None) else None,
            'updated_at': p.updated_at.strftime('%Y-%m-%d %H:%M') if getattr(p, 'updated_at', None) else None,
            'lines': [],
            'detail_count': 0,
            'total_amount': float(p.quotation_customer or 0) / 10000 if getattr(p, 'quotation_customer', None) else 0,
        }
    except Exception as e:
        logger.warning(f'_project_summary_for_approval error: {e}')
        return None


@api_v1_bp.route('/mobile/approval/<int:instance_id>', methods=['GET'])
@jwt_required()
def mobile_approval_detail(instance_id):
    """审批详情(审批人视角) — 业务对象 + 申请人 + 流程节点."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    inst = ApprovalInstance.query.get(instance_id)
    if not inst:
        return api_response(success=False, code=404, message='审批实例不存在')

    submitter = User.query.get(inst.created_by) if inst.created_by else None
    submitter_dict = None
    if submitter:
        submitter_dict = {
            'id': submitter.id,
            'name': submitter.real_name or submitter.username,
            'department': getattr(submitter, 'department', '') or '',
            'avatar_color': '#3A6FB7',
        }

    # 业务对象 summary
    business_obj = None
    if inst.object_type == 'expense':
        business_obj = _expense_summary_for_approval(inst.object_id)
    elif inst.object_type == 'project':
        business_obj = _project_summary_for_approval(inst.object_id)
    elif inst.object_type == 'pricing_order':
        business_obj = _pricing_order_summary_for_approval(inst.object_id)
    elif inst.object_type == 'quotation':
        business_obj = _quotation_summary_for_approval(inst.object_id)

    # 是否当前审批人? + 当前步骤可编辑字段
    is_current = False
    editable_fields = []
    try:
        from app.helpers.approval_helpers import get_step_actual_approver
        step_info = inst.get_current_step_info()
        if step_info:
            approver = get_step_actual_approver(step_info, inst)
            is_current = bool(approver and approver.id == user_id)
            # 当前审批人才返回 editable_fields(避免非审批人意外用到)
            if is_current:
                editable_fields = step_info.get('editable_fields') or []
    except Exception:
        pass

    # 转交信息: 当前步骤被代理时, 显示已转交给谁
    delegated_to_dict = None
    if getattr(inst, 'delegated_to_id', None):
        d = User.query.get(inst.delegated_to_id)
        if d:
            delegated_to_dict = {
                'id': d.id,
                'name': d.real_name or d.username,
            }

    return api_response(success=True, data={
        'id': inst.id,
        'object_type': inst.object_type,
        'object_type_label': OBJECT_TYPE_LABEL.get(inst.object_type, inst.object_type),
        'object_id': inst.object_id,
        'object_name': _get_object_name(inst.object_type, inst.object_id),
        'submitter': submitter_dict,
        'submitter_stats': _applicant_stats(inst.created_by, inst.object_type),
        'created_at': inst.started_at.strftime('%Y-%m-%d %H:%M') if inst.started_at else None,
        'flow': _approval_flow_for_instance(inst, current_user_id=user_id),
        'business_obj': business_obj,
        'is_current_approver': is_current,
        'editable_fields': editable_fields,  # 当前步骤可编辑字段(仅当前审批人有值)
        'delegated_to': delegated_to_dict,
    })


@api_v1_bp.route('/mobile/approval/flow-by-object', methods=['GET'])
@jwt_required()
def mobile_approval_flow_by_object():
    """通过 object_type + object_id 查当前活跃 ApprovalInstance 的流程节点.

    用于业务详情页(项目/批价单/报价单等)顶部状态 chip 点击展开流程,
    无需依赖 instance_id (业务页面不直接持有 instance).
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    object_type = (request.args.get('object_type') or '').strip()
    object_id = request.args.get('object_id', type=int)
    if not object_type or not object_id:
        return api_response(success=False, code=400, message='object_type/object_id 必填')
    try:
        from app.helpers.approval_helpers import get_object_approval_instance
        inst = get_object_approval_instance(object_type, object_id)
        if not inst:
            return api_response(success=True, data={'flow': [], 'instance_id': None})
        return api_response(success=True, data={
            'flow': _approval_flow_for_instance(inst, current_user_id=user_id),
            'instance_id': inst.id,
            'status': inst.status.value if hasattr(inst.status, 'value') else str(inst.status),
        })
    except Exception as e:
        logger.warning(f'flow-by-object error: {e}')
        return api_response(success=False, code=500, message='查询失败')


@api_v1_bp.route('/mobile/approval/forward-targets', methods=['GET'])
@jwt_required()
def mobile_approval_forward_targets():
    """转交目标用户搜索 — 任何登录用户都可调用 (不查 user.view 权限).

    返回轻量字段(id/name/role/department), 限 30 条.
    支持 ?q= 搜索 username/real_name.
    """
    user_id = int(get_jwt_identity())
    me = User.query.get(user_id)
    if not me:
        return api_response(success=False, code=401, message='用户不存在')

    q = (request.args.get('q') or '').strip()
    query = User.query.filter(User.id != user_id)  # 不能转给自己
    # 排除 inactive 用户
    if hasattr(User, '_is_active'):
        query = query.filter(User._is_active == True)
    if q:
        like = f'%{q}%'
        query = query.filter(
            (User.username.like(like)) |
            (User.real_name.like(like))
        )
    users = query.limit(30).all()

    return api_response(success=True, data={
        'items': [
            {
                'id': u.id,
                'name': u.real_name or u.username,
                'username': u.username,
                'department': getattr(u, 'department', '') or '',
                'role': u.role or '',
                'company_name': getattr(u, 'company_name', '') or '',
            }
            for u in users
        ],
    })


@api_v1_bp.route('/mobile/approval/<int:instance_id>/forward', methods=['POST'])
@jwt_required()
def mobile_approval_forward(instance_id):
    """转交给指定用户 — 真转交实现:
    1. 设置 instance.delegated_to_id = target_id (get_step_actual_approver 会优先返回)
    2. 写一条 ApprovalRecord(action='forward') 留审计
    3. target 用户的"待我审批"列表会出现这条; 原审批人列表自动消失
    4. target 处理完(approve/reject) 后 process_approval 会清空 delegated_*  字段
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    data = request.get_json() or {}
    target_id = data.get('target_user_id')
    comment = (data.get('comment') or '').strip()
    if not target_id:
        return api_response(success=False, code=400, message='请指定转交目标用户')
    target_id = int(target_id)
    if target_id == user_id:
        return api_response(success=False, code=400, message='不能转交给自己')

    target = User.query.get(target_id)
    if not target:
        return api_response(success=False, code=404, message='目标用户不存在')

    inst = ApprovalInstance.query.get(instance_id)
    if not inst or inst.status != ApprovalStatus.PENDING:
        return api_response(success=False, code=404, message='审批实例不存在或已处理')

    from app.helpers.approval_helpers import get_step_actual_approver
    step_info = inst.get_current_step_info()
    if not step_info:
        return api_response(success=False, code=400, message='审批步骤异常')
    actual = get_step_actual_approver(step_info, inst)
    # 注意: 这里 get_step_actual_approver 已 honor delegated_to_id,
    # 所以重复转交 (B → C 后 C 再 → D) 时, 当前 actual 是 C, 校验 user_id == C
    if not actual or actual.id != user_id:
        return api_response(success=False, code=403, message='您不是当前审批人')

    try:
        from datetime import datetime
        from app.models.approval import ApprovalRecord
        target_name = target.real_name or target.username
        # 设置代理字段(关键 — 之前只写 record 不改这, 所以是假转交)
        inst.delegated_to_id = target_id
        inst.delegated_at = datetime.now()
        inst.delegated_by_id = user_id
        # 写审计 record
        rec = ApprovalRecord(
            instance_id=instance_id,
            step_id=step_info.get('step_id') if isinstance(step_info, dict) else None,
            approver_id=user_id,
            action='forward',
            comment=f'转交给 {target_name}: {comment}' if comment else f'转交给 {target_name}',
        )
        db.session.add(rec)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f'mobile approval forward error: {e}', exc_info=True)
        return api_response(success=False, code=500, message=f'转交失败: {str(e)[:80]}')

    return api_response(success=True, message=f'已转交给 {target.real_name or target.username}')
