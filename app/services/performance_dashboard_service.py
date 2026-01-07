"""绩效看板聚合服务

复用 PerformanceService 的计算逻辑，添加报销预算和活跃度评分功能。
"""

from datetime import datetime
from sqlalchemy import func, extract
from app import db
from app.models.expense import Expense, ExpenseDetail, EXPENSE_CATEGORIES
from app.models.expense_budget import ExpenseBudget, RoleExpenseBudget
from app.models.user import User
from app.models.action import Action, ActionReply
from app.models.customer import Company
from app.models.project import Project
from app.services.performance_service import PerformanceService
from app.models.salary_config import EmployeeSalaryConfig, QuarterlyPerformanceData, SalesTeamConfig
from app.models.performance_config import (
    RolePerformanceTarget, UserPerformanceTarget, PerformanceMetricsDefinition
)
from app.services.exchange_rate_service import exchange_rate_service
from config import Config
import logging

logger = logging.getLogger(__name__)


class PerformanceDashboardService:
    """绩效看板聚合服务 - 复用现有计算逻辑"""

    # 报销科目映射（用于预算对比）
    EXPENSE_CATEGORY_MAP = {
        'entertainment': ['entertainment'],  # 招待费
        'travel': ['travel_accommodation'],  # 差旅住宿
        'transport': ['local_transport', 'fuel', 'parking'],  # 交通费（市内交通+油费+停车费）
        'office': ['office_supplies'],  # 办公费
        'communication': ['communication'],  # 通讯费
        'other': ['meals', 'other'],  # 其他
    }

    @staticmethod
    def _get_expense_scopes(user, year):
        """根据用户角色确定费用统计范围（支持多范围）

        返回用户所有适用的费用范围，始终包含个人:
        - 普通用户 → [个人]
        - 团队负责人 → [个人, 团队]
        - 部门负责人 → [个人, 部门]
        - 部门+团队负责人 → [个人, 团队, 部门]
        - CEO/Admin/Finance → [个人, 公司]

        Returns:
            list: 范围列表，每个元素为 (user_ids, scope_type, scope_name)
        """
        from app.models.performance_config import ConfigurablePerformanceService

        scopes = []

        # 1. CEO/Admin/Finance -> 个人 + 公司范围
        if user.role in ['ceo', 'admin', 'finance', 'finance_director', 'finace_director']:
            scopes.append(([user.id], 'personal', '个人'))
            user_ids = ConfigurablePerformanceService.get_user_ids_by_scope(user.id, 'company')
            scopes.append((user_ids, 'company', '公司'))
            return scopes

        # 2. 始终添加个人范围（第一位）
        scopes.append(([user.id], 'personal', '个人'))

        # 3. 团队负责人 -> 添加团队范围（第二位）
        team = SalesTeamConfig.query.filter(
            SalesTeamConfig.team_leader_id == user.id,
            SalesTeamConfig.is_active == True
        ).first()
        if team:
            member_configs = EmployeeSalaryConfig.query.filter(
                EmployeeSalaryConfig.team_id == team.id,
                EmployeeSalaryConfig.year == year
            ).all()
            member_ids = list(set([c.user_id for c in member_configs] + [user.id]))
            scopes.append((member_ids, 'team', team.team_name))

        # 4. 部门负责人 -> 添加部门范围（第三位）
        if user.is_department_manager and user.department:
            user_ids = ConfigurablePerformanceService.get_user_ids_by_scope(user.id, 'department')
            scopes.append((user_ids, 'department', user.department))

        return scopes

    @staticmethod
    def _get_expense_scope(user, year):
        """根据用户角色确定费用统计范围（单范围，向后兼容）

        Returns:
            tuple: (user_ids, scope_type, scope_name)
        """
        scopes = PerformanceDashboardService._get_expense_scopes(user, year)
        return scopes[0] if scopes else ([user.id], 'personal', '个人')

    @staticmethod
    def get_dashboard_data(user_id, year):
        """获取完整的看板数据

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            dict: 看板数据，包含：
                - summary: 年度汇总卡片数据
                - goal_achievement: 目标达成数据（月度趋势）
                - expense_budget: 报销预算对比
                - activity_score: 活跃度评分
                - industry_trend: 行业分布趋势
                - monthly_growth: 月度增长数据
                - customer_type_stats: 客户类型分布（全局）
                - customer_trend: 客户新增趋势（最近12个月）
                - customer_activity: 客户活跃度趋势
                - customer_value: 客户价值排名
        """
        try:
            # 复用现有服务获取年度统计
            yearly_stats = PerformanceService.get_yearly_statistics(user_id, year)
            # 行业分布使用全局模式（不按年份过滤，显示最近12个月）
            industry_stats = PerformanceService.get_monthly_industry_statistics(user_id)  # 全局模式

            # 从绩效目标配置获取目标数据（使用新的目标表）
            targets_dict = PerformanceDashboardService.get_user_kpi_targets(user_id, year)

            # 如果新目标表无数据，回退到薪资配置
            if not targets_dict:
                employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()
                if employee_config and employee_config.grade_id:
                    # 获取年度目标
                    annual_target = employee_config.get_effective_value('annual_target', 0)
                    monthly_targets_config = employee_config.monthly_targets or {}

                    for month in range(1, 13):
                        # 优先级: 1.月度配置 2.年度平摊
                        # 注意：薪资配置中目标单位是万元，需转换为元以匹配 PerformanceService
                        if str(month) in monthly_targets_config and monthly_targets_config[str(month)]:
                            monthly_target = float(monthly_targets_config[str(month)]) * 10000  # 万元→元
                        else:
                            monthly_target = (annual_target / 12 * 10000) if annual_target else 0  # 万元→元

                        targets_dict[month] = {
                            'sales_amount_target': monthly_target,  # 元
                            'implant_amount_target': 0,  # 植入额目标暂不设置
                            'new_customers_target': 0,
                            'new_projects_target': 0
                        }

            # 新增聚合逻辑
            # 获取费用预算范围（根据用户角色，支持多范围）
            user = User.query.get(user_id)
            expense_scopes = PerformanceDashboardService._get_expense_scopes(user, year)

            # 为每个范围获取费用预算数据
            expense_budgets = []
            current_month = datetime.now().month
            for scope_user_ids, scope_type, scope_name in expense_scopes:
                budget_data = PerformanceDashboardService.get_expense_budget_data(user_id, year, scope_user_ids)
                budget_data['scope_type'] = scope_type
                budget_data['scope_name'] = scope_name
                budget_data['current_month'] = current_month
                budget_data['current_year'] = year
                expense_budgets.append(budget_data)

            # 保持 expense_budget 为第一个范围（向后兼容）
            expense_budget = expense_budgets[0] if expense_budgets else PerformanceDashboardService._empty_expense_budget()

            # 活跃度使用全局模式（不按年份过滤，显示最近12个月）
            activity_score = PerformanceDashboardService.get_activity_score(user_id)  # 全局模式
            activity_monthly_trend = PerformanceDashboardService.get_monthly_activity_trend(user_id)  # 全局模式

            # 客户分布数据（全局模式，最近12个月）
            customer_type_stats = PerformanceService.calculate_customer_type_statistics(user_id)  # 全局模式
            customer_trend = PerformanceService.get_monthly_customer_statistics(user_id)  # 全局模式
            customer_activity = PerformanceDashboardService.get_customer_activity_trend(user_id)
            customer_value = PerformanceDashboardService.get_customer_value_ranking(user_id)

            # 汇总年度数据
            summary = PerformanceDashboardService._calculate_yearly_summary(yearly_stats, targets_dict)

            # 计算月度增长
            monthly_growth = PerformanceDashboardService._calculate_monthly_growth(yearly_stats)

            # 格式化目标达成数据
            goal_achievement = PerformanceDashboardService._format_goal_achievement(
                yearly_stats, targets_dict
            )

            # 检查是否为M级管理者并获取团队目标
            team_summary = PerformanceDashboardService._get_team_summary_for_manager(user_id, year)

            # 获取配置的绩效项目列表（用于前端动态列显示）
            configured_items = PerformanceDashboardService._get_configured_performance_items(user_id, year)

            return {
                'summary': summary,
                'team_summary': team_summary,
                'goal_achievement': goal_achievement,
                'expense_budget': expense_budget,
                'expense_budgets': expense_budgets,  # 多范围费用预算数据
                'activity_score': activity_score,
                'activity_monthly_trend': activity_monthly_trend,
                'industry_trend': industry_stats,
                'monthly_growth': monthly_growth,
                'configured_items': configured_items,
                # 客户分布数据
                'customer_type_stats': customer_type_stats,
                'customer_trend': customer_trend,
                'customer_activity': customer_activity,
                'customer_value': customer_value,
            }

        except Exception as e:
            logger.error(f"获取看板数据失败: {e}")
            empty_budget = PerformanceDashboardService._empty_expense_budget()
            return {
                'summary': PerformanceDashboardService._empty_summary(),
                'team_summary': None,
                'goal_achievement': [],
                'expense_budget': empty_budget,
                'expense_budgets': [empty_budget],  # 多范围费用预算数据
                'activity_score': PerformanceDashboardService._empty_activity_score(),
                'activity_monthly_trend': [],
                'industry_trend': {},
                'monthly_growth': [],
                'configured_items': ['implant_amount', 'sales_amount', 'new_customers', 'new_projects'],
                # 客户分布数据默认值
                'customer_type_stats': {},
                'customer_trend': {},
                'customer_activity': [],
                'customer_value': [],
            }

    @staticmethod
    def get_expense_budget_data(user_id, year, scope_user_ids=None):
        """获取报销预算数据

        Args:
            user_id: 用户ID
            year: 年份
            scope_user_ids: 可选，范围内的用户ID列表（用于团队/部门/公司汇总）

        Returns:
            dict: 报销预算数据
        """
        try:
            # 确定目标用户ID列表
            target_user_ids = scope_user_ids or [user_id]
            is_multi_user = len(target_user_ids) > 1

            # 汇总所有目标用户的预算
            budget_total = 0
            has_any_budget = False

            for uid in target_user_ids:
                # 获取个人预算
                user_budget = ExpenseBudget.query.filter_by(user_id=uid, year=year).first()
                if user_budget:
                    budget_total += float(user_budget.total_budget or 0)
                    has_any_budget = True
                else:
                    # 回退到角色默认预算
                    user = User.query.get(uid)
                    if user and user.role:
                        role_budget = RoleExpenseBudget.query.filter_by(
                            role_code=user.role, year=year
                        ).first()
                        if role_budget:
                            budget_total += float(role_budget.total_budget or 0)
                            has_any_budget = True

            # 获取已报销金额（已审批通过的，包括待支付和已支付）
            # 支持多货币转换：将所有报销单金额转换为系统基准货币后汇总
            base_currency = Config.DEFAULT_CURRENCY  # 系统基准货币（CNY）

            expenses = Expense.query.filter(
                Expense.owner_id.in_(target_user_ids),
                extract('year', Expense.created_at) == year,
                Expense.status.in_(['approved', 'awaiting_payment', 'paid']),
                Expense.is_deleted == False
            ).all()

            expense_total = 0.0
            for expense in expenses:
                amount = float(expense.total_amount or 0)
                # 如果报销单货币与系统基准货币不同，进行汇率转换
                if expense.currency and expense.currency != base_currency:
                    try:
                        amount = exchange_rate_service.convert_amount(
                            amount, expense.currency, base_currency
                        )
                    except Exception as conv_err:
                        logger.warning(f"报销单 {expense.id} 货币转换失败 {expense.currency} -> {base_currency}: {conv_err}")
                        # 转换失败时保持原值
                expense_total += amount

            # 按科目统计实际报销
            by_category = PerformanceDashboardService._get_expense_by_category(target_user_ids, year)

            # 计算月度趋势
            monthly_trend = PerformanceDashboardService._get_expense_monthly_trend(target_user_ids, year)

            # 计算使用率和剩余
            remaining = budget_total - expense_total
            usage_rate = (expense_total / budget_total * 100) if budget_total > 0 else 0

            # 按科目预算对比（多用户模式下汇总所有用户的分类预算）
            category_comparison = {}
            category_budgets_total = {}  # 汇总各分类预算

            for uid in target_user_ids:
                user_budget = ExpenseBudget.query.filter_by(user_id=uid, year=year).first()
                effective = user_budget
                if not effective:
                    u = User.query.get(uid)
                    if u and u.role:
                        effective = RoleExpenseBudget.query.filter_by(role_code=u.role, year=year).first()

                if effective:
                    cat_budgets = effective.get_category_budgets()
                    for cat_key, amount in cat_budgets.items():
                        category_budgets_total[cat_key] = category_budgets_total.get(cat_key, 0) + amount

            # 生成分类对比数据
            for cat_key, cat_budget in category_budgets_total.items():
                actual = by_category.get(cat_key, 0)
                category_comparison[cat_key] = {
                    'budget': cat_budget,
                    'expense': actual,
                    'actual': actual,
                    'remaining': cat_budget - actual,
                    'usage_rate': (actual / cat_budget * 100) if cat_budget > 0 else 0
                }

            return {
                'budget_total': budget_total,
                'expense_total': expense_total,
                'remaining': remaining,
                'usage_rate': round(usage_rate, 1),
                'by_category': by_category,
                'category_comparison': category_comparison,
                'monthly_trend': monthly_trend,
                'has_budget': has_any_budget,
                'is_multi_user': is_multi_user
            }

        except Exception as e:
            logger.error(f"获取报销预算数据失败: {e}")
            return PerformanceDashboardService._empty_expense_budget()

    @staticmethod
    def _get_expense_by_category(user_ids, year):
        """按科目统计实际报销金额（支持多货币转换）

        Args:
            user_ids: 用户ID或用户ID列表
            year: 年份
        """
        try:
            # 兼容单个ID和列表
            if not isinstance(user_ids, (list, tuple)):
                user_ids = [user_ids]

            base_currency = Config.DEFAULT_CURRENCY  # 系统基准货币（CNY）

            # 查询已审批的报销明细，同时获取报销单货币
            query = db.session.query(
                ExpenseDetail.expense_category,
                ExpenseDetail.current_amount,
                Expense.currency
            ).join(Expense).filter(
                Expense.owner_id.in_(user_ids),
                extract('year', Expense.created_at) == year,
                Expense.status.in_(['approved', 'awaiting_payment', 'paid']),
                Expense.is_deleted == False
            )

            # 按科目汇总，同时进行货币转换
            raw_totals = {}
            for row in query.all():
                category = row[0]
                amount = float(row[1] or 0)
                expense_currency = row[2] or base_currency

                # 货币转换
                if expense_currency != base_currency:
                    try:
                        amount = exchange_rate_service.convert_amount(
                            amount, expense_currency, base_currency
                        )
                    except Exception as conv_err:
                        logger.warning(f"分类统计货币转换失败 {expense_currency} -> {base_currency}: {conv_err}")

                raw_totals[category] = raw_totals.get(category, 0) + amount

            # 映射到预算科目
            result = {}
            for budget_cat, expense_cats in PerformanceDashboardService.EXPENSE_CATEGORY_MAP.items():
                total = sum(raw_totals.get(ec, 0) for ec in expense_cats)
                result[budget_cat] = round(total, 2)

            return result

        except Exception as e:
            logger.error(f"按科目统计报销失败: {e}")
            return {}

    @staticmethod
    def _get_expense_monthly_trend(user_ids, year):
        """获取月度报销趋势（支持多货币转换）

        Args:
            user_ids: 用户ID或用户ID列表
            year: 年份
        """
        try:
            # 兼容单个ID和列表
            if not isinstance(user_ids, (list, tuple)):
                user_ids = [user_ids]

            base_currency = Config.DEFAULT_CURRENCY  # 系统基准货币（CNY）

            # 查询每笔报销单的月份、金额和货币
            query = db.session.query(
                extract('month', Expense.created_at).label('month'),
                Expense.total_amount,
                Expense.currency
            ).filter(
                Expense.owner_id.in_(user_ids),
                extract('year', Expense.created_at) == year,
                Expense.status.in_(['approved', 'awaiting_payment', 'paid']),
                Expense.is_deleted == False
            )

            # 按月份汇总，同时进行货币转换
            monthly_data = {}
            for row in query.all():
                month = int(row[0])
                amount = float(row[1] or 0)
                expense_currency = row[2] or base_currency

                # 货币转换
                if expense_currency != base_currency:
                    try:
                        amount = exchange_rate_service.convert_amount(
                            amount, expense_currency, base_currency
                        )
                    except Exception as conv_err:
                        logger.warning(f"月度趋势货币转换失败 {expense_currency} -> {base_currency}: {conv_err}")

                monthly_data[month] = monthly_data.get(month, 0) + amount

            # 补全12个月
            trend = []
            cumulative = 0
            for month in range(1, 13):
                amount = monthly_data.get(month, 0)
                cumulative += amount
                trend.append({
                    'month': month,
                    'amount': round(amount, 2),
                    'cumulative': round(cumulative, 2)
                })

            return trend

        except Exception as e:
            logger.error(f"获取月度报销趋势失败: {e}")
            return []

    @staticmethod
    def get_activity_score(user_id, year=None, month=None, year_month=None):
        """计算活跃度评分

        评分维度（权重）：
        - 行动记录数 (30%): 满分50条/月或600条/年
        - 回复数 (10%): 满分30条/月或360条/年
        - 平均字数 (20%): 满分200字
        - 客户覆盖率 (20%): 拜访客户数/总客户数
        - 项目关联率 (20%): 关联项目的行动数/总行动数

        Args:
            user_id: 用户ID
            year: 年份（可选，None表示全局分析）
            month: 月份（可选，需配合year使用）
            year_month: 年月字符串格式 'YYYY-MM'（可选，用于跨年月份查询）

        Returns:
            dict: 活跃度评分数据
        """
        try:
            # 构建基础过滤条件
            action_filters = [Action.owner_id == user_id]

            # 支持三种模式：
            # 1. year_month: 跨年月份查询（优先级最高）
            # 2. year + month: 指定年月
            # 3. year: 指定年份
            # 4. 无参数: 全局分析（最近12个月基准）
            if year_month:
                # 解析 'YYYY-MM' 格式
                ym_year, ym_month = map(int, year_month.split('-'))
                action_filters.append(extract('year', Action.created_at) == ym_year)
                action_filters.append(extract('month', Action.created_at) == ym_month)
                base_action_count = 50
                base_reply_count = 30
            elif year is not None:
                action_filters.append(extract('year', Action.created_at) == year)
                if month:
                    action_filters.append(extract('month', Action.created_at) == month)
                base_action_count = 50 if month else 600
                base_reply_count = 30 if month else 360
            else:
                # 全局模式：使用最近12个月的基准
                base_action_count = 600
                base_reply_count = 360

            # 数量维度 - 行动记录数
            action_count = Action.query.filter(*action_filters).count()

            # 数量维度 - 回复数
            reply_filters = [ActionReply.owner_id == user_id]
            if year_month:
                ym_year, ym_month = map(int, year_month.split('-'))
                reply_filters.append(extract('year', ActionReply.created_at) == ym_year)
                reply_filters.append(extract('month', ActionReply.created_at) == ym_month)
            elif year is not None:
                reply_filters.append(extract('year', ActionReply.created_at) == year)
                if month:
                    reply_filters.append(extract('month', ActionReply.created_at) == month)
            reply_count = ActionReply.query.filter(*reply_filters).count()

            # 质量维度 - 平均字数
            avg_length_result = db.session.query(
                func.avg(func.length(Action.communication))
            ).filter(*action_filters).scalar()
            avg_length = float(avg_length_result or 0)

            # 质量维度 - 客户覆盖率
            total_customers = Company.query.filter(
                Company.owner_id == user_id,
                Company.is_deleted == False
            ).count()

            covered_customers = db.session.query(
                func.count(func.distinct(Action.company_id))
            ).filter(
                *action_filters,
                Action.company_id.isnot(None)
            ).scalar() or 0

            customer_coverage = (covered_customers / total_customers * 100) if total_customers > 0 else 0

            # 质量维度 - 项目关联率
            total_actions = action_count
            linked_actions = Action.query.filter(
                *action_filters,
                Action.project_id.isnot(None)
            ).count()
            project_link_rate = (linked_actions / total_actions * 100) if total_actions > 0 else 0

            # 各维度得分（0-100）
            action_score = min(action_count / base_action_count * 100, 100)
            reply_score = min(reply_count / base_reply_count * 100, 100)
            length_score = min(avg_length / 200 * 100, 100)
            coverage_score = min(customer_coverage, 100)
            link_score = min(project_link_rate, 100)

            # 综合评分（加权平均）
            score = (
                action_score * 0.3 +
                reply_score * 0.1 +
                length_score * 0.2 +
                coverage_score * 0.2 +
                link_score * 0.2
            )

            # 等级判定
            if score >= 80:
                grade = 'A'
                grade_text = '优秀'
            elif score >= 60:
                grade = 'B'
                grade_text = '良好'
            elif score >= 40:
                grade = 'C'
                grade_text = '一般'
            else:
                grade = 'D'
                grade_text = '待提升'

            return {
                'score': round(score, 1),
                'grade': grade,
                'grade_text': grade_text,
                'breakdown': {
                    'action_count': {
                        'value': action_count,
                        'target': base_action_count,
                        'score': round(action_score, 1),
                        'weight': 0.3
                    },
                    'reply_count': {
                        'value': reply_count,
                        'target': base_reply_count,
                        'score': round(reply_score, 1),
                        'weight': 0.1
                    },
                    'avg_length': {
                        'value': round(avg_length),
                        'target': 200,
                        'score': round(length_score, 1),
                        'weight': 0.2
                    },
                    'customer_coverage': {
                        'value': round(customer_coverage, 1),
                        'target': 100,
                        'score': round(coverage_score, 1),
                        'weight': 0.2
                    },
                    'project_link_rate': {
                        'value': round(project_link_rate, 1),
                        'target': 100,
                        'score': round(link_score, 1),
                        'weight': 0.2
                    },
                },
                'raw_data': {
                    'total_customers': total_customers,
                    'covered_customers': covered_customers,
                    'total_actions': total_actions,
                    'linked_actions': linked_actions,
                }
            }

        except Exception as e:
            logger.error(f"计算活跃度评分失败: {e}")
            return PerformanceDashboardService._empty_activity_score()

    @staticmethod
    def get_monthly_activity_trend(user_id, year=None):
        """获取月度活跃度趋势

        Args:
            user_id: 用户ID
            year: 年份（可选，None表示全局模式返回最近12个月）

        Returns:
            list: 月度活跃度数据列表
                - 指定年份模式: [{month: 1, score: ..., ...}, ...]
                - 全局模式: [{month: '2024-02', score: ..., ...}, ...]
        """
        try:
            trend = []

            if year is not None:
                # 指定年份模式：返回该年1-12月
                for month in range(1, 13):
                    score_data = PerformanceDashboardService.get_activity_score(user_id, year, month)
                    trend.append({
                        'month': month,
                        'score': score_data['score'],
                        'grade': score_data['grade'],
                        'action_count': score_data['breakdown']['action_count']['value'],
                        'reply_count': score_data['breakdown']['reply_count']['value'],
                    })
            else:
                # 全局模式：返回最近12个月（跨年）
                from datetime import datetime
                from dateutil.relativedelta import relativedelta

                now = datetime.now()
                for i in range(11, -1, -1):  # 从11个月前到当前月
                    target_date = now - relativedelta(months=i)
                    year_month = target_date.strftime('%Y-%m')

                    score_data = PerformanceDashboardService.get_activity_score(
                        user_id, year_month=year_month
                    )
                    trend.append({
                        'month': year_month,  # 格式: '2024-02'
                        'score': score_data['score'],
                        'grade': score_data['grade'],
                        'action_count': score_data['breakdown']['action_count']['value'],
                        'reply_count': score_data['breakdown']['reply_count']['value'],
                    })

            return trend
        except Exception as e:
            logger.error(f"获取月度活跃度趋势失败: {e}")
            return []

    @staticmethod
    def get_customer_activity_trend(user_id):
        """获取客户活跃度趋势（最近12个月）

        基于 Action 表统计用户客户的活跃情况

        Args:
            user_id: 用户ID

        Returns:
            list: 月度客户活跃度数据
                [{month: '2025-02', active_customers: 12, total_actions: 45}, ...]
        """
        try:
            from dateutil.relativedelta import relativedelta

            trend = []
            now = datetime.now()

            for i in range(11, -1, -1):  # 从11个月前到当前月
                target_date = now - relativedelta(months=i)
                year_month = target_date.strftime('%Y-%m')
                ym_year = target_date.year
                ym_month = target_date.month

                # 统计该月该用户客户的行动记录
                # 行动记录必须关联到该用户创建的客户
                action_query = db.session.query(
                    func.count(func.distinct(Action.company_id)).label('active_customers'),
                    func.count(Action.id).label('total_actions')
                ).join(
                    Company, Action.company_id == Company.id
                ).filter(
                    Company.owner_id == user_id,
                    Company.is_deleted == False,
                    extract('year', Action.created_at) == ym_year,
                    extract('month', Action.created_at) == ym_month
                ).first()

                active_customers = action_query[0] or 0
                total_actions = action_query[1] or 0

                trend.append({
                    'month': year_month,
                    'active_customers': active_customers,
                    'total_actions': total_actions
                })

            return trend
        except Exception as e:
            logger.error(f"获取客户活跃度趋势失败: {e}")
            return []

    @staticmethod
    def get_customer_value_ranking(user_id, limit=10):
        """获取客户价值排名

        基于客户关联的项目数量和批价单金额

        Args:
            user_id: 用户ID
            limit: 返回数量限制（默认Top 10）

        Returns:
            list: 客户价值排名数据
                [{company_id, company_name, company_type, project_count, total_amount}, ...]
        """
        try:
            from app.models.pricing_order import PricingOrder

            # 子查询：每个客户关联的项目数
            project_subquery = db.session.query(
                Project.company_id,
                func.count(Project.id).label('project_count')
            ).filter(
                Project.owner_id == user_id
            ).group_by(Project.company_id).subquery()

            # 子查询：每个客户关联的已审批批价单金额
            # 批价单通过项目关联到客户
            amount_subquery = db.session.query(
                Project.company_id,
                func.coalesce(func.sum(PricingOrder.pricing_total_amount), 0).label('total_amount')
            ).join(
                PricingOrder, Project.id == PricingOrder.project_id
            ).filter(
                Project.owner_id == user_id,
                PricingOrder.status == 'approved'
            ).group_by(Project.company_id).subquery()

            # 主查询：获取客户信息和统计数据
            query = db.session.query(
                Company.id,
                Company.name,
                Company.company_type,
                func.coalesce(project_subquery.c.project_count, 0).label('project_count'),
                func.coalesce(amount_subquery.c.total_amount, 0).label('total_amount')
            ).outerjoin(
                project_subquery, Company.id == project_subquery.c.company_id
            ).outerjoin(
                amount_subquery, Company.id == amount_subquery.c.company_id
            ).filter(
                Company.owner_id == user_id,
                Company.is_deleted == False
            ).order_by(
                func.coalesce(amount_subquery.c.total_amount, 0).desc(),
                func.coalesce(project_subquery.c.project_count, 0).desc()
            ).limit(limit)

            result = []
            for row in query.all():
                result.append({
                    'company_id': row[0],
                    'company_name': row[1],
                    'company_type': row[2] or 'other',
                    'project_count': row[3],
                    'total_amount': float(row[4])
                })

            return result
        except Exception as e:
            logger.error(f"获取客户价值排名失败: {e}")
            return []

    @staticmethod
    def _calculate_yearly_summary(yearly_stats, targets_dict):
        """计算年度汇总数据"""
        try:
            totals = {
                'implant_amount': 0,
                'sales_amount': 0,
                'new_customers': 0,
                'new_projects': 0,
            }
            targets = {
                'implant_amount': 0,
                'sales_amount': 0,
                'new_customers': 0,
                'new_projects': 0,
            }

            for i, stats in enumerate(yearly_stats):
                month = i + 1
                totals['implant_amount'] += getattr(stats, 'implant_amount_actual', 0) or 0
                totals['sales_amount'] += getattr(stats, 'sales_amount_actual', 0) or 0
                totals['new_customers'] += getattr(stats, 'new_customers_actual', 0) or 0
                totals['new_projects'] += getattr(stats, 'new_projects_actual', 0) or 0

                if month in targets_dict:
                    target = targets_dict[month]
                    # 新格式为dict，从薪资配置系统获取
                    if isinstance(target, dict):
                        targets['implant_amount'] += float(target.get('implant_amount_target', 0) or 0)
                        targets['sales_amount'] += float(target.get('sales_amount_target', 0) or 0)
                        targets['new_customers'] += int(target.get('new_customers_target', 0) or 0)
                        targets['new_projects'] += int(target.get('new_projects_target', 0) or 0)
                    else:
                        # 兼容旧格式 PerformanceTarget 对象
                        targets['implant_amount'] += float(target.implant_amount_target or 0)
                        targets['sales_amount'] += float(target.sales_amount_target or 0)
                        targets['new_customers'] += int(target.new_customers_target or 0)
                        targets['new_projects'] += int(target.new_projects_target or 0)

            # 计算达成率
            achievement = {}
            for key in totals:
                target_val = targets[key]
                actual_val = totals[key]
                rate = (actual_val / target_val * 100) if target_val > 0 else 0
                achievement[key] = {
                    'actual': round(actual_val, 2) if isinstance(actual_val, float) else actual_val,
                    'target': round(target_val, 2) if isinstance(target_val, float) else target_val,
                    'rate': round(rate, 1),
                    'status': 'success' if rate >= 100 else ('warning' if rate >= 80 else 'danger')
                }

            return achievement

        except Exception as e:
            logger.error(f"计算年度汇总失败: {e}")
            return PerformanceDashboardService._empty_summary()

    @staticmethod
    def _calculate_monthly_growth(yearly_stats):
        """计算月度环比增长"""
        try:
            growth = []
            prev_values = None

            for i, stats in enumerate(yearly_stats):
                month = i + 1
                current = {
                    'implant_amount': getattr(stats, 'implant_amount_actual', 0) or 0,
                    'sales_amount': getattr(stats, 'sales_amount_actual', 0) or 0,
                    'new_customers': getattr(stats, 'new_customers_actual', 0) or 0,
                    'new_projects': getattr(stats, 'new_projects_actual', 0) or 0,
                }

                month_growth = {'month': month}
                for key, value in current.items():
                    if prev_values and prev_values[key] > 0:
                        change = value - prev_values[key]
                        change_rate = (change / prev_values[key]) * 100
                    else:
                        change = 0
                        change_rate = 0

                    month_growth[key] = {
                        'value': round(value, 2) if isinstance(value, float) else value,
                        'change': round(change, 2) if isinstance(change, float) else change,
                        'change_rate': round(change_rate, 1),
                        'trend': 'up' if change > 0 else ('down' if change < 0 else 'flat')
                    }

                growth.append(month_growth)
                prev_values = current

            return growth

        except Exception as e:
            logger.error(f"计算月度增长失败: {e}")
            return []

    @staticmethod
    def _format_goal_achievement(yearly_stats, targets_dict):
        """格式化目标达成数据（用于图表）"""
        try:
            achievement = []

            for i, stats in enumerate(yearly_stats):
                month = i + 1
                target = targets_dict.get(month)

                # 获取目标值，兼容新格式(dict)和旧格式(PerformanceTarget对象)
                def get_target_value(target, field, default=0, as_int=False):
                    if not target:
                        return default
                    if isinstance(target, dict):
                        val = target.get(field, default) or default
                    else:
                        val = getattr(target, field, default) or default
                    return int(val) if as_int else float(val)

                month_data = {
                    'month': month,
                    'implant_amount': {
                        'actual': getattr(stats, 'implant_amount_actual', 0) or 0,
                        'target': get_target_value(target, 'implant_amount_target'),
                    },
                    'sales_amount': {
                        'actual': getattr(stats, 'sales_amount_actual', 0) or 0,
                        'target': get_target_value(target, 'sales_amount_target'),
                    },
                    'new_customers': {
                        'actual': getattr(stats, 'new_customers_actual', 0) or 0,
                        'target': get_target_value(target, 'new_customers_target', as_int=True),
                    },
                    'new_projects': {
                        'actual': getattr(stats, 'new_projects_actual', 0) or 0,
                        'target': get_target_value(target, 'new_projects_target', as_int=True),
                    },
                }

                # 计算达成率
                for key in ['implant_amount', 'sales_amount', 'new_customers', 'new_projects']:
                    target_val = month_data[key]['target']
                    actual_val = month_data[key]['actual']
                    rate = (actual_val / target_val * 100) if target_val > 0 else 0
                    month_data[key]['rate'] = round(rate, 1)

                achievement.append(month_data)

            return achievement

        except Exception as e:
            logger.error(f"格式化目标达成数据失败: {e}")
            return []

    @staticmethod
    def set_expense_budget(user_id, year, budget_data, operator_id=None):
        """设置年度报销预算

        Args:
            user_id: 用户ID
            year: 年份
            budget_data: 预算数据字典
            operator_id: 操作者ID

        Returns:
            ExpenseBudget: 预算对象
        """
        try:
            budget = ExpenseBudget.query.filter_by(user_id=user_id, year=year).first()

            if not budget:
                budget = ExpenseBudget(user_id=user_id, year=year)
                budget.created_by = operator_id
                db.session.add(budget)

            # 更新预算值
            budget.total_budget = budget_data.get('total_budget', 0)
            budget.entertainment_budget = budget_data.get('entertainment_budget', 0)
            budget.travel_budget = budget_data.get('travel_budget', 0)
            budget.transport_budget = budget_data.get('transport_budget', 0)
            budget.office_budget = budget_data.get('office_budget', 0)
            budget.communication_budget = budget_data.get('communication_budget', 0)
            budget.other_budget = budget_data.get('other_budget', 0)
            budget.updated_by = operator_id

            db.session.commit()
            return budget

        except Exception as e:
            db.session.rollback()
            logger.error(f"设置报销预算失败: {e}")
            raise

    # === 空数据模板 ===

    @staticmethod
    def _empty_summary():
        """空汇总数据"""
        return {
            'implant_amount': {'actual': 0, 'target': 0, 'rate': 0, 'status': 'danger'},
            'sales_amount': {'actual': 0, 'target': 0, 'rate': 0, 'status': 'danger'},
            'new_customers': {'actual': 0, 'target': 0, 'rate': 0, 'status': 'danger'},
            'new_projects': {'actual': 0, 'target': 0, 'rate': 0, 'status': 'danger'},
        }

    @staticmethod
    def _empty_expense_budget():
        """空报销预算数据"""
        return {
            'budget_total': 0,
            'expense_total': 0,
            'remaining': 0,
            'usage_rate': 0,
            'by_category': {},
            'category_comparison': {},
            'monthly_trend': [],
            'has_budget': False,
            'is_multi_user': False,
            'scope_type': 'personal',
            'scope_name': '个人',
            'current_month': datetime.now().month,
            'current_year': datetime.now().year
        }

    @staticmethod
    def _empty_activity_score():
        """空活跃度数据"""
        return {
            'score': 0,
            'grade': 'D',
            'grade_text': '待提升',
            'breakdown': {
                'action_count': {'value': 0, 'target': 600, 'score': 0, 'weight': 0.3},
                'reply_count': {'value': 0, 'target': 360, 'score': 0, 'weight': 0.1},
                'avg_length': {'value': 0, 'target': 200, 'score': 0, 'weight': 0.2},
                'customer_coverage': {'value': 0, 'target': 100, 'score': 0, 'weight': 0.2},
                'project_link_rate': {'value': 0, 'target': 100, 'score': 0, 'weight': 0.2},
            },
            'raw_data': {
                'total_customers': 0,
                'covered_customers': 0,
                'total_actions': 0,
                'linked_actions': 0,
            }
        }

    @staticmethod
    def get_user_kpi_targets(user_id, year):
        """
        获取用户的所有KPI目标（从新的目标表读取）

        优先级：
        1. UserPerformanceTarget (用户个人目标) - 优先使用
        2. RolePerformanceTarget (角色默认目标) - 回退使用

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            dict: {month: {item_code: target_value, ...}, ...}
                  如果没有配置返回空字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {}

            role_code = user.role
            targets_dict = {}

            # 1. 获取角色目标配置
            role_targets = RolePerformanceTarget.query.filter_by(
                role_code=role_code,
                year=year
            ).all()
            role_targets_dict = {rt.item_code: rt for rt in role_targets}

            # 2. 获取用户个人目标配置（独立查询，不依赖角色目标）
            user_targets = UserPerformanceTarget.query.filter_by(
                user_id=user_id,
                year=year
            ).all()
            user_targets_dict = {ut.item_code: ut for ut in user_targets}

            # 3. 如果两者都没有配置，返回空字典（让调用方回退到薪资配置）
            if not role_targets and not user_targets:
                return {}

            # 4. 合并所有目标项目代码（用户个人目标 + 角色目标）
            all_item_codes = set(role_targets_dict.keys()) | set(user_targets_dict.keys())

            # 5. 构建月度目标字典
            for month in range(1, 13):
                month_targets = {
                    'sales_amount_target': 0,
                    'implant_amount_target': 0,
                    'new_customers_target': 0,
                    'new_projects_target': 0
                }

                for item_code in all_item_codes:
                    user_target = user_targets_dict.get(item_code)
                    role_target = role_targets_dict.get(item_code)

                    # 确定年度目标值（用户个人目标优先）
                    annual_target = 0
                    if user_target and user_target.annual_target_override:
                        annual_target = float(user_target.annual_target_override)
                    elif role_target and role_target.annual_target:
                        annual_target = float(role_target.annual_target)

                    # 计算月度目标（按优先级：月度配置 → 季度配置÷3 → 年度配置÷12）
                    monthly_target = 0

                    # 优先级1：月度配置
                    if user_target and user_target.enable_monthly_override and user_target.monthly_targets_override:
                        user_monthly_val = user_target.monthly_targets_override.get(str(month))
                        if user_monthly_val:
                            monthly_target = float(user_monthly_val)
                    elif role_target and role_target.enable_monthly and role_target.monthly_targets:
                        monthly_val = role_target.monthly_targets.get(str(month))
                        if monthly_val:
                            monthly_target = float(monthly_val)

                    # 优先级2：季度配置（季度目标 ÷ 3）
                    if monthly_target == 0:
                        quarter = (month - 1) // 3 + 1  # 1-3月=Q1, 4-6月=Q2, 7-9月=Q3, 10-12月=Q4
                        quarterly_target = None

                        # 用户季度配置优先
                        if user_target and user_target.enable_quarterly_override:
                            q_targets = {
                                1: user_target.q1_target_override,
                                2: user_target.q2_target_override,
                                3: user_target.q3_target_override,
                                4: user_target.q4_target_override
                            }
                            quarterly_target = q_targets.get(quarter)

                        # 回退到角色季度配置
                        if quarterly_target is None and role_target and role_target.enable_quarterly:
                            q_targets = {
                                1: role_target.q1_target,
                                2: role_target.q2_target,
                                3: role_target.q3_target,
                                4: role_target.q4_target
                            }
                            quarterly_target = q_targets.get(quarter)

                        if quarterly_target:
                            monthly_target = float(quarterly_target) / 3  # 季度目标除以3

                    # 优先级3：年度配置（年度目标 ÷ 12）
                    if monthly_target == 0 and annual_target:
                        monthly_target = annual_target / 12

                    # 映射到标准字段名
                    target_key = PerformanceDashboardService._map_item_code_to_target_key(item_code)
                    if target_key:
                        # 注意：PerformanceService使用元为单位，需要转换
                        if item_code in ['sales_target', 'implant_amount', 'high_price_amount']:
                            monthly_target = monthly_target * 10000  # 万元→元
                        month_targets[target_key] = monthly_target

                targets_dict[month] = month_targets

            return targets_dict

        except Exception as e:
            logger.error(f"获取用户KPI目标失败: user_id={user_id}, year={year}, error={e}")
            return {}

    @staticmethod
    def _map_item_code_to_target_key(item_code):
        """将绩效项目代码映射到目标字段名"""
        mapping = {
            'sales_target': 'sales_amount_target',
            'implant_amount': 'implant_amount_target',
            'new_customers': 'new_customers_target',
            'new_projects': 'new_projects_target',
        }
        return mapping.get(item_code)

    @staticmethod
    def _get_configured_performance_items(user_id, year):
        """
        获取用户配置的绩效项目代码列表

        优先级：
        1. 用户个人配置 (UserPerformanceTarget)
        2. 角色默认配置 (RolePerformanceTarget)
        3. 默认显示所有指标

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            list: 绩效项目代码列表，如 ['implant_amount', 'sales_amount', 'new_customers', 'new_projects']
        """
        try:
            # 默认指标顺序
            default_items = ['implant_amount', 'sales_amount', 'new_customers', 'new_projects']

            # item_code 到 前端 metric key 的映射
            code_to_metric = {
                'implant_amount': 'implant_amount',
                'sales_target': 'sales_amount',
                'new_customers': 'new_customers',
                'new_projects': 'new_projects',
            }

            # 1. 查用户个人配置
            user_items = UserPerformanceTarget.query.filter_by(
                user_id=user_id, year=year
            ).all()

            if user_items:
                # 有个人配置，返回有目标的项目
                result = []
                for item in user_items:
                    if item.annual_target_override and item.annual_target_override > 0:
                        metric_key = code_to_metric.get(item.item_code)
                        if metric_key and metric_key not in result:
                            result.append(metric_key)
                if result:
                    # 按默认顺序排序
                    return [m for m in default_items if m in result]

            # 2. 回退到角色配置
            user = User.query.get(user_id)
            if user and user.role:
                role_items = RolePerformanceTarget.query.filter_by(
                    role_code=user.role, year=year
                ).all()

                if role_items:
                    result = []
                    for item in role_items:
                        if item.annual_target and item.annual_target > 0:
                            metric_key = code_to_metric.get(item.item_code)
                            if metric_key and metric_key not in result:
                                result.append(metric_key)
                    if result:
                        # 按默认顺序排序
                        return [m for m in default_items if m in result]

            # 3. 默认显示所有
            return default_items

        except Exception as e:
            logger.error(f"获取配置的绩效项目失败: user_id={user_id}, year={year}, error={e}")
            return ['implant_amount', 'sales_amount', 'new_customers', 'new_projects']

    @staticmethod
    def _get_team_summary_for_manager(user_id, year):
        """
        获取M级管理者的团队目标汇总数据

        仅当用户是M级管理者且是团队负责人时返回团队数据

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            dict: 团队汇总数据，格式与summary相同，或None（非M级管理者/无团队）
        """
        try:
            # 检查用户是否为M级管理者
            employee_config = EmployeeSalaryConfig.query.filter_by(
                user_id=user_id, year=year
            ).first()

            if not employee_config:
                return None

            # 检查职级是否为M级
            if not employee_config.grade or employee_config.grade.grade_type != 'M':
                return None

            # 查找该用户作为负责人的团队
            team = SalesTeamConfig.query.filter_by(
                team_leader_id=user_id, is_active=True
            ).first()

            if not team:
                return None

            # 导入团队绩效计算函数（避免循环导入）
            from app.api.v1.salary import calculate_team_performance

            # 获取团队绩效数据
            team_perf = calculate_team_performance(user_id, year)

            if not team_perf or team_perf.get('team_target', 0) <= 0:
                return None

            # 转换为与summary相同的格式
            # 注意：team_achievement 和 team_target 单位是万元
            team_summary = {
                'sales_amount': {
                    'actual': team_perf['team_achievement'],
                    'target': team_perf['team_target'],
                    'rate': round(team_perf['team_completion_rate'] * 100, 1),
                    'status': 'success' if team_perf['team_completion_rate'] >= 1 else (
                        'warning' if team_perf['team_completion_rate'] >= 0.8 else 'danger'
                    )
                }
            }

            logger.info(f"M级管理者团队目标: user_id={user_id}, year={year}, "
                       f"team_target={team_perf['team_target']}, "
                       f"team_achievement={team_perf['team_achievement']}")

            return team_summary

        except Exception as e:
            logger.error(f"获取团队目标失败: user_id={user_id}, year={year}, error={e}")
            return None
