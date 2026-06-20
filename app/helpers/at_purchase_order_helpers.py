# -*- coding: utf-8 -*-
"""
AT 采购订单详情页 · 数据聚合 helpers

把 ORM 对象转换成 at_* 组件期望的 dict shapes:
  - build_approval_data(order)    → {status, nodes, duration} | None
  - build_stages_data(order)      → 7 阶段列表(含 attachments)
  - build_items_data(order)       → 订单明细列表
  - build_shipments_data(order)   → 发货记录列表(含 carriers/waybill/items)
  - build_current_action(order, approval_data) → 当前阶段动作卡 dict | None

附件按方案②取自现有字段(supplier_confirmation_file / factory_test_report_url /
shipment.delivery_proof 等),不新增数据库列。
"""
import json
import logging
from datetime import datetime, date
from flask_babel import lazy_gettext as _l, gettext as _

logger = logging.getLogger(__name__)


# ─── 7 阶段配置 ─────────────────────────────────────────
STAGE_DEFS = [
    {'key': 'submit',  'label': _l('提交审批'), 'icon': 'edit'},
    {'key': 'confirm', 'label': _l('供应商确认'), 'icon': 'check'},
    {'key': 'prep',    'label': _l('备料'),      'icon': 'box'},
    {'key': 'produce', 'label': _l('生产'),      'icon': 'factory'},
    {'key': 'test',    'label': _l('测试'),      'icon': 'flask'},
    {'key': 'ship',    'label': _l('待发货'),    'icon': 'truck'},
    {'key': 'receive', 'label': _l('验收入库'),  'icon': 'archive'},
]

# production_status 对应的阶段索引(0-based,指向 STAGE_DEFS)
# 设计:审批通过=index 1(供应商确认),producing/preparing 等 production_status 对应到 prep/produce/test/ship
PRODUCTION_STAGE_INDEX = {
    'not_started': 1,   # 还未生产 → 当前为供应商确认
    'preparing':   2,
    'producing':   3,
    'testing':     4,
    'packaging':   4,   # packaging 视为 testing 后期
    'ready':       5,   # 待发货
    'completed':   6,   # 验收入库
    'stored':      6,
}


def _fmt_date(dt):
    if not dt:
        return None
    if isinstance(dt, str):
        return dt[:10]
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d')
    return str(dt)


