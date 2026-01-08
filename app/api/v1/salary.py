# -*- coding: utf-8 -*-
"""用户薪资 API 端点

提供用户薪资配置和计算数据接口，支持 JWT 和 Session 认证。
"""

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_login import current_user
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.salary_config import (
    SalaryGradeConfig, SalaryGradeBandwidth, SalaryBaseParams,
    SalaryStepRules, EmployeeSalaryConfig, QuarterlyPerformanceData,
    SalaryCalculationResult, SalesTeamConfig, SalaryPeriodSnapshot
)
# 2026-01-08: 废弃旧的 KPI 目标系统，不再需要导入 UserPerformanceTarget, RolePerformanceTarget
from app.utils.auth import flexible_auth
from app.utils.permissions import get_accessible_users
from app.models.pricing_order import PricingOrder
from app import db
from datetime import datetime
from sqlalchemy import extract
from config import Config
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


def check_salary_view_access(auth_user, target_user_id):
    """检查用户是否有权限查看目标用户的薪资数据"""
    if not auth_user:
        return False

    # 管理员可以访问所有用户
    if auth_user.role == 'admin':
        return True

    # 检查是否有用户管理查看权限
    if auth_user.has_permission('user_management', 'view'):
        accessible_users = get_accessible_users(auth_user, 'user_management')
        accessible_user_ids = [u.id for u in accessible_users]
        return target_user_id in accessible_user_ids

    return False


def check_salary_edit_access(auth_user, target_user_id):
    """检查用户是否有权限编辑目标用户的薪资配置"""
    if not auth_user:
        return False

    # 管理员可以编辑所有用户
    if auth_user.role == 'admin':
        return True

    # 检查是否有用户管理编辑权限
    return auth_user.has_permission('user_management', 'edit')


