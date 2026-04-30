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
# 端点 11: 产品搜索
# GET /internal/api/products?search=&limit=
# ---------------------------------------------------------------------------

@internal_api_bp.route('/products', methods=['GET'])
@internal_auth_required
def list_products():
    limit = _parse_limit(default=30)
    search = request.args.get('search', '').strip()

    try:
        from app.models.product import Product

        query = Product.query.filter(Product.status != 'deleted') if hasattr(Product, 'status') else Product.query

        if search:
            query = query.filter(
                db.or_(
                    Product.product_name.ilike(f'%{search}%'),
                    Product.model.ilike(f'%{search}%') if hasattr(Product, 'model') else False,
                )
            )

        items = query.order_by(Product.id.desc()).limit(limit).all()

        result = []
        for p in items:
            result.append({
                'id': p.id,
                'product_name': p.product_name,
                'model': getattr(p, 'model', None),
                'brand': getattr(p, 'brand', None),
                'category': getattr(p, 'category', None),
                'retail_price': getattr(p, 'retail_price', None),
                'currency': getattr(p, 'currency', None),
                'status': getattr(p, 'status', None),
            })
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
        return jsonify({
            'id': art.id,
            'title': art.title,
            'topic': art.topic,
            'summary': art.summary,
            'content': content,
            'updated_at': art.updated_at.isoformat() if art.updated_at else None,
        })
    except Exception as e:
        logger.exception(f'[internal_api] wiki_article error: {e}')
        return jsonify({'error': str(e)}), 500


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
