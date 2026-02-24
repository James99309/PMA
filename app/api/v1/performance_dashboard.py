"""绩效看板 API 端点

提供用户绩效看板的数据接口，支持 JWT 和 Session 认证。
"""

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_login import current_user
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.services.performance_dashboard_service import PerformanceDashboardService
from app.services.exchange_rate_service import exchange_rate_service
from app.utils.auth import flexible_auth
from app.utils.permissions import get_accessible_users
from app.utils.dictionary_helpers import get_company_type_options, get_industry_options, COMPANY_TYPE_LABELS, INDUSTRY_LABELS
from app import db
from config import Config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_current_user_flexible():
    """获取当前用户，支持 JWT 和 Session 认证"""
    # 先尝试 JWT
    try:
        verify_jwt_in_request(optional=True)
        jwt_id = get_jwt_identity()
        if jwt_id:
            user_id = int(jwt_id) if isinstance(jwt_id, str) else jwt_id
            return User.query.get(user_id)
    except Exception:
        pass

    # 回退到 Session
    if current_user and current_user.is_authenticated:
        return current_user

    return None


def check_user_access(auth_user, target_user_id):
    """检查用户是否有权限访问目标用户的绩效数据"""
    if not auth_user:
        return False

    # 用户可以访问自己的绩效数据
    if auth_user.id == target_user_id:
        return True

    # 管理员可以访问所有用户
    if auth_user.role == 'admin':
        return True

    # 检查是否在可访问用户列表中（基于用户管理权限）
    accessible_users = get_accessible_users(auth_user, 'user_management')
    accessible_user_ids = [u.id for u in accessible_users]

    return target_user_id in accessible_user_ids


@api_v1_bp.route('/performance/dashboard/<int:user_id>', methods=['GET'])
@flexible_auth
def get_performance_dashboard(user_id):
    """获取用户绩效看板完整数据

    Args:
        user_id: 目标用户ID

    Query Params:
        year: 年份（默认当前年）

    Returns:
        JSON: 包含以下数据的看板信息
            - summary: 年度汇总卡片数据
            - goal_achievement: 目标达成数据（月度趋势）
            - expense_budget: 报销预算对比
            - activity_score: 活跃度评分
            - industry_trend: 行业分布趋势
            - monthly_growth: 月度增长数据
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查
    if not check_user_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户绩效数据")

    # 获取年份参数
    year = request.args.get('year', datetime.now().year, type=int)
    # lite 模式：仅返回首页所需的轻量数据
    lite = request.args.get('lite', '0') == '1'

    try:
        # 获取看板数据
        dashboard_data = PerformanceDashboardService.get_dashboard_data(user_id, year, lite=lite)

        # 获取目标用户的货币配置
        target_user = User.query.get(user_id)
        user_currency = target_user.settlement_currency if target_user else Config.DEFAULT_CURRENCY
        user_exchange_rate = exchange_rate_service.get_exchange_rate('CNY', user_currency)

        response_data = {
            'user_id': user_id,
            'year': year,
            'user_role': target_user.role if target_user else '',
            'currency_config': {
                'currency': user_currency,
                'exchange_rate': user_exchange_rate
            },
            **dashboard_data
        }

        # 完整模式才返回字典数据（lite 模式不需要）
        if not lite:
            from app.utils.i18n import get_current_language
            lang = get_current_language()

            company_type_dict = {k: v for k, v in get_company_type_options()}
            for k, v in COMPANY_TYPE_LABELS.items():
                if k not in company_type_dict:
                    company_type_dict[k] = v.get(lang, v.get('zh', k))

            industry_dict = {k: v for k, v in get_industry_options()}
            for k, v in INDUSTRY_LABELS.items():
                if k not in industry_dict:
                    industry_dict[k] = v.get(lang, v.get('zh', k))

            response_data['dictionaries'] = {
                'company_type': company_type_dict,
                'industry': industry_dict
            }

        return api_response(
            success=True,
            message="获取成功",
            data=response_data
        )
    except Exception as e:
        logger.error(f"获取绩效看板数据失败: {e}")
        return api_response(success=False, code=500, message=f"获取数据失败: {str(e)}")


@api_v1_bp.route('/performance/expense-budget/<int:user_id>', methods=['GET'])
@flexible_auth
def get_expense_budget(user_id):
    """获取用户报销预算数据

    Args:
        user_id: 目标用户ID

    Query Params:
        year: 年份（默认当前年）

    Returns:
        JSON: 报销预算对比数据
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查
    if not check_user_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户数据")

    year = request.args.get('year', datetime.now().year, type=int)

    try:
        budget_data = PerformanceDashboardService.get_expense_budget_data(user_id, year)

        return api_response(
            success=True,
            message="获取成功",
            data={
                'user_id': user_id,
                'year': year,
                **budget_data
            }
        )
    except Exception as e:
        logger.error(f"获取报销预算数据失败: {e}")
        return api_response(success=False, code=500, message=f"获取数据失败: {str(e)}")