def is_period_settled(year: int, period_type: str, period_value: int) -> bool:
    """
    判断指定周期是否已结算（即快照应锁定）

    结算规则：
    - 月度结算：上个月及之前的月份视为已结算
    - 季度结算：上个季度及之前的季度视为已结算

    Args:
        year: 年份
        period_type: 'monthly' 或 'quarterly'
        period_value: 月份 1-12 或 季度 1-4

    Returns:
        bool: True=已结算, False=未结算
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_quarter = (current_month - 1) // 3 + 1

    if period_type == 'monthly':
        # 月度：本月之前为已结算
        if year < current_year:
            return True  # 去年及之前全部结算
        elif year == current_year:
            return period_value < current_month  # 本月之前的月份已结算
        else:
            return False  # 未来年份未结算

    elif period_type == 'quarterly':
        # 季度：本季度之前为已结算
        if year < current_year:
            return True  # 去年及之前全部结算
        elif year == current_year:
            return period_value < current_quarter  # 本季度之前已结算
        else:
            return False  # 未来年份未结算

    return False


def auto_generate_and_confirm_snapshots(user_id: int, year: int) -> dict:
    """
    自动生成或确认指定年份的月度快照

    规则：
    - 只为当年生成（不更新往年）
    - 只处理已结算周期
    - 无快照：生成并直接设为 confirmed
    - 有draft：自动改为 confirmed
    - 有confirmed/published：跳过

    Args:
        user_id: 用户ID
        year: 年份

    Returns:
        dict: {'created': [...], 'confirmed': [...], 'skipped': [...]}
    """
    result = {'created': [], 'confirmed': [], 'skipped': []}

    # 只处理当年
    current_year = datetime.now().year
    if year != current_year:
        return result

    # 获取员工配置（按年份过滤）
    employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()
    if not employee_config:
        return result

    # 计算所有月度数据
    try:
        monthly_data = calculate_monthly_salary_breakdown(employee_config, year)
    except Exception as e:
        logger.error(f"计算月度薪资数据失败: user_id={user_id}, year={year}, error={e}")
        return result

    # 获取现有快照
    existing_snapshots = {
        s.period_value: s
        for s in SalaryPeriodSnapshot.query.filter_by(
            user_id=user_id, year=year, period_type='monthly'
        ).all()
    }

    for month_data in monthly_data:
        month = month_data['month']

        # 检查是否已结算
        if not is_period_settled(year, 'monthly', month):
            result['skipped'].append({'month': month, 'reason': 'not_settled'})
            continue

        existing = existing_snapshots.get(month)

        if existing:
            if existing.status in ['confirmed', 'published']:
                # 已锁定，跳过
                result['skipped'].append({'month': month, 'reason': 'locked'})
                continue
            elif existing.status == 'draft':
                # draft 状态，自动确认
                existing.status = 'confirmed'
                existing.confirmed_at = datetime.utcnow()
                result['confirmed'].append(month)
        else:
            # 创建新快照，直接设为 confirmed
            snapshot = SalaryPeriodSnapshot(
                user_id=user_id,
                year=year,
                period_type='monthly',
                period_value=month,
                calculated_base_salary=month_data.get('base_salary', 0),
                calculated_management_allowance=0,  # 管理津贴暂不在月度数据中
                calculated_performance_salary=month_data.get('performance_salary', 0),
                calculated_commission=month_data.get('personal_commission', 0),
                calculated_team_share=month_data.get('team_share_commission', 0),
                calculated_total=month_data.get('monthly_total', 0),
                calculation_params={
                    'monthly_target': month_data.get('monthly_target', 0),
                    'monthly_achievement': month_data.get('monthly_achievement', 0),
                    'monthly_completion_rate': month_data.get('monthly_completion_rate', 0),
                    'quarterly_completion_rate': month_data.get('quarterly_completion_rate', 0),
                    'is_quarter_end': month_data.get('is_quarter_end', False),
                    'grade_code': employee_config.grade.grade_code if employee_config.grade else None,
                },
                status='confirmed',
                confirmed_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.session.add(snapshot)
            result['created'].append(month)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存快照失败: user_id={user_id}, year={year}, error={e}")
        result = {'created': [], 'confirmed': [], 'skipped': [], 'error': str(e)}

    return result


def get_quarterly_target_from_performance_config(user_id, year, quarter, annual_target):
    """
    从绩效配置获取季度目标

    2026-01-08: 废弃旧的 RolePerformanceTarget/UserPerformanceTarget 系统
    统一使用 EmployeeSalaryConfig，直接返回年度目标 / 4

    参数：
        user_id: 用户ID
        year: 年份
        quarter: 季度（1-4）
        annual_target: 年度目标（从薪资配置获取）

    返回：
        季度目标值（年度目标 / 4）
    """
    # 废弃旧系统，直接使用年度目标平摊
    return annual_target / 4 if annual_target > 0 else 0


def get_monthly_target(employee_config, year, month):
    """
    获取月度目标，优先级：
    1. 月度目标配置
    2. 季度目标平摊（从绩效配置获取季度目标）
    3. 年度目标平摊
    """
    annual_target = employee_config.get_effective_value('annual_target', 0)

    # 1. 检查月度目标配置
    if employee_config.monthly_targets:
        targets = employee_config.monthly_targets
        if str(month) in targets and targets[str(month)]:
            return float(targets[str(month)])

    # 2. 检查季度目标（从绩效配置获取季度目标，平摊到3个月）
    quarter = (month - 1) // 3 + 1
    quarterly_data = QuarterlyPerformanceData.query.filter_by(
        user_id=employee_config.user_id,
        year=year,
        quarter=quarter
    ).first()
    if quarterly_data and quarterly_data.achievement:
        # 从绩效配置获取季度目标，平摊到3个月
        quarterly_target = get_quarterly_target_from_performance_config(
            employee_config.user_id, year, quarter, annual_target
        )
        return quarterly_target / 3

    # 3. 年度目标平摊
    return annual_target / 12


def calculate_monthly_performance(user_id, year, month):
    """
    从批价单计算月度业绩数据
    所有阈值和参数从配置表获取，不硬编码

    核心变更：提成按单个订单计算，而不是汇总后计算
    - 每个高批价订单单独计算：超出部分 × 查阶梯表(订单高批价率)
    - 汇总所有订单提成
    """
    # 从配置表获取高批价阈值（使用 pricing_baseline 参数）
    high_price_threshold_param = SalaryBaseParams.query.filter_by(
        param_code='pricing_baseline'
    ).first()
    # pricing_baseline 存储的是百分比形式（如46），需要除以100转换为小数
    high_price_threshold = float(high_price_threshold_param.param_value) / 100 if high_price_threshold_param else 0.46

    # 查询当月已审批的批价单
    orders = PricingOrder.query.filter(
        PricingOrder.created_by == user_id,
        PricingOrder.status == 'approved',
        extract('year', PricingOrder.approved_at) == year,
        extract('month', PricingOrder.approved_at) == month
    ).all()

    # 计算销售额
    sales_amount = sum(o.pricing_total_amount or 0 for o in orders)

    # 初始化统计变量
    high_price_order_total = 0     # 高批价订单总额
    high_price_amount = 0          # 超出部分累计（提成基数）
    high_price_commission = 0       # 提成金额累计（按订单计算）
    total_discount_weight = 0       # 折扣率加权总和
    total_order_amount = 0          # 订单金额总和（用于加权平均）

    for o in orders:
        order_amount = o.pricing_total_amount or 0
        discount_rate = o.pricing_total_discount_rate or 0

        # 累计计算平均折扣率（按金额加权）
        if discount_rate > 0:
            total_discount_weight += order_amount * discount_rate
            total_order_amount += order_amount

        # 高批价订单处理
        if discount_rate >= high_price_threshold and discount_rate > 0:
            # 高批价订单总额
            high_price_order_total += order_amount

            # 阈值金额 = 订单金额 × (阈值/折扣率)
            threshold_amount = order_amount * (high_price_threshold / discount_rate)

            # 超出部分 = 订单金额 - 阈值金额
            extra_portion = order_amount - threshold_amount
            high_price_amount += extra_portion

            # 单个订单高批价率 = 超出部分 / 阈值金额（仅用于统计显示）
            order_high_price_rate = extra_portion / threshold_amount if threshold_amount > 0 else 0

            # 根据订单折扣率查阶梯表（阈值代表折扣率档位：45%、50%、55%、60%）
            order_commission_rate = SalaryStepRules.get_coefficient(
                'commission_rate', discount_rate * 100
            )

            # 该订单提成
            order_commission = extra_portion * order_commission_rate
            high_price_commission += order_commission

    # 高批价占比（高批价订单金额 / 总销售额）- 用于UI显示"高批价占比"
    high_price_ratio = high_price_order_total / sales_amount if sales_amount > 0 else 0

    # 平均折扣率（按金额加权）- 用于UI显示"批价率"
    avg_discount_rate = total_discount_weight / total_order_amount if total_order_amount > 0 else 0

    return {
        'sales_amount': sales_amount / 10000,  # 转万元
        'high_price_amount': high_price_amount / 10000,        # 超出部分累计（提成基数）
        'high_price_order_total': high_price_order_total / 10000,  # 高批价订单总额
        'high_price_ratio': high_price_ratio,                  # 高批价占比（金额占比）
        'avg_discount_rate': avg_discount_rate,                # 平均折扣率（批价率）
        'high_price_commission': high_price_commission / 10000,  # 按订单计算的提成汇总
        'order_count': len(orders)
    }


def calculate_annual_performance_from_orders(user_id, year):
    """
    从批价单实时计算年度业绩数据（替代 QuarterlyPerformanceData）

    统一数据源：月度、季度、年度都从批价单计算，确保数据一致性

    Returns:
        dict: {
            'annual_achievement': 年度销售额（万元）,
            'high_price_achievement': 高批价销售额（万元）- 超出部分累计,
            'high_price_commission': 年度提成汇总（按订单计算）,
            'quarterly_summary': 季度汇总列表
        }
    """
    monthly_data = []

    # 计算每月业绩
    for month in range(1, 13):
        perf = calculate_monthly_performance(user_id, year, month)
        monthly_data.append({
            'month': month,
            'sales_amount': perf['sales_amount'],
            'high_price_amount': perf['high_price_amount'],       # 超出部分
            'high_price_order_total': perf['high_price_order_total'],  # 高批价订单总额
            'high_price_ratio': perf['high_price_ratio'],         # 高批价占比
            'avg_discount_rate': perf['avg_discount_rate'],       # 平均折扣率
            'high_price_commission': perf['high_price_commission'],  # 按订单计算的提成
            'order_count': perf['order_count']
        })

    # 年度汇总
    annual_achievement = sum(m['sales_amount'] for m in monthly_data)
    high_price_achievement = sum(m['high_price_amount'] for m in monthly_data)
    high_price_order_total = sum(m['high_price_order_total'] for m in monthly_data)
    high_price_commission = sum(m['high_price_commission'] for m in monthly_data)

    # 年度高批价占比（高批价订单总额 / 总销售额）
    if annual_achievement > 0:
        avg_high_price_ratio = high_price_order_total / annual_achievement
    else:
        avg_high_price_ratio = 0

    # 按季度汇总
    quarterly_summary = []
    for quarter in range(1, 5):
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        quarter_months = monthly_data[start_month - 1:end_month]

        q_achievement = sum(m['sales_amount'] for m in quarter_months)
        q_high_price = sum(m['high_price_amount'] for m in quarter_months)
        q_high_price_order_total = sum(m['high_price_order_total'] for m in quarter_months)
        q_commission = sum(m['high_price_commission'] for m in quarter_months)

        # 季度高批价占比
        q_high_price_ratio = q_high_price_order_total / q_achievement if q_achievement > 0 else 0

        # 季度平均折扣率（按金额加权）
        q_total_sales = sum(m['sales_amount'] for m in quarter_months)
        if q_total_sales > 0:
            q_weighted_discount = sum(
                m['sales_amount'] * m['avg_discount_rate']
                for m in quarter_months if m['sales_amount'] > 0
            )
            q_avg_discount_rate = q_weighted_discount / q_total_sales
        else:
            q_avg_discount_rate = 0

        quarterly_summary.append({
            'quarter': quarter,
            'achievement': round(q_achievement, 2),
            'high_price_amount': round(q_high_price, 2),           # 超出部分累计
            'high_price_order_total': round(q_high_price_order_total, 2),  # 高批价订单总额
            'high_price_ratio': round(q_high_price_ratio, 4),      # 高批价占比（金额占比）
            'high_price_rate': round(q_avg_discount_rate, 4),      # 平均折扣率（批价率）
            'high_price_commission': round(q_commission, 4),        # 季度提成
            'completion_rate': 0,  # 需要目标值才能计算，后续在调用处填充
            'data_source': 'calculated'
        })

    return {
        'annual_achievement': round(annual_achievement, 2),
        'high_price_achievement': round(high_price_achievement, 2),
        'high_price_order_total': round(high_price_order_total, 2),
        'high_price_ratio': round(avg_high_price_ratio, 4),
        'high_price_commission': round(high_price_commission, 4),
        'quarterly_summary': quarterly_summary,
        'monthly_data': monthly_data
    }


def calculate_member_annual_commission(user_id, year):
    """
    计算成员年度高批价提成（原始提成，用于团队分成计算）

    Returns:
        float: 年度高批价提成总额（万元）
    """
    total_commission = 0
    for month in range(1, 13):
        perf = calculate_monthly_performance(user_id, year, month)
        total_commission += perf['high_price_commission']
    return total_commission


def calculate_team_performance(team_leader_id, year):
    """
    计算团队业绩数据（用于M级管理者的综合完成率计算）

    Returns:
        dict: {
            'team_target': 团队年度目标（万元）,
            'team_achievement': 团队年度业绩（万元）,
            'team_completion_rate': 团队完成率,
            'quarterly_data': 季度数据列表
        }
    """
    # 查找该用户作为负责人的团队
    team = SalesTeamConfig.query.filter_by(
        team_leader_id=team_leader_id,
        is_active=True
    ).first()

    if not team:
        return {
            'team_target': 0,
            'team_achievement': 0,
            'team_completion_rate': 0,
            'quarterly_data': [{'quarter': q, 'achievement': 0, 'target': 0, 'completion_rate': 0} for q in range(1, 5)],
            'member_count': 0
        }

    # 获取团队成员（按年份过滤）
    members = EmployeeSalaryConfig.query.filter_by(team_id=team.id, year=year).all()

    if not members:
        return {
            'team_target': 0,
            'team_achievement': 0,
            'team_completion_rate': 0,
            'quarterly_data': [{'quarter': q, 'achievement': 0, 'target': 0, 'completion_rate': 0} for q in range(1, 5)],
            'member_count': 0
        }

    # 汇总团队目标和业绩
    team_target = 0
    team_achievement = 0
    quarterly_data = []

    # 预先计算所有成员的年度业绩
    member_annual_perfs = {}
    for member in members:
        member_target = member.get_effective_value('annual_target', 0)
        team_target += member_target
        member_perf = calculate_annual_performance_from_orders(member.user_id, year)
        member_annual_perfs[member.user_id] = member_perf
        team_achievement += member_perf['annual_achievement']

    # 计算季度数据
    quarterly_target = team_target / 4 if team_target > 0 else 0
    for quarter in range(1, 5):
        q_achievement = 0
        for member in members:
            member_perf = member_annual_perfs[member.user_id]
            # 从季度汇总中获取该季度业绩
            q_data = member_perf['quarterly_summary'][quarter - 1]
            q_achievement += q_data['achievement']

        q_completion_rate = q_achievement / quarterly_target if quarterly_target > 0 else 0
        quarterly_data.append({
            'quarter': quarter,
            'achievement': round(q_achievement, 2),
            'target': round(quarterly_target, 2),
            'completion_rate': round(q_completion_rate, 4)
        })

    team_completion_rate = team_achievement / team_target if team_target > 0 else 0

    return {
        'team_target': round(team_target, 2),
        'team_achievement': round(team_achievement, 2),
        'team_completion_rate': round(team_completion_rate, 4),
        'quarterly_data': quarterly_data,
        'member_count': len(members)
    }


def calculate_monthly_salary_breakdown(employee_config, year):
    """
    计算1-12月的薪资明细
    所有计算规则从配置表获取：
    - SalaryStepRules: 阶梯规则（绩效系数、提成比例、年终奖月数）
    - SalaryBaseParams: 基础参数（年终奖阈值等）
    - EmployeeSalaryConfig: 员工个人配置（可覆盖职级默认值）

    绩效发放规则：季度发放，在季末月份（3、6、9、12月）显示该季度的绩效
    M级管理者：绩效使用综合完成率（个人权重 × 个人完成率 + 团队权重 × 团队完成率）
    """
    monthly_data = []
    ytd_total = 0
    ytd_achievement = 0
    ytd_target = 0

    # 从员工配置获取有效值（优先个人覆盖，否则使用职级默认）
    monthly_base = employee_config.get_effective_value('monthly_base_salary', 0)
    monthly_perf_base = employee_config.get_effective_value('monthly_performance_base', 0)
    annual_target = employee_config.get_effective_value('annual_target', 0)
    # 季度目标改为从绩效配置动态获取（不再硬编码 annual_target / 4）
    # quarterly_target 将在循环中按季度获取
    personal_weight = employee_config.get_effective_value('personal_weight', 1)
    team_weight = 1 - personal_weight

    # 获取员工个人的提成系数和年终奖系数（支持个人调整）
    commission_multiplier = float(employee_config.commission_rate_multiplier or 1)
    bonus_multiplier = float(employee_config.bonus_multiplier or 1)

    # 判断是否为M级管理者
    grade = employee_config.grade
    is_manager = grade and grade.grade_type == 'M'

    # M级管理者：获取团队季度数据
    team_quarterly_data = None
    if is_manager and team_weight > 0:
        team_perf = calculate_team_performance(employee_config.user_id, year)
        team_quarterly_data = {q['quarter']: q for q in team_perf['quarterly_data']}

    # 从基础参数表获取年终奖阈值（不硬编码0.9）
    bonus_threshold_param = SalaryBaseParams.query.filter_by(
        param_code='annual_bonus_threshold'
    ).first()
    bonus_threshold = float(bonus_threshold_param.param_value) if bonus_threshold_param else 0.9

    # 预先计算每月业绩数据，用于季度汇总
    monthly_perf_cache = {}
    for m in range(1, 13):
        monthly_perf_cache[m] = calculate_monthly_performance(employee_config.user_id, year, m)

    for month in range(1, 13):
        # 1. 基础工资（固定）
        base_salary = monthly_base / 10000  # 转万元

        # 2. 获取月度目标（优先月度配置 → 季度平摊 → 年度平摊）
        monthly_target = get_monthly_target(employee_config, year, month)

        # 3. 获取月度业绩（从缓存获取）
        perf_data = monthly_perf_cache[month]
        monthly_achievement = perf_data['sales_amount']

        # 4. 计算当月完成率（用于显示，非用于绩效计算）
        monthly_completion_rate = monthly_achievement / monthly_target if monthly_target > 0 else 0

        # 5. 绩效工资（季度发放：仅在季末月份3、6、9、12显示）
        # M级管理者：使用综合季度完成率（个人权重 × 个人 + 团队权重 × 团队）
        performance_salary = 0
        perf_coefficient = 0
        quarterly_completion_rate = 0
        comprehensive_quarterly_rate = 0
        team_quarterly_rate = 0

        if month in [3, 6, 9, 12]:
            # 季末月份：计算该季度的绩效
            quarter = month // 3
            quarter_start = (quarter - 1) * 3 + 1
            quarter_end = quarter * 3

            # 从绩效配置获取该季度的目标（优先绩效配置，否则年度目标/4）
            quarterly_target = get_quarterly_target_from_performance_config(
                employee_config.user_id, year, quarter, annual_target
            )

            # 汇总个人季度业绩
            quarterly_achievement = sum(
                monthly_perf_cache[m]['sales_amount']
                for m in range(quarter_start, quarter_end + 1)
            )

            # 个人季度完成率
            quarterly_completion_rate = quarterly_achievement / quarterly_target if quarterly_target > 0 else 0

            # 计算综合季度完成率（M级考虑团队权重）
            if is_manager and team_quarterly_data and team_weight > 0:
                team_q_data = team_quarterly_data.get(quarter, {})
                team_quarterly_rate = team_q_data.get('completion_rate', 0)
                comprehensive_quarterly_rate = (
                    quarterly_completion_rate * personal_weight +
                    team_quarterly_rate * team_weight
                )
            else:
                comprehensive_quarterly_rate = quarterly_completion_rate

            # 用综合季度完成率查阶梯表
            perf_coefficient = SalaryStepRules.get_coefficient('performance_coefficient', comprehensive_quarterly_rate * 100)

            # 季度绩效 = 月绩效基数 × 3个月 × 系数
            performance_salary = monthly_perf_base * 3 * perf_coefficient / 10000

        # 6. 个人提成（季度发放：仅在季末月份显示，汇总该季度所有订单提成）
        # 不乘以发放系数，直接按订单计算后汇总
        personal_commission = 0
        quarterly_commission = 0
        team_share_commission = 0  # 团队分成（M级管理者从下属获得）
        team_deduction_rate = 0  # 团队分成扣减比例（团队成员需上交的比例）

        # 检查是否需要扣除团队分成（团队成员需要上交部分提成给负责人）
        member_team = employee_config.team
        if member_team and member_team.team_leader_id and member_team.team_leader_id != employee_config.user_id:
            # 获取团队负责人的配置，读取分成比例
            leader_config = EmployeeSalaryConfig.query.filter_by(
                user_id=member_team.team_leader_id
            ).first()
            if leader_config:
                team_deduction_rate = float(leader_config.team_share_rate_override or 20) / 100

        if month in [3, 6, 9, 12]:
            # 季末月份：汇总该季度的提成
            quarter = month // 3
            quarter_start = (quarter - 1) * 3 + 1
            quarter_end = quarter * 3

            # 汇总季度内所有订单的提成
            quarterly_commission = sum(
                monthly_perf_cache[m]['high_price_commission']
                for m in range(quarter_start, quarter_end + 1)
            )
            # 乘以个人提成系数，并扣除团队分成（如果是团队成员）
            personal_commission = quarterly_commission * commission_multiplier * (1 - team_deduction_rate)

            # M级管理者：计算从下属获得的团队分成
            if is_manager:
                team_share_rate = float(employee_config.team_share_rate_override or 20) / 100
                managed_team = SalesTeamConfig.query.filter_by(
                    team_leader_id=employee_config.user_id,
                    is_active=True
                ).first()

                if managed_team:
                    for member in managed_team.members:
                        if member.user_id == employee_config.user_id:
                            continue  # 跳过自己

                        # 计算成员该季度的高批价提成
                        member_quarterly_commission = sum(
                            calculate_monthly_performance(member.user_id, year, m)['high_price_commission']
                            for m in range(quarter_start, quarter_end + 1)
                        )
                        member_multiplier = float(member.commission_rate_multiplier or 1)
                        # 负责人分成 = 成员提成 × 成员系数 × 分成比例
                        team_share_commission += member_quarterly_commission * member_multiplier * team_share_rate

        # 7. 年终奖计提（从阶梯规则表获取月数，乘以个人系数）
        ytd_achievement += monthly_achievement
        ytd_target += monthly_target
        ytd_completion_rate = ytd_achievement / ytd_target if ytd_target > 0 else 0

        bonus_accrual = 0
        if ytd_completion_rate >= bonus_threshold:
            # 从阶梯规则表获取年终奖月数（阈值为百分比形式）
            bonus_months = SalaryStepRules.get_coefficient('annual_bonus', ytd_completion_rate * 100)
            # 按月份比例预提，乘以个人年终奖系数
            bonus_accrual = monthly_base * bonus_months * bonus_multiplier * (month / 12) / 10000

        # 8. 月合计（包含团队分成）
        monthly_total = base_salary + performance_salary + personal_commission + team_share_commission + bonus_accrual
        ytd_total += monthly_total

        monthly_data.append({
            'month': month,
            'base_salary': round(base_salary, 4),
            'performance_salary': round(performance_salary, 4),
            'personal_commission': round(personal_commission, 4),
            'team_share_commission': round(team_share_commission, 4),  # 团队分成（M级在季末显示）
            'bonus_accrual': round(bonus_accrual, 4),
            'monthly_total': round(monthly_total, 4),
            'ytd_total': round(ytd_total, 4),

            # 计算依据（用于前端悬浮提示）
            'monthly_target': round(monthly_target, 2),
            'monthly_achievement': round(monthly_achievement, 2),
            'monthly_completion_rate': round(monthly_completion_rate, 4),
            'quarterly_completion_rate': round(quarterly_completion_rate, 4),  # 个人季度完成率
            'team_quarterly_rate': round(team_quarterly_rate, 4),  # 团队季度完成率（M级）
            'comprehensive_quarterly_rate': round(comprehensive_quarterly_rate, 4),  # 综合季度完成率（绩效计算依据）
            'perf_coefficient': perf_coefficient,
            'is_quarter_end': month in [3, 6, 9, 12],  # 是否季末月份
            'is_manager': is_manager,  # 是否M级管理者
            'team_deduction_rate': round(team_deduction_rate, 4),  # 团队分成扣减比例（团队成员）
            'high_price_amount': round(perf_data['high_price_amount'], 2),
            'high_price_ratio': round(perf_data['high_price_ratio'], 4),  # 高批价占比
            'avg_discount_rate': round(perf_data['avg_discount_rate'], 4),  # 平均折扣率
            'monthly_high_price_commission': round(perf_data['high_price_commission'], 4),  # 当月订单提成
            'quarterly_commission': round(quarterly_commission, 4),  # 季度提成汇总（季末显示）
            'commission_multiplier': commission_multiplier,
            'bonus_multiplier': bonus_multiplier,
            'ytd_completion_rate': round(ytd_completion_rate, 4)
        })

    return monthly_data


@api_v1_bp.route('/salary/grades', methods=['GET'])
@flexible_auth
def get_salary_grades():
    """获取所有可用职级列表

    Returns:
        JSON: 包含L级和M级职级列表
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    try:
        # 获取所有激活的职级配置
        grades = SalaryGradeConfig.query.filter_by(is_active=True).order_by(
            SalaryGradeConfig.grade_type,
            SalaryGradeConfig.sort_order
        ).all()

        # 按类型分组
        l_grades = []
        m_grades = []

        for grade in grades:
            grade_data = {
                'id': grade.id,
                'code': grade.grade_code,
                'name': grade.grade_name,
                'type': grade.grade_type,
                'annual_target': float(grade.annual_target) if grade.annual_target else 0,
                'monthly_base': float(grade.monthly_base_salary) if grade.monthly_base_salary else 0,
                'monthly_perf': float(grade.monthly_performance_base) if grade.monthly_performance_base else 0,
                'personal_weight': float(grade.personal_weight) if grade.personal_weight else 1
            }

            # 获取带宽信息
            if grade.bandwidth:
                bw = grade.bandwidth
                grade_data['bandwidth'] = {
                    'base_salary_min': float(bw.base_salary_min) if bw.base_salary_min else None,
                    'base_salary_mid': float(bw.base_salary_mid) if bw.base_salary_mid else grade_data['monthly_base'],
                    'base_salary_max': float(bw.base_salary_max) if bw.base_salary_max else None,
                    'performance_base_min': float(bw.performance_base_min) if bw.performance_base_min else None,
                    'performance_base_mid': float(bw.performance_base_mid) if bw.performance_base_mid else grade_data['monthly_perf'],
                    'performance_base_max': float(bw.performance_base_max) if bw.performance_base_max else None,
                    'target_min': float(bw.target_min) if bw.target_min else None,
                    'target_mid': float(bw.target_mid) if bw.target_mid else grade_data['annual_target'],
                    'target_max': float(bw.target_max) if bw.target_max else None
                }

            if grade.grade_type == 'L':
                l_grades.append(grade_data)
            else:
                m_grades.append(grade_data)

        return api_response(
            success=True,
            message="获取成功",
            data={
                'l_grades': l_grades,
                'm_grades': m_grades,
                'all_grades': l_grades + m_grades
            }
        )

    except Exception as e:
        logger.error(f"获取职级列表失败: {e}")
        return api_response(success=False, code=500, message=f"获取失败: {str(e)}")


