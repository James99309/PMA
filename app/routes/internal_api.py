"""
Internal API Blueprint — MCP Server 专用内部接口
鉴权方式: X-Internal-Token (环境变量 INTERNAL_API_TOKEN) + X-User-ID header
数据访问: 以指定用户身份通过 get_viewable_data 过滤
"""

import hmac
import os
import logging
from functools import wraps
from datetime import datetime, date

from flask import Blueprint, request, jsonify, g, current_app
from app import db
from app.models.user import User
from app.utils.access_control import get_viewable_data

logger = logging.getLogger(__name__)

internal_api_bp = Blueprint('internal_api', __name__, url_prefix='/internal/api')


# ---------------------------------------------------------------------------
# 鉴权装饰器
# ---------------------------------------------------------------------------

def internal_auth_required(f):
    """验证 X-Internal-Token + X-User-ID，成功后将 user 存入 g.current_user"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. 验证 token
        expected_token = os.environ.get('INTERNAL_API_TOKEN', '').strip()
        if not expected_token:
            return jsonify({'error': 'INTERNAL_API_TOKEN not configured on server'}), 503

        provided_token = request.headers.get('X-Internal-Token', '')
        if not hmac.compare_digest(provided_token, expected_token):
            return jsonify({'error': 'Invalid or missing X-Internal-Token'}), 401

        # 2. 验证 user id
        raw_user_id = request.headers.get('X-User-ID', '').strip()
        if not raw_user_id:
            return jsonify({'error': 'Missing X-User-ID header'}), 400

        try:
            user_id = int(raw_user_id)
        except ValueError:
            return jsonify({'error': 'X-User-ID must be an integer'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': f'User {user_id} not found'}), 404

        if not user.is_active:
            return jsonify({'error': f'User {user_id} is inactive'}), 403

        # 3. 存入 g
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _safe_datetime(dt):
    """将 datetime/date/float/None 统一转成 ISO 字符串"""
    if dt is None:
        return None
    if isinstance(dt, (datetime,)):
        return dt.isoformat()
    if isinstance(dt, date):
        return dt.isoformat()
    if isinstance(dt, (int, float)):
        try:
            return datetime.fromtimestamp(dt).isoformat()
        except Exception:
            return str(dt)
    return str(dt)


def _parse_limit(default=50, max_limit=200):
    """解析 ?limit= 参数，限制上界"""
    try:
        limit = int(request.args.get('limit', default))
        return min(max(1, limit), max_limit)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# 端点 1: 报价单
# GET /internal/api/quotations?status=&search=&limit=
# ---------------------------------------------------------------------------

@internal_api_bp.route('/quotations', methods=['GET'])
@internal_auth_required
def list_quotations():
    user = g.current_user
    limit = _parse_limit(default=50)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    project_id = request.args.get('project_id', '').strip()
    owner_name = request.args.get('owner_name', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    try:
        from app.models.quotation import Quotation

        filters = [Quotation.is_deleted == False] if hasattr(Quotation, 'is_deleted') else []
        query = get_viewable_data(Quotation, user, filters)

        if status:
            query = query.filter(Quotation.approval_status == status)
        if search:
            query = query.filter(Quotation.quotation_number.ilike(f'%{search}%'))
        if project_id:
            query = query.filter(Quotation.project_id == int(project_id))
        if owner_name:
            query = query.join(User, Quotation.owner_id == User.id).filter(
                db.or_(User.real_name.ilike(f'%{owner_name}%'), User.username.ilike(f'%{owner_name}%'))
            )
        if date_from:
            try:
                query = query.filter(Quotation.created_at >= datetime.fromisoformat(date_from))
            except ValueError:
                pass
        if date_to:
            try:
                query = query.filter(Quotation.created_at <= datetime.fromisoformat(date_to))
            except ValueError:
                pass

        items = query.order_by(Quotation.created_at.desc()).limit(limit).all()

        result = []
        for q in items:
            owner_name = None
            if q.owner:
                owner_name = q.owner.real_name or q.owner.username

            customer_name = None
            try:
                if q.customer:
                    customer_name = q.customer.company_name
            except Exception:
                pass

            result.append({
                'id': q.id,
                'quotation_number': q.quotation_number,
                'status': q.approval_status,
                'amount': q.amount,
                'currency': q.currency,
                'project_stage': q.project_stage,
                'project_type': q.project_type,
                'customer_name': customer_name,
                'owner_name': owner_name,
                'owner_id': q.owner_id,
                'created_at': _safe_datetime(q.created_at),
                'updated_at': _safe_datetime(q.updated_at),
            })

        return jsonify(result)

    except ImportError:
        return jsonify([])
    except Exception as e:
        logger.exception(f'[internal_api] list_quotations error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 2: 项目
# GET /internal/api/projects?status=&search=&limit=
# ---------------------------------------------------------------------------

@internal_api_bp.route('/projects', methods=['GET'])
@internal_auth_required
def list_projects():
    user = g.current_user
    limit = _parse_limit(default=50)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    try:
        from app.models.project import Project

        filters = [Project.is_deleted == False]

        query = get_viewable_data(Project, user, filters)

        if status:
            query = query.filter(Project.status == status)

        if search:
            query = query.filter(
                Project.project_name.ilike(f'%{search}%')
            )

        items = query.order_by(Project.id.desc()).limit(limit).all()

        result = []
        for p in items:
            owner_name = None
            try:
                if p.owner:
                    owner_name = p.owner.real_name or p.owner.username
            except Exception:
                pass

            result.append({
                'id': p.id,
                'project_name': p.project_name,
                'status': p.status,
                'current_stage': p.current_stage,
                'project_type': p.project_type,
                'industry': p.industry,
                'owner_id': p.owner_id,
                'owner_name': owner_name,
                'is_active': p.is_active,
                'activity_status': p.activity_status,
                'delivery_forecast': _safe_datetime(p.delivery_forecast),
                'report_time': _safe_datetime(p.report_time),
            })

        return jsonify(result)

    except ImportError:
        return jsonify([])
    except Exception as e:
        logger.exception(f'[internal_api] list_projects error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 3: 客户公司
# GET /internal/api/customers?search=&limit=
# ---------------------------------------------------------------------------

@internal_api_bp.route('/customers', methods=['GET'])
@internal_auth_required
def list_customers():
    user = g.current_user
    limit = _parse_limit(default=50)
    search = request.args.get('search', '').strip()

    try:
        from app.models.customer import Company

        filters = [Company.is_deleted == False]

        query = get_viewable_data(Company, user, filters)

        if search:
            query = query.filter(
                Company.company_name.ilike(f'%{search}%')
            )

        items = query.order_by(Company.id.desc()).limit(limit).all()

        result = []
        for c in items:
            owner_name = None
            try:
                if c.owner:
                    owner_name = c.owner.real_name or c.owner.username
            except Exception:
                pass

            result.append({
                'id': c.id,
                'company_code': c.company_code,
                'company_name': c.company_name,
                'company_type': c.company_type,
                'industry': c.industry,
                'country': c.country,
                'city': c.city,
                'status': c.status,
                'owner_id': c.owner_id,
                'owner_name': owner_name,
                'created_at': _safe_datetime(c.created_at),
            })

        return jsonify(result)

    except ImportError:
        return jsonify([])
    except Exception as e:
        logger.exception(f'[internal_api] list_customers error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 4: 待审批
# GET /internal/api/approvals/pending
# ---------------------------------------------------------------------------

@internal_api_bp.route('/approvals/pending', methods=['GET'])
@internal_auth_required
def list_pending_approvals():
    user = g.current_user

    try:
        from app.models.approval import ApprovalInstance, ApprovalStatus
        from app.helpers.approval_helpers import get_step_actual_approver

        base_instances = ApprovalInstance.query.filter(
            ApprovalInstance.status == ApprovalStatus.PENDING
        ).all()

        MAX_RESULTS = 20
        result = []
        for instance in base_instances:
            if len(result) >= MAX_RESULTS:
                break
            try:
                current_step_info = instance.get_current_step_info()
                if not current_step_info:
                    continue

                actual_approver = get_step_actual_approver(current_step_info, instance)
                if not actual_approver or actual_approver.id != user.id:
                    continue

                # 获取发起人名称
                creator_name = None
                try:
                    if instance.creator:
                        creator_name = instance.creator.real_name or instance.creator.username
                except Exception:
                    pass

                result.append({
                    'instance_id': instance.id,
                    'object_type': instance.object_type,
                    'object_id': instance.object_id,
                    'current_step': instance.current_step,
                    'started_at': _safe_datetime(instance.started_at),
                    'created_by': instance.created_by,
                    'creator_name': creator_name,
                    'template_name': (
                        instance.template_snapshot.get('template_name', '')
                        if instance.template_snapshot
                        else (instance.process.name if instance.process else '')
                    ),
                })
            except Exception as step_err:
                logger.debug(f'[internal_api] pending approval instance {instance.id} error: {step_err}')
                continue

        return jsonify(result)

    except ImportError:
        # ApprovalInstance 或 get_step_actual_approver 不存在时返回空列表
        return jsonify([])
    except Exception as e:
        logger.exception(f'[internal_api] list_pending_approvals error: {e}')
        return jsonify([])


# ---------------------------------------------------------------------------
# 端点 5: 本月报价统计
# GET /internal/api/stats/summary
# ---------------------------------------------------------------------------

@internal_api_bp.route('/stats/summary', methods=['GET'])
@internal_auth_required
def stats_summary():
    user = g.current_user

    try:
        from app.models.quotation import Quotation
        from sqlalchemy import func as sqlfunc

        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        filters = [Quotation.is_deleted == False] if hasattr(Quotation, 'is_deleted') else []
        base_query = get_viewable_data(Quotation, user, filters)

        this_month_query = base_query.filter(Quotation.created_at >= month_start)
        total_count = this_month_query.count()

        status_counts = (
            this_month_query
            .with_entities(Quotation.approval_status, sqlfunc.count(Quotation.id))
            .group_by(Quotation.approval_status)
            .all()
        )
        status_map = {s: cnt for s, cnt in status_counts}

        approved_amount = (
            this_month_query
            .filter(Quotation.approval_status == 'approved')
            .with_entities(sqlfunc.sum(Quotation.amount))
            .scalar()
        ) or 0.0

        return jsonify({
            'period': f'{now.year}-{now.month:02d}',
            'total_count': total_count,
            'status_breakdown': status_map,
            'approved_amount': approved_amount,
            'currency_note': 'raw field value, no unit conversion applied',
        })

    except ImportError:
        return jsonify({'error': 'Required models not available'}), 503
    except Exception as e:
        logger.exception(f'[internal_api] stats_summary error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 6: 报价单详情（含行项目）
# GET /internal/api/quotations/<id>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/quotations/<int:quotation_id>', methods=['GET'])
@internal_auth_required
def get_quotation_detail(quotation_id):
    user = g.current_user
    try:
        from app.models.quotation import Quotation, QuotationDetail

        filters = [Quotation.is_deleted == False] if hasattr(Quotation, 'is_deleted') else []
        q = get_viewable_data(Quotation, user, filters).filter(Quotation.id == quotation_id).first()
        if not q:
            return jsonify({'error': 'Not found or no permission'}), 404

        owner_name = (q.owner.real_name or q.owner.username) if q.owner else None
        customer_name = q.customer.company_name if q.customer else None
        contact_name = q.contact.name if q.contact else None
        project_name = q.project.project_name if q.project else None

        items = []
        for d in q.details:
            if d.row_type == 'section':
                items.append({'row_type': 'section', 'section_label': d.section_label, 'sort_order': d.sort_order})
            else:
                items.append({
                    'row_type': 'product',
                    'product_name': d.product_name,
                    'product_model': d.product_model,
                    'product_mn': d.product_mn,
                    'brand': d.brand,
                    'unit': d.unit,
                    'quantity': d.quantity,
                    'unit_price': d.unit_price,
                    'total_price': d.total_price,
                    'currency': d.currency,
                    'item_note': d.item_note,
                    'sort_order': d.sort_order,
                })

        extra = q.extra_fields or {}
        return jsonify({
            'id': q.id,
            'quotation_number': q.quotation_number,
            'status': q.approval_status,
            'amount': q.amount,
            'currency': q.currency,
            'project_id': q.project_id,
            'project_name': project_name,
            'customer_name': customer_name,
            'contact_name': contact_name,
            'owner_name': owner_name,
            'owner_id': q.owner_id,
            'project_stage': q.project_stage,
            'project_type': q.project_type,
            'notes': q.notes,
            'payment_terms': extra.get('payment_terms'),
            'delivery_terms': extra.get('delivery_terms'),
            'validity': extra.get('validity'),
            'created_at': _safe_datetime(q.created_at),
            'updated_at': _safe_datetime(q.updated_at),
            'items': items,
            'items_count': len(items),
        })
    except Exception as e:
        logger.exception(f'[internal_api] get_quotation_detail error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 7: 项目详情（含最近报价单摘要）
# GET /internal/api/projects/<id>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/projects/<int:project_id>', methods=['GET'])
@internal_auth_required
def get_project_detail(project_id):
    user = g.current_user
    try:
        from app.models.project import Project
        from app.models.quotation import Quotation

        p = get_viewable_data(Project, user, [Project.is_deleted == False]).filter(Project.id == project_id).first()
        if not p:
            return jsonify({'error': 'Not found or no permission'}), 404

        owner_name = (p.owner.real_name or p.owner.username) if p.owner else None

        # 最近 5 份报价单摘要
        q_filters = [Quotation.is_deleted == False, Quotation.project_id == project_id] if hasattr(Quotation, 'is_deleted') else [Quotation.project_id == project_id]
        recent_quotations = (
            get_viewable_data(Quotation, user, q_filters)
            .order_by(Quotation.created_at.desc())
            .limit(5).all()
        )
        total_quotation_count = get_viewable_data(Quotation, user, q_filters).count()

        quotation_list = []
        for q in recent_quotations:
            quotation_list.append({
                'id': q.id,
                'quotation_number': q.quotation_number,
                'status': q.approval_status,
                'amount': q.amount,
                'currency': q.currency,
                'owner_name': (q.owner.real_name or q.owner.username) if q.owner else None,
                'created_at': _safe_datetime(q.created_at),
            })

        return jsonify({
            'id': p.id,
            'project_name': p.project_name,
            'project_type': p.project_type,
            'current_stage': p.current_stage,
            'status': p.status,
            'activity_status': p.activity_status,
            'industry': p.industry,
            'owner_id': p.owner_id,
            'owner_name': owner_name,
            'delivery_forecast': _safe_datetime(p.delivery_forecast),
            'report_time': _safe_datetime(p.report_time) if hasattr(p, 'report_time') else None,
            'created_at': _safe_datetime(p.created_at) if hasattr(p, 'created_at') else None,
            'quotations_total': total_quotation_count,
            'quotations_recent': quotation_list,
            'quotations_note': f'显示最近 {len(quotation_list)} 份，共 {total_quotation_count} 份' if total_quotation_count > 5 else None,
        })
    except Exception as e:
        logger.exception(f'[internal_api] get_project_detail error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 8: 客户详情（含联系人）
# GET /internal/api/customers/<id>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/customers/<int:company_id>', methods=['GET'])
@internal_auth_required
def get_customer_detail(company_id):
    user = g.current_user
    try:
        from app.models.customer import Company, Contact

        c = get_viewable_data(Company, user, [Company.is_deleted == False]).filter(Company.id == company_id).first()
        if not c:
            return jsonify({'error': 'Not found or no permission'}), 404

        owner_name = (c.owner.real_name or c.owner.username) if c.owner else None

        contacts = Contact.query.filter_by(company_id=company_id).order_by(Contact.is_primary.desc()).all()
        contact_list = [{
            'id': ct.id,
            'name': ct.name,
            'department': getattr(ct, 'department', None),
            'position': getattr(ct, 'position', None),
            'phone': ct.phone,
            'email': ct.email,
            'is_primary': ct.is_primary,
        } for ct in contacts]

        return jsonify({
            'id': c.id,
            'company_code': getattr(c, 'company_code', None),
            'company_name': c.company_name,
            'company_type': c.company_type,
            'industry': c.industry,
            'country': c.country,
            'city': getattr(c, 'city', None),
            'address': getattr(c, 'address', None),
            'status': c.status,
            'owner_id': c.owner_id,
            'owner_name': owner_name,
            'created_at': _safe_datetime(c.created_at),
            'contacts': contact_list,
        })
    except Exception as e:
        logger.exception(f'[internal_api] get_customer_detail error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 9: 报销单列表
# GET /internal/api/expenses?status=&search=&date_from=&date_to=&limit=
# ---------------------------------------------------------------------------

@internal_api_bp.route('/expenses', methods=['GET'])
@internal_auth_required
def list_expenses():
    user = g.current_user
    limit = _parse_limit(default=30)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    try:
        from app.models.expense import Expense

        filters = [Expense.is_deleted == False]
        query = get_viewable_data(Expense, user, filters)

        if status:
            query = query.filter(Expense.status == status)
        if search:
            query = query.filter(Expense.title.ilike(f'%{search}%'))
        if date_from:
            try:
                query = query.filter(Expense.created_at >= datetime.fromisoformat(date_from))
            except ValueError:
                pass
        if date_to:
            try:
                query = query.filter(Expense.created_at <= datetime.fromisoformat(date_to))
            except ValueError:
                pass

        items = query.order_by(Expense.created_at.desc()).limit(limit).all()

        result = []
        for e in items:
            owner_name = (e.owner.real_name or e.owner.username) if e.owner else None
            result.append({
                'id': e.id,
                'expense_number': getattr(e, 'expense_number', None),
                'title': e.title,
                'status': e.status,
                'total_amount': e.total_amount,
                'currency': getattr(e, 'currency', 'CNY'),
                'payment_status': getattr(e, 'payment_status', None),
                'owner_name': owner_name,
                'owner_id': e.owner_id,
                'created_at': _safe_datetime(e.created_at),
            })
        return jsonify(result)
    except Exception as e:
        logger.exception(f'[internal_api] list_expenses error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 10: 批价单列表
# GET /internal/api/pricing-orders?status=&search=&limit=
# ---------------------------------------------------------------------------

@internal_api_bp.route('/pricing-orders', methods=['GET'])
@internal_auth_required
def list_pricing_orders():
    user = g.current_user
    limit = _parse_limit(default=30)
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    try:
        from app.models.pricing_order import PricingOrder

        query = get_viewable_data(PricingOrder, user, [])

        if status:
            query = query.filter(PricingOrder.status == status)
        if search:
            query = query.filter(PricingOrder.order_number.ilike(f'%{search}%'))

        items = query.order_by(PricingOrder.id.desc()).limit(limit).all()

        result = []
        for p in items:
            creator_name = None
            try:
                if p.creator:
                    creator_name = p.creator.real_name or p.creator.username
            except Exception:
                pass
            result.append({
                'id': p.id,
                'order_number': p.order_number,
                'status': p.status,
                'pricing_total_amount': p.pricing_total_amount,
                'settlement_total_amount': p.settlement_total_amount,
                'currency': p.currency,
                'creator_name': creator_name,
                'created_at': _safe_datetime(p.created_at) if hasattr(p, 'created_at') else None,
            })
        return jsonify(result)
    except Exception as e:
        logger.exception(f'[internal_api] list_pricing_orders error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 11: 产品搜索 (扩展版,支持 system-config skill 选型)
# GET /internal/api/products?search=&category=&category_id=&status=&frequency=&include_specs=&limit=
#
# 参数:
#   search        : 模糊匹配 product_name / model
#   category      : 分类名(如"合路平台")或 ID(如"2");支持中文名直查
#   category_id   : 同 category,但只接 int (兼容)
#   status        : 'active' (默认,只查在产) / 'discontinued' / 'upcoming' / 'any'
#   frequency     : 频率交集过滤,如 "350-470" / "UHF"(=350-470) / "VHF"(=136-174)
#                   只返回工作频率范围与该范围有交集的产品
#                   双工 "TX:.../RX:..." 取整体跨度匹配
#   include_specs : "1"=列表里附带每个产品的关键 specs(频率/载波/工作模式等)
#   limit         : 默认 30,上限 200
# ---------------------------------------------------------------------------

# 频率常用别名
_FREQ_ALIASES = {
    'UHF': '350-470',
    'VHF': '136-174',
    'FM':  '87-108',
    '800': '800-870',
}

# 列表里要返回的关键规格字段
_KEY_SPEC_FIELDS = [
    '工作频率', '载波容量支持', '载波容量', '工作模式', '辐射方向',
    '增益', '安装方式', '防护等级', '光口数量', '光口类型',
    '定位功能', '输出功率',
]


def _parse_freq_ranges(value: str):
    """解析频率字段值为 [(low, high), ...] 区间列表。

    支持:
      "400-470"                    → [(400.0, 470.0)]
      "TX:361-366 / RX:351-356"    → [(351.0, 366.0)]    取整体跨度
      "400-470 MHz"                → [(400.0, 470.0)]
      "350-470" + UHF/VHF 别名     → [(350.0, 470.0)]

    解析失败返回 [];skill 端按"无频率信息"跳过。
    """
    import re
    if not value:
        return []

    # 别名展开
    v = value.strip().upper()
    for alias, real in _FREQ_ALIASES.items():
        if v == alias:
            value = real
            break

    # 提取所有数字-数字段
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)', value)
    if not matches:
        return []

    nums = [(float(a), float(b)) for a, b in matches]
    # 双工 TX/RX 等多段时,取整体范围
    if len(nums) > 1:
        lo = min(min(a, b) for a, b in nums)
        hi = max(max(a, b) for a, b in nums)
        return [(lo, hi)]
    a, b = nums[0]
    return [(min(a, b), max(a, b))]


def _freq_overlaps(spec_value: str, target: str) -> bool:
    """判断产品频率字段 spec_value 与目标频率 target 是否有交集。"""
    s = _parse_freq_ranges(spec_value)
    t = _parse_freq_ranges(target)
    if not s or not t:
        return False
    return any(sa <= tb and ta <= sb for sa, sb in s for ta, tb in t)


@internal_api_bp.route('/products', methods=['GET'])
@internal_auth_required
def list_products():
    limit = min(_parse_limit(default=30), 200)
    search = request.args.get('search', '').strip()
    category_arg = (request.args.get('category', '') or request.args.get('category_id', '')).strip()
    status_arg = request.args.get('status', 'active').strip().lower()
    frequency = request.args.get('frequency', '').strip()
    include_specs = request.args.get('include_specs', '').strip() in ('1', 'true', 'yes')

    try:
        from app.models.product import Product
        from app.models.product_code import ProductCategory
        from app.models.product_spec import ProductSpec

        query = Product.query.filter(Product.is_deleted == False)

        # 状态过滤
        if status_arg != 'any':
            query = query.filter(Product.status == status_arg)

        # 文本搜索
        if search:
            query = query.filter(
                db.or_(
                    Product.product_name.ilike(f'%{search}%'),
                    Product.model.ilike(f'%{search}%'),
                    Product.product_mn.ilike(f'%{search}%'),
                )
            )

        # 分类过滤(支持名称或 ID)
        if category_arg:
            if category_arg.isdigit():
                query = query.filter(Product.category_id == int(category_arg))
            else:
                cat = ProductCategory.query.filter(ProductCategory.name == category_arg).first()
                if cat:
                    query = query.filter(Product.category_id == cat.id)
                else:
                    return jsonify([])

        # 没有频率筛选时直接走数据库 limit
        if not frequency:
            items = query.order_by(Product.product_name).limit(limit).all()
        else:
            # 频率筛选要在 Python 层做(范围交集逻辑非简单 SQL)
            # 取适度大窗口后用 _freq_overlaps 过滤,避免全表扫
            candidate_limit = min(limit * 5, 1000)
            candidates = query.order_by(Product.product_name).limit(candidate_limit).all()
            items = []
            for p in candidates:
                # 取该产品的"工作频率"spec
                freq_spec = ProductSpec.query.filter_by(
                    product_id=p.id, field_name='工作频率'
                ).first()
                if freq_spec and _freq_overlaps(freq_spec.field_value, frequency):
                    items.append(p)
                if len(items) >= limit:
                    break

        # 序列化
        result = []
        for p in items:
            row = {
                'id': p.id,
                'product_mn': getattr(p, 'product_mn', None),
                'product_name': p.product_name,
                'model': getattr(p, 'model', None),
                'brand': getattr(p, 'brand', None),
                'category': getattr(p, 'category', None),
                'category_id': getattr(p, 'category_id', None),
                'retail_price': getattr(p, 'retail_price', None),
                'currency': getattr(p, 'currency', None),
                'status': getattr(p, 'status', None),
                'unit': getattr(p, 'unit', None),
            }
            if include_specs:
                key_specs = {}
                specs = ProductSpec.query.filter(
                    ProductSpec.product_id == p.id,
                    ProductSpec.field_name.in_(_KEY_SPEC_FIELDS),
                ).all()
                for s in specs:
                    key_specs[s.field_name] = s.field_value
                row['key_specs'] = key_specs
            result.append(row)
        return jsonify(result)
    except Exception as e:
        logger.exception(f'[internal_api] list_products error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 12: 团队成员
# GET /internal/api/users
# ---------------------------------------------------------------------------

@internal_api_bp.route('/users', methods=['GET'])
@internal_auth_required
def list_users():
    user = g.current_user
    try:
        # 厂家管理员可看全部；其他人只看同公司
        if user.is_vendor_user() and user.role == 'admin':
            users = User.query.filter(User.is_active == True).order_by(User.real_name).all()
        else:
            users = User.query.filter(
                User.is_active == True,
                User.company_name == user.company_name,
            ).order_by(User.real_name).all()

        result = [{
            'id': u.id,
            'username': u.username,
            'real_name': u.real_name,
            'department': u.department,
            'role': u.role,
            'company_name': u.company_name,
            'email': u.email,
        } for u in users]
        return jsonify(result)
    except Exception as e:
        logger.exception(f'[internal_api] list_users error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 13: 跨模块仪表盘
# GET /internal/api/dashboard?period=this_month
# ---------------------------------------------------------------------------

@internal_api_bp.route('/dashboard', methods=['GET'])
@internal_auth_required
def dashboard():
    user = g.current_user
    try:
        from app.models.quotation import Quotation
        from app.models.project import Project
        from app.models.approval import ApprovalInstance, ApprovalStatus
        from app.helpers.approval_helpers import get_step_actual_approver
        from sqlalchemy import func as sqlfunc

        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)

        # 本月报价统计
        q_filters = [Quotation.is_deleted == False] if hasattr(Quotation, 'is_deleted') else []
        q_base = get_viewable_data(Quotation, user, q_filters)
        q_month = q_base.filter(Quotation.created_at >= month_start)

        q_total = q_month.count()
        q_status = {s: c for s, c in q_month.with_entities(Quotation.approval_status, sqlfunc.count(Quotation.id)).group_by(Quotation.approval_status).all()}
        q_amount = q_month.filter(Quotation.approval_status == 'approved').with_entities(sqlfunc.sum(Quotation.amount)).scalar() or 0

        # 项目总数（活跃）
        p_active = get_viewable_data(Project, user, [Project.is_deleted == False, Project.is_active == True]).count()

        # 待审批数
        pending_count = 0
        try:
            instances = ApprovalInstance.query.filter(ApprovalInstance.status == ApprovalStatus.PENDING).all()
            for inst in instances:
                try:
                    step = inst.get_current_step_info()
                    if step and get_step_actual_approver(step, inst) and get_step_actual_approver(step, inst).id == user.id:
                        pending_count += 1
                except Exception:
                    pass
        except Exception:
            pass

        return jsonify({
            'period': f'{now.year}-{now.month:02d}',
            'quotations': {
                'total_this_month': q_total,
                'by_status': q_status,
                'approved_amount': q_amount,
            },
            'projects': {
                'active_count': p_active,
            },
            'approvals': {
                'pending_count': pending_count,
            },
        })
    except Exception as e:
        logger.exception(f'[internal_api] dashboard error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 14: 报销单详情（含行项目）
# GET /internal/api/expenses/<id>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/expenses/<int:expense_id>', methods=['GET'])
@internal_auth_required
def get_expense_detail(expense_id):
    user = g.current_user
    try:
        from app.models.expense import Expense, ExpenseDetail

        filters = [Expense.is_deleted == False]
        e = get_viewable_data(Expense, user, filters).filter(Expense.id == expense_id).first()
        if not e:
            return jsonify({'error': 'Not found or no permission'}), 404

        owner_name = (e.owner.real_name or e.owner.username) if e.owner else None
        customer_name = e.customer.company_name if getattr(e, 'customer', None) else None
        project_name = e.project.project_name if getattr(e, 'project', None) else None

        items = []
        for d in e.details:
            items.append({
                'id': d.id,
                'expense_date': d.expense_date.isoformat() if d.expense_date else None,
                'expense_category': d.expense_category,
                'description': d.description,
                'current_amount': d.current_amount,
                'invoice_amount': d.invoice_amount,
                'currency': d.currency,
                'exchange_rate': getattr(d, 'exchange_rate', 1.0),
                'document_count': getattr(d, 'document_count', 1),
            })

        return jsonify({
            'id': e.id,
            'expense_number': getattr(e, 'expense_number', None),
            'title': e.title,
            'description': e.description,
            'status': e.status,
            'total_amount': e.total_amount,
            'currency': getattr(e, 'currency', 'CNY'),
            'payment_status': getattr(e, 'payment_status', None),
            'payment_date': _safe_datetime(getattr(e, 'payment_date', None)),
            'payment_method': getattr(e, 'payment_method', None),
            'owner_name': owner_name,
            'owner_id': e.owner_id,
            'customer_name': customer_name,
            'project_name': project_name,
            'created_at': _safe_datetime(e.created_at),
            'items': items,
            'items_count': len(items),
        })
    except Exception as e:
        logger.exception(f'[internal_api] get_expense_detail error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 14b: 工作类型字典
# GET /internal/api/work-types
# ---------------------------------------------------------------------------

@internal_api_bp.route('/work-types', methods=['GET'])
@internal_auth_required
def list_work_types():
    """返回工作日志支持的所有工作类型（code → label），按分组整理。"""
    from app.models.worklog import WorkItem
    hidden = {'market_planning', 'brand_promotion', 'event_execution'}
    groups = [
        ('通用',   ['meeting', 'internal_training', 'other']),
        ('行销',   ['customer_visit', 'presales_support', 'business_negotiation', 'customer_maintenance']),
        ('市场',   ['video_production', 'material_design', 'social_media_operation', 'channel_activity', 'brand_event']),
        ('服务',   ['onsite_maintenance', 'service_response', 'technical_support', 'troubleshooting']),
        ('行政',   ['admin_affairs', 'office_management', 'asset_management']),
        ('人事',   ['hr_affairs', 'recruitment', 'employee_relations', 'performance_management']),
        ('财务',   ['finance_work', 'expense_review', 'accounting']),
        ('产品',   ['product_research', 'requirement_analysis', 'product_planning']),
        ('供应链', ['procurement', 'inventory_management', 'logistics', 'quality_tracking']),
        ('任务',   ['product_confirmation', 'task_work']),
    ]
    result = []
    for group_name, codes in groups:
        items = []
        for code in codes:
            label = WorkItem.TYPE_LABELS.get(code, code)
            items.append({'code': code, 'label': label})
        result.append({'group': group_name, 'types': items})
    return jsonify({'groups': result})


# ---------------------------------------------------------------------------
# 端点 15: 创建行动记录
# POST /internal/api/actions
# ---------------------------------------------------------------------------

@internal_api_bp.route('/actions', methods=['POST'])
@internal_auth_required
def create_action():
    user = g.current_user
    try:
        from app.models.action import Action
        from app.models.customer import Company, Contact
        from app.models.project import Project

        data = request.get_json() or {}
        communication = (data.get('communication') or '').strip()
        if not communication:
            return jsonify({'error': '行动记录内容不能为空'}), 400

        action_date = date.today()
        if data.get('date'):
            try:
                action_date = date.fromisoformat(data['date'])
            except ValueError:
                pass

        company_id = data.get('company_id')
        project_id = data.get('project_id')
        contact_id = data.get('contact_id')

        # 权限验证：确认用户有权访问关联的项目/客户
        if project_id:
            p = get_viewable_data(Project, user, [Project.is_deleted == False]).filter(Project.id == project_id).first()
            if not p:
                return jsonify({'error': f'项目 {project_id} 不存在或无权访问'}), 404
        if company_id:
            c = get_viewable_data(Company, user, [Company.is_deleted == False]).filter(Company.id == company_id).first()
            if not c:
                return jsonify({'error': f'客户 {company_id} 不存在或无权访问'}), 404

        action = Action(
            date=action_date,
            communication=communication,
            company_id=company_id,
            project_id=project_id,
            contact_id=contact_id,
            owner_id=user.id,
            is_shared=True,
        )
        db.session.add(action)
        db.session.commit()

        return jsonify({
            'success': True,
            'id': action.id,
            'date': action.date.isoformat(),
            'message': '行动记录已创建',
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f'[internal_api] create_action error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 16: 创建/获取工作日志草稿 + 添加工作项
# POST /internal/api/worklogs
# ---------------------------------------------------------------------------

@internal_api_bp.route('/worklogs', methods=['POST'])
@internal_auth_required
def create_worklog_item():
    user = g.current_user
    try:
        from app.models.worklog import WorkLog, WorkItem

        data = request.get_json() or {}
        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'error': '工作项标题不能为空'}), 400

        log_date = date.today()
        if data.get('date'):
            try:
                log_date = date.fromisoformat(data['date'])
            except ValueError:
                pass

        # 解析时间跨度（可选，HH:MM 或 HH:MM:SS）
        from datetime import time as _time
        def _parse_time(v):
            if not v: return None
            try:
                return _time.fromisoformat(str(v))
            except ValueError:
                return None
        start_time = _parse_time(data.get('start_time'))
        end_time = _parse_time(data.get('end_time'))

        # 获取或创建当日日志
        worklog = WorkLog.get_or_create(user.id, log_date)
        if worklog.status == 'submitted':
            return jsonify({'error': f'{log_date} 的日志已提交，无法添加工作项'}), 400

        item = WorkItem(
            title=title,
            description=data.get('description', ''),
            planned_date=log_date,
            work_type=data.get('work_type', 'other'),
            status=data.get('status', 'completed'),
            actual_hours=data.get('actual_hours'),
            start_time=start_time,
            end_time=end_time,
            project_id=data.get('project_id'),
            customer_id=data.get('company_id'),
            owner_id=user.id,
            worklog_id=worklog.id,
        )
        db.session.add(item)
        db.session.commit()

        return jsonify({
            'success': True,
            'worklog_id': worklog.id,
            'item_id': item.id,
            'date': log_date.isoformat(),
            'worklog_status': worklog.status,
            'message': f'工作项已添加到 {log_date} 日志',
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f'[internal_api] create_worklog_item error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 17: 提交工作日志
# POST /internal/api/worklogs/<date>/submit
# ---------------------------------------------------------------------------

@internal_api_bp.route('/worklogs/<log_date>/submit', methods=['POST'])
@internal_auth_required
def submit_worklog(log_date):
    user = g.current_user
    try:
        from app.models.worklog import WorkLog

        try:
            target_date = date.fromisoformat(log_date)
        except ValueError:
            return jsonify({'error': '日期格式无效，请用 YYYY-MM-DD'}), 400

        worklog = WorkLog.get_or_create(user.id, target_date)

        if worklog.status == 'submitted':
            return jsonify({'error': f'{log_date} 的日志已经提交过了'}), 400

        worklog.status = 'submitted'
        worklog.submitted_at = datetime.now()

        data = request.get_json() or {}
        if data.get('additional_notes'):
            worklog.additional_notes = data['additional_notes'].strip()

        db.session.commit()

        return jsonify({
            'success': True,
            'worklog_id': worklog.id,
            'date': log_date,
            'submitted_at': worklog.submitted_at.isoformat(),
            'message': f'{log_date} 日志已提交',
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(f'[internal_api] submit_worklog error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 端点 18-implant: 植入分析
# GET /internal/api/implant/overview?year=0
# GET /internal/api/implant/records?search=&project_id=&owner_name=&year=&limit=20
# ---------------------------------------------------------------------------

@internal_api_bp.route('/implant/overview', methods=['GET'])
@internal_auth_required
def implant_overview():
    """植入分析概览：总植入额、数量、项目数、本月/上月环比。year=0 表示全部年份。"""
    try:
        from app.models.quotation import Quotation, QuotationDetail
        from app.models.project import Project
        from app.utils.access_control import get_viewable_data
        from sqlalchemy import func, and_

        user = g.current_user
        year = int(request.args.get('year', datetime.utcnow().year))

        # 最新报价单子查询（每项目只统计最新一份）
        latest_subq = db.session.query(
            Quotation.project_id,
            func.max(Quotation.id).label('latest_id')
        ).group_by(Quotation.project_id).subquery()

        # 基础查询：用户可见报价单 JOIN 最新子查询 JOIN 项目 JOIN 明细（implant_subtotal > 0）
        q_filters = [Quotation.is_deleted == False] if hasattr(Quotation, 'is_deleted') else []
        visible_q_ids = get_viewable_data(Quotation, user, q_filters).with_entities(Quotation.id)

        base = db.session.query(
            QuotationDetail.total_price,
            QuotationDetail.quantity,
            QuotationDetail.created_at,
            Project.id.label('project_id'),
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            latest_subq, and_(
                Quotation.project_id == latest_subq.c.project_id,
                Quotation.id == latest_subq.c.latest_id
            )
        ).join(
            Project, Quotation.project_id == Project.id
        ).filter(
            Quotation.id.in_(visible_q_ids),
            QuotationDetail.implant_subtotal > 0,
            Project.is_deleted == False,
        )

        if year > 0:
            base = base.filter(
                QuotationDetail.created_at >= datetime(year, 1, 1),
                QuotationDetail.created_at < datetime(year + 1, 1, 1),
            )

        stats = base.with_entities(
            func.sum(QuotationDetail.total_price).label('total_amount'),
            func.sum(QuotationDetail.quantity).label('total_qty'),
            func.count(func.distinct(Project.id)).label('project_count'),
        ).first()

        now = datetime.utcnow()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = datetime(now.year - 1, 12, 1) if now.month == 1 else datetime(now.year, now.month - 1, 1)

        this_amt = base.filter(QuotationDetail.created_at >= this_month_start).with_entities(
            func.sum(QuotationDetail.total_price)).scalar() or 0
        last_amt = base.filter(
            QuotationDetail.created_at >= last_month_start,
            QuotationDetail.created_at < this_month_start,
        ).with_entities(func.sum(QuotationDetail.total_price)).scalar() or 0

        mom = round((float(this_amt) - float(last_amt)) / float(last_amt) * 100, 1) if last_amt else 0

        return jsonify({
            'year': year if year > 0 else 'all',
            'total_amount': float(stats.total_amount or 0),
            'total_quantity': int(stats.total_qty or 0),
            'project_count': int(stats.project_count or 0),
            'this_month_amount': float(this_amt),
            'last_month_amount': float(last_amt),
            'mom_rate': mom,
        })
    except Exception as e:
        logger.exception(f'[internal_api] implant_overview error: {e}')
        return jsonify({'error': str(e)}), 500


@internal_api_bp.route('/implant/records', methods=['GET'])
@internal_auth_required
def implant_records():
    """植入明细记录：按项目+产品展示，支持搜索/项目/负责人/年份筛选。"""
    try:
        from app.models.quotation import Quotation, QuotationDetail
        from app.models.project import Project
        from app.models.user import User
        from app.utils.access_control import get_viewable_data
        from sqlalchemy import func, or_, and_

        user = g.current_user
        search = request.args.get('search', '').strip()
        project_id = request.args.get('project_id', type=int)
        owner_name = request.args.get('owner_name', '').strip()
        year = request.args.get('year', type=int)
        limit = min(int(request.args.get('limit', 30)), 100)

        latest_subq = db.session.query(
            Quotation.project_id,
            func.max(Quotation.id).label('latest_id')
        ).group_by(Quotation.project_id).subquery()

        q_filters = [Quotation.is_deleted == False] if hasattr(Quotation, 'is_deleted') else []
        visible_q_ids = get_viewable_data(Quotation, user, q_filters).with_entities(Quotation.id)

        q = db.session.query(
            QuotationDetail.product_name,
            QuotationDetail.product_model,
            QuotationDetail.product_mn,
            QuotationDetail.quantity,
            QuotationDetail.unit_price,
            QuotationDetail.total_price,
            QuotationDetail.implant_subtotal,
            QuotationDetail.created_at,
            Quotation.id.label('quotation_id'),
            Quotation.quotation_number,
            Project.id.label('project_id'),
            Project.project_name,
            Project.current_stage,
            User.real_name.label('owner_name'),
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            latest_subq, and_(
                Quotation.project_id == latest_subq.c.project_id,
                Quotation.id == latest_subq.c.latest_id
            )
        ).join(
            Project, Quotation.project_id == Project.id
        ).join(
            User, Quotation.owner_id == User.id
        ).filter(
            Quotation.id.in_(visible_q_ids),
            QuotationDetail.implant_subtotal > 0,
            Project.is_deleted == False,
        )

        if year:
            q = q.filter(
                QuotationDetail.created_at >= datetime(year, 1, 1),
                QuotationDetail.created_at < datetime(year + 1, 1, 1),
            )
        if project_id:
            q = q.filter(Project.id == project_id)
        if owner_name:
            q = q.filter(User.real_name.ilike(f'%{owner_name}%'))
        if search:
            q = q.filter(or_(
                QuotationDetail.product_name.ilike(f'%{search}%'),
                QuotationDetail.product_model.ilike(f'%{search}%'),
                Project.project_name.ilike(f'%{search}%'),
            ))

        rows = q.order_by(QuotationDetail.implant_subtotal.desc()).limit(limit).all()

        records = []
        for r in rows:
            records.append({
                'product_name': r.product_name or '',
                'product_model': r.product_model or '',
                'product_mn': r.product_mn or '',
                'quantity': int(r.quantity or 0),
                'unit_price': float(r.unit_price or 0),
                'total_price': float(r.total_price or 0),
                'implant_subtotal': float(r.implant_subtotal or 0),
                'project_name': r.project_name or '',
                'project_id': r.project_id,
                'stage': r.current_stage or '',
                'quotation_number': r.quotation_number or '',
                'quotation_id': r.quotation_id,
                'owner_name': r.owner_name or '',
                'created_at': r.created_at.strftime('%Y-%m-%d') if r.created_at else '',
            })

        return jsonify({'records': records, 'count': len(records)})
    except Exception as e:
        logger.exception(f'[internal_api] implant_records error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 18a: 知识库分类目录
# GET /internal/api/wiki/topics
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/topics', methods=['GET'])
@internal_auth_required
def wiki_topics():
    """返回知识库所有 topic 分类及各自的文章数量。"""
    try:
        from app.models.knowledge import KnowledgeTopic, KnowledgeWikiArticle
        from sqlalchemy import func

        topics = KnowledgeTopic.query.order_by(KnowledgeTopic.sort_order, KnowledgeTopic.name).all()

        # 统计每个 topic 的文章数
        counts = dict(
            db.session.query(KnowledgeWikiArticle.topic, func.count(KnowledgeWikiArticle.id))
            .group_by(KnowledgeWikiArticle.topic)
            .all()
        )

        result = []
        for t in topics:
            result.append({
                'name': t.name,
                'description': t.description or '',
                'article_count': counts.get(t.name, 0),
            })

        # 若 KnowledgeTopic 表为空，退化为从文章表聚合
        if not result:
            rows = (
                db.session.query(KnowledgeWikiArticle.topic, func.count(KnowledgeWikiArticle.id))
                .group_by(KnowledgeWikiArticle.topic)
                .order_by(KnowledgeWikiArticle.topic)
                .all()
            )
            result = [{'name': r[0], 'description': '', 'article_count': r[1]} for r in rows]

        return jsonify({'topics': result})
    except Exception as e:
        logger.exception(f'[internal_api] wiki_topics error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 18b: 知识库单篇文章全文
# GET /internal/api/wiki/articles/<id>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/articles/<int:article_id>', methods=['GET'])
@internal_auth_required
def wiki_article(article_id):
    """按 ID 返回单篇文章的完整 Markdown 内容。"""
    try:
        from app.services.wiki import storage
        from app.models.knowledge import KnowledgeWikiArticle

        art = KnowledgeWikiArticle.query.get(article_id)
        if not art:
            return jsonify({'error': f'文章 {article_id} 不存在'}), 404

        content = storage.read_article_content(art.file_path)
        images = [
            {'index': m['index'], 'path': m['path'], 'caption': m.get('caption', '')}
            for m in (art.image_manifest or [])
        ]
        return jsonify({
            'id': art.id,
            'title': art.title,
            'topic': art.topic,
            'summary': art.summary,
            'content': content,
            'updated_at': art.updated_at.isoformat() if art.updated_at else None,
            'images': images,
            'asset_base_url': f'/internal/api/wiki/articles/{art.id}/asset/',
        })
    except Exception as e:
        logger.exception(f'[internal_api] wiki_article error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 18b-asset: 知识库文章图片资产（内部 API 版）
# GET /internal/api/wiki/articles/<id>/asset/<path:rel>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/articles/<int:article_id>/asset/<path:rel>', methods=['GET'])
@internal_auth_required
def wiki_article_asset(article_id, rel):
    """Serve an image from wiki/<topic>/_assets/<slug>/...
    Internal API variant — uses internal_auth_required (not session login).
    """
    from flask import send_file, abort
    from app.services.wiki.paths import get_wiki_dir
    from app.models.knowledge import KnowledgeWikiArticle

    art = KnowledgeWikiArticle.query.get(article_id)
    if art is None:
        abort(404)

    expected_prefix = f'_assets/{art.slug}/'
    if '..' in rel or not rel.startswith(expected_prefix):
        abort(400)

    abs_path = (get_wiki_dir() / art.topic / rel).resolve()
    base = (get_wiki_dir() / art.topic).resolve()
    try:
        abs_path.relative_to(base)
    except ValueError:
        abort(400)
    if not abs_path.is_file():
        abort(404)
    return send_file(str(abs_path))


# ---------------------------------------------------------------------------
# 端点 18c: 知识库搜索（仅返回摘要，不含全文）
# GET /internal/api/wiki/search?q=问题&topic=可选
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/search', methods=['GET'])
@internal_auth_required
def wiki_search():
    """全文检索知识库，返回标题+摘要+内容预览，不含全文。
    需要完整正文请用 GET /wiki/articles/<id>。
    """
    question = request.args.get('q', '').strip()
    topic = request.args.get('topic', '').strip() or None
    top_k = min(int(request.args.get('top_k', 5)), 10)
    if not question:
        return jsonify({'error': '问题不能为空'}), 400
    try:
        from app.services.wiki.querier import _full_text_search
        from app.services.wiki import storage
        from app.models.knowledge import KnowledgeWikiArticle

        hits = _full_text_search(question, top_k, topic=topic)
        fts_hit = len(hits) > 0

        # 全文检索 0 命中时退化为最近更新的文章（不读全文，只返回摘要）
        if not hits:
            q = KnowledgeWikiArticle.query
            if topic:
                q = q.filter_by(topic=topic)
            hits = q.order_by(KnowledgeWikiArticle.updated_at.desc()).limit(top_k).all()

        articles = []
        for art in hits:
            # 读取内容只为生成预览，不返回全文
            content = storage.read_article_content(art.file_path)
            preview = content[:300].rstrip() + ('…' if len(content) > 300 else '') if content else ''
            articles.append({
                'id': art.id,
                'title': art.title,
                'topic': art.topic,
                'summary': art.summary,
                'preview': preview,
                'images': [
                    {'index': m['index'], 'path': m['path'], 'caption': m.get('caption', '')}
                    for m in (art.image_manifest or [])
                ],
                'asset_base_url': f'/internal/api/wiki/articles/{art.id}/asset/',
            })

        return jsonify({
            'question': question,
            'articles': articles,
            'fts_hit': fts_hit,
        })
    except Exception as e:
        logger.exception(f'[internal_api] wiki_search error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 15: 文件列表
# GET /internal/api/files?folder_id=
# ---------------------------------------------------------------------------

@internal_api_bp.route('/files', methods=['GET'])
@internal_auth_required
def list_files():
    user = g.current_user
    folder_id = request.args.get('folder_id')
    if folder_id:
        try:
            folder_id = int(folder_id)
        except ValueError:
            folder_id = None
    try:
        from app.services.file_manager_service import FileManagerService
        result = FileManagerService.list_files(user, folder_id=folder_id)
        folders = [{'id': f['id'], 'name': f['name']} for f in result.get('folders', [])]
        files = []
        for f in result.get('files', []):
            files.append({
                'id': f['id'],
                'name': f['display_name'],
                'size': f.get('file_size'),
                'mime_type': f.get('mime_type'),
                'created_at': f.get('created_at'),
            })
        return jsonify({'folders': folders, 'files': files})
    except Exception as e:
        logger.exception(f'[internal_api] list_files error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 16: 读取文件内容（Base64）
# GET /internal/api/files/<id>/content
# ---------------------------------------------------------------------------

FILE_SIZE_LIMIT = 10 * 1024 * 1024   # 10MB 硬限制
FILE_SIZE_WARN  =  5 * 1024 * 1024   # 5MB 警告

@internal_api_bp.route('/files/<int:file_ref_id>/content', methods=['GET'])
@internal_auth_required
def get_file_content(file_ref_id):
    user = g.current_user
    try:
        import base64
        from app.models.file_manager import UserFileRef
        from app.utils.smart_storage_manager import SmartStorageManager

        ref = UserFileRef.query.filter_by(
            id=file_ref_id, user_id=user.id, is_deleted=False
        ).first()
        if not ref:
            return jsonify({'error': '文件不存在或无权访问'}), 404

        lib = ref.file_library
        if not lib:
            return jsonify({'error': '文件记录损坏'}), 500

        file_size = lib.file_size or 0
        mime_type = lib.mime_type or 'application/octet-stream'
        display_name = ref.display_name

        if file_size > FILE_SIZE_LIMIT:
            size_mb = file_size / 1024 / 1024
            return jsonify({
                'error': f'文件过大（{size_mb:.1f} MB），超过 10MB 限制，请直接在 PMA 中查看',
                'file_name': display_name,
                'file_size': file_size,
                'skipped': True,
            }), 413

        storage = SmartStorageManager()
        data = storage.download_file(lib.storage_path, bucket_type='file_library')
        if not data:
            return jsonify({'error': '文件下载失败'}), 500

        warn = None
        if file_size > FILE_SIZE_WARN:
            warn = f'文件较大（{file_size/1024/1024:.1f} MB），处理可能较慢'

        return jsonify({
            'file_name': display_name,
            'mime_type': mime_type,
            'file_size': file_size,
            'data': base64.b64encode(data).decode('utf-8'),
            'warning': warn,
        })
    except Exception as e:
        logger.exception(f'[internal_api] get_file_content error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 19: 行动记录搜索
# GET /internal/api/actions?search=&company_id=&project_id=&days=30&limit=30
# ---------------------------------------------------------------------------

@internal_api_bp.route('/actions', methods=['GET'])
@internal_auth_required
def list_actions():
    """行动记录列表，支持关键词/客户/项目/时间范围筛选。"""
    user = g.current_user
    try:
        from app.models.action import Action
        from app.models.customer import Company, Contact
        from app.models.project import Project
        from app.utils.access_control import get_viewable_data
        from sqlalchemy import or_

        search = request.args.get('search', '').strip()
        company_id = request.args.get('company_id', type=int)
        project_id = request.args.get('project_id', type=int)
        days = request.args.get('days', type=int)
        limit = min(int(request.args.get('limit', 30)), 100)

        q = get_viewable_data(Action, user, []).order_by(Action.date.desc(), Action.created_at.desc())

        if search:
            q = q.filter(Action.communication.ilike(f'%{search}%'))
        if company_id:
            q = q.filter(Action.company_id == company_id)
        if project_id:
            q = q.filter(Action.project_id == project_id)
        if days:
            from datetime import timedelta
            cutoff = datetime.utcnow().date() - timedelta(days=days)
            q = q.filter(Action.date >= cutoff)

        actions = q.limit(limit).all()

        result = []
        for a in actions:
            company_name = a.company.company_name if a.company else ''
            project_name = a.project.project_name if a.project else ''
            contact_name = (a.contact.name if a.contact else '') if a.contact_id else ''
            owner_name = (a.owner.real_name or a.owner.username) if a.owner else ''
            result.append({
                'id': a.id,
                'date': a.date.isoformat() if a.date else '',
                'communication': a.communication or '',
                'company_id': a.company_id,
                'company_name': company_name,
                'project_id': a.project_id,
                'project_name': project_name,
                'contact_name': contact_name,
                'owner_name': owner_name,
                'created_at': a.created_at.strftime('%Y-%m-%d') if a.created_at else '',
            })

        return jsonify({'actions': result, 'count': len(result)})
    except Exception as e:
        logger.exception(f'[internal_api] list_actions error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 20: 工作项搜索
# GET /internal/api/work-items?search=&work_type=&days=30&limit=30
# ---------------------------------------------------------------------------

@internal_api_bp.route('/work-items', methods=['GET'])
@internal_auth_required
def list_work_items():
    """工作项列表，支持关键词/类型/时间范围筛选。"""
    user = g.current_user
    try:
        from app.models.worklog import WorkItem

        search = request.args.get('search', '').strip()
        work_type = request.args.get('work_type', '').strip()
        days = request.args.get('days', type=int)
        limit = min(int(request.args.get('limit', 30)), 100)

        q = WorkItem.query.filter(
            WorkItem.owner_id == user.id,
            WorkItem.is_deleted == False,
        ).order_by(WorkItem.planned_date.desc())

        if search:
            q = q.filter(WorkItem.title.ilike(f'%{search}%'))
        if work_type:
            q = q.filter(WorkItem.work_type == work_type)
        if days:
            from datetime import timedelta
            cutoff = datetime.utcnow().date() - timedelta(days=days)
            q = q.filter(WorkItem.planned_date >= cutoff)

        items = q.limit(limit).all()

        result = []
        for w in items:
            result.append({
                'id': w.id,
                'title': w.title or '',
                'work_type': w.work_type or '',
                'type_label': WorkItem.TYPE_LABELS.get(w.work_type, w.work_type or ''),
                'planned_date': w.planned_date.isoformat() if w.planned_date else '',
                'status': w.status or '',
                'actual_hours': w.actual_hours,
                'project_id': w.project_id,
                'notes': w.execution_notes or '',
            })

        return jsonify({'items': result, 'count': len(result)})
    except Exception as e:
        logger.exception(f'[internal_api] list_work_items error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 21: 批价单详情
# GET /internal/api/pricing-orders/<id>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/pricing-orders/<int:order_id>', methods=['GET'])
@internal_auth_required
def get_pricing_order_detail(order_id):
    """批价单完整详情，含行项目和审批状态。"""
    user = g.current_user
    try:
        from app.models.pricing_order import PricingOrder, PricingOrderDetail

        order = get_viewable_data(PricingOrder, user, []).filter(PricingOrder.id == order_id).first()
        if not order:
            return jsonify({'error': '批价单不存在或无权访问'}), 404

        details = []
        for d in order.pricing_details:
            details.append({
                'id': d.id,
                'product_name': d.product_name or '',
                'product_model': d.product_model or '',
                'product_mn': d.product_mn or '',
                'quantity': d.quantity,
                'market_price': float(d.market_price or 0),
                'unit_price': float(d.unit_price or 0),
                'discount_rate': float(d.discount_rate or 1),
                'total_price': float(d.total_price or 0),
            })

        project_name = order.project.project_name if order.project else ''
        dealer_name = order.dealer.name if order.dealer else ''
        distributor_name = order.distributor.name if order.distributor else ''
        creator_name = ''
        if order.creator:
            creator_name = order.creator.real_name or order.creator.username

        return jsonify({
            'id': order.id,
            'order_number': order.order_number,
            'project_id': order.project_id,
            'project_name': project_name,
            'dealer_name': dealer_name,
            'distributor_name': distributor_name,
            'is_direct_contract': order.is_direct_contract,
            'status': order.status,
            'currency': order.currency,
            'pricing_total_amount': float(order.pricing_total_amount or 0),
            'settlement_total_amount': float(order.settlement_total_amount or 0),
            'notes': order.notes or '',
            'creator_name': creator_name,
            'created_at': order.created_at.strftime('%Y-%m-%d') if order.created_at else '',
            'details': details,
        })
    except Exception as e:
        logger.exception(f'[internal_api] get_pricing_order_detail error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 22: 产品详情
# GET /internal/api/products/<id>
# ---------------------------------------------------------------------------

@internal_api_bp.route('/products/<int:product_id>', methods=['GET'])
@internal_auth_required
def get_product_detail(product_id):
    """产品详情，含规格参数。"""
    try:
        from app.models.product import Product

        p = Product.query.get(product_id)
        if not p:
            return jsonify({'error': '产品不存在'}), 404

        specs = []
        if hasattr(p, 'specs'):
            for s in p.specs.order_by('display_order').limit(30).all():
                specs.append({'field': s.field_name or '', 'value': s.field_value or ''})

        return jsonify({
            'id': p.id,
            'product_name': p.product_name or '',
            'model': p.model or '',
            'product_mn': p.product_mn or '',
            'type': p.type or '',
            'category': p.category or '',
            'brand': p.brand or '',
            'unit': p.unit or '',
            'retail_price': float(p.retail_price or 0),
            'currency': p.currency or 'CNY',
            'status': p.status or '',
            'specification': p.specification or '',
            'is_vendor_product': p.is_vendor_product,
            'specs': specs,
        })
    except Exception as e:
        logger.exception(f'[internal_api] get_product_detail error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 23: 销售订单搜索
# GET /internal/api/sales-orders?search=&status=&limit=20
# ---------------------------------------------------------------------------

@internal_api_bp.route('/sales-orders', methods=['GET'])
@internal_auth_required
def list_sales_orders():
    """销售订单列表，支持关键词/状态筛选。"""
    user = g.current_user
    try:
        from app.models.sales_order import SalesOrder
        from app.utils.access_control import get_viewable_data

        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)

        from app.models.user import User as UserModel
        is_admin = user.role in ('admin', 'ceo', 'finance_director', 'finace_director')
        q = SalesOrder.query.order_by(SalesOrder.created_at.desc())
        if not is_admin:
            q = q.filter(SalesOrder.created_by_id == user.id)

        if search:
            q = q.filter(SalesOrder.order_number.ilike(f'%{search}%'))
        if status:
            q = q.filter(SalesOrder.status == status)

        orders = q.limit(limit).all()

        result = []
        for o in orders:
            customer_name = o.customer.name if o.customer else ''
            project_name = o.project.project_name if o.project else ''
            creator_name = (o.creator.real_name or o.creator.username) if o.creator else ''
            result.append({
                'id': o.id,
                'order_number': o.order_number,
                'status': o.status,
                'customer_name': customer_name,
                'project_id': o.project_id,
                'project_name': project_name,
                'total_amount': float(o.total_amount or 0),
                'currency': o.currency,
                'creator_name': creator_name,
                'created_at': o.created_at.strftime('%Y-%m-%d') if o.created_at else '',
            })

        return jsonify({'orders': result, 'count': len(result)})
    except Exception as e:
        logger.exception(f'[internal_api] list_sales_orders error: {e}')
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# Wiki 写入端点（MCP 上传/编译/去重）
# ═══════════════════════════════════════════════════════════════════

# ---------------------------------------------------------------------------
# 端点 W1: 上传文件到个人文件夹（base64）
# POST /internal/api/files/upload
# Body JSON: { content_base64, filename, folder_id?(int) }
# Returns: { file_id, file_library_id, sha256, size }
# ---------------------------------------------------------------------------

@internal_api_bp.route('/files/upload', methods=['POST'])
@internal_auth_required
def upload_file_to_personal_folder():
    """通用文件上传到 PMA 个人文件夹。返回 file_id（UserFileRef.id）。"""
    user = g.current_user
    data = request.get_json(silent=True) or {}
    content_b64 = data.get('content_base64', '')
    filename = (data.get('filename') or '').strip()
    folder_id = data.get('folder_id')

    if not content_b64 or not filename:
        return jsonify({'error': 'content_base64 和 filename 必填'}), 400

    try:
        import base64
        try:
            file_data = base64.b64decode(content_b64, validate=True)
        except Exception as e:
            return jsonify({'error': f'base64 解码失败: {e}'}), 400

        if len(file_data) > 10 * 1024 * 1024:
            return jsonify({
                'error': f'文件过大（{len(file_data)/1024/1024:.1f}MB > 10MB）'
            }), 413

        from app.services.file_manager_service import FileManagerService
        ok, result = FileManagerService.upload_file_from_bytes(
            user, file_data, filename, folder_id=folder_id
        )
        if not ok:
            return jsonify({'error': str(result)}), 400

        # result 是 UserFileRef.to_dict()
        return jsonify({
            'file_id': result.get('id'),
            'file_library_id': result.get('file_library_id'),
            'filename': result.get('display_name') or filename,
            'size': len(file_data),
        })
    except Exception as e:
        logger.exception(f'[internal_api] upload_file error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 W2: 添加 wiki 原始文件（自动异步编译）
# POST /internal/api/wiki/raw-files
# Body JSON: { file_id(UserFileRef.id), topic, title?, scope? }
# Returns: { raw_id, ingest_status, topic, scope, title }
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/raw-files', methods=['POST'])
@internal_auth_required
def wiki_add_raw_file():
    """从用户个人文件夹的 file_id（UserFileRef）添加为 wiki 原始资料。
    成功后自动后台异步编译 + 发送站内通知。
    """
    user = g.current_user
    data = request.get_json(silent=True) or {}
    file_id = data.get('file_id')
    topic = (data.get('topic') or '').strip()
    title = (data.get('title') or '').strip()
    scope = (data.get('scope') or 'personal').strip()

    if not file_id or not topic:
        return jsonify({'error': 'file_id 和 topic 必填'}), 400
    if scope not in ('personal', 'department', 'company', 'system'):
        return jsonify({'error': f'非法 scope: {scope}'}), 400

    try:
        import threading
        from app.services.wiki import storage, compiler
        from app.services.wiki.scope import can_write_scope
        from app.services.wiki.paths import ensure_wiki_structure
        from app.models.knowledge import KnowledgeRawFile, KnowledgeTopic
        from app.models.file_manager import UserFileRef
        from app.models.file_library import FileLibrary
        from app.services.file_manager_service import FileManagerService

        # 1. topic 校验
        try:
            storage.validate_topic(topic)
        except storage.WikiPathError as e:
            return jsonify({'error': str(e)}), 400

        if user.role not in ('admin', 'ceo'):
            allowed = {t[0] for t in db.session.query(KnowledgeTopic.name).all()}
            if topic not in allowed:
                return jsonify({'error': f'topic "{topic}" 不在预定义列表中，请联系管理员创建'}), 403

        # 2. scope 权限
        if not can_write_scope(user, scope):
            return jsonify({'error': f'无权限写入 {scope} 级别'}), 403

        # 3. 解析 file_ref → file_library
        ref = UserFileRef.query.filter_by(id=file_id, user_id=user.id).first()
        if not ref:
            return jsonify({'error': f'file_id {file_id} 不存在或非本人文件'}), 404

        fl = FileLibrary.query.get(ref.file_library_id)
        if not fl:
            return jsonify({'error': '关联的 file_library 记录不存在'}), 404

        content = FileManagerService.read_file_content_auto_decompress(fl)
        if content is None:
            return jsonify({'error': '无法读取文件内容'}), 500

        # 4. 落盘 + 体检
        ensure_wiki_structure()
        safe_name = storage.dated_filename(fl.original_filename)
        raw_path = storage.save_raw_file(topic, safe_name, content)

        from pathlib import Path
        from app.services.wiki.paths import get_wiki_root
        abs_path = get_wiki_root() / raw_path
        reason = storage.validate_raw_file_for_wiki(abs_path)
        if reason:
            try:
                abs_path.unlink(missing_ok=True)
            except Exception:
                pass
            return jsonify({'error': reason}), 400

        # 5. 创建 raw 记录
        raw = KnowledgeRawFile(
            file_library_id=fl.id,
            topic=topic,
            raw_path=raw_path,
            title=title or ref.display_name or fl.original_filename,
            added_by=user.id,
            scope=scope,
            owner_id=user.id,
            owner_department=user.department,
        )
        db.session.add(raw)
        db.session.commit()

        logger.info(f'[internal_api/wiki] add_raw user={user.id} ref={file_id} → raw_id={raw.id}')

        # 6. 异步触发编译 + 通知（复用 knowledge_wiki._async_ingest_and_notify）
        from app.views.knowledge_wiki import _async_ingest_and_notify
        app = current_app._get_current_object()
        threading.Thread(
            target=_async_ingest_and_notify,
            args=(raw.id, user.id, app),
            daemon=True,
        ).start()

        return jsonify({
            'raw_id': raw.id,
            'ingest_status': raw.ingest_status,
            'topic': raw.topic,
            'scope': raw.scope,
            'title': raw.title,
        })
    except Exception as e:
        logger.exception(f'[internal_api] wiki_add_raw error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 W3: 查询 raw 文件编译状态
# GET /internal/api/wiki/raw-files/<id>/status
# Returns: { raw_id, ingest_status, ingest_error?, ingested_at?, article_ids[] }
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/raw-files/<int:raw_id>/status', methods=['GET'])
@internal_auth_required
def wiki_raw_file_status(raw_id):
    """查 raw 文件的编译状态 + 已生成的文章 ID。
    可见性：所有者 / admin / ceo / 部门经理(department scope) — 复用现有 visible_raw_files_query
    """
    user = g.current_user
    try:
        from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
        from app.services.wiki.scope import visible_raw_files_query

        raw = visible_raw_files_query(user).filter_by(id=raw_id).first()
        if not raw:
            return jsonify({'error': f'raw_id {raw_id} 不存在或无权查看'}), 404

        # 反查由本 raw 贡献的 articles
        article_ids = []
        try:
            arts = KnowledgeWikiArticle.query.filter(
                KnowledgeWikiArticle.source_raw_ids.isnot(None)
            ).all()
            for a in arts:
                if raw.id in (a.source_raw_ids or []):
                    article_ids.append({'id': a.id, 'title': a.title, 'topic': a.topic, 'slug': a.slug})
        except Exception:
            pass

        return jsonify({
            'raw_id': raw.id,
            'topic': raw.topic,
            'title': raw.title,
            'ingest_status': raw.ingest_status,
            'ingest_error': raw.ingest_error,
            'ingested_at': raw.ingested_at.isoformat() if raw.ingested_at else None,
            'article_ids': article_ids,
        })
    except Exception as e:
        logger.exception(f'[internal_api] wiki_raw_status error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 W4: 批量去重检查
# POST /internal/api/wiki/check-files
# Body JSON: { file_library_ids: [int, ...] }
# Returns: { results: { "<file_library_id>": { in_wiki, raw_id?, status?, topic? } } }
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/check-files', methods=['POST'])
@internal_auth_required
def wiki_check_files():
    """批量查 file_library_ids 是否已在 wiki。"""
    data = request.get_json(silent=True) or {}
    fl_ids = data.get('file_library_ids') or []
    if not isinstance(fl_ids, list) or not fl_ids:
        return jsonify({'error': 'file_library_ids 必填且为非空数组'}), 400

    try:
        from app.models.knowledge import KnowledgeRawFile

        raws = KnowledgeRawFile.query.filter(
            KnowledgeRawFile.file_library_id.in_(fl_ids)
        ).all()

        # 同一 file_library_id 可能有多条 raw（不同 topic 多次入库），取最新
        status_map = {}
        for raw in raws:
            fid = str(raw.file_library_id)
            existing = status_map.get(fid)
            if not existing or (raw.created_at and raw.created_at > existing.get('_t')):
                status_map[fid] = {
                    'in_wiki': raw.ingest_status == 'ingested',
                    'raw_id': raw.id,
                    'status': raw.ingest_status,
                    'topic': raw.topic,
                    'title': raw.title,
                    '_t': raw.created_at,
                }

        for v in status_map.values():
            v.pop('_t', None)
        for fid in fl_ids:
            if str(fid) not in status_map:
                status_map[str(fid)] = {'in_wiki': False}

        return jsonify({'results': status_map})
    except Exception as e:
        logger.exception(f'[internal_api] wiki_check_files error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------------------------------
# 端点 W5: 同步重新编译（失败重试）
# POST /internal/api/wiki/raw-files/<id>/ingest
# Body JSON (可选): { async: bool, default true }
# Returns:
#   async=true → { triggered: true, raw_id }
#   async=false → 同步等待 30-60s，返回 { raw_id, operations: [...] }
# ---------------------------------------------------------------------------

@internal_api_bp.route('/wiki/raw-files/<int:raw_id>/ingest', methods=['POST'])
@internal_auth_required
def wiki_ingest_raw_file(raw_id):
    """触发某个 raw 文件的（重新）编译。默认异步，async=false 时同步阻塞。"""
    user = g.current_user
    data = request.get_json(silent=True) or {}
    is_async = data.get('async', True)

    try:
        from app.models.knowledge import KnowledgeRawFile
        from app.services.wiki import compiler

        raw = KnowledgeRawFile.query.get(raw_id)
        if not raw:
            return jsonify({'error': f'raw_id {raw_id} 不存在'}), 404

        is_admin = user.role in ('admin', 'ceo')
        if not is_admin and raw.owner_id != user.id:
            return jsonify({'error': '只有文件所有者或管理员可以触发编译'}), 403

        if is_async:
            import threading
            from app.views.knowledge_wiki import _async_ingest_and_notify
            app = current_app._get_current_object()
            threading.Thread(
                target=_async_ingest_and_notify,
                args=(raw.id, user.id, app),
                daemon=True,
            ).start()
            return jsonify({'triggered': True, 'raw_id': raw.id, 'mode': 'async'})

        # 同步模式（仅用于失败重试少量文件）
        try:
            result = compiler.ingest_raw_file(raw_id)
        except compiler.IngestError as e:
            return jsonify({'error': str(e)}), 400

        return jsonify({
            'raw_id': raw.id,
            'mode': 'sync',
            'operations': result.get('operations', []),
        })
    except Exception as e:
        logger.exception(f'[internal_api] wiki_ingest error: {e}')
        return jsonify({'error': str(e)}), 500