@api_v1_bp.route('/performance/expense-budget/<int:user_id>', methods=['POST'])
@flexible_auth
def set_expense_budget(user_id):
    """设置用户年度报销预算

    Args:
        user_id: 目标用户ID

    Body:
        year: 年份
        total_budget: 年度总预算
        entertainment_budget: 招待费预算（可选）
        travel_budget: 差旅费预算（可选）
        transport_budget: 交通费预算（可选）
        office_budget: 办公费预算（可选）
        communication_budget: 通讯费预算（可选）
        other_budget: 其他费用预算（可选）

    Returns:
        JSON: 操作结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查：只有管理员或有配置管理编辑权限的用户可以设置预算
    if auth_user.role != 'admin' and not auth_user.has_permission('config_management', 'edit'):
        return api_response(success=False, code=403, message="无权限设置预算")

    # 检查目标用户是否在可访问范围内
    if not check_user_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户")

    try:
        data = request.get_json()
        if not data:
            return api_response(success=False, code=400, message="请求数据无效")

        year = data.get('year', datetime.now().year)

        budget = PerformanceDashboardService.set_expense_budget(
            user_id=user_id,
            year=year,
            budget_data=data,
            operator_id=auth_user.id
        )

        return api_response(
            success=True,
            message="预算设置成功",
            data={
                'user_id': user_id,
                'year': year,
                'budget_id': budget.id
            }
        )
    except Exception as e:
        logger.error(f"设置报销预算失败: {e}")
        return api_response(success=False, code=500, message=f"设置失败: {str(e)}")


@api_v1_bp.route('/performance/activity-score/<int:user_id>', methods=['GET'])
@flexible_auth
def get_activity_score(user_id):
    """获取用户活跃度评分

    Args:
        user_id: 目标用户ID

    Query Params:
        year: 年份（默认当前年）
        month: 月份（可选，不传则返回年度评分）

    Returns:
        JSON: 活跃度评分数据
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查
    if not check_user_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户数据")

    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', type=int)

    try:
        score_data = PerformanceDashboardService.get_activity_score(user_id, year, month)

        return api_response(
            success=True,
            message="获取成功",
            data={
                'user_id': user_id,
                'year': year,
                'month': month,
                **score_data
            }
        )
    except Exception as e:
        logger.error(f"获取活跃度评分失败: {e}")
        return api_response(success=False, code=500, message=f"获取数据失败: {str(e)}")


@api_v1_bp.route('/performance/activity-trend/<int:user_id>', methods=['GET'])
@flexible_auth
def get_activity_trend(user_id):
    """获取用户月度活跃度趋势

    Args:
        user_id: 目标用户ID

    Query Params:
        year: 年份（默认当前年）

    Returns:
        JSON: 12个月的活跃度趋势数据
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查
    if not check_user_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户数据")

    year = request.args.get('year', datetime.now().year, type=int)

    try:
        trend_data = PerformanceDashboardService.get_monthly_activity_trend(user_id, year)

        return api_response(
            success=True,
            message="获取成功",
            data={
                'user_id': user_id,
                'year': year,
                'trend': trend_data
            }
        )
    except Exception as e:
        logger.error(f"获取活跃度趋势失败: {e}")
        return api_response(success=False, code=500, message=f"获取数据失败: {str(e)}")


@api_v1_bp.route('/performance/se-details/<int:user_id>', methods=['GET'])
@flexible_auth
def get_se_details(user_id):
    """获取 SE 绩效明细数据（方案植入明细 + 方案批价明细）

    Args:
        user_id: 目标用户ID

    Query Params:
        year: 年份（默认当前年）

    Returns:
        JSON: SE 明细数据
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    if not check_user_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户数据")

    year = request.args.get('year', datetime.now().year, type=int)

    try:
        detail_data = PerformanceDashboardService.get_se_detail_data(user_id, year)

        return api_response(
            success=True,
            message="获取成功",
            data=detail_data
        )
    except Exception as e:
        logger.error(f"获取SE绩效明细失败: {e}")
        return api_response(success=False, code=500, message=f"获取数据失败: {str(e)}")