@api_v1_bp.route('/salary/user/<int:user_id>/annual-target', methods=['GET'])
@flexible_auth
def get_user_annual_target(user_id):
    """获取用户的年度销售目标（从薪资配置）

    用于绩效配置页面获取薪资配置中的年度目标（只读显示）

    Args:
        user_id: 用户ID

    Query Params:
        year: 年份（默认当前年）

    Returns:
        JSON: 包含年度目标值
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    year = request.args.get('year', datetime.now().year, type=int)

    try:
        # 查询用户薪资配置（按年份）
        config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()

        if config:
            # 获取有效的年度目标（优先个人覆盖，否则使用职级默认）
            annual_target = config.get_effective_value('annual_target', 0)
        else:
            # 没有薪资配置，尝试获取用户的职级默认值
            user = User.query.get(user_id)
            if user and user.role:
                # 根据用户角色查找对应的职级配置
                grade = SalaryGradeConfig.query.filter_by(
                    role_code=user.role,
                    is_active=True
                ).first()
                annual_target = float(grade.annual_target or 0) if grade else 0
            else:
                annual_target = 0

        return api_response(
            success=True,
            data={
                'user_id': user_id,
                'year': year,
                'annual_target': annual_target
            }
        )
    except Exception as e:
        logger.error(f"获取用户年度目标失败: {e}", exc_info=True)
        return api_response(success=False, code=500, message=f"获取失败: {str(e)}")


@api_v1_bp.route('/user/<int:user_id>/salary', methods=['GET'])
@flexible_auth
def get_user_salary_dashboard(user_id):
    """获取用户薪资看板数据

    Args:
        user_id: 目标用户ID

    Query Params:
        year: 年份（默认当前年）

    Returns:
        JSON: 包含薪资配置、概览、明细、季度数据等
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查
    if not check_salary_view_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户薪资数据")

    # 获取年份参数
    year = request.args.get('year', datetime.now().year, type=int)

    # 自动生成/确认当年已结算周期的快照
    current_year = datetime.now().year
    if year == current_year:
        auto_generate_and_confirm_snapshots(user_id, year)

    try:
        # 获取员工薪资配置（按年份过滤）
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()

        if not employee_config or not employee_config.grade_id:
            return api_response(
                success=True,
                message="获取成功",
                data={
                    'has_config': False,
                    'config': {},
                    'overview': {},
                    'breakdown': {},
                    'quarterly_data': [],
                    'team_share_details': []
                }
            )

        # 获取职级配置
        grade = employee_config.grade

        # 构建配置信息
        config_data = {
            'use_custom_config': employee_config.use_custom_config,
            'grade_code': grade.grade_code if grade else None,
            'grade_name': grade.grade_name if grade else None,
            'grade_type': grade.grade_type if grade else None,
            'team_name': employee_config.team.team_name if employee_config.team else None,
        }

        # 获取有效配置值
        monthly_base = employee_config.get_effective_value('monthly_base_salary', 0)
        monthly_perf = employee_config.get_effective_value('monthly_performance_base', 0)
        annual_target = employee_config.get_effective_value('annual_target', 0)
        personal_weight = employee_config.get_effective_value('personal_weight', 1)

        # 从批价单实时计算年度业绩（统一数据源）
        annual_perf = calculate_annual_performance_from_orders(user_id, year)
        annual_achievement = annual_perf['annual_achievement']

        # 计算年度完成率
        personal_completion_rate = annual_achievement / annual_target if annual_target > 0 else 0

        # 计算综合完成率（管理层考虑团队权重）
        team_weight = 1 - personal_weight
        team_completion_rate = 0
        team_perf_data = None

        # M级管理者：获取真实的团队完成率
        is_manager = grade and grade.grade_type == 'M'
        if is_manager and team_weight > 0:
            team_perf_data = calculate_team_performance(user_id, year)
            team_completion_rate = team_perf_data['team_completion_rate']

        # 构建季度汇总列表（使用综合完成率）
        # 季度目标从绩效配置动态获取
        team_quarterly_target = team_perf_data['team_target'] / 4 if team_perf_data and team_perf_data['team_target'] > 0 else 0
        quarterly_list = []

        for idx, q in enumerate(annual_perf['quarterly_summary']):
            quarter = q['quarter']
            # 从绩效配置获取该季度目标
            quarterly_target = get_quarterly_target_from_performance_config(
                user_id, year, quarter, annual_target
            )
            personal_q_achievement = q['achievement']
            personal_q_rate = personal_q_achievement / quarterly_target if quarterly_target > 0 else 0

            # M级：获取团队季度数据
            team_q_achievement = 0
            team_q_rate = 0
            if is_manager and team_perf_data and team_weight > 0:
                team_q_data = team_perf_data['quarterly_data'][idx]
                team_q_achievement = team_q_data['achievement']
                team_q_rate = team_q_data['completion_rate']

            # 综合完成率 = 个人完成率 × 个人权重 + 团队完成率 × 团队权重
            comprehensive_q_rate = personal_q_rate * personal_weight + team_q_rate * team_weight

            q_data = {
                'quarter': q['quarter'],
                'personal_achievement': round(personal_q_achievement, 2),  # 个人季度业绩
                'team_achievement': round(team_q_achievement, 2),  # 团队季度业绩（M级）
                'achievement': round(personal_q_achievement, 2),  # 兼容旧字段
                'personal_completion_rate': round(personal_q_rate, 4),  # 个人完成率
                'team_completion_rate': round(team_q_rate, 4),  # 团队完成率（M级）
                'completion_rate': round(comprehensive_q_rate, 4),  # 综合完成率（用于绩效计算）
                'is_manager': is_manager,
                'high_price_ratio': q.get('high_price_ratio', 0),
                'high_price_rate': q.get('high_price_rate', 0),
                'high_price_commission': q.get('high_price_commission', 0),
                'data_source': q.get('data_source', 'calculated')
            }
            quarterly_list.append(q_data)

        # 计算年度综合完成率
        if is_manager and team_weight > 0:
            comprehensive_rate = (
                personal_completion_rate * personal_weight +
                team_completion_rate * team_weight
            )
        else:
            comprehensive_rate = personal_completion_rate

        # 构建概览数据
        overview_data = {
            'annual_target': annual_target,
            'annual_achievement': annual_achievement,
            'personal_completion_rate': personal_completion_rate,
            'team_completion_rate': team_completion_rate,  # 团队完成率
            'comprehensive_completion_rate': comprehensive_rate,
            'personal_weight': personal_weight,
            'team_weight': team_weight,
            'is_manager': grade and grade.grade_type == 'M'
        }

        # 如果是M级，添加团队数据
        if team_perf_data:
            overview_data['team_target'] = team_perf_data['team_target']
            overview_data['team_achievement'] = team_perf_data['team_achievement']
            overview_data['team_member_count'] = team_perf_data['member_count']

        # 计算薪资明细
        # 年基础工资
        annual_base_salary = monthly_base * 12 / 10000  # 转换为万元

        # 管理津贴
        monthly_mgmt = 0
        if employee_config.use_custom_config and employee_config.monthly_management_allowance_override:
            monthly_mgmt = float(employee_config.monthly_management_allowance_override)
        management_allowance = monthly_mgmt * 12 / 10000

        # 绩效工资（季度发放：每个季度用综合季度完成率查表，然后汇总）
        # M级管理者：使用综合季度完成率（个人权重 × 个人 + 团队权重 × 团队）
        performance_salary = 0
        for idx, q_data in enumerate(annual_perf['quarterly_summary']):
            quarter = q_data['quarter']
            # 从绩效配置获取该季度目标
            quarterly_target = get_quarterly_target_from_performance_config(
                user_id, year, quarter, annual_target
            )
            # 个人季度完成率
            q_personal_rate = q_data['achievement'] / quarterly_target if quarterly_target > 0 else 0

            # 计算综合季度完成率（M级考虑团队权重）
            if grade and grade.grade_type == 'M' and team_perf_data and team_weight > 0:
                team_q_data = team_perf_data['quarterly_data'][idx]
                q_team_rate = team_q_data['completion_rate']
                q_comprehensive_rate = q_personal_rate * personal_weight + q_team_rate * team_weight
            else:
                q_comprehensive_rate = q_personal_rate

            # 用综合季度完成率查阶梯表
            q_perf_coefficient = SalaryStepRules.get_coefficient('performance_coefficient', q_comprehensive_rate * 100)
            # 季度绩效 = 月绩效基数 × 3个月 × 季度系数
            q_performance = monthly_perf * 3 * q_perf_coefficient / 10000
            performance_salary += q_performance

        # 获取高批价数据（从批价单实时计算）
        high_price_achievement = annual_perf['high_price_achievement']  # 超出部分累计（提成基数）
        high_price_commission = annual_perf['high_price_commission']    # 按订单计算的提成汇总

        # 批价提成（已按订单单独计算提成比例后汇总）
        commission_multiplier = float(employee_config.commission_rate_multiplier or 1)

        # 检查是否需要扣除团队分成（团队成员需要上交部分提成给负责人）
        team_deduction_rate = 0
        member_team = employee_config.team
        if member_team and member_team.team_leader_id and member_team.team_leader_id != employee_config.user_id:
            # 获取团队负责人的配置，读取分成比例
            leader_config = EmployeeSalaryConfig.query.filter_by(
                user_id=member_team.team_leader_id
            ).first()
            if leader_config:
                team_deduction_rate = float(leader_config.team_share_rate_override or 20) / 100

        # 成员提成 = 原提成 × 个人系数 × (1 - 分成比例)
        personal_commission = high_price_commission * commission_multiplier * (1 - team_deduction_rate)

        # 团队分成（管理层从下属提成中获取）
        team_commission_share = 0
        team_share_details = []
        if grade and grade.grade_type == 'M':
            # 获取自己的分成比例配置
            team_share_rate = float(employee_config.team_share_rate_override or 20) / 100

            # 查询自己负责的团队
            managed_team = SalesTeamConfig.query.filter_by(
                team_leader_id=employee_config.user_id,
                is_active=True
            ).first()

            if managed_team:
                # 计算每个成员的提成分成（按年份过滤）
                for member in managed_team.members.filter_by(year=year):
                    if member.user_id == employee_config.user_id:
                        continue  # 跳过自己

                    # 计算成员年度高批价提成（原始提成，未扣分成）
                    member_commission = calculate_member_annual_commission(member.user_id, year)
                    member_multiplier = float(member.commission_rate_multiplier or 1)
                    member_commission_with_multiplier = member_commission * member_multiplier

                    # 负责人分成 = 成员提成 × 分成比例
                    share_amount = member_commission_with_multiplier * team_share_rate
                    team_commission_share += share_amount

                    team_share_details.append({
                        'member_id': member.user_id,
                        'member_name': member.user.real_name if member.user else f'用户{member.user_id}',
                        'commission_base': round(member_commission_with_multiplier, 2),
                        'share_rate': team_share_rate,
                        'share_amount': round(share_amount, 2)
                    })

        # 提成（季度发放，不乘以发放系数）
        # 直接使用按订单计算后汇总的提成金额
        final_commission = personal_commission + team_commission_share

        # 年终奖（阈值为百分比形式）
        bonus_months = SalaryStepRules.get_coefficient('annual_bonus', comprehensive_rate * 100)
        bonus_multiplier = float(employee_config.bonus_multiplier or 1)
        annual_bonus = monthly_base * bonus_months * bonus_multiplier / 10000

        # 年总收入
        annual_total = annual_base_salary + management_allowance + performance_salary + final_commission + annual_bonus

        # 构建薪资明细数据
        breakdown_data = {
            'annual_base_salary': round(annual_base_salary, 4),
            'base_salary_formula': f'{int(monthly_base):,} × 12',
            'management_allowance': round(management_allowance, 4),
            'management_formula': f'{int(monthly_mgmt):,} × 12' if monthly_mgmt > 0 else None,
            'performance_salary': round(performance_salary, 4),
            'performance_formula': f'{int(monthly_perf):,} × 3 × Σ(季度系数)',
            'personal_commission': round(personal_commission, 4),  # 只显示个人提成部分
            'commission_formula': f'Σ订单提成({high_price_commission:.2f}) × {commission_multiplier}' + (f' × {1-team_deduction_rate:.0%}' if team_deduction_rate > 0 else ''),
            'team_commission_share': round(team_commission_share, 4),
            'team_share_rate': float(employee_config.team_share_rate_override or 20) / 100 if grade and grade.grade_type == 'M' else 0,
            'team_share_formula': f'Σ下属提成 × {int(employee_config.team_share_rate_override or 20)}%' if grade and grade.grade_type == 'M' and team_commission_share > 0 else None,
            'annual_bonus': round(annual_bonus, 4),
            'bonus_formula': f'{int(monthly_base):,} × {bonus_months}' if bonus_months > 0 else '综合完成率<90%，不发',
            'annual_total_income': round(annual_total, 4)
        }

        # 计算月度薪资明细
        monthly_data = calculate_monthly_salary_breakdown(employee_config, year)

        # 获取已有快照数据
        snapshots = {
            s.period_value: s
            for s in SalaryPeriodSnapshot.query.filter_by(
                user_id=user_id, year=year, period_type='monthly'
            ).all()
        }

        # 为每个月份添加快照状态标记
        for month_data in monthly_data:
            month = month_data['month']
            is_settled = is_period_settled(year, 'monthly', month)
            snapshot = snapshots.get(month)

            if is_settled and snapshot and snapshot.status in ['confirmed', 'published']:
                # 已结算 + 有锁定快照：使用快照数据
                month_data['is_snapshot'] = True
                month_data['is_settled'] = True
                month_data['snapshot_status'] = snapshot.status
                # 可选：用快照数据覆盖实时计算值（保持数据一致性）
                if snapshot.calculated_total:
                    month_data['monthly_total'] = float(snapshot.calculated_total)
                if snapshot.calculated_base_salary:
                    month_data['base_salary'] = float(snapshot.calculated_base_salary)
                if snapshot.calculated_performance_salary:
                    month_data['performance_salary'] = float(snapshot.calculated_performance_salary)
                if snapshot.calculated_commission:
                    month_data['personal_commission'] = float(snapshot.calculated_commission)
                if snapshot.calculated_team_share:
                    month_data['team_share_commission'] = float(snapshot.calculated_team_share)
            else:
                # 未结算或无快照：使用实时计算数据
                month_data['is_snapshot'] = False
                month_data['is_settled'] = is_settled
                month_data['snapshot_status'] = None

        # ========== 货币转换逻辑 ==========
        # 获取目标用户的结算货币
        target_user = User.query.get(user_id)
        user_currency = (target_user.settlement_currency if target_user else None) or Config.DEFAULT_CURRENCY

        # 默认使用系统货币信息
        from app.utils.i18n import get_currency_symbol as get_symbol
        from app.utils.currency_helpers import get_amount_unit_by_code, get_amount_divisor_by_code

        currency_symbol = get_symbol(user_currency)
        amount_unit = get_amount_unit_by_code(user_currency)

        # 如果用户货币与系统默认不同，进行汇率转换
        if user_currency != Config.DEFAULT_CURRENCY:
            from app.services.exchange_rate_service import exchange_rate_service

            # 获取系统默认除数和目标除数
            system_divisor = Config.AMOUNT_DIVISOR  # 10000 for CNY
            target_divisor = get_amount_divisor_by_code(user_currency)  # 1000 for HKD

            # 转换系数 = 系统除数 / 目标除数 × 汇率
            # 例如：CNY万元 → HKD K: 10000/1000 × 1.11 ≈ 11.1
            exchange_rate = exchange_rate_service.get_exchange_rate(Config.DEFAULT_CURRENCY, user_currency)
            conversion_factor = (system_divisor / target_divisor) * exchange_rate

            def convert_amount(amount):
                """转换金额（从系统货币单位到用户货币单位）"""
                if amount is None or amount == 0:
                    return amount
                return round(amount * conversion_factor, 4)

            # 转换 overview 中的金额
            overview_data['annual_target'] = convert_amount(overview_data.get('annual_target', 0))
            overview_data['annual_achievement'] = convert_amount(overview_data.get('annual_achievement', 0))
            if 'team_target' in overview_data:
                overview_data['team_target'] = convert_amount(overview_data['team_target'])
            if 'team_achievement' in overview_data:
                overview_data['team_achievement'] = convert_amount(overview_data['team_achievement'])

            # 转换 breakdown 中的金额
            amount_fields = ['annual_base_salary', 'management_allowance', 'performance_salary',
                           'personal_commission', 'team_commission_share', 'annual_bonus', 'annual_total_income']
            for field in amount_fields:
                if field in breakdown_data:
                    breakdown_data[field] = convert_amount(breakdown_data[field])

            # 转换季度数据
            for q in quarterly_list:
                q['personal_achievement'] = convert_amount(q.get('personal_achievement', 0))
                q['team_achievement'] = convert_amount(q.get('team_achievement', 0))
                q['achievement'] = convert_amount(q.get('achievement', 0))

            # 转换团队分成详情
            for detail in team_share_details:
                detail['commission_base'] = convert_amount(detail.get('commission_base', 0))
                detail['share_amount'] = convert_amount(detail.get('share_amount', 0))

            # 转换月度数据（月度数据是元，不是万元，需要不同的转换）
            # 月度薪资直接用汇率转换，不改变单位
            for month in monthly_data:
                for field in ['base_salary', 'performance_salary', 'personal_commission',
                             'team_share_commission', 'monthly_total']:
                    if field in month:
                        original = month[field]
                        if original and original != 0:
                            month[field] = round(original * exchange_rate, 2)

        return api_response(
            success=True,
            message="获取成功",
            data={
                'has_config': True,
                'config': config_data,
                'overview': overview_data,
                'breakdown': breakdown_data,
                'quarterly_data': quarterly_list,
                'team_share_details': team_share_details,
                'monthly_data': monthly_data,
                # 新增：返回货币信息供前端使用
                'currency': user_currency,
                'currency_symbol': currency_symbol,
                'amount_unit': amount_unit
            }
        )

    except Exception as e:
        logger.error(f"获取用户薪资数据失败: {e}")
        import traceback
        traceback.print_exc()
        return api_response(success=False, code=500, message=f"获取数据失败: {str(e)}")


