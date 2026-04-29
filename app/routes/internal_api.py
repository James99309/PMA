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

    try:
        from app.models.quotation import Quotation

        filters = [Quotation.is_deleted == False] if hasattr(Quotation, 'is_deleted') else []

        query = get_viewable_data(Quotation, user, filters)

        if status:
            query = query.filter(Quotation.approval_status == status)

        if search:
            query = query.filter(
                db.or_(
                    Quotation.quotation_number.ilike(f'%{search}%'),
                )
            )

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

        # 本月报价单（按 created_at 过滤）
        this_month_query = base_query.filter(Quotation.created_at >= month_start)

        total_count = this_month_query.count()

        # 状态分布
        status_counts = (
            this_month_query
            .with_entities(Quotation.approval_status, sqlfunc.count(Quotation.id))
            .group_by(Quotation.approval_status)
            .all()
        )
        status_map = {s: cnt for s, cnt in status_counts}

        # 金额合计（仅 approved）
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