def _safe_json_load(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def _unpack_multi_file_field(raw_value, default_name=_l('附件'), uploaded_at=None):
    """
    把一个数据库列(可能是单 URL 字符串、或 JSON 数组字符串)解包成 attachment 列表。

    单文件场景的旧字段 supplier_confirmation_file / factory_test_report_url 是 URL 字符串,
    多文件场景统一存 JSON 数组 [{name, url}, ...] (后端 endpoint 自动判断)
    """
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        s = raw_value.strip()
        # 尝试解析 JSON 数组
        if s.startswith('['):
            try:
                items = json.loads(s)
                if isinstance(items, list):
                    return [
                        _attachment_record(
                            name=(it.get('name') if isinstance(it, dict) else None) or default_name,
                            url=(it.get('url') if isinstance(it, dict) else it),
                            uploaded_at=uploaded_at,
                        )
                        for it in items if it
                    ]
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        # 单 URL 字符串
        return [_attachment_record(name=default_name, url=s, uploaded_at=uploaded_at)]
    return []


def _attachment_record(name, url, uploaded_at=None, size=None):
    """单个附件 dict — at_file_preview_modal 期望的形态

    自动从 URL 提取真实扩展名塞到 type 字段:前端预览靠这个判断是图片/PDF 还是普通文件。
    (如果 name 本身就是文件名带扩展名也支持;但很多场景 name 是中文标签,所以优先 URL)
    """
    ext = ''
    if url and isinstance(url, str):
        # 去掉 query/fragment,取最后一个 . 后的部分
        clean = url.split('?')[0].split('#')[0]
        if '.' in clean:
            ext = clean.rsplit('.', 1)[-1].lower()
    # 若 URL 没扩展名,退而从 name 中提取
    if not ext and name and '.' in name:
        ext = name.rsplit('.', 1)[-1].lower()
    return {
        'name': name or _('附件'),
        'url': url or '#',
        'uploaded_at': _fmt_date(uploaded_at) if uploaded_at else None,
        'size': size,
        'type': ext,
    }


# ─── 审批数据 ──────────────────────────────────────────
def build_approval_data(order, approval_flow_impl_result=None):
    """
    PO 专用 thin wrapper — 通用逻辑见 app.helpers.at_approval_helpers.build_approval_data
    """
    from app.helpers.at_approval_helpers import build_approval_data as _build
    return _build(
        submitter=order.created_by,
        submitted_at=order.created_at,
        flow_result=approval_flow_impl_result,
    )


def _to_date(s):
    if not s:
        return None
    if isinstance(s, (datetime, date)):
        return s if isinstance(s, date) and not isinstance(s, datetime) else s.date()
    try:
        return datetime.strptime(s[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# ─── 阶段数据(含附件) ──────────────────────────────
def build_stages_data(order, approval_done):
    """
    构造 7 阶段数据,自动标记 done/current/future + 聚合附件。

    Args:
        order: PurchaseOrder ORM
        approval_done: bool, 审批是否已通过(决定是否进入执行阶段)
    """
    # 确定当前阶段索引
    if not approval_done:
        current_idx = 0  # 卡在提交审批
    else:
        prod_status = (order.production_status or 'not_started').lower()
        current_idx = PRODUCTION_STAGE_INDEX.get(prod_status, 1)

        # 待发货(5) 阶段:若所有明细都已发完(dispatched 已开发货单),
        # 阶段推进到 验收入库(6),允许在 6 阶段做签收;所有签收后 PO.status=stored 自动完成
        if current_idx == 5 and order.details:
            all_dispatched = all(
                (d.dispatched_quantity or 0) >= (d.quantity or 0)
                for d in order.details
            )
            if all_dispatched:
                current_idx = 6

    # PO 已入库 / 已完成 → 所有阶段全部标 done(包括最后的验收入库节点)
    is_finished = (order.status in ('stored', 'completed')
                   or getattr(order, 'acceptance_status', None) == 'passed')

    # 阶段历史时间映射 (stage_key → date string)
    history_map = {}
    if hasattr(order, 'stage_history') and order.stage_history:
        for h in order.stage_history:
            if h.from_stage and h.created_at:
                history_map[h.from_stage] = _fmt_date(h.created_at)

    # 提交审批时间 = order.created_at
    submit_date = _fmt_date(order.created_at)
    # 供应商确认时间
    confirm_date = _fmt_date(order.supplier_confirmed_date) if order.supplier_confirmed_date else None
    # ready / packaging 等里程碑日期
    ship_date = _fmt_date(order.milestone_ship_date) if order.milestone_ship_date else None
    receive_date = _fmt_date(order.acceptance_date) if order.acceptance_date else None
    test_date = _fmt_date(order.milestone_test_complete_date) if order.milestone_test_complete_date else None

    stages = []
    for idx, sdef in enumerate(STAGE_DEFS):
        if is_finished:
            status = 'done'
        elif idx < current_idx:
            status = 'done'
        elif idx == current_idx:
            status = 'current'
        else:
            status = 'future'

        # 附件聚合
        attachments = []
        if sdef['key'] == 'submit':
            # 创建即完成,无附件
            pass
        elif sdef['key'] == 'confirm':
            attachments.extend(_unpack_multi_file_field(
                order.supplier_confirmation_file,
                default_name=_('供应商确认单'),
                uploaded_at=order.supplier_confirmed_date,
            ))
        elif sdef['key'] == 'test':
            attachments.extend(_unpack_multi_file_field(
                order.factory_test_report_url,
                default_name=_('出厂测试报告'),
                uploaded_at=order.factory_test_signed_at,
            ))
        elif sdef['key'] == 'ship':
            # 聚合所有发货单的运单/送货单(documents 字段)
            if hasattr(order, 'shipments') and order.shipments:
                for s in order.shipments:
                    docs = _safe_json_load(getattr(s, 'documents', None))
                    for d in docs:
                        attachments.append(_attachment_record(
                            name=f"{s.shipment_number} · {d.get('name', _('发货单据'))}",
                            url=d.get('url'),
                            uploaded_at=s.ship_date,
                        ))
        elif sdef['key'] == 'receive':
            # 聚合所有发货单的签收凭证(delivery_proof)
            if hasattr(order, 'shipments') and order.shipments:
                for s in order.shipments:
                    proofs = _safe_json_load(getattr(s, 'delivery_proof', None))
                    for p in proofs:
                        attachments.append(_attachment_record(
                            name=f"{s.shipment_number} · {p.get('name', _('签收回执'))}",
                            url=p.get('url'),
                            uploaded_at=s.received_date,
                        ))

        # 节点日期
        # 阶段 key(STAGE_DEFS)与 stage_history.from_stage(production_status 命名) 的映射
        # 用户点"备料完成"时,advance_stage 写入 from_stage='preparing',即"备料"阶段的完成时间
        STAGE_KEY_TO_PROD = {
            'prep':    'preparing',
            'produce': 'producing',
            'test':    'testing',
            'ship':    'ready',
        }
        date_str = None
        if sdef['key'] == 'submit' and idx <= current_idx:
            date_str = submit_date
        elif sdef['key'] == 'confirm':
            date_str = confirm_date or history_map.get('not_started')
        elif sdef['key'] == 'test':
            # 测试节点:优先 stage_history,其次里程碑日期/附件
            date_str = (history_map.get('testing') or history_map.get('packaging')
                        or test_date
                        or (attachments[0]['uploaded_at'] if attachments else None))
        elif sdef['key'] == 'ship':
            date_str = ship_date or history_map.get('ready')
        elif sdef['key'] == 'receive':
            date_str = receive_date or history_map.get('completed') or history_map.get('stored')
        else:
            # prep / produce 等 → 用映射后的 production_status 名查 history
            mapped_key = STAGE_KEY_TO_PROD.get(sdef['key'], sdef['key'])
            date_str = history_map.get(mapped_key)

        # 每个阶段的备注(在附件预览模态里展示)
        notes_str = ''
        if sdef['key'] == 'confirm':
            notes_str = order.supplier_confirmation_notes or ''
        elif sdef['key'] == 'ship':
            # 聚合所有发货单的备注
            if hasattr(order, 'shipments') and order.shipments:
                _parts = []
                for s in order.shipments:
                    if getattr(s, 'notes', None):
                        _parts.append(f"{s.shipment_number}:{s.notes}")
                notes_str = '\n'.join(_parts)
        elif sdef['key'] == 'receive':
            if hasattr(order, 'shipments') and order.shipments:
                _parts = []
                for s in order.shipments:
                    if getattr(s, 'received_notes', None):
                        _parts.append(f"{s.shipment_number}:{s.received_notes}")
                notes_str = '\n'.join(_parts)

        stages.append({
            'key': sdef['key'],
            'label': sdef['label'],
            'icon': sdef['icon'],
            'status': status,
            'date': date_str,
            'notes': notes_str,
            'attachments': attachments,
        })

    return stages


# ─── 订单明细(展示) ────────────────────────────────
def build_items_data(order):
    items = []
    for d in order.details:
        items.append({
            'desc':  d.product_name,
            'spec':  d.product_desc or '',
            'model': d.product_model or '',
            'code':  (d.product.product_mn if getattr(d, 'product', None) and getattr(d.product, 'product_mn', None) else ''),
            'qty':   d.quantity or 0,
            'unit':  d.unit or '',
            'price': float(d.unit_price or 0),
        })
    return items


# ─── 订单明细(编辑模态预填 — ATItemTable 期望的字段名) ───
def build_editable_items_data(order):
    """详情页"编辑订单"模态需要预填 ATItemTable,字段名按 JS 控制器约定。"""
    items = []
    for d in order.details:
        items.append({
            'id': d.id,
            'product_id': d.product_id,
            'name':  d.product_name,
            'spec':  d.product_desc or '',
            'model': d.product_model or '',
            'code':  (d.product.product_mn if getattr(d, 'product', None) and getattr(d.product, 'product_mn', None) else ''),
            'qty':   d.quantity or 0,
            'unit':  d.unit or '',
            'price': float(d.unit_price or 0),
            'sales_order_detail_id': getattr(d, 'sales_order_detail_id', None),
        })
    return items


# ─── 发货记录 ────────────────────────────────────────
SHIPMENT_STATUS_TONE = {
    'pending':    'neutral',
    'shipped':    'info',
    'in_transit': 'info',
    'delivered':  'success',
    'received':   'success',
    'exception':  'danger',
}
# 发货单自身状态映射(与 PO 主阶段"待发货"区分,pending = 已开单未发出)
SHIPMENT_STATUS_LABEL = {
    'pending':    _l('已开单'),
    'shipped':    _l('已发出'),
    'in_transit': _l('运输中'),
    'delivered':  _l('已送达'),
    'received':   _l('已签收'),
    'exception':  _l('异常'),
}


def build_shipments_data(order):
    if not getattr(order, 'shipments', None):
        return []
    out = []
    for s in order.shipments:
        items = []
        for d in (s.details or []):
            sns = _safe_json_load(d.serial_numbers)
            items.append({
                'name': d.product_name,
                'model': d.product_model or '',
                'qty': d.quantity or 0,
                'sn_count': len(sns),
                'sn_range': _format_sn_range(sns),
            })
        # 快递单 / 签收单:取各自 JSON 列表第一项即可(若有多个保留第一个为主)
        docs   = _safe_json_load(getattr(s, 'documents', None))
        proofs = _safe_json_load(getattr(s, 'delivery_proof', None))
        # 用 _attachment_record 包一下,保证 type 字段从 URL 推断出来(供前端预览判断图片/PDF)
        express_file = _attachment_record(docs[0].get('name'), docs[0].get('url')) if docs else None
        receipt_file = _attachment_record(proofs[0].get('name'), proofs[0].get('url')) if proofs else None
        out.append({
            'id': s.id,
            'number': s.shipment_number,
            'target': (s.sales_order.customer.company_name
                       if s.sales_order and getattr(s.sales_order, 'customer', None)
                       else _('入公司仓库')),
            'target_sub': s.sales_order.order_number if s.sales_order else None,
            'qty': s.total_quantity or 0,
            'status': s.status,
            'status_label': SHIPMENT_STATUS_LABEL.get(s.status, s.status),
            'status_tone':  SHIPMENT_STATUS_TONE.get(s.status, 'neutral'),
            'date':    _fmt_date(s.received_date or s.ship_date),
            'ship_date': _fmt_date(s.ship_date),
            'eta':     _fmt_date(s.expected_arrival),
            'carrier': s.carrier,
            'waybill': s.tracking_number,
            'express': express_file,   # {name, url, size?} | None
            'receipt': receipt_file,   # {name, url, size?} | None
            'notes': s.notes or '',    # 发货备注(create-from-po 时传入)
            'received_notes': s.received_notes or '',  # 签收备注
            'ship_items': items,       # 避开 dict.items 方法名冲突
        })
    return out


def _format_sn_range(sn_list):
    """SN 列表 → '120 个 · XXX-001~120' / '120 个 · XXX-001 等'"""
    if not sn_list:
        return ''
    if len(sn_list) == 1:
        return sn_list[0]
    # 检测连续段:同前缀 + 数字递增
    import re
    parsed = []
    for s in sn_list:
        m = re.match(r'^(.*?)(\d+)$', str(s))
        if not m:
            parsed = None
            break
        parsed.append((m.group(1), int(m.group(2))))
    if parsed and len(set(p[0] for p in parsed)) == 1:
        nums = [p[1] for p in parsed]
        if all(nums[i] == nums[i-1] + 1 for i in range(1, len(nums))):
            return f"{len(sn_list)} 个 · {sn_list[0]} ~ {sn_list[-1]}"
    return f"{len(sn_list)} 个 · {sn_list[0]} 等"


# ─── 当前阶段动作卡 ──────────────────────────────────
def build_current_action(order, approval_data, current_user_id=None):
    """
    根据订单状态返回 at_current_action_card 期望的 dict,或 None(已完成态)。
    """
    # 审批阶段(draft / pending / rejected / recalled)
    # 头部已经有对应主按钮(提交审批 / 重新提交 / 召回审批),
    # 不再用「当前阶段卡」重复,直接返回 None 隐藏。
    if order.status in ('draft', 'pending', 'rejected', 'recalled'):
        return None

    # 执行阶段
    if order.status in ('stored', 'completed') or (order.acceptance_status == 'passed'):
        return None  # 已完成

    prod_status = (order.production_status or 'not_started').lower()

    # 待发货 阶段:若所有明细已发完,跳到「验收入库」动作卡(无主按钮,签收在发货行)
    if prod_status == 'ready' and order.details:
        all_dispatched = all(
            (d.dispatched_quantity or 0) >= (d.quantity or 0)
            for d in order.details
        )
        if all_dispatched:
            return {
                'phase': 'execution',
                'icon': 'archive',
                'title_label': _('当前阶段'),
                'title': _('验收入库'),
                'desc': _('所有货物已发出,等待签收'),
                'hint': _('在下方发货记录逐单签收,全部签收后自动入库'),
                'btn_label': '',
                'btn_onclick': '',
            }

    action_map = {
        'not_started': {
            'icon': 'check', 'title': _('供应商确认'),
            'desc': _('等待供应商盖章确认订单'),
            'hint': _('确认完成后将进入备料环节'),
            'btn_label': _('上传供应商确认单'),
            'btn_onclick': 'atOpenStageModal(\'supplier-confirm\')',
        },
        'preparing': {
            'icon': 'box', 'title': _('备料'),
            'desc': _('采购部正在准备物料'),
            'hint': _('物料备齐后点击完成,进入生产环节'),
            'btn_label': _('备料完成'),
            'btn_onclick': "atAdvanceStage('producing', '%s')" % _('备料完成'),
        },
        'producing': {
            'icon': 'factory', 'title': _('生产'),
            'desc': _('供应商正在生产订单中的物料'),
            'hint': _('生产完毕后点击完成,进入测试环节'),
            'btn_label': _('生产完成'),
            'btn_onclick': "atAdvanceStage('testing', '%s')" % _('生产完成'),
        },
        'testing': {
            'icon': 'flask', 'title': _('出厂测试'),
            'desc': _('需要上传 QA 测试报告'),
            'hint': _('通过后即可发货'),
            'btn_label': _('上传测试报告'),
            'btn_onclick': 'atOpenStageModal(\'upload-test\')',
        },
        'ready': {
            'icon': 'truck', 'title': _('待发货'),
            'desc': _('可向客户订单或公司仓库发货'),
            'hint': _('可分多次发货'),
            'btn_label': _('创建发货单'),
            'btn_onclick': 'atOpenStageModal(\'create-shipment\')',
        },
    }
    a = action_map.get(prod_status)
    if not a:
        return None
    return {
        'phase': 'execution',
        'icon': a['icon'],
        'title_label': _('当前阶段'),
        'title': a['title'],
        'desc': a.get('desc'),
        'hint': a.get('hint'),
        'btn_label': a.get('btn_label'),
        'btn_onclick': a.get('btn_onclick', ''),
    }
