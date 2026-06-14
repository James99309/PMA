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
# 2026-01-08: 废弃旧的 KPI 目标系统，不再需要导入 RolePerformanceTarget, UserPerformanceTarget, PerformanceMetricsDefinition
from app.models.monthly_activity_snapshot import MonthlyActivitySnapshot
from app.utils.activity_tracker import FROZEN_STAGES
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
    def get_dashboard_data(user_id, year, lite=False):
        """获取完整的看板数据

        Args:
            user_id: 用户ID
            year: 年份
            lite: 轻量模式，仅返回 summary/configured_items/expense_budgets（首页用）

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

            # 获取配置的绩效项目列表（提前获取，用于按需触发角色专属计算）
            configured_items = PerformanceDashboardService._get_configured_performance_items(user_id, year)

            # 按需加载角色专属指标（仅在配置管理中启用后才计算）
            pm_codes = {'pm_implant_amount', 'pm_sales_amount'}
            se_codes = {'se_implant_amount', 'se_sales_amount',
                        'se_confirm_count', 'se_sales_support', 'se_confirm_quality'}
            configured_set = set(configured_items) if configured_items else set()

            if configured_items and pm_codes & configured_set:
                pm_stats = PerformanceService.calculate_pm_yearly_statistics_batch(user_id, year)
                for i, rs in enumerate(pm_stats):
                    if i < len(yearly_stats):
                        yearly_stats[i].pm_implant_amount_actual = rs.pm_implant_amount_actual
                        yearly_stats[i].pm_sales_amount_actual = rs.pm_sales_amount_actual

            if configured_items and se_codes & configured_set:
                se_stats = PerformanceService.calculate_se_yearly_statistics_batch(user_id, year)
                for i, rs in enumerate(se_stats):
                    if i < len(yearly_stats):
                        yearly_stats[i].se_implant_amount_actual = rs.se_implant_amount_actual
                        yearly_stats[i].se_sales_amount_actual = rs.se_sales_amount_actual
                        yearly_stats[i].se_confirm_count_actual = getattr(rs, 'se_confirm_count_actual', 0)
                        yearly_stats[i].se_sales_support_actual = getattr(rs, 'se_sales_support_actual', 0)
                        yearly_stats[i].se_confirm_quality_actual = getattr(rs, 'se_confirm_quality_actual', 0)

            # 技术培训(2026-06-14):se_training_count 改为"技术培训"任务完成数(按月),替代手工录入
            if configured_items and 'se_training_count' in configured_set:
                from app.helpers.at_dashboard_helpers import _act_hr_task_count
                from datetime import date as _date
                _u = User.query.get(user_id)
                for i in range(12):
                    m = i + 1
                    s = _date(year, m, 1)
                    e = _date(year + 1, 1, 1) if m == 12 else _date(year, m + 1, 1)
                    if i < len(yearly_stats):
                        yearly_stats[i].se_training_count_actual = _act_hr_task_count(_u, s, e, 'se_tech_training')

            # 产品经理(2026-06-14):研发计划达成/质量处理/上市支持 改任务驱动 + 新品上市自动,
            # 统一复用 _KPI_ACTUAL_FNS 按月计算(单一来源),让本路径与 AT 看板口径一致
            _pm_auto_codes = {'pm_dev_rate', 'pm_quality_rate', 'pm_support_count', 'pm_new_launch'} & configured_set
            if configured_items and _pm_auto_codes:
                from app.helpers.at_dashboard_helpers import _KPI_ACTUAL_FNS
                from datetime import date as _date
                _u = User.query.get(user_id)
                for code in _pm_auto_codes:
                    fn = _KPI_ACTUAL_FNS.get(code)
                    if not fn:
                        continue
                    for i in range(12):
                        m = i + 1
                        s = _date(year, m, 1)
                        e = _date(year + 1, 1, 1) if m == 12 else _date(year, m + 1, 1)
                        if i < len(yearly_stats):
                            setattr(yearly_stats[i], f'{code}_actual', fn(_u, s, e))

            # 从手工录入表加载辅助指标（替代自动采集）
            manual_codes = {'se_response_rate', 'se_content_output', 'se_satisfaction'}
            if configured_items and manual_codes & configured_set:
                from app.models.performance_manual_entry import PerformanceManualEntry
                entries = PerformanceManualEntry.query.filter_by(
                    user_id=user_id, year=year
                ).filter(
                    PerformanceManualEntry.metric_code.in_(manual_codes & configured_set)
                ).all()

                monthly_map = {}   # code → {month: value}
                quarterly_map = {} # code → {quarter: value}
                for e in entries:
                    if e.period_type == 'monthly':
                        monthly_map.setdefault(e.metric_code, {})[e.period] = float(e.value or 0)
                    else:
                        quarterly_map.setdefault(e.metric_code, {})[e.period] = float(e.value or 0)

                for code in manual_codes & configured_set:
                    for i in range(12):
                        month = i + 1
                        quarter = (i // 3) + 1
                        val = monthly_map.get(code, {}).get(month, 0) or quarterly_map.get(code, {}).get(quarter, 0)
                        if i < len(yearly_stats):
                            setattr(yearly_stats[i], f'{code}_actual', val)

            # 从绩效目标配置获取目标数据（使用新的目标表）
            targets_dict = PerformanceDashboardService.get_user_kpi_targets(user_id, year)
            logger.info(f"[DEBUG] get_user_kpi_targets returned: {bool(targets_dict)}, keys: {list(targets_dict.keys()) if targets_dict else []}")

            # 如果新目标表无数据，回退到薪资配置
            if not targets_dict:
                logger.info(f"[DEBUG] Falling back to EmployeeSalaryConfig for user_id={user_id}")
                employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()
                logger.info(f"[DEBUG] employee_config found: {bool(employee_config)}")
                if employee_config:
                    logger.info(f"[DEBUG] grade_id: {employee_config.grade_id}, use_custom_config: {employee_config.use_custom_config}")
                    logger.info(f"[DEBUG] annual_target_override: {employee_config.annual_target_override}")
                    if employee_config.grade:
                        logger.info(f"[DEBUG] grade.annual_target: {employee_config.grade.annual_target}")

                if employee_config and employee_config.grade_id:
                    # 获取年度目标
                    annual_target = employee_config.get_effective_value('annual_target', 0)
                    logger.info(f"[DEBUG] get_effective_value('annual_target'): {annual_target}")
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
                    logger.info(f"[DEBUG] Final targets_dict month 1: {targets_dict.get(1, {})}")

            # 获取费用预算范围（根据用户角色，支持多范围）
            user = User.query.get(user_id)
            expense_scopes = PerformanceDashboardService._get_expense_scopes(user, year)

            # 为每个范围获取费用预算数据（使用目标用户的结算货币）
            expense_budgets = []
            current_month = datetime.now().month
            for scope_user_ids, scope_type, scope_name in expense_scopes:
                budget_data = PerformanceDashboardService.get_expense_budget_data(user_id, year, scope_user_ids, target_user=user)
                budget_data['scope_type'] = scope_type
                budget_data['scope_name'] = scope_name
                budget_data['current_month'] = current_month
                budget_data['current_year'] = year
                expense_budgets.append(budget_data)

            # 保持 expense_budget 为第一个范围（向后兼容）
            expense_budget = expense_budgets[0] if expense_budgets else PerformanceDashboardService._empty_expense_budget()

            # 汇总年度数据（传入 user_id 用于计算客户活跃度）
            summary = PerformanceDashboardService._calculate_yearly_summary(yearly_stats, targets_dict, user_id)

            # lite 模式：仅返回首页所需的轻量数据，跳过重型聚合查询
            if lite:
                return {
                    'summary': summary,
                    'configured_items': configured_items,
                    'expense_budget': expense_budget,
                    'expense_budgets': expense_budgets,
                }

            # === 以下为完整模式的重型查询 ===

            # 方案经理和产品经理不需要活跃度、行业分布和客户分布数据
            target_user = User.query.get(user_id)
            skip_activity_tabs = target_user and target_user.role in ('solution_manager', 'product_manager')

            if skip_activity_tabs:
                industry_stats = {}
                activity_score = PerformanceDashboardService._empty_activity_score()
                activity_monthly_trend = []
                customer_type_stats = {}
                customer_trend = {}
                customer_activity = []
                customer_value = []
            else:
                # 行业分布使用全局模式（不按年份过滤，显示最近12个月）
                industry_stats = PerformanceService.get_monthly_industry_statistics(user_id)  # 全局模式

                # 活跃度使用全局模式（不按年份过滤，显示最近12个月）
                activity_score = PerformanceDashboardService.get_activity_score(user_id)  # 全局模式
                activity_monthly_trend = PerformanceDashboardService.get_monthly_activity_trend(user_id)  # 全局模式

                # 客户分布数据（全局模式，最近12个月）
                customer_type_stats = PerformanceService.calculate_customer_type_statistics(user_id)  # 全局模式
                customer_trend = PerformanceService.get_monthly_customer_statistics(user_id)  # 全局模式
                customer_activity = PerformanceDashboardService.get_customer_activity_trend(user_id)
                customer_value = PerformanceDashboardService.get_customer_value_ranking(user_id)

            # 计算月度增长
            monthly_growth = PerformanceDashboardService._calculate_monthly_growth(yearly_stats)

            # 格式化目标达成数据（传入配置项和user_id以支持动态指标）
            goal_achievement = PerformanceDashboardService._format_goal_achievement(
                yearly_stats, targets_dict, configured_items, user_id, year
            )

            # 检查是否为M级管理者并获取团队目标
            team_summary = PerformanceDashboardService._get_team_summary_for_manager(user_id, year)

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
                'configured_items': [],  # 异常时返回空列表，前端显示"未配置绩效目标"
                # 客户分布数据默认值
                'customer_type_stats': {},
                'customer_trend': {},
                'customer_activity': [],
                'customer_value': [],
            }

    @staticmethod
    def get_expense_budget_data(user_id, year, scope_user_ids=None, target_user=None):
        """获取报销预算数据

        Args:
            user_id: 用户ID
            year: 年份
            scope_user_ids: 可选，范围内的用户ID列表（用于团队/部门/公司汇总）
            target_user: 可选，目标用户对象（用于确定结算货币）
                        - 查看自己时：使用自己的结算货币
                        - 查看他人时：使用对方的结算货币

        Returns:
            dict: 报销预算数据（包含 currency 字段表示使用的货币）
        """
        try:
            # 确定目标用户ID列表
            target_user_ids = scope_user_ids or [user_id]
            is_multi_user = len(target_user_ids) > 1

            # 确定目标货币：使用目标用户的结算货币，或系统默认货币
            if target_user:
                target_currency = target_user.settlement_currency or Config.DEFAULT_CURRENCY
            elif not is_multi_user:
                # 单用户模式，获取该用户的结算货币
                user = User.query.get(user_id)
                target_currency = (user.settlement_currency if user else None) or Config.DEFAULT_CURRENCY
            else:
                # 多用户模式，使用系统默认货币
                target_currency = Config.DEFAULT_CURRENCY

            # 批量预加载用户和预算数据（避免循环内N+1查询）
            users_map = {u.id: u for u in User.query.filter(User.id.in_(target_user_ids)).all()}
            budgets_map = {b.user_id: b for b in ExpenseBudget.query.filter(
                ExpenseBudget.user_id.in_(target_user_ids), ExpenseBudget.year == year).all()}

            # 批量预加载角色预算（对无个人预算的用户）
            no_budget_roles = set()
            for uid in target_user_ids:
                if uid not in budgets_map:
                    member_user = users_map.get(uid)
                    if member_user and member_user.role:
                        no_budget_roles.add(member_user.role)
            role_budgets_map = {}
            if no_budget_roles:
                role_budgets_map = {rb.role_code: rb for rb in RoleExpenseBudget.query.filter(
                    RoleExpenseBudget.role_code.in_(no_budget_roles), RoleExpenseBudget.year == year).all()}

            # 汇总所有目标用户的预算（支持多货币转换）
            budget_total = 0
            has_any_budget = False

            for uid in target_user_ids:
                member_user = users_map.get(uid)
                member_currency = (member_user.settlement_currency if member_user else None) or Config.DEFAULT_CURRENCY

                user_budget = budgets_map.get(uid)
                if user_budget:
                    budget_amount = float(user_budget.total_budget or 0)
                    if member_currency != target_currency and budget_amount > 0:
                        try:
                            budget_amount = exchange_rate_service.convert_amount(
                                budget_amount, member_currency, target_currency
                            )
                        except Exception as conv_err:
                            logger.warning(f"用户 {uid} 预算货币转换失败 {member_currency} -> {target_currency}: {conv_err}")
                    budget_total += budget_amount
                    has_any_budget = True
                else:
                    if member_user and member_user.role:
                        role_budget = role_budgets_map.get(member_user.role)
                        if role_budget:
                            budget_amount = float(role_budget.total_budget or 0)
                            if Config.DEFAULT_CURRENCY != target_currency and budget_amount > 0:
                                try:
                                    budget_amount = exchange_rate_service.convert_amount(
                                        budget_amount, Config.DEFAULT_CURRENCY, target_currency
                                    )
                                except Exception as conv_err:
                                    logger.warning(f"角色预算货币转换失败 {Config.DEFAULT_CURRENCY} -> {target_currency}: {conv_err}")
                            budget_total += budget_amount
                            has_any_budget = True

            # 先计算月度趋势（使用目标货币），然后复用其结果求总额（避免冗余全量查询）
            monthly_trend = PerformanceDashboardService._get_expense_monthly_trend(target_user_ids, year, target_currency)
            expense_total = sum(m['amount'] for m in monthly_trend) if monthly_trend else 0.0

            # 按科目统计实际报销（使用目标货币）
            by_category = PerformanceDashboardService._get_expense_by_category(target_user_ids, year, target_currency)

            # 计算使用率和剩余
            remaining = budget_total - expense_total
            usage_rate = (expense_total / budget_total * 100) if budget_total > 0 else 0

            # 按科目预算对比（多用户模式下汇总所有用户的分类预算，支持多货币转换）
            # 复用上面批量预加载的 users_map、budgets_map、role_budgets_map
            category_comparison = {}
            category_budgets_total = {}  # 汇总各分类预算

            for uid in target_user_ids:
                member_user = users_map.get(uid)
                member_currency = (member_user.settlement_currency if member_user else None) or Config.DEFAULT_CURRENCY
                is_role_budget = False

                effective = budgets_map.get(uid)
                if not effective:
                    if member_user and member_user.role:
                        effective = role_budgets_map.get(member_user.role)
                        is_role_budget = True

                if effective:
                    cat_budgets = effective.get_category_budgets()
                    # 确定源货币：个人预算用用户结算货币，角色预算用系统默认货币
                    source_currency = Config.DEFAULT_CURRENCY if is_role_budget else member_currency

                    for cat_key, amount in cat_budgets.items():
                        # 如果源货币与目标货币不同，进行汇率转换
                        if source_currency != target_currency and amount > 0:
                            try:
                                amount = exchange_rate_service.convert_amount(
                                    amount, source_currency, target_currency
                                )
                            except Exception as conv_err:
                                logger.warning(f"分类预算货币转换失败 {source_currency} -> {target_currency}: {conv_err}")
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
                'is_multi_user': is_multi_user,
                'currency': target_currency  # 返回使用的货币代码
            }

        except Exception as e:
            logger.error(f"获取报销预算数据失败: {e}")
            return PerformanceDashboardService._empty_expense_budget()

    @staticmethod
    def _get_expense_by_category(user_ids, year, target_currency=None):
        """按科目统计实际报销金额（支持多货币转换）

        Args:
            user_ids: 用户ID或用户ID列表
            year: 年份
            target_currency: 目标货币（转换后的货币），默认为系统默认货币
        """
        try:
            # 兼容单个ID和列表
            if not isinstance(user_ids, (list, tuple)):
                user_ids = [user_ids]

            base_currency = target_currency or Config.DEFAULT_CURRENCY  # 使用目标货币或系统默认货币

            # 查询已审批的报销明细，同时获取报销单货币
            # 🔥 修复：使用 attributed_to_id 统计费用（如果设置了归属人）
            query = db.session.query(
                ExpenseDetail.expense_category,
                ExpenseDetail.current_amount,
                Expense.currency
            ).join(Expense).filter(
                func.coalesce(Expense.attributed_to_id, Expense.owner_id).in_(user_ids),
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
    def _get_expense_monthly_trend(user_ids, year, target_currency=None):
        """获取月度报销趋势（支持多货币转换）

        Args:
            user_ids: 用户ID或用户ID列表
            year: 年份
            target_currency: 目标货币（转换后的货币），默认为系统默认货币
        """
        try:
            # 兼容单个ID和列表
            if not isinstance(user_ids, (list, tuple)):
                user_ids = [user_ids]

            base_currency = target_currency or Config.DEFAULT_CURRENCY  # 使用目标货币或系统默认货币

            # 查询每笔报销单的月份、金额和货币
            # 🔥 修复：使用 attributed_to_id 统计费用（如果设置了归属人）
            query = db.session.query(
                extract('month', Expense.created_at).label('month'),
                Expense.total_amount,
                Expense.currency
            ).filter(
                func.coalesce(Expense.attributed_to_id, Expense.owner_id).in_(user_ids),
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
        - 行动记录数 (20%): 动态目标=在跟项目数×30(年)/×2.5(月)
        - 回复数 (10%): 动态目标=行动目标/3
        - 平均字数 (15%): 固定目标50字
        - 客户覆盖率 (15%): 拜访客户数/总客户数
        - 项目关联率 (15%): 关联项目的行动数/总行动数
        - 客户活跃度 (15%): (highly_active+active+normal)/总客户数
        - 项目活跃度 (10%): (highly_active+active+normal)/非冻结项目数

        Args:
            user_id: 用户ID
            year: 年份（可选，None表示全局分析）
            month: 月份（可选，需配合year使用）
            year_month: 年月字符串格式 'YYYY-MM'（可选，用于跨年月份查询）

        Returns:
            dict: 活跃度评分数据
        """
        try:
            # 动态目标：基于在跟项目数
            active_project_count = Project.query.filter(
                Project.owner_id == user_id,
                ~Project.current_stage.in_(FROZEN_STAGES)
            ).count()

            # 构建基础过滤条件
            action_filters = [Action.owner_id == user_id]

            is_monthly = False
            if year_month:
                ym_year, ym_month = map(int, year_month.split('-'))
                action_filters.append(extract('year', Action.created_at) == ym_year)
                action_filters.append(extract('month', Action.created_at) == ym_month)
                is_monthly = True
            elif year is not None:
                action_filters.append(extract('year', Action.created_at) == year)
                if month:
                    action_filters.append(extract('month', Action.created_at) == month)
                    is_monthly = True
            # else: 全局模式（年度基准）

            # 动态目标计算
            if is_monthly:
                base_action_count = max(int(active_project_count * 2.5), 3)
                base_reply_count = max(int(base_action_count / 3), 1)
            else:
                base_action_count = max(active_project_count * 30, 30)
                base_reply_count = max(int(base_action_count / 3), 10)
            avg_length_target = 50

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

            # 业务维度 - 客户活跃度 & 项目活跃度
            # 历史月份从快照取，当前月用实时计算
            customer_activity_data = None
            project_activity_data = None
            if is_monthly:
                # 统一提取年月，无论来自 year_month 还是 year+month
                if year_month:
                    ym_year, ym_month = map(int, year_month.split('-'))
                else:
                    ym_year, ym_month = year, month

                # 当前月不查快照，用实时数据
                now = datetime.now()
                is_current_month = (ym_year == now.year and ym_month == now.month)

                if not is_current_month:
                    snapshot = MonthlyActivitySnapshot.query.filter_by(
                        user_id=user_id, year=ym_year, month=ym_month
                    ).first()
                    if snapshot:
                        customer_activity_rate = float(snapshot.customer_activity_rate)
                        project_activity_rate = float(snapshot.project_activity_rate)
                        customer_activity_data = {
                            'rate': customer_activity_rate,
                            'highly_active_count': snapshot.customer_highly_active,
                            'active_count': snapshot.customer_active,
                            'normal_count': snapshot.customer_normal,
                            'to_follow_count': snapshot.customer_to_follow,
                            'dormant_count': snapshot.customer_dormant,
                            'churned_count': snapshot.customer_churned,
                            'total_count': snapshot.customer_total,
                        }
                        project_activity_data = {
                            'rate': project_activity_rate,
                            'highly_active_count': snapshot.project_highly_active,
                            'active_count': snapshot.project_active,
                            'normal_count': snapshot.project_normal,
                            'to_follow_count': snapshot.project_to_follow,
                            'dormant_count': snapshot.project_dormant,
                            'churned_count': snapshot.project_churned,
                            'total_count': snapshot.project_total,
                            'frozen_count': snapshot.project_frozen,
                            'active_total': snapshot.project_total - snapshot.project_frozen,
                            'healthy_count': snapshot.project_highly_active + snapshot.project_active + snapshot.project_normal,
                            'stage_breakdown': {},
                        }

            if customer_activity_data is None:
                customer_activity_data = PerformanceService.calculate_customer_activity_rate(user_id)
            customer_activity_rate = customer_activity_data['rate']

            if project_activity_data is None:
                project_activity_data = PerformanceService.calculate_project_activity_rate(user_id)
            project_activity_rate = project_activity_data['rate']

            # 各维度得分（0-100）
            action_score = min(action_count / base_action_count * 100, 100) if base_action_count > 0 else 0
            reply_score = min(reply_count / base_reply_count * 100, 100) if base_reply_count > 0 else 0
            length_score = min(avg_length / avg_length_target * 100, 100)
            coverage_score = min(customer_coverage, 100)
            link_score = min(project_link_rate, 100)
            customer_activity_score = min(customer_activity_rate, 100)
            project_activity_score = min(project_activity_rate, 100)

            # 综合评分（加权平均，7维度）
            score = (
                action_score * 0.20 +
                reply_score * 0.10 +
                length_score * 0.15 +
                coverage_score * 0.15 +
                link_score * 0.15 +
                customer_activity_score * 0.15 +
                project_activity_score * 0.10
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
                        'weight': 0.20
                    },
                    'reply_count': {
                        'value': reply_count,
                        'target': base_reply_count,
                        'score': round(reply_score, 1),
                        'weight': 0.10
                    },
                    'avg_length': {
                        'value': round(avg_length),
                        'target': avg_length_target,
                        'score': round(length_score, 1),
                        'weight': 0.15
                    },
                    'customer_coverage': {
                        'value': round(customer_coverage, 1),
                        'target': 100,
                        'score': round(coverage_score, 1),
                        'weight': 0.15
                    },
                    'project_link_rate': {
                        'value': round(project_link_rate, 1),
                        'target': 100,
                        'score': round(link_score, 1),
                        'weight': 0.15
                    },
                    'customer_activity': {
                        'value': round(customer_activity_rate, 1),
                        'target': 100,
                        'score': round(customer_activity_score, 1),
                        'weight': 0.15
                    },
                    'project_activity': {
                        'value': round(project_activity_rate, 1),
                        'target': 100,
                        'score': round(project_activity_score, 1),
                        'weight': 0.10
                    },
                },
                'raw_data': {
                    'total_customers': total_customers,
                    'covered_customers': covered_customers,
                    'total_actions': total_actions,
                    'linked_actions': linked_actions,
                    'customer_activity_detail': {
                        'highly_active_count': customer_activity_data.get('highly_active_count', 0),
                        'active_count': customer_activity_data.get('active_count', 0),
                        'normal_count': customer_activity_data.get('normal_count', 0),
                        'to_follow_count': customer_activity_data.get('to_follow_count', 0),
                        'dormant_count': customer_activity_data.get('dormant_count', 0),
                        'churned_count': customer_activity_data.get('churned_count', 0),
                        'total_count': customer_activity_data.get('total_count', 0)
                    },
                    'project_activity_detail': {
                        'healthy_count': project_activity_data.get('healthy_count', 0),
                        'highly_active_count': project_activity_data.get('highly_active_count', 0),
                        'active_count': project_activity_data.get('active_count', 0),
                        'normal_count': project_activity_data.get('normal_count', 0),
                        'to_follow_count': project_activity_data.get('to_follow_count', 0),
                        'dormant_count': project_activity_data.get('dormant_count', 0),
                        'churned_count': project_activity_data.get('churned_count', 0),
                        'total_count': project_activity_data.get('total_count', 0),
                        'active_total': project_activity_data.get('active_total', 0),
                        'frozen_count': project_activity_data.get('frozen_count', 0),
                        'stage_breakdown': project_activity_data.get('stage_breakdown', {})
                    }
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
            list: 月度活跃度数据列表（含各维度数据用于图表联动）
        """
        try:
            trend = []

            def _build_trend_item(score_data, month_label):
                bd = score_data['breakdown']
                return {
                    'month': month_label,
                    'score': score_data['score'],
                    'grade': score_data['grade'],
                    'action_count': bd['action_count']['value'],
                    'reply_count': bd['reply_count']['value'],
                    'avg_length': bd['avg_length']['value'],
                    'customer_coverage': bd['customer_coverage']['value'],
                    'customer_activity': bd['customer_activity']['value'],
                    'project_activity': bd['project_activity']['value'],
                    'project_link_rate': bd['project_link_rate']['value'],
                }

            if year is not None:
                for month in range(1, 13):
                    score_data = PerformanceDashboardService.get_activity_score(user_id, year, month)
                    trend.append(_build_trend_item(score_data, month))
            else:
                from datetime import datetime
                from dateutil.relativedelta import relativedelta

                now = datetime.now()
                for i in range(11, -1, -1):
                    target_date = now - relativedelta(months=i)
                    year_month = target_date.strftime('%Y-%m')

                    score_data = PerformanceDashboardService.get_activity_score(
                        user_id, year_month=year_month
                    )
                    trend.append(_build_trend_item(score_data, year_month))

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
            from app.models.project_customer_association import ProjectCustomerAssociation

            # 子查询：每个客户关联的项目数（通过 ProjectCustomerAssociation 关联）
            project_subquery = db.session.query(
                ProjectCustomerAssociation.company_id,
                func.count(func.distinct(Project.id)).label('project_count')
            ).join(
                Project, ProjectCustomerAssociation.project_id == Project.id
            ).filter(
                Project.owner_id == user_id
            ).group_by(ProjectCustomerAssociation.company_id).subquery()

            # 子查询：每个客户关联的已审批批价单金额
            # 批价单通过项目关联到客户
            amount_subquery = db.session.query(
                ProjectCustomerAssociation.company_id,
                func.coalesce(func.sum(PricingOrder.pricing_total_amount), 0).label('total_amount')
            ).join(
                Project, ProjectCustomerAssociation.project_id == Project.id
            ).join(
                PricingOrder, Project.id == PricingOrder.project_id
            ).filter(
                Project.owner_id == user_id,
                PricingOrder.status == 'approved'
            ).group_by(ProjectCustomerAssociation.company_id).subquery()

            # 主查询：获取客户信息和统计数据
            query = db.session.query(
                Company.id,
                Company.company_name,
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
    def get_se_detail_data(user_id, year):
        """获取 SE 绩效明细数据（方案植入明细 + 方案批价明细）

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            dict: {implant_details: [...], pricing_details: [...]}
        """
        try:
            from app.models.relation import ProjectMember
            from app.models.pricing_order import PricingOrder
            from sqlalchemy import text

            # 植入明细 SQL — 查所有 SE 有参与的项目（含未正式计入的）
            # is_counted = SE 有任何参与记录（project_members/报价确认/work_items/actions）
            implant_sql = text("""
                SELECT p.id, p.project_name,
                    true as is_counted,
                    COALESCE(wi.cnt, 0) as work_item_count,
                    COALESCE(swi.cnt, 0) as shared_work_item_count,
                    COALESCE(act.cnt, 0) as action_count,
                    COALESCE(imp.amount, 0) as implant_amount,
                    COALESCE(qc.cnt, 0) as confirmation_count
                FROM (
                    SELECT DISTINCT project_id FROM (
                        SELECT project_id FROM project_members
                            WHERE user_id = :user_id AND role = 'solution_engineer'
                        UNION
                        SELECT project_id FROM quotations
                            WHERE confirmed_by = :user_id AND project_id IS NOT NULL
                        UNION
                        SELECT project_id FROM work_items
                            WHERE owner_id = :user_id AND project_id IS NOT NULL
                        UNION
                        SELECT wi2.project_id FROM work_items wi2
                            WHERE wi2.shared_with_users IS NOT NULL
                              AND CAST(wi2.shared_with_users AS text) LIKE '%' || CAST(:user_id AS text) || '%'
                              AND wi2.project_id IS NOT NULL
                        UNION
                        SELECT project_id FROM actions
                            WHERE owner_id = :user_id AND project_id IS NOT NULL
                    ) all_projects
                ) involved
                JOIN projects p ON involved.project_id = p.id
                LEFT JOIN (
                    SELECT project_id, COUNT(*) as cnt
                    FROM work_items WHERE owner_id = :user_id
                    GROUP BY project_id
                ) wi ON wi.project_id = p.id
                LEFT JOIN (
                    SELECT wi2.project_id, COUNT(*) as cnt
                    FROM work_items wi2
                    WHERE wi2.shared_with_users IS NOT NULL
                      AND CAST(wi2.shared_with_users AS text) LIKE '%' || CAST(:user_id AS text) || '%'
                    GROUP BY wi2.project_id
                ) swi ON swi.project_id = p.id
                LEFT JOIN (
                    SELECT project_id, COUNT(*) as cnt
                    FROM actions WHERE owner_id = :user_id
                    GROUP BY project_id
                ) act ON act.project_id = p.id
                LEFT JOIN (
                    SELECT project_id, COUNT(*) as cnt
                    FROM quotations WHERE confirmed_by = :user_id
                    GROUP BY project_id
                ) qc ON qc.project_id = p.id
                LEFT JOIN (
                    SELECT q.project_id, SUM(qd.quantity * qd.market_price) as amount
                    FROM quotation_details qd
                    JOIN quotations q ON qd.quotation_id = q.id
                    JOIN products prod ON qd.product_mn = prod.product_mn
                    WHERE prod.is_vendor_product = true
                      AND EXTRACT(year FROM q.created_at) = :year
                    GROUP BY q.project_id
                ) imp ON imp.project_id = p.id
                ORDER BY COALESCE(imp.amount, 0) DESC, p.id DESC
            """)

            implant_rows = db.session.execute(implant_sql, {'user_id': user_id, 'year': year}).fetchall()

            implant_details = []
            for row in implant_rows:
                # Columns: 0=id, 1=project_name, 2=is_counted, 3=work_item_count, 4=shared_work_item_count, 5=action_count, 6=implant_amount, 7=confirmation_count
                total_interactions = row[3] + row[4] + row[5] + row[7]
                if total_interactions >= 10:
                    badge_level = 'core'       # 核心
                elif total_interactions >= 3:
                    badge_level = 'active'     # 活跃
                else:
                    badge_level = 'engaged'    # 参与

                implant_details.append({
                    'project_id': row[0],
                    'project_name': row[1],
                    'is_counted': bool(row[2]),
                    'work_item_count': row[3],
                    'shared_work_item_count': row[4],
                    'action_count': row[5],
                    'total_interactions': total_interactions,
                    'badge_level': badge_level,
                    'implant_amount': float(row[6]),
                    'confirmation_count': row[7],
                })

            # 批价明细 SQL（仅 approved + 当年）
            pricing_sql = text("""
                WITH se_projects AS (
                    SELECT DISTINCT project_id FROM (
                        SELECT project_id FROM project_members
                            WHERE user_id = :user_id AND role = 'solution_engineer'
                        UNION
                        SELECT project_id FROM quotations
                            WHERE confirmed_by = :user_id AND project_id IS NOT NULL
                        UNION
                        SELECT project_id FROM work_items
                            WHERE owner_id = :user_id AND project_id IS NOT NULL
                        UNION
                        SELECT project_id FROM actions
                            WHERE owner_id = :user_id AND project_id IS NOT NULL
                    ) all_se_projects
                )
                SELECT po.order_number, p.project_name,
                    po.pricing_total_amount, po.approved_at
                FROM pricing_orders po
                JOIN se_projects sp ON po.project_id = sp.project_id
                JOIN projects p ON po.project_id = p.id
                WHERE po.status = 'approved'
                  AND EXTRACT(year FROM po.approved_at) = :year
                ORDER BY po.approved_at DESC
            """)

            pricing_rows = db.session.execute(pricing_sql, {'user_id': user_id, 'year': year}).fetchall()

            pricing_details = []
            for row in pricing_rows:
                pricing_details.append({
                    'order_no': row[0],
                    'project_name': row[1],
                    'amount': float(row[2]) if row[2] else 0,
                    'approved_at': row[3].strftime('%Y-%m-%d') if row[3] else '',
                })

            return {
                'implant_details': implant_details,
                'pricing_details': pricing_details,
            }
        except Exception as e:
            logger.error(f"获取SE绩效明细失败: {e}")
            return {'implant_details': [], 'pricing_details': []}

    @staticmethod
    def _calculate_yearly_summary(yearly_stats, targets_dict, user_id=None):
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

            # 动态检测已启用的角色指标（通过 yearly_stats 上的属性存在性判断）
            extra_keys = []
            for key in ['pm_implant_amount', 'pm_sales_amount', 'se_implant_amount', 'se_sales_amount',
                         'se_response_rate', 'se_training_count', 'se_content_output', 'se_satisfaction']:
                if yearly_stats and hasattr(yearly_stats[0], f'{key}_actual'):
                    extra_keys.append(key)
                    totals[key] = 0
                    targets[key] = 0

            for i, stats in enumerate(yearly_stats):
                month = i + 1
                totals['implant_amount'] += getattr(stats, 'implant_amount_actual', 0) or 0
                totals['sales_amount'] += getattr(stats, 'sales_amount_actual', 0) or 0
                totals['new_customers'] += getattr(stats, 'new_customers_actual', 0) or 0
                totals['new_projects'] += getattr(stats, 'new_projects_actual', 0) or 0

                for key in extra_keys:
                    totals[key] += getattr(stats, f'{key}_actual', 0) or 0

                if month in targets_dict:
                    target = targets_dict[month]
                    # 新格式为dict，从薪资配置系统获取
                    if isinstance(target, dict):
                        targets['implant_amount'] += float(target.get('implant_amount_target', 0) or 0)
                        targets['sales_amount'] += float(target.get('sales_amount_target', 0) or 0)
                        targets['new_customers'] += int(target.get('new_customers_target', 0) or 0)
                        targets['new_projects'] += int(target.get('new_projects_target', 0) or 0)
                        for key in extra_keys:
                            targets[key] += float(target.get(f'{key}_target', 0) or 0)
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

            # 添加客户活跃度指标
            if user_id:
                activity_data = PerformanceService.calculate_customer_activity_rate(user_id)
                # 客户活跃度是百分比指标，目标暂定为80%
                activity_target = 80
                activity_rate = activity_data['rate']
                # 达成率 = 实际活跃度 / 目标活跃度 * 100
                achievement_rate = (activity_rate / activity_target * 100) if activity_target > 0 else 0
                achievement['customer_activity_rate'] = {
                    'actual': activity_rate,
                    'target': activity_target,
                    'rate': round(achievement_rate, 1),
                    'status': 'success' if achievement_rate >= 100 else ('warning' if achievement_rate >= 80 else 'danger'),
                    # 附加详情数据
                    'highly_active_count': activity_data['highly_active_count'],
                    'active_count': activity_data['active_count'],
                    'total_count': activity_data['total_count']
                }
            else:
                achievement['customer_activity_rate'] = {
                    'actual': 0,
                    'target': 80,
                    'rate': 0,
                    'status': 'danger',
                    'highly_active_count': 0,
                    'active_count': 0,
                    'total_count': 0
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
    def _format_goal_achievement(yearly_stats, targets_dict, configured_items=None, user_id=None, year=None):
        """格式化目标达成数据（用于图表）

        Args:
            yearly_stats: 年度统计数据（12个月）
            targets_dict: 目标值字典 {month: {field: value}}
            configured_items: 用户配置的绩效项目代码列表（可选，None时使用默认4指标）
            user_id: 用户ID（可选，用于获取客户活跃度等快照指标）
            year: 年份（可选，用于从快照表取历史数据）
        """
        try:
            achievement = []

            # yearly_stats 中可用的指标映射: item_code -> (actual_field, target_field)
            stats_field_mapping = {
                'implant_amount': ('implant_amount_actual', 'implant_amount_target'),
                'sales_amount': ('sales_amount_actual', 'sales_amount_target'),
                'new_customers': ('new_customers_actual', 'new_customers_target'),
                'new_projects': ('new_projects_actual', 'new_projects_target'),
                'pm_implant_amount': ('pm_implant_amount_actual', 'pm_implant_amount_target'),
                'pm_sales_amount': ('pm_sales_amount_actual', 'pm_sales_amount_target'),
                'pm_dev_rate': ('pm_dev_rate_actual', 'pm_dev_rate_target'),
                'pm_quality_rate': ('pm_quality_rate_actual', 'pm_quality_rate_target'),
                'pm_support_count': ('pm_support_count_actual', 'pm_support_count_target'),
                'pm_new_launch': ('pm_new_launch_actual', 'pm_new_launch_target'),
                'se_implant_amount': ('se_implant_amount_actual', 'se_implant_amount_target'),
                'se_sales_amount': ('se_sales_amount_actual', 'se_sales_amount_target'),
                'se_response_rate': ('se_response_rate_actual', 'se_response_rate_target'),
                'se_training_count': ('se_training_count_actual', 'se_training_count_target'),
                'se_content_output': ('se_content_output_actual', 'se_content_output_target'),
                'se_satisfaction': ('se_satisfaction_actual', 'se_satisfaction_target'),
                'se_confirm_count': ('se_confirm_count_actual', 'se_confirm_count_target'),
                'se_sales_support': ('se_sales_support_actual', 'se_sales_support_target'),
                'se_confirm_quality': ('se_confirm_quality_actual', 'se_confirm_quality_target'),
            }

            # 客户活跃度：优先从快照取历史数据，当前月用实时计算
            activity_rate = None
            activity_snapshots = {}
            if configured_items and 'customer_activity_rate' in configured_items and user_id:
                activity_data = PerformanceService.calculate_customer_activity_rate(user_id)
                activity_rate = activity_data['rate']
                stat_year = year or datetime.now().year
                activity_snapshots = PerformanceDashboardService.get_activity_snapshots(user_id, stat_year)

            # 获取目标值，兼容新格式(dict)和旧格式(PerformanceTarget对象)
            def get_target_value(target, field, default=0, as_int=False):
                if not target:
                    return default
                if isinstance(target, dict):
                    val = target.get(field, default) or default
                else:
                    val = getattr(target, field, default) or default
                return int(val) if as_int else float(val)

            # 决定要处理的指标列表
            items_to_process = configured_items if configured_items else list(stats_field_mapping.keys())

            for i, stats in enumerate(yearly_stats):
                month = i + 1
                target = targets_dict.get(month)
                month_data = {'month': month}

                for item_code in items_to_process:
                    if item_code in stats_field_mapping:
                        actual_field, target_field = stats_field_mapping[item_code]
                        actual_val = getattr(stats, actual_field, 0) or 0
                        is_int = item_code in ('new_customers', 'new_projects')
                        target_val = get_target_value(target, target_field, as_int=is_int)
                        rate = (actual_val / target_val * 100) if target_val > 0 else 0
                        month_data[item_code] = {
                            'actual': actual_val,
                            'target': target_val,
                            'rate': round(rate, 1)
                        }
                    elif item_code == 'customer_activity_rate':
                        # 当前月用实时值，历史月从快照取
                        target_val = get_target_value(target, 'customer_activity_rate_target', default=0)
                        current_year = datetime.now().year
                        current_month = datetime.now().month
                        is_current = (month == current_month and (year or current_year) == current_year)

                        if is_current:
                            actual = activity_rate or 0
                        else:
                            snapshot = activity_snapshots.get(month)
                            actual = float(snapshot.customer_activity_rate) if snapshot else 0
                        rate = (actual / target_val * 100) if actual and target_val > 0 else 0
                        month_data[item_code] = {
                            'actual': actual,
                            'target': target_val,
                            'rate': round(rate, 1)
                        }

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
            'customer_activity_rate': {
                'actual': 0, 'target': 80, 'rate': 0, 'status': 'danger',
                'highly_active_count': 0, 'active_count': 0, 'total_count': 0
            },
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
            'current_year': datetime.now().year,
            'currency': Config.DEFAULT_CURRENCY  # 默认使用系统货币
        }

    @staticmethod
    def _empty_activity_score():
        """空活跃度数据"""
        return {
            'score': 0,
            'grade': 'D',
            'grade_text': '待提升',
            'breakdown': {
                'action_count': {'value': 0, 'target': 30, 'score': 0, 'weight': 0.20},
                'reply_count': {'value': 0, 'target': 10, 'score': 0, 'weight': 0.10},
                'avg_length': {'value': 0, 'target': 50, 'score': 0, 'weight': 0.15},
                'customer_coverage': {'value': 0, 'target': 100, 'score': 0, 'weight': 0.15},
                'project_link_rate': {'value': 0, 'target': 100, 'score': 0, 'weight': 0.15},
                'customer_activity': {'value': 0, 'target': 100, 'score': 0, 'weight': 0.15},
                'project_activity': {'value': 0, 'target': 100, 'score': 0, 'weight': 0.10},
            },
            'raw_data': {
                'total_customers': 0,
                'covered_customers': 0,
                'total_actions': 0,
                'linked_actions': 0,
                'customer_activity_detail': {
                    'highly_active_count': 0, 'active_count': 0,
                    'normal_count': 0, 'to_follow_count': 0,
                    'dormant_count': 0, 'churned_count': 0,
                    'total_count': 0
                },
                'project_activity_detail': {
                    'healthy_count': 0, 'highly_active_count': 0,
                    'active_count': 0, 'normal_count': 0,
                    'to_follow_count': 0, 'dormant_count': 0,
                    'churned_count': 0, 'total_count': 0,
                    'active_total': 0, 'frozen_count': 0,
                    'stage_breakdown': {}
                }
            }
        }

    @staticmethod
    def get_user_kpi_targets(user_id, year):
        """
        获取用户的所有KPI目标（从 UserPerformanceTarget 读取）

        优先从 UserPerformanceTarget 读取目标值，按优先级拆分到每月：
        月度配置 > 季度÷3 > 年度÷12

        如果无数据，返回空字典让调用方回退到 EmployeeSalaryConfig

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            dict: {month: {target_field: value}} 或空字典
        """
        from app.models.performance_config import UserPerformanceTarget, RolePerformanceTarget

        user_targets = UserPerformanceTarget.query.filter_by(
            user_id=user_id, year=year
        ).all()
        user_map = {t.item_code: t for t in user_targets}

        # 角色默认目标(成员自动继承):个人覆盖 > 角色默认(逐字段合并)
        role_map = {}
        _user = User.query.get(user_id)
        if _user and _user.role:
            role_map = {t.item_code: t for t in RolePerformanceTarget.query.filter_by(
                role_code=_user.role, year=year).all()}

        all_codes = set(user_map) | set(role_map)
        if not all_codes:
            return {}

        # 金额类 item_code 需要从万元转换为元（与 EmployeeSalaryConfig 回退逻辑一致）
        amount_item_codes = {
            'sales_target', 'implant_amount',
            'pm_implant_amount', 'pm_sales_amount',
            'se_implant_amount', 'se_sales_amount',
            'team_sales_amount', 'team_implant_amount',
            'channel_sales_amount', 'channel_implant_amount',
        }
        # 比率/评分类:水平目标(level)——每期目标即该值本身,不做 /12、/3 摊分
        rate_item_codes = {
            'se_response_rate', 'customer_activity_rate',
            'se_confirm_quality', 'se_satisfaction',
            'project_activity_rate', 'team_project_activity_rate',
            'team_customer_activity_rate', 'fail_rate', 'team_fail_rate',
            'channel_customer_activity_rate', 'channel_project_activity_rate', 'channel_fail_rate',
            # 积分制:单项得分为水平值(不按月/季摊分)
            'pm_quality_rate', 'pm_new_launch', 'pm_support_count',
        }

        targets_dict = {}
        for month in range(1, 13):
            targets_dict[month] = {}

        def _eff(code, user_field, role_field):
            """逐字段有效值:个人覆盖非空 > 角色默认"""
            ut, rt = user_map.get(code), role_map.get(code)
            if ut is not None:
                v = getattr(ut, user_field, None)
                if v is not None:
                    return v
            if rt is not None:
                return getattr(rt, role_field, None)
            return None

        for item_code in all_codes:
            target_key = PerformanceDashboardService._map_item_code_to_target_key(item_code)
            if not target_key:
                continue

            # 金额类目标存储单位为万元，需要 * 10000 转为元
            is_amount = item_code in amount_item_codes
            multiplier = 10000 if is_amount else 1

            annual = float(_eff(item_code, 'annual_target_override', 'annual_target') or 0)
            enable_m = bool(_eff(item_code, 'enable_monthly_override', 'enable_monthly'))
            monthly_map = _eff(item_code, 'monthly_targets_override', 'monthly_targets') or {}
            enable_q = bool(_eff(item_code, 'enable_quarterly_override', 'enable_quarterly'))

            is_rate = item_code in rate_item_codes

            for month in range(1, 13):
                monthly_val = 0

                # 优先级: 月度配置 > 季度配置 > 年度
                # 比率/评分类为水平目标:取值本身,不做摊分
                if enable_m and monthly_map:
                    monthly_val = float(monthly_map.get(str(month), 0) or 0)
                elif enable_q:
                    quarter = (month - 1) // 3 + 1
                    q_val = float(_eff(item_code, f'q{quarter}_target_override', f'q{quarter}_target') or 0)
                    monthly_val = q_val if is_rate else (q_val / 3)
                elif annual > 0:
                    monthly_val = annual if is_rate else (annual / 12)

                targets_dict[month][target_key] = monthly_val * multiplier

        return targets_dict

    # 2026-01-08: 删除 _get_user_kpi_targets_legacy 方法，旧的 KPI 目标系统已废弃

    @staticmethod
    def _map_item_code_to_target_key(item_code):
        """将绩效项目代码映射到目标字段名"""
        mapping = {
            'sales_target': 'sales_amount_target',
            'implant_amount': 'implant_amount_target',
            'new_customers': 'new_customers_target',
            'new_projects': 'new_projects_target',
            'pm_implant_amount': 'pm_implant_amount_target',
            'pm_sales_amount': 'pm_sales_amount_target',
            'se_implant_amount': 'se_implant_amount_target',
            'se_sales_amount': 'se_sales_amount_target',
            'se_response_rate': 'se_response_rate_target',
            'se_training_count': 'se_training_count_target',
            'se_content_output': 'se_content_output_target',
            'se_satisfaction': 'se_satisfaction_target',
            'se_confirm_count': 'se_confirm_count_target',
            'se_sales_support': 'se_sales_support_target',
            'se_confirm_quality': 'se_confirm_quality_target',
            'project_activity_rate': 'project_activity_rate_target',
            'team_project_activity_rate': 'team_project_activity_rate_target',
            'quotation_count': 'quotation_count_target',
            'customer_activity_rate': 'customer_activity_rate_target',
            'team_sales_amount': 'team_sales_amount_target',
            'team_implant_amount': 'team_implant_amount_target',
            'team_new_projects': 'team_new_projects_target',
            'team_new_customers': 'team_new_customers_target',
            'team_customer_activity_rate': 'team_customer_activity_rate_target',
            'fail_rate': 'fail_rate_target',
            'team_fail_rate': 'team_fail_rate_target',
            'channel_sales_amount': 'channel_sales_amount_target',
            'channel_implant_amount': 'channel_implant_amount_target',
            'channel_new_projects': 'channel_new_projects_target',
            'channel_new_customers': 'channel_new_customers_target',
            'channel_customer_activity_rate': 'channel_customer_activity_rate_target',
            'channel_project_activity_rate': 'channel_project_activity_rate_target',
            'channel_fail_rate': 'channel_fail_rate_target',
            'channel_new_dealers': 'channel_new_dealers_target',
            'pm_dev_rate': 'pm_dev_rate_target',
            'pm_new_launch': 'pm_new_launch_target',
            'pm_quality_rate': 'pm_quality_rate_target',
            'pm_support_count': 'pm_support_count_target',
        }
        return mapping.get(item_code)

    @staticmethod
    def has_kpi_config(user, year=None):
        """单一事实源:该用户是否有「会渲染出来」的 KPI 考核项。

        决定仪表盘 KPI 卡 / 绩效入口是否显示——配置驱动,不再按角色硬编码。
        口径与 at_dashboard_helpers._kpi_config_driven 一致:
          - 有角色方案(ROLE_KPI_SCHEMES) → 显示(考核项写死,始终全显)
          - 否则:配了「个人覆盖 / 角色默认」考核项,且至少一项有目标(>0)→ 显示
        """
        if not user:
            return False
        from datetime import datetime
        year = year or datetime.now().year
        role = getattr(user, 'role', None) or ''
        # 1) 方案角色:始终显示
        try:
            from app.services.role_kpi_schemes import get_role_scheme_codes
            if get_role_scheme_codes(role):
                return True
        except Exception:
            pass
        # 2) 配置的考核项(个人覆盖;无则回退角色默认行)
        try:
            codes = PerformanceDashboardService._get_configured_performance_items(user.id, year) or []
        except Exception:
            codes = []
        if not codes and role:
            try:
                from app.models.performance_config import RolePerformanceTarget
                rows = RolePerformanceTarget.query.filter_by(role_code=role, year=year).all()
                codes = [r.item_code for r in rows if getattr(r, 'enabled', True) is not False]
            except Exception:
                codes = []
        if not codes:
            return False
        # 3) 非方案角色:至少一项配了目标(>0),否则视为未配置(避免空卡)
        try:
            tmap = PerformanceDashboardService.get_user_kpi_targets(user.id, year) or {}
            for c in codes:
                tkey = f'{c}_target'
                if any(float((tmap.get(m) or {}).get(tkey, 0) or 0) > 0 for m in range(1, 13)):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _get_configured_performance_items(user_id, year):
        """
        获取用户配置的绩效项目代码列表

        从用户绩效配置 (UserPerformanceTarget) 读取，如果没有配置则返回空列表

        Args:
            user_id: 用户ID
            year: 年份

        Returns:
            list: 绩效项目代码列表
        """
        from app.models.performance_config import UserPerformanceTarget

        # item_code 到看板 metric_code 的映射
        item_code_mapping = {
            'sales_target': 'sales_amount',
            'implant_amount': 'implant_amount',
            'new_customers': 'new_customers',
            'new_projects': 'new_projects',
            'customer_activity_rate': 'customer_activity_rate',
            'high_price_amount': 'high_price_amount',
            'quotation_count': 'quotation_count',
            'pm_implant_amount': 'pm_implant_amount',
            'pm_sales_amount': 'pm_sales_amount',
            'se_implant_amount': 'se_implant_amount',
            'se_sales_amount': 'se_sales_amount',
            'se_response_rate': 'se_response_rate',
            'se_training_count': 'se_training_count',
            'se_content_output': 'se_content_output',
            'se_satisfaction': 'se_satisfaction',
            'se_confirm_count': 'se_confirm_count',
            'se_sales_support': 'se_sales_support',
            'se_confirm_quality': 'se_confirm_quality',
            'project_activity_rate': 'project_activity_rate',
            'team_project_activity_rate': 'team_project_activity_rate',
            'team_sales_amount': 'team_sales_amount',
            'team_implant_amount': 'team_implant_amount',
            'team_new_projects': 'team_new_projects',
            'team_new_customers': 'team_new_customers',
            'team_customer_activity_rate': 'team_customer_activity_rate',
            'fail_rate': 'fail_rate',
            'team_fail_rate': 'team_fail_rate',
            'channel_sales_amount': 'channel_sales_amount',
            'channel_implant_amount': 'channel_implant_amount',
            'channel_new_projects': 'channel_new_projects',
            'channel_new_customers': 'channel_new_customers',
            'channel_customer_activity_rate': 'channel_customer_activity_rate',
            'channel_project_activity_rate': 'channel_project_activity_rate',
            'channel_fail_rate': 'channel_fail_rate',
            'channel_new_dealers': 'channel_new_dealers',
            'pm_dev_rate': 'pm_dev_rate',
            'pm_new_launch': 'pm_new_launch',
            'pm_quality_rate': 'pm_quality_rate',
            'pm_support_count': 'pm_support_count',
        }

        try:
            # 角色写死考核方案优先:有方案的角色考核项由方案决定,不再看勾选
            from app.services.role_kpi_schemes import get_role_scheme_codes
            user_obj = User.query.get(user_id)
            if user_obj:
                scheme_codes = get_role_scheme_codes(user_obj.role)
                if scheme_codes:
                    return [item_code_mapping.get(c, c) for c in scheme_codes]

            # 从用户绩效配置读取
            user_targets = UserPerformanceTarget.query.filter_by(
                user_id=user_id, year=year
            ).all()

            if not user_targets:
                # 当前年份无配置，回退到最近一年的配置
                latest_target = UserPerformanceTarget.query.filter_by(
                    user_id=user_id
                ).order_by(UserPerformanceTarget.year.desc()).first()

                if latest_target:
                    user_targets = UserPerformanceTarget.query.filter_by(
                        user_id=user_id, year=latest_target.year
                    ).all()

            if not user_targets:
                return []

            # 转换为看板指标代码(个人行 ∪ 角色默认行:
            # 角色后续新增的默认考核项,对已有个人配置的成员同样生效)
            configured_codes = []
            for target in user_targets:
                item_code = target.item_code
                mapped_code = item_code_mapping.get(item_code, item_code)
                if mapped_code not in configured_codes:
                    configured_codes.append(mapped_code)

            try:
                from app.models.performance_config import RolePerformanceTarget
                if user_obj and user_obj.role:
                    for rt in RolePerformanceTarget.query.filter_by(
                            role_code=user_obj.role, year=year).all():
                        mapped = item_code_mapping.get(rt.item_code, rt.item_code)
                        if mapped not in configured_codes:
                            configured_codes.append(mapped)
            except Exception:
                pass

            return configured_codes

        except Exception as e:
            logger.warning(f"读取用户绩效配置失败: {e}，返回空列表")
            return []

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

            # 转换为与summary相同的格式（元）
            # team_achievement 和 team_target 原单位是万元，需乘10000转为元
            team_summary = {
                'sales_amount': {
                    'actual': team_perf['team_achievement'] * 10000,
                    'target': team_perf['team_target'] * 10000,
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

    # === 季度绩效得分 ===

    @staticmethod
    def get_quarterly_scores(user_id, year):
        """计算用户按季度的绩效得分

        从 role_performance_items 获取权重，从 yearly_stats 获取实际值，
        对比目标值计算达成率和加权得分。

        Returns:
            dict: {Q1: {total_score, total_weight, items: [...]}, Q2: ..., Q3: ..., Q4: ...}
        """
        from app.models.performance_config import RolePerformanceConfig, RolePerformanceItem

        try:
            # 获取用户角色
            user = User.query.get(user_id)
            if not user:
                return {}

            # 角色写死考核方案优先(含权重);无方案才走 DB 角色配置
            from app.services.role_kpi_schemes import get_role_scheme
            scheme = get_role_scheme(user.role)
            if scheme:
                from types import SimpleNamespace
                from app.models.performance_config import PerformanceMetricsDefinition
                _name_fallback = {
                    'se_confirm_count': '报价确认量', 'se_sales_support': '销售配合广度',
                    'se_confirm_quality': '确认质量', 'se_implant_amount': '方案植入额',
                    'se_sales_amount': '方案批价额',
                }
                _defs = {m.metric_code: m.metric_name
                         for m in PerformanceMetricsDefinition.query.filter(
                             PerformanceMetricsDefinition.metric_code.in_(
                                 [it['item_code'] for it in scheme])).all()}
                # 权重:角色级覆盖(role_performance_targets.weight) > 岗位方案默认
                from app.models.performance_config import RolePerformanceTarget
                _w_over = {t.item_code: float(t.weight)
                           for t in RolePerformanceTarget.query.filter_by(
                               role_code=user.role, year=year).all()
                           if getattr(t, 'weight', None) is not None}
                items = [SimpleNamespace(
                            item_code=it['item_code'],
                            weight=_w_over.get(it['item_code'], it['weight']),
                            item_name=_defs.get(it['item_code'])
                                      or _name_fallback.get(it['item_code'], it['item_code']))
                         for it in scheme]
            else:
                role_config = RolePerformanceConfig.query.filter_by(
                    role=user.role, is_active=True
                ).first()

                if not role_config:
                    return {}

                items = RolePerformanceItem.query.filter_by(
                    role_config_id=role_config.id, is_enabled=True
                ).order_by(RolePerformanceItem.sort_order).all()

                if not items:
                    return {}

            # 获取完整看板数据（含所有指标的月度数据）
            dashboard_data = PerformanceDashboardService.get_dashboard_data(user_id, year, lite=False)
            goal_achievement = dashboard_data.get('goal_achievement', [])

            # 获取目标数据
            targets_dict = PerformanceDashboardService.get_user_kpi_targets(user_id, year)

            # item_code 到看板 metric_code 的映射
            code_mapping = {
                'sales_target': 'sales_amount',
                'implant_amount': 'implant_amount',
                'new_customers': 'new_customers',
                'new_projects': 'new_projects',
                'customer_activity_rate': 'customer_activity_rate',
                'pm_implant_amount': 'pm_implant_amount',
                'pm_sales_amount': 'pm_sales_amount',
                'se_implant_amount': 'se_implant_amount',
                'se_sales_amount': 'se_sales_amount',
                'se_response_rate': 'se_response_rate',
                'se_training_count': 'se_training_count',
                'se_content_output': 'se_content_output',
                'se_satisfaction': 'se_satisfaction',
                'se_confirm_count': 'se_confirm_count',
                'se_sales_support': 'se_sales_support',
                'se_confirm_quality': 'se_confirm_quality',
            }

            # 计分方式单一事实源(scoring_mode + data_type),供下方分支
            from app.helpers.scoring_modes import (
                load_metric_meta as _load_meta, scoring_mode_of as _scoring_mode_of,
                is_avg_aggregated as _is_avg_aggregated,
                tiered_achievement as _tiered_achievement)
            _metric_meta = _load_meta()

            result = {}
            for quarter in range(1, 5):
                start_month = (quarter - 1) * 3  # 0-indexed into goal_achievement list
                quarter_items = []
                total_score = 0
                total_weight = 0

                for item in items:
                    metric_code = code_mapping.get(item.item_code, item.item_code)
                    weight = float(item.weight or 0)
                    mode = _scoring_mode_of(metric_code, _metric_meta)
                    _dtype = (_metric_meta.get(metric_code) or {}).get('data_type')
                    is_avg = _is_avg_aggregated(_dtype)   # 率/评分类跨期取平均

                    # 汇总季度3个月:累加实际/目标 + 记录水平目标(首个非零)与有数据月数
                    q_actual_sum = 0.0
                    q_target_sum = 0.0
                    level_target = 0.0
                    months_with_data = 0
                    for m_idx in range(start_month, min(start_month + 3, len(goal_achievement))):
                        md = goal_achievement[m_idx].get(metric_code, {})
                        a = md.get('actual', 0) or 0
                        t = md.get('target', 0) or 0
                        q_actual_sum += a
                        q_target_sum += t
                        if a > 0:
                            months_with_data += 1
                        if t > 0 and level_target == 0:
                            level_target = t

                    if mode == 'tiered':
                        # 固定档位制(植入品质):实际取季度均值(水平值),按及格/良好两线换算;
                        # 阈值写死,无目标,权重恒计入分母。
                        q_actual = (q_actual_sum / months_with_data) if months_with_data > 0 else 0
                        total_weight += weight
                        achievement_rate = round(_tiered_achievement(q_actual), 1)
                        weighted_score = achievement_rate * weight / 100
                        q_target = 0
                    elif mode == 'cumulative':
                        # 积分制:单项得分(水平值)× 实际累计,封顶权重;权重恒计入(不做=0分,不归一)
                        per_unit = level_target if level_target > 0 else 1.0
                        total_weight += weight
                        weighted_score = min(q_actual_sum * per_unit, weight)
                        achievement_rate = round(weighted_score / weight * 100, 1) if weight > 0 else 0
                        q_actual, q_target = q_actual_sum, per_unit
                    else:
                        # 目标制/反向:率类取平均,其余累加;无目标→整项剔除(不计权重,与前端一致)
                        if is_avg:
                            q_actual = (q_actual_sum / months_with_data) if months_with_data > 0 else 0
                            q_target = level_target
                        else:
                            q_actual, q_target = q_actual_sum, q_target_sum
                        if q_target <= 0:
                            continue
                        total_weight += weight
                        if mode == 'inverse':
                            achievement_rate = 100 if q_actual <= q_target else min(q_target / q_actual * 100, 100)
                        else:
                            achievement_rate = min(q_actual / q_target * 100, 100)
                        weighted_score = achievement_rate * weight / 100

                    total_score += weighted_score

                    quarter_items.append({
                        'code': metric_code,
                        'name': item.item_name,
                        'weight': weight,
                        'mode': mode,
                        'target': round(q_target, 2),
                        'actual': round(q_actual, 2),
                        'achievement_rate': round(achievement_rate, 1),
                        'weighted_score': round(weighted_score, 1),
                    })

                result[f'Q{quarter}'] = {
                    'total_score': round(total_score, 1),
                    'total_weight': round(total_weight, 1),
                    'items': quarter_items,
                }

            return result

        except Exception as e:
            logger.error(f"计算季度绩效得分失败: {e}")
            return {}

    # === 月度活跃度快照 ===

    @staticmethod
    def create_monthly_activity_snapshot(user_id, year, month):
        """计算并存储某月的活跃度快照（upsert）"""
        try:
            customer_data = PerformanceService.calculate_customer_activity_rate(user_id)
            project_data = PerformanceService.calculate_project_activity_rate(user_id)

            snapshot = MonthlyActivitySnapshot.query.filter_by(
                user_id=user_id, year=year, month=month
            ).first()
            if not snapshot:
                snapshot = MonthlyActivitySnapshot(user_id=user_id, year=year, month=month)
                db.session.add(snapshot)

            # 客户活跃度
            snapshot.customer_total = customer_data.get('total_count', 0)
            snapshot.customer_highly_active = customer_data.get('highly_active_count', 0)
            snapshot.customer_active = customer_data.get('active_count', 0)
            snapshot.customer_normal = customer_data.get('normal_count', 0)
            snapshot.customer_to_follow = customer_data.get('to_follow_count', 0)
            snapshot.customer_dormant = customer_data.get('dormant_count', 0)
            snapshot.customer_churned = customer_data.get('churned_count', 0)
            snapshot.customer_activity_rate = customer_data.get('rate', 0)

            # 项目活跃度
            snapshot.project_total = project_data.get('total_count', 0)
            snapshot.project_highly_active = project_data.get('highly_active_count', 0)
            snapshot.project_active = project_data.get('active_count', 0)
            snapshot.project_normal = project_data.get('normal_count', 0)
            snapshot.project_to_follow = project_data.get('to_follow_count', 0)
            snapshot.project_dormant = project_data.get('dormant_count', 0)
            snapshot.project_churned = project_data.get('churned_count', 0)
            snapshot.project_frozen = project_data.get('frozen_count', 0)
            snapshot.project_activity_rate = project_data.get('rate', 0)

            snapshot.calculated_at = datetime.utcnow()
            db.session.commit()
            return snapshot
        except Exception as e:
            db.session.rollback()
            logger.warning(f"创建活跃度快照失败: user_id={user_id}, {year}-{month}, error={e}")
            return None

    @staticmethod
    def get_activity_snapshots(user_id, year):
        """获取某用户某年的月度快照 {month: snapshot}"""
        snapshots = MonthlyActivitySnapshot.query.filter_by(
            user_id=user_id, year=year
        ).order_by(MonthlyActivitySnapshot.month).all()
        return {s.month: s for s in snapshots}