@api_v1_bp.route('/user/<int:user_id>/salary/config', methods=['GET'])
@flexible_auth
def get_user_salary_config(user_id):
    """获取用户薪资配置详情（用于编辑模态框）

    Args:
        user_id: 目标用户ID

    Returns:
        JSON: 包含配置详情和带宽信息
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查
    if not check_salary_view_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户薪资配置")

    try:
        # 获取年份参数
        year = request.args.get('year', datetime.now().year, type=int)

        # 获取员工薪资配置（按年份筛选）
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()

        config_data = {}
        bandwidth_data = {}
        default_personal_weight = 1

        if employee_config:
            config_data = {
                'use_custom_config': employee_config.use_custom_config,
                'grade_id': employee_config.grade_id,
                'grade_code': employee_config.grade.grade_code if employee_config.grade else None,
                'grade_name': employee_config.grade.grade_name if employee_config.grade else None,
                'grade_type': employee_config.grade.grade_type if employee_config.grade else None,
                'monthly_base_salary_override': float(employee_config.monthly_base_salary_override) if employee_config.monthly_base_salary_override else None,
                'monthly_performance_base_override': float(employee_config.monthly_performance_base_override) if employee_config.monthly_performance_base_override else None,
                'monthly_management_allowance_override': float(employee_config.monthly_management_allowance_override) if employee_config.monthly_management_allowance_override else None,
                'annual_target_override': float(employee_config.annual_target_override) if employee_config.annual_target_override else None,
                'personal_weight_override': float(employee_config.personal_weight_override) if employee_config.personal_weight_override else None,
                'commission_rate_multiplier': float(employee_config.commission_rate_multiplier) if employee_config.commission_rate_multiplier else 1,
                'bonus_multiplier': float(employee_config.bonus_multiplier) if employee_config.bonus_multiplier else 1,
                'team_share_rate_override': float(employee_config.team_share_rate_override) if employee_config.team_share_rate_override else None,
                'config_notes': employee_config.config_notes,
                'configured_at': employee_config.configured_at.strftime('%Y-%m-%d %H:%M') if employee_config.configured_at else None,
                'configured_by_name': employee_config.configured_by_user.real_name if employee_config.configured_by_user else None
            }

            # 获取职级带宽
            if employee_config.grade:
                grade = employee_config.grade
                default_personal_weight = float(grade.personal_weight) if grade.personal_weight else 1

                if grade.bandwidth:
                    bw = grade.bandwidth
                    bandwidth_data = {
                        'base_salary_min': float(bw.base_salary_min) if bw.base_salary_min else None,
                        'base_salary_mid': float(bw.base_salary_mid) if bw.base_salary_mid else float(grade.monthly_base_salary) if grade.monthly_base_salary else None,
                        'base_salary_max': float(bw.base_salary_max) if bw.base_salary_max else None,
                        'performance_base_min': float(bw.performance_base_min) if bw.performance_base_min else None,
                        'performance_base_mid': float(bw.performance_base_mid) if bw.performance_base_mid else float(grade.monthly_performance_base) if grade.monthly_performance_base else None,
                        'performance_base_max': float(bw.performance_base_max) if bw.performance_base_max else None,
                        'target_min': float(bw.target_min) if bw.target_min else None,
                        'target_mid': float(bw.target_mid) if bw.target_mid else float(grade.annual_target) if grade.annual_target else None,
                        'target_max': float(bw.target_max) if bw.target_max else None
                    }
                else:
                    # 使用职级默认值作为中位值
                    bandwidth_data = {
                        'base_salary_min': None,
                        'base_salary_mid': float(grade.monthly_base_salary) if grade.monthly_base_salary else None,
                        'base_salary_max': None,
                        'performance_base_min': None,
                        'performance_base_mid': float(grade.monthly_performance_base) if grade.monthly_performance_base else None,
                        'performance_base_max': None,
                        'target_min': None,
                        'target_mid': float(grade.annual_target) if grade.annual_target else None,
                        'target_max': None
                    }

        # 获取团队成员和团队目标（如果是M级且有团队）
        team_members = []
        team_target = 0
        if employee_config and employee_config.grade:
            grade_type = employee_config.grade.grade_type
            if grade_type == 'M':
                # 查找该用户作为负责人的团队
                team = SalesTeamConfig.query.filter_by(
                    team_leader_id=user_id,
                    is_active=True
                ).first()
                if team:
                    # 获取团队成员（按年份过滤）
                    members = EmployeeSalaryConfig.query.filter_by(team_id=team.id, year=year).all()
                    for m in members:
                        # 获取成员的有效年度目标
                        member_target = m.annual_target_override
                        if member_target is None and m.grade:
                            member_target = m.grade.annual_target
                        team_members.append({
                            'id': m.user_id,
                            'real_name': m.user.real_name if m.user else None,
                            'username': m.user.username if m.user else None,
                            'annual_target': float(member_target) if member_target else 0
                        })
                        # 累加团队目标
                        if member_target:
                            team_target += float(member_target)

        return api_response(
            success=True,
            message="获取成功",
            data={
                'config': config_data,
                'bandwidth': bandwidth_data,
                'default_personal_weight': default_personal_weight,
                'team_members': team_members,
                'team_target': team_target
            }
        )

    except Exception as e:
        logger.error(f"获取用户薪资配置失败: {e}")
        return api_response(success=False, code=500, message=f"获取配置失败: {str(e)}")


@api_v1_bp.route('/user/<int:user_id>/salary/config', methods=['POST'])
@flexible_auth
def save_user_salary_config(user_id):
    """保存用户薪资配置

    Args:
        user_id: 目标用户ID

    Body:
        grade_id: 职级ID（必需，首次创建或更换职级时）
        use_custom_config: 是否使用自定义配置
        monthly_base_salary_override: 月基础工资覆盖
        monthly_performance_base_override: 月绩效基数覆盖
        monthly_management_allowance_override: 月管理津贴覆盖
        annual_target_override: 年度目标覆盖
        personal_weight_override: 个人权重覆盖
        commission_rate_multiplier: 提成比例系数
        bonus_multiplier: 年终奖系数
        team_share_rate_override: 团队分成比例覆盖
        config_notes: 配置备注

    Returns:
        JSON: 操作结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 权限检查
    if not check_salary_edit_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限编辑该用户薪资配置")

    try:
        data = request.get_json()
        logger.info(f"[DEBUG] save_user_salary_config 收到数据: user_id={user_id}, data={data}")
        logger.info(f"[DEBUG] annual_target_override in data: {'annual_target_override' in data}, value: {data.get('annual_target_override')}")
        if not data:
            return api_response(success=False, code=400, message="请求数据无效")

        # 获取年份参数
        year = data.get('year', datetime.now().year)

        # 获取或创建员工薪资配置（按年份）
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()
        is_new = False

        if not employee_config:
            # 创建新配置 - 必须提供grade_id
            grade_id = data.get('grade_id')
            if not grade_id:
                return api_response(success=False, code=400, message="首次配置必须选择职级")

            # 验证职级是否存在
            grade = SalaryGradeConfig.query.get(grade_id)
            if not grade or not grade.is_active:
                return api_response(success=False, code=400, message="无效的职级")

            employee_config = EmployeeSalaryConfig(
                user_id=user_id,
                grade_id=grade_id,
                year=year,  # 设置年份
                use_custom_config=False,
                commission_rate_multiplier=1,
                bonus_multiplier=1
            )
            db.session.add(employee_config)
            is_new = True

        # 更新职级（如果提供了grade_id）
        if 'grade_id' in data and data['grade_id']:
            new_grade_id = data['grade_id']
            if new_grade_id != employee_config.grade_id:
                # 验证职级是否存在
                grade = SalaryGradeConfig.query.get(new_grade_id)
                if not grade or not grade.is_active:
                    return api_response(success=False, code=400, message="无效的职级")
                employee_config.grade_id = new_grade_id
                # 更换职级时清除所有覆盖值，使用新职级默认值
                employee_config.monthly_base_salary_override = None
                employee_config.monthly_performance_base_override = None
                employee_config.monthly_management_allowance_override = None
                employee_config.annual_target_override = None
                employee_config.personal_weight_override = None
                employee_config.commission_rate_multiplier = 1
                employee_config.bonus_multiplier = 1
                employee_config.team_share_rate_override = None
                employee_config.use_custom_config = False

        # 更新配置模式
        use_custom = data.get('use_custom_config', False)
        employee_config.use_custom_config = use_custom

        if use_custom:
            # 更新覆盖值
            if 'monthly_base_salary_override' in data:
                employee_config.monthly_base_salary_override = data['monthly_base_salary_override']
            if 'monthly_performance_base_override' in data:
                employee_config.monthly_performance_base_override = data['monthly_performance_base_override']
            if 'monthly_management_allowance_override' in data:
                employee_config.monthly_management_allowance_override = data['monthly_management_allowance_override']
            if 'annual_target_override' in data:
                employee_config.annual_target_override = data['annual_target_override']
            if 'personal_weight_override' in data:
                employee_config.personal_weight_override = data['personal_weight_override']
            if 'commission_rate_multiplier' in data:
                employee_config.commission_rate_multiplier = data['commission_rate_multiplier']
            if 'bonus_multiplier' in data:
                employee_config.bonus_multiplier = data['bonus_multiplier']
            if 'team_share_rate_override' in data:
                employee_config.team_share_rate_override = data['team_share_rate_override']
        else:
            # 清除所有覆盖值
            employee_config.monthly_base_salary_override = None
            employee_config.monthly_performance_base_override = None
            employee_config.monthly_management_allowance_override = None
            employee_config.annual_target_override = None
            employee_config.personal_weight_override = None
            employee_config.commission_rate_multiplier = 1
            employee_config.bonus_multiplier = 1
            employee_config.team_share_rate_override = None

        employee_config.config_notes = data.get('config_notes')
        employee_config.configured_by = auth_user.id
        employee_config.configured_at = datetime.utcnow()

        # 处理团队成员（M级）
        if 'team_member_ids' in data:
            team_member_ids = data.get('team_member_ids', [])

            # 验证所有成员都有当年的薪资配置
            if team_member_ids:
                missing_configs = []
                for member_id in team_member_ids:
                    member_config = EmployeeSalaryConfig.query.filter_by(user_id=member_id, year=year).first()
                    if not member_config:
                        user = User.query.get(member_id)
                        missing_configs.append(user.real_name or user.username if user else str(member_id))

                if missing_configs:
                    return api_response(
                        success=False,
                        code=400,
                        message=f"以下成员需要先配置薪资: {', '.join(missing_configs)}"
                    )

            # 查找或创建团队配置
            team = SalesTeamConfig.query.filter_by(
                team_leader_id=user_id,
                is_active=True
            ).first()

            if not team and team_member_ids:
                # 创建新团队
                user = User.query.get(user_id)
                team = SalesTeamConfig(
                    team_name=f"{user.real_name or user.username}的团队",
                    team_leader_id=user_id,
                    leader_grade=employee_config.grade.grade_code if employee_config.grade else None,
                    is_active=True
                )
                db.session.add(team)
                db.session.flush()

            if team:
                # 清除当年旧的团队成员关系
                EmployeeSalaryConfig.query.filter_by(team_id=team.id, year=year).update({'team_id': None})

                # 设置新的团队成员关系（当年配置）
                for member_id in team_member_ids:
                    member_config = EmployeeSalaryConfig.query.filter_by(user_id=member_id, year=year).first()
                    if member_config:
                        member_config.team_id = team.id

        db.session.commit()

        return api_response(
            success=True,
            message="薪资配置保存成功" if not is_new else "薪资配置创建成功",
            data={
                'user_id': user_id,
                'grade_id': employee_config.grade_id,
                'use_custom_config': employee_config.use_custom_config,
                'is_new': is_new
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"保存用户薪资配置失败: {e}")
        return api_response(success=False, code=500, message=f"保存失败: {str(e)}")


@api_v1_bp.route('/user/<int:user_id>/salary/config/impact', methods=['GET'])
@flexible_auth
def get_config_change_impact(user_id):
    """获取配置修改的影响范围

    用于管理员修改配置前弹出提示，显示哪些周期会受影响。

    Args:
        user_id: 目标用户ID

    Returns:
        JSON: {
            'affected_periods': [draft状态的快照列表],
            'locked_periods': [confirmed/published状态的快照列表]
        }
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    if not check_salary_edit_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限")

    try:
        year = datetime.now().year

        # 获取所有相关快照
        snapshots = SalaryPeriodSnapshot.query.filter_by(
            user_id=user_id, year=year
        ).all()

        affected = []
        locked = []

        for s in snapshots:
            period_info = {
                'year': s.year,
                'type': s.period_type,
                'value': s.period_value,
                'status': s.status,
                'month_name': f'{s.period_value}月' if s.period_type == 'monthly' else f'Q{s.period_value}'
            }

            if s.status in ['confirmed', 'published']:
                locked.append(period_info)
            else:
                affected.append(period_info)

        return api_response(
            success=True,
            data={
                'affected_periods': affected,
                'locked_periods': locked,
                'year': year
            }
        )

    except Exception as e:
        logger.error(f"获取配置影响范围失败: {e}")
        return api_response(success=False, code=500, message=f"获取失败: {str(e)}")


@api_v1_bp.route('/user/<int:user_id>/salary/config/update-snapshots', methods=['POST'])
@flexible_auth
def update_snapshots_after_config_change(user_id):
    """配置修改后更新快照

    仅管理员调用，用于个人配置修改后重新计算并更新 draft 状态的快照。
    confirmed/published 状态的快照不受影响。

    Args:
        user_id: 目标用户ID

    Returns:
        JSON: 更新结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 只有管理员可以触发快照更新
    if auth_user.role != 'admin':
        return api_response(success=False, code=403, message="仅管理员可执行此操作")

    if not check_salary_edit_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限")

    try:
        year = datetime.now().year

        # 获取员工配置（按年份过滤）
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()
        if not employee_config:
            return api_response(success=False, code=404, message="用户薪资配置不存在")

        # 重新计算月度数据
        monthly_data = calculate_monthly_salary_breakdown(employee_config, year)

        # 获取所有 draft 状态的快照
        draft_snapshots = SalaryPeriodSnapshot.query.filter_by(
            user_id=user_id, year=year, period_type='monthly', status='draft'
        ).all()

        updated_count = 0
        for snapshot in draft_snapshots:
            month = snapshot.period_value
            # 找到对应月份的计算数据
            month_data = next((m for m in monthly_data if m['month'] == month), None)
            if month_data:
                snapshot.calculated_base_salary = month_data.get('base_salary', 0)
                snapshot.calculated_performance_salary = month_data.get('performance_salary', 0)
                snapshot.calculated_commission = month_data.get('personal_commission', 0)
                snapshot.calculated_team_share = month_data.get('team_share_commission', 0)
                snapshot.calculated_total = month_data.get('monthly_total', 0)
                snapshot.calculation_params = {
                    'monthly_target': month_data.get('monthly_target', 0),
                    'monthly_achievement': month_data.get('monthly_achievement', 0),
                    'monthly_completion_rate': month_data.get('monthly_completion_rate', 0),
                    'is_quarter_end': month_data.get('is_quarter_end', False),
                    'grade_code': employee_config.grade.grade_code if employee_config.grade else None,
                    'updated_at': datetime.utcnow().isoformat()
                }
                snapshot.updated_at = datetime.utcnow()
                updated_count += 1

        db.session.commit()

        return api_response(
            success=True,
            message=f"已更新 {updated_count} 个快照",
            data={
                'updated_count': updated_count,
                'year': year
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新快照失败: {e}")
        return api_response(success=False, code=500, message=f"更新失败: {str(e)}")


@api_v1_bp.route('/user/<int:user_id>/salary/snapshots/recalculate', methods=['POST'])
@flexible_auth
def recalculate_snapshots(user_id):
    """
    重新计算指定范围的快照（管理员专用）

    Body:
        from_month: 起始月份 (1-12)
        to_month: 结束月份 (1-12)
        year: 年份

    逻辑：
        1. 验证管理员权限
        2. 获取用户配置和目标年份的月度数据
        3. 对 from_month 到 to_month 的每个月：
           - 如果快照存在：更新计算值
           - 如果快照不存在：创建新快照
           - 状态设置：已结算月份设为 confirmed，未结算设为 draft
        4. 提交数据库更改
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 只有管理员可以重新计算快照
    if auth_user.role != 'admin':
        return api_response(success=False, code=403, message="仅管理员可执行此操作")

    data = request.get_json() or {}
    from_month = data.get('from_month', 1)
    to_month = data.get('to_month', 12)
    year = data.get('year', datetime.now().year)

    # 验证月份范围
    from_month = max(1, min(12, int(from_month)))
    to_month = max(from_month, min(12, int(to_month)))

    try:
        # 获取员工配置（按年份过滤）
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()
        if not employee_config:
            return api_response(success=False, code=404, message="用户薪资配置不存在")

        # 重新计算月度数据
        monthly_data = calculate_monthly_salary_breakdown(employee_config, year)

        created_count = 0
        updated_count = 0

        for month in range(from_month, to_month + 1):
            month_data = next((m for m in monthly_data if m['month'] == month), None)
            if not month_data:
                continue

            # 判断该月是否已结算
            is_settled = is_period_settled(year, 'monthly', month)

            # 查找或创建快照
            snapshot = SalaryPeriodSnapshot.query.filter_by(
                user_id=user_id, year=year, period_type='monthly', period_value=month
            ).first()

            if snapshot:
                # 更新现有快照
                snapshot.calculated_base_salary = month_data.get('base_salary', 0)
                snapshot.calculated_performance_salary = month_data.get('performance_salary', 0)
                snapshot.calculated_commission = month_data.get('personal_commission', 0)
                snapshot.calculated_team_share = month_data.get('team_share_commission', 0)
                snapshot.calculated_total = month_data.get('monthly_total', 0)
                snapshot.status = 'confirmed' if is_settled else 'draft'
                snapshot.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # 创建新快照
                new_snapshot = SalaryPeriodSnapshot(
                    user_id=user_id,
                    year=year,
                    period_type='monthly',
                    period_value=month,
                    calculated_base_salary=month_data.get('base_salary', 0),
                    calculated_performance_salary=month_data.get('performance_salary', 0),
                    calculated_commission=month_data.get('personal_commission', 0),
                    calculated_team_share=month_data.get('team_share_commission', 0),
                    calculated_total=month_data.get('monthly_total', 0),
                    status='confirmed' if is_settled else 'draft',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(new_snapshot)
                created_count += 1

        db.session.commit()

        return api_response(
            success=True,
            message=f"已更新 {updated_count} 个快照，新建 {created_count} 个快照",
            data={
                'updated_count': updated_count,
                'created_count': created_count,
                'from_month': from_month,
                'to_month': to_month,
                'year': year
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"重新计算快照失败: {e}")
        return api_response(success=False, code=500, message=f"重新计算失败: {str(e)}")


# ===================== 薪资快照 API =====================

@api_v1_bp.route('/user/<int:user_id>/salary/snapshots', methods=['GET'])
@flexible_auth
def get_user_salary_snapshots(user_id):
    """获取用户的薪资快照列表

    Args:
        user_id: 目标用户ID
        year: 年份（可选，默认当前年份）

    Returns:
        JSON: 快照列表
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    if not check_salary_view_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限访问该用户薪资快照")

    try:
        year = request.args.get('year', datetime.now().year, type=int)

        snapshots = SalaryPeriodSnapshot.query.filter_by(
            user_id=user_id,
            year=year
        ).order_by(SalaryPeriodSnapshot.period_type, SalaryPeriodSnapshot.period_value).all()

        return api_response(
            success=True,
            message="获取成功",
            data={
                'snapshots': [s.to_dict() for s in snapshots],
                'year': year
            }
        )

    except Exception as e:
        logger.error(f"获取用户薪资快照失败: {e}")
        return api_response(success=False, code=500, message=f"获取失败: {str(e)}")


@api_v1_bp.route('/user/<int:user_id>/salary/snapshots/create', methods=['POST'])
@flexible_auth
def create_salary_snapshot(user_id):
    """创建薪资快照

    Args:
        user_id: 目标用户ID

    Body:
        year: 年份
        period_type: 周期类型 ('monthly' 或 'quarterly')
        period_value: 周期值（月份1-12 或 季度1-4）

    Returns:
        JSON: 创建的快照信息
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 需要编辑权限来创建快照
    if not check_salary_edit_access(auth_user, user_id):
        return api_response(success=False, code=403, message="无权限创建薪资快照")

    try:
        data = request.get_json()
        if not data:
            return api_response(success=False, code=400, message="请求数据无效")

        year = data.get('year', datetime.now().year)
        period_type = data.get('period_type', 'monthly')
        period_value = data.get('period_value')

        if not period_value:
            return api_response(success=False, code=400, message="缺少周期值")

        if period_type == 'monthly' and (period_value < 1 or period_value > 12):
            return api_response(success=False, code=400, message="月份必须在1-12之间")
        if period_type == 'quarterly' and (period_value < 1 or period_value > 4):
            return api_response(success=False, code=400, message="季度必须在1-4之间")

        # 检查是否已存在快照
        existing = SalaryPeriodSnapshot.query.filter_by(
            user_id=user_id,
            year=year,
            period_type=period_type,
            period_value=period_value
        ).first()

        if existing:
            if existing.status == 'published':
                return api_response(success=False, code=400, message="该周期快照已发布，无法重新创建")
            # 已确认的快照也不能重新创建
            if existing.status == 'confirmed':
                return api_response(success=False, code=400, message="该周期快照已确认，如需重新计算请先取消确认")

        # 获取员工薪资配置（按年份过滤）
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()
        if not employee_config:
            return api_response(success=False, code=400, message="该用户没有薪资配置")

        # 计算薪资数据
        if period_type == 'monthly':
            # 月度快照
            monthly_data = calculate_monthly_salary_breakdown(employee_config, year)
            month_data = None
            for md in monthly_data:
                if md['month'] == period_value:
                    month_data = md
                    break

            if not month_data:
                return api_response(success=False, code=400, message="无法计算该月份数据")

            calculated_values = {
                'base_salary': month_data.get('base_salary', 0),
                'management_allowance': month_data.get('management_allowance', 0),
                'performance_salary': month_data.get('performance_salary', 0),
                'commission': month_data.get('commission', 0),
                'team_share': month_data.get('team_share_commission', 0),
                'total': month_data.get('month_total', 0)
            }

            # 保存计算参数
            calc_params = {
                'grade_code': employee_config.grade.grade_code if employee_config.grade else None,
                'monthly_target': month_data.get('monthly_target', 0),
                'achievement': month_data.get('achievement', 0),
                'completion_rate': month_data.get('completion_rate', 0),
                'is_quarter_end': month_data.get('is_quarter_end', False),
            }

        else:
            # 季度快照 - 汇总季度内各月数据
            monthly_data = calculate_monthly_salary_breakdown(employee_config, year)
            quarter_months = [(period_value - 1) * 3 + i for i in range(1, 4)]

            quarter_values = {
                'base_salary': 0,
                'management_allowance': 0,
                'performance_salary': 0,
                'commission': 0,
                'team_share': 0,
                'total': 0
            }

            for md in monthly_data:
                if md['month'] in quarter_months:
                    quarter_values['base_salary'] += md.get('base_salary', 0)
                    quarter_values['management_allowance'] += md.get('management_allowance', 0)
                    quarter_values['performance_salary'] += md.get('performance_salary', 0)
                    quarter_values['commission'] += md.get('commission', 0)
                    quarter_values['team_share'] += md.get('team_share_commission', 0)
                    quarter_values['total'] += md.get('month_total', 0)

            calculated_values = quarter_values
            calc_params = {
                'grade_code': employee_config.grade.grade_code if employee_config.grade else None,
                'quarter_months': quarter_months,
            }

        # 创建或更新快照
        if existing:
            snapshot = existing
            snapshot.calculated_base_salary = calculated_values['base_salary']
            snapshot.calculated_management_allowance = calculated_values['management_allowance']
            snapshot.calculated_performance_salary = calculated_values['performance_salary']
            snapshot.calculated_commission = calculated_values['commission']
            snapshot.calculated_team_share = calculated_values['team_share']
            snapshot.calculated_total = calculated_values['total']
            snapshot.calculation_params = calc_params
            snapshot.updated_at = datetime.utcnow()
        else:
            snapshot = SalaryPeriodSnapshot(
                user_id=user_id,
                year=year,
                period_type=period_type,
                period_value=period_value,
                calculated_base_salary=calculated_values['base_salary'],
                calculated_management_allowance=calculated_values['management_allowance'],
                calculated_performance_salary=calculated_values['performance_salary'],
                calculated_commission=calculated_values['commission'],
                calculated_team_share=calculated_values['team_share'],
                calculated_total=calculated_values['total'],
                calculation_params=calc_params,
                status='draft',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(snapshot)

        db.session.commit()

        return api_response(
            success=True,
            message="快照创建成功",
            data=snapshot.to_dict()
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建薪资快照失败: {e}")
        import traceback
        traceback.print_exc()
        return api_response(success=False, code=500, message=f"创建失败: {str(e)}")


@api_v1_bp.route('/salary/snapshots/<int:snapshot_id>', methods=['GET'])
@flexible_auth
def get_salary_snapshot(snapshot_id):
    """获取单个快照详情

    Args:
        snapshot_id: 快照ID

    Returns:
        JSON: 快照详情
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    try:
        snapshot = SalaryPeriodSnapshot.query.get(snapshot_id)
        if not snapshot:
            return api_response(success=False, code=404, message="快照不存在")

        # 权限检查
        if not check_salary_view_access(auth_user, snapshot.user_id):
            return api_response(success=False, code=403, message="无权限访问该快照")

        return api_response(
            success=True,
            message="获取成功",
            data=snapshot.to_dict()
        )

    except Exception as e:
        logger.error(f"获取薪资快照失败: {e}")
        return api_response(success=False, code=500, message=f"获取失败: {str(e)}")


@api_v1_bp.route('/salary/snapshots/<int:snapshot_id>/confirm', methods=['POST'])
@flexible_auth
def confirm_salary_snapshot(snapshot_id):
    """确认薪资快照（锁定计算值）

    Args:
        snapshot_id: 快照ID

    Returns:
        JSON: 操作结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    try:
        snapshot = SalaryPeriodSnapshot.query.get(snapshot_id)
        if not snapshot:
            return api_response(success=False, code=404, message="快照不存在")

        # 权限检查
        if not check_salary_edit_access(auth_user, snapshot.user_id):
            return api_response(success=False, code=403, message="无权限确认该快照")

        if snapshot.status == 'published':
            return api_response(success=False, code=400, message="快照已发布，无法修改状态")

        snapshot.status = 'confirmed'
        snapshot.confirmed_at = datetime.utcnow()
        snapshot.confirmed_by = auth_user.id
        snapshot.updated_at = datetime.utcnow()

        db.session.commit()

        return api_response(
            success=True,
            message="快照已确认",
            data=snapshot.to_dict()
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"确认薪资快照失败: {e}")
        return api_response(success=False, code=500, message=f"确认失败: {str(e)}")


@api_v1_bp.route('/salary/snapshots/<int:snapshot_id>/unconfirm', methods=['POST'])
@flexible_auth
def unconfirm_salary_snapshot(snapshot_id):
    """取消确认薪资快照（解锁以便重新计算）

    Args:
        snapshot_id: 快照ID

    Returns:
        JSON: 操作结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    try:
        snapshot = SalaryPeriodSnapshot.query.get(snapshot_id)
        if not snapshot:
            return api_response(success=False, code=404, message="快照不存在")

        # 权限检查 - 需要管理员权限
        if auth_user.role != 'admin':
            return api_response(success=False, code=403, message="只有管理员可以取消确认快照")

        if snapshot.status == 'published':
            return api_response(success=False, code=400, message="快照已发布，无法取消确认")

        if snapshot.status != 'confirmed':
            return api_response(success=False, code=400, message="快照未确认")

        snapshot.status = 'draft'
        snapshot.confirmed_at = None
        snapshot.confirmed_by = None
        snapshot.updated_at = datetime.utcnow()

        db.session.commit()

        return api_response(
            success=True,
            message="已取消确认，可重新计算",
            data=snapshot.to_dict()
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"取消确认薪资快照失败: {e}")
        return api_response(success=False, code=500, message=f"操作失败: {str(e)}")


@api_v1_bp.route('/salary/snapshots/<int:snapshot_id>/publish', methods=['POST'])
@flexible_auth
def publish_salary_snapshot(snapshot_id):
    """发布薪资快照（最终锁定，不可修改）

    Args:
        snapshot_id: 快照ID

    Returns:
        JSON: 操作结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    try:
        snapshot = SalaryPeriodSnapshot.query.get(snapshot_id)
        if not snapshot:
            return api_response(success=False, code=404, message="快照不存在")

        # 权限检查 - 需要管理员或财务权限
        if auth_user.role not in ['admin', 'finance', 'finance_director']:
            return api_response(success=False, code=403, message="只有管理员或财务可以发布快照")

        if snapshot.status == 'published':
            return api_response(success=False, code=400, message="快照已发布")

        if snapshot.status != 'confirmed':
            return api_response(success=False, code=400, message="请先确认快照再发布")

        snapshot.status = 'published'
        snapshot.published_at = datetime.utcnow()
        snapshot.published_by = auth_user.id
        snapshot.updated_at = datetime.utcnow()

        db.session.commit()

        return api_response(
            success=True,
            message="快照已发布",
            data=snapshot.to_dict()
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"发布薪资快照失败: {e}")
        return api_response(success=False, code=500, message=f"发布失败: {str(e)}")


@api_v1_bp.route('/salary/snapshots/<int:snapshot_id>/adjust', methods=['POST'])
@flexible_auth
def adjust_salary_snapshot(snapshot_id):
    """财务调整薪资快照

    Args:
        snapshot_id: 快照ID

    Body:
        adjusted_base_salary: 调整后的基础工资（可选）
        adjusted_management_allowance: 调整后的管理津贴（可选）
        adjusted_performance_salary: 调整后的绩效工资（可选）
        adjusted_commission: 调整后的提成（可选）
        adjusted_team_share: 调整后的团队分成（可选）
        adjusted_total: 调整后的合计（可选）
        adjustment_reason: 调整原因（必填）

    Returns:
        JSON: 调整后的快照信息
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    try:
        snapshot = SalaryPeriodSnapshot.query.get(snapshot_id)
        if not snapshot:
            return api_response(success=False, code=404, message="快照不存在")

        # 权限检查 - 需要管理员或财务权限
        if auth_user.role not in ['admin', 'finance', 'finance_director']:
            return api_response(success=False, code=403, message="只有管理员或财务可以调整快照")

        if snapshot.status == 'published':
            return api_response(success=False, code=400, message="快照已发布，无法调整")

        data = request.get_json()
        if not data:
            return api_response(success=False, code=400, message="请求数据无效")

        # 调整原因必填
        adjustment_reason = data.get('adjustment_reason', '').strip()
        if not adjustment_reason:
            return api_response(success=False, code=400, message="请填写调整原因")

        # 更新调整值
        if 'adjusted_base_salary' in data:
            snapshot.adjusted_base_salary = data['adjusted_base_salary']
        if 'adjusted_management_allowance' in data:
            snapshot.adjusted_management_allowance = data['adjusted_management_allowance']
        if 'adjusted_performance_salary' in data:
            snapshot.adjusted_performance_salary = data['adjusted_performance_salary']
        if 'adjusted_commission' in data:
            snapshot.adjusted_commission = data['adjusted_commission']
        if 'adjusted_team_share' in data:
            snapshot.adjusted_team_share = data['adjusted_team_share']
        if 'adjusted_total' in data:
            snapshot.adjusted_total = data['adjusted_total']

        snapshot.adjustment_reason = adjustment_reason
        snapshot.adjusted_by = auth_user.id
        snapshot.adjusted_at = datetime.utcnow()
        snapshot.updated_at = datetime.utcnow()

        db.session.commit()

        return api_response(
            success=True,
            message="调整已保存",
            data=snapshot.to_dict()
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"调整薪资快照失败: {e}")
        return api_response(success=False, code=500, message=f"调整失败: {str(e)}")


@api_v1_bp.route('/salary/snapshots/<int:snapshot_id>/clear-adjustment', methods=['POST'])
@flexible_auth
def clear_salary_snapshot_adjustment(snapshot_id):
    """清除薪资快照的财务调整

    Args:
        snapshot_id: 快照ID

    Returns:
        JSON: 操作结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    try:
        snapshot = SalaryPeriodSnapshot.query.get(snapshot_id)
        if not snapshot:
            return api_response(success=False, code=404, message="快照不存在")

        # 权限检查 - 需要管理员权限
        if auth_user.role != 'admin':
            return api_response(success=False, code=403, message="只有管理员可以清除调整")

        if snapshot.status == 'published':
            return api_response(success=False, code=400, message="快照已发布，无法清除调整")

        # 清除所有调整值
        snapshot.adjusted_base_salary = None
        snapshot.adjusted_management_allowance = None
        snapshot.adjusted_performance_salary = None
        snapshot.adjusted_commission = None
        snapshot.adjusted_team_share = None
        snapshot.adjusted_total = None
        snapshot.adjustment_reason = None
        snapshot.adjusted_by = None
        snapshot.adjusted_at = None
        snapshot.updated_at = datetime.utcnow()

        db.session.commit()

        return api_response(
            success=True,
            message="调整已清除，恢复为系统计算值",
            data=snapshot.to_dict()
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"清除薪资快照调整失败: {e}")
        return api_response(success=False, code=500, message=f"操作失败: {str(e)}")


@api_v1_bp.route('/salary/snapshots/batch-create', methods=['POST'])
@flexible_auth
def batch_create_salary_snapshots():
    """批量创建薪资快照（为多个用户创建指定周期的快照）

    Body:
        user_ids: 用户ID列表
        year: 年份
        period_type: 周期类型 ('monthly' 或 'quarterly')
        period_value: 周期值

    Returns:
        JSON: 创建结果
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 批量操作需要管理员或财务权限
    if auth_user.role not in ['admin', 'finance', 'finance_director']:
        return api_response(success=False, code=403, message="只有管理员或财务可以批量创建快照")

    try:
        data = request.get_json()
        if not data:
            return api_response(success=False, code=400, message="请求数据无效")

        user_ids = data.get('user_ids', [])
        year = data.get('year', datetime.now().year)
        period_type = data.get('period_type', 'monthly')
        period_value = data.get('period_value')

        if not user_ids:
            return api_response(success=False, code=400, message="请选择用户")
        if not period_value:
            return api_response(success=False, code=400, message="请选择周期")

        success_count = 0
        failed_users = []

        for user_id in user_ids:
            try:
                # 检查用户是否有薪资配置（按年份过滤）
                employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()
                if not employee_config:
                    user = User.query.get(user_id)
                    failed_users.append({
                        'user_id': user_id,
                        'name': user.real_name if user else str(user_id),
                        'reason': '没有薪资配置'
                    })
                    continue

                # 检查是否已存在已确认/已发布的快照
                existing = SalaryPeriodSnapshot.query.filter_by(
                    user_id=user_id,
                    year=year,
                    period_type=period_type,
                    period_value=period_value
                ).first()

                if existing and existing.status in ['confirmed', 'published']:
                    user = User.query.get(user_id)
                    failed_users.append({
                        'user_id': user_id,
                        'name': user.real_name if user else str(user_id),
                        'reason': f'已存在{existing.status}状态的快照'
                    })
                    continue

                # 计算数据并创建快照
                if period_type == 'monthly':
                    monthly_data = calculate_monthly_salary_breakdown(employee_config, year)
                    month_data = None
                    for md in monthly_data:
                        if md['month'] == period_value:
                            month_data = md
                            break

                    if not month_data:
                        failed_users.append({
                            'user_id': user_id,
                            'name': employee_config.user.real_name if employee_config.user else str(user_id),
                            'reason': '无法计算该月份数据'
                        })
                        continue

                    calculated_values = {
                        'base_salary': month_data.get('base_salary', 0),
                        'management_allowance': month_data.get('management_allowance', 0),
                        'performance_salary': month_data.get('performance_salary', 0),
                        'commission': month_data.get('commission', 0),
                        'team_share': month_data.get('team_share_commission', 0),
                        'total': month_data.get('month_total', 0)
                    }
                else:
                    monthly_data = calculate_monthly_salary_breakdown(employee_config, year)
                    quarter_months = [(period_value - 1) * 3 + i for i in range(1, 4)]

                    calculated_values = {
                        'base_salary': 0,
                        'management_allowance': 0,
                        'performance_salary': 0,
                        'commission': 0,
                        'team_share': 0,
                        'total': 0
                    }

                    for md in monthly_data:
                        if md['month'] in quarter_months:
                            calculated_values['base_salary'] += md.get('base_salary', 0)
                            calculated_values['management_allowance'] += md.get('management_allowance', 0)
                            calculated_values['performance_salary'] += md.get('performance_salary', 0)
                            calculated_values['commission'] += md.get('commission', 0)
                            calculated_values['team_share'] += md.get('team_share_commission', 0)
                            calculated_values['total'] += md.get('month_total', 0)

                # 创建或更新快照
                if existing:
                    existing.calculated_base_salary = calculated_values['base_salary']
                    existing.calculated_management_allowance = calculated_values['management_allowance']
                    existing.calculated_performance_salary = calculated_values['performance_salary']
                    existing.calculated_commission = calculated_values['commission']
                    existing.calculated_team_share = calculated_values['team_share']
                    existing.calculated_total = calculated_values['total']
                    existing.updated_at = datetime.utcnow()
                else:
                    snapshot = SalaryPeriodSnapshot(
                        user_id=user_id,
                        year=year,
                        period_type=period_type,
                        period_value=period_value,
                        calculated_base_salary=calculated_values['base_salary'],
                        calculated_management_allowance=calculated_values['management_allowance'],
                        calculated_performance_salary=calculated_values['performance_salary'],
                        calculated_commission=calculated_values['commission'],
                        calculated_team_share=calculated_values['team_share'],
                        calculated_total=calculated_values['total'],
                        status='draft',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.session.add(snapshot)

                success_count += 1

            except Exception as e:
                user = User.query.get(user_id)
                failed_users.append({
                    'user_id': user_id,
                    'name': user.real_name if user else str(user_id),
                    'reason': str(e)
                })

        db.session.commit()

        return api_response(
            success=True,
            message=f"批量创建完成：成功 {success_count} 个，失败 {len(failed_users)} 个",
            data={
                'success_count': success_count,
                'failed_count': len(failed_users),
                'failed_users': failed_users
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量创建薪资快照失败: {e}")
        return api_response(success=False, code=500, message=f"批量创建失败: {str(e)}")


# ===================== 配置修改影响范围 API =====================

@api_v1_bp.route('/salary/config-change-impact', methods=['POST'])
@flexible_auth
def check_config_change_impact():
    """检查配置修改的影响范围

    用于在保存薪资配置前提醒用户修改将影响哪些数据。

    Body:
        change_type: 修改类型
            - 'grade': 修改职级默认配置
            - 'employee': 修改员工个人配置
            - 'step_rules': 修改阶梯规则
            - 'base_params': 修改基础参数
        target_id: 目标ID（职级ID或员工ID）
        year: 年份（可选，默认当前年）

    Returns:
        JSON: {
            'affected_users': 受影响的用户数,
            'affected_user_list': 受影响用户列表（最多10个）,
            'draft_snapshots': 草稿状态快照数,
            'confirmed_snapshots': 已确认快照数,
            'published_snapshots': 已发布快照数,
            'warning_level': 警告级别 ('low', 'medium', 'high'),
            'message': 提示信息
        }
    """
    auth_user = get_current_user_flexible()
    if not auth_user:
        return api_response(success=False, code=401, message="未认证")

    # 需要编辑权限
    if auth_user.role not in ['admin', 'finance', 'finance_director']:
        return api_response(success=False, code=403, message="无权限查看影响范围")

    try:
        data = request.get_json()
        if not data:
            return api_response(success=False, code=400, message="请求数据无效")

        change_type = data.get('change_type')
        target_id = data.get('target_id')
        year = data.get('year', datetime.now().year)

        if not change_type:
            return api_response(success=False, code=400, message="缺少修改类型")

        affected_user_ids = []
        affected_user_list = []

        # 根据修改类型确定受影响的用户
        if change_type == 'grade':
            # 修改职级配置：影响使用该职级的所有用户
            if not target_id:
                return api_response(success=False, code=400, message="缺少职级ID")

            employees = EmployeeSalaryConfig.query.filter_by(grade_id=target_id).all()
            for emp in employees:
                affected_user_ids.append(emp.user_id)
                if len(affected_user_list) < 10:
                    affected_user_list.append({
                        'id': emp.user_id,
                        'name': emp.user.real_name if emp.user else f'用户{emp.user_id}',
                        'use_custom': emp.use_custom_config
                    })

        elif change_type == 'employee':
            # 修改员工个人配置：只影响该员工
            if not target_id:
                return api_response(success=False, code=400, message="缺少员工ID")

            affected_user_ids = [target_id]
            user = User.query.get(target_id)
            if user:
                affected_user_list.append({
                    'id': target_id,
                    'name': user.real_name or user.username,
                    'use_custom': True
                })

        elif change_type == 'step_rules':
            # 修改阶梯规则：影响所有有薪资配置的用户
            employees = EmployeeSalaryConfig.query.filter(
                EmployeeSalaryConfig.grade_id.isnot(None)
            ).all()
            for emp in employees:
                affected_user_ids.append(emp.user_id)
                if len(affected_user_list) < 10:
                    affected_user_list.append({
                        'id': emp.user_id,
                        'name': emp.user.real_name if emp.user else f'用户{emp.user_id}',
                        'use_custom': emp.use_custom_config
                    })

        elif change_type == 'base_params':
            # 修改基础参数：影响所有有薪资配置的用户
            employees = EmployeeSalaryConfig.query.filter(
                EmployeeSalaryConfig.grade_id.isnot(None)
            ).all()
            for emp in employees:
                affected_user_ids.append(emp.user_id)
                if len(affected_user_list) < 10:
                    affected_user_list.append({
                        'id': emp.user_id,
                        'name': emp.user.real_name if emp.user else f'用户{emp.user_id}',
                        'use_custom': emp.use_custom_config
                    })

        else:
            return api_response(success=False, code=400, message="无效的修改类型")

        # 查询受影响用户的快照统计
        draft_count = 0
        confirmed_count = 0
        published_count = 0

        if affected_user_ids:
            # 草稿状态快照
            draft_count = SalaryPeriodSnapshot.query.filter(
                SalaryPeriodSnapshot.user_id.in_(affected_user_ids),
                SalaryPeriodSnapshot.year == year,
                SalaryPeriodSnapshot.status == 'draft'
            ).count()

            # 已确认快照
            confirmed_count = SalaryPeriodSnapshot.query.filter(
                SalaryPeriodSnapshot.user_id.in_(affected_user_ids),
                SalaryPeriodSnapshot.year == year,
                SalaryPeriodSnapshot.status == 'confirmed'
            ).count()

            # 已发布快照
            published_count = SalaryPeriodSnapshot.query.filter(
                SalaryPeriodSnapshot.user_id.in_(affected_user_ids),
                SalaryPeriodSnapshot.year == year,
                SalaryPeriodSnapshot.status == 'published'
            ).count()

        # 确定警告级别
        warning_level = 'low'
        if published_count > 0:
            warning_level = 'high'
        elif confirmed_count > 0:
            warning_level = 'medium'
        elif len(affected_user_ids) > 5:
            warning_level = 'medium'

        # 构建提示信息
        messages = []
        if len(affected_user_ids) > 0:
            messages.append(f'将影响 {len(affected_user_ids)} 位员工的薪资计算')
        if draft_count > 0:
            messages.append(f'{draft_count} 个草稿快照将需要重新计算')
        if confirmed_count > 0:
            messages.append(f'{confirmed_count} 个已确认快照可能需要重新审核')
        if published_count > 0:
            messages.append(f'⚠️ {published_count} 个已发布快照不会受影响（已锁定）')

        if not messages:
            messages.append('此修改不会影响任何现有数据')

        return api_response(
            success=True,
            message="获取成功",
            data={
                'affected_users': len(affected_user_ids),
                'affected_user_list': affected_user_list,
                'draft_snapshots': draft_count,
                'confirmed_snapshots': confirmed_count,
                'published_snapshots': published_count,
                'warning_level': warning_level,
                'message': '；'.join(messages)
            }
        )

    except Exception as e:
        logger.error(f"检查配置修改影响范围失败: {e}")
        import traceback
        traceback.print_exc()
        return api_response(success=False, code=500, message=f"检查失败: {str(e)}")
