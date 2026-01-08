"""KPI实际值计算服务

根据PerformanceMetricsDefinition中配置的data_source_config自动计算KPI实际值
支持从多种数据模型（PricingOrder, Quotation, Project, Company等）汇总计算

使用示例:
    from app.services.kpi_calculation_service import KpiCalculationService

    # 获取某用户某年某月的销售额KPI
    value = KpiCalculationService.get_kpi_value(
        user_id=13,
        item_code='sales_target',
        year=2025,
        month=3
    )

    # 获取年度累计值
    annual_value = KpiCalculationService.get_kpi_value(
        user_id=13,
        item_code='sales_target',
        year=2025
    )
"""

from datetime import datetime
from sqlalchemy import func
from app import db
import logging

logger = logging.getLogger(__name__)


class KpiCalculationService:
    """KPI实际值计算服务"""

    # 支持的数据模型映射
    MODEL_MAPPING = {
        'PricingOrder': 'app.models.pricing_order.PricingOrder',
        'Quotation': 'app.models.quotation.Quotation',
        'Project': 'app.models.project.Project',
        'Company': 'app.models.customer.Company',
    }

    @staticmethod
    def get_kpi_value(user_id, item_code, year, month=None):
        """
        根据item_code获取KPI实际值

        Args:
            user_id: 用户ID
            item_code: KPI项目代码（如 sales_target, new_customers）
            year: 年份
            month: 月份（可选，不填则返回年度累计）

        Returns:
            float: KPI实际值，如果无法计算则返回0
        """
        from app.models.performance_config import PerformanceMetricsDefinition

        try:
            # 查找指标定义
            metric = PerformanceMetricsDefinition.query.filter_by(
                metric_code=item_code,
                is_active=True
            ).first()

            if not metric:
                logger.warning(f"未找到KPI定义: {item_code}")
                return 0

            # 获取数据源配置
            config = metric.available_sources
            if not config:
                # 没有数据源配置，可能是手动录入类型
                return KpiCalculationService._get_manual_value(user_id, item_code, year, month)

            source_type = config.get('type')
            if source_type == 'manual':
                return KpiCalculationService._get_manual_value(user_id, item_code, year, month)

            # 自动计算类型
            return KpiCalculationService._calculate_from_source(
                user_id, config, year, month
            )

        except Exception as e:
            logger.error(f"计算KPI值失败 user_id={user_id}, item_code={item_code}: {e}")
            return 0

    @staticmethod
    def _get_manual_value(user_id, item_code, year, month=None):
        """
        获取手动录入的KPI值

        TODO: 需要创建KPI实际值录入表来存储手动录入的数据
        目前返回0
        """
        # 手动录入类，从统计表读取（待实现）
        return 0

    @staticmethod
    def _calculate_from_source(user_id, config, year, month=None):
        """
        从数据源自动计算KPI值

        Args:
            user_id: 用户ID
            config: 数据源配置 {
                'model': 'PricingOrder',
                'field': 'pricing_total_amount',
                'aggregate': 'sum',  # sum, count, avg
                'filter': {'status': 'approved', 'created_by': '{user_id}'},
                'date_field': 'approved_at'
            }
            year: 年份
            month: 月份（可选）

        Returns:
            float: 计算得到的KPI值
        """
        model_name = config.get('model')
        field = config.get('field', 'id')
        aggregate = config.get('aggregate', 'sum')
        date_field = config.get('date_field', 'created_at')
        filters = config.get('filter', {})

        # 获取模型类
        Model = KpiCalculationService._get_model_class(model_name)
        if not Model:
            logger.warning(f"未找到模型类: {model_name}")
            return 0

        try:
            # 构建基础查询
            query = db.session.query(Model)

            # 应用过滤条件
            for key, value in filters.items():
                if not hasattr(Model, key):
                    continue

                # 替换占位符
                if value == '{user_id}':
                    value = user_id

                query = query.filter(getattr(Model, key) == value)

            # 日期范围过滤
            if hasattr(Model, date_field):
                date_column = getattr(Model, date_field)

                if month:
                    # 月度数据
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1)
                    else:
                        end_date = datetime(year, month + 1, 1)
                else:
                    # 年度数据
                    start_date = datetime(year, 1, 1)
                    end_date = datetime(year + 1, 1, 1)

                query = query.filter(
                    date_column >= start_date,
                    date_column < end_date
                )

            # 聚合计算
            if aggregate == 'count':
                result = query.count()
            elif hasattr(Model, field):
                field_column = getattr(Model, field)
                if aggregate == 'sum':
                    result = query.with_entities(func.sum(field_column)).scalar()
                elif aggregate == 'avg':
                    result = query.with_entities(func.avg(field_column)).scalar()
                else:
                    result = query.with_entities(func.sum(field_column)).scalar()
            else:
                result = 0

            return float(result) if result else 0

        except Exception as e:
            logger.error(f"从数据源计算KPI值失败: {e}", exc_info=True)
            return 0

    @staticmethod
    def _get_model_class(model_name):
        """
        根据模型名称获取模型类

        Args:
            model_name: 模型名称（如 'PricingOrder'）

        Returns:
            Model class or None
        """
        try:
            if model_name == 'PricingOrder':
                from app.models.pricing_order import PricingOrder
                return PricingOrder
            elif model_name == 'Quotation':
                from app.models.quotation import Quotation
                return Quotation
            elif model_name == 'Project':
                from app.models.project import Project
                return Project
            elif model_name == 'Company':
                from app.models.customer import Company
                return Company
            else:
                logger.warning(f"不支持的模型类型: {model_name}")
                return None
        except ImportError as e:
            logger.error(f"导入模型失败: {model_name}, {e}")
            return None

    @staticmethod
    def get_kpi_target(user_id, item_code, year):
        """
        获取用户的KPI目标值

        2026-01-08: 废弃旧的 RolePerformanceTarget/UserPerformanceTarget 系统
        统一使用 EmployeeSalaryConfig，返回 None 让调用方回退到新系统

        Args:
            user_id: 用户ID
            item_code: KPI项目代码
            year: 年份

        Returns:
            None: 已废弃，返回 None
        """
        # 废弃旧系统，返回 None 让调用方使用 EmployeeSalaryConfig
        return None

    @staticmethod
    def get_kpi_rate(user_id, item_code, year, month=None):
        """
        计算KPI完成率

        Args:
            user_id: 用户ID
            item_code: KPI项目代码
            year: 年份
            month: 月份（可选）

        Returns:
            float: 完成率百分比（如 85.5 表示85.5%），如果无法计算则返回0
        """
        actual = KpiCalculationService.get_kpi_value(user_id, item_code, year, month)
        target = KpiCalculationService.get_kpi_target(user_id, item_code, year)

        if not target or target == 0:
            return 0

        # 如果是月度数据，需要按比例计算目标
        if month:
            # 假设目标均匀分布到每个月
            monthly_target = target / 12
            # 计算到该月为止的累计目标
            ytd_target = monthly_target * month
            # 获取到该月为止的累计实际值
            ytd_actual = 0
            for m in range(1, month + 1):
                ytd_actual += KpiCalculationService.get_kpi_value(user_id, item_code, year, m)
            return (ytd_actual / ytd_target * 100) if ytd_target else 0
        else:
            return (actual / target * 100) if target else 0

    @staticmethod
    def get_all_kpi_values(user_id, year, month=None):
        """
        获取用户所有启用的KPI的实际值

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份（可选）

        Returns:
            dict: {item_code: value}
        """
        from app.models.performance_config import PerformanceMetricsDefinition

        result = {}
        metrics = PerformanceMetricsDefinition.query.filter_by(is_active=True).all()

        for metric in metrics:
            result[metric.metric_code] = KpiCalculationService.get_kpi_value(
                user_id, metric.metric_code, year, month
            )

        return result

    @staticmethod
    def get_kpi_context(user_id, year, month=None):
        """
        获取用于公式计算的KPI上下文

        返回包含所有KPI变量的字典，可直接用于公式求值

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份（可选）

        Returns:
            dict: {
                'kpi_sales_target': 150.5,
                'kpi_sales_target_target': 200.0,
                'kpi_sales_target_rate': 75.25,
                ...
            }
        """
        from app.models.performance_config import PerformanceMetricsDefinition

        context = {}
        metrics = PerformanceMetricsDefinition.query.filter_by(is_active=True).all()

        for metric in metrics:
            code = metric.metric_code

            # 实际值
            actual = KpiCalculationService.get_kpi_value(user_id, code, year, month)
            context[f'kpi_{code}'] = actual

            # 目标值
            target = KpiCalculationService.get_kpi_target(user_id, code, year)
            context[f'kpi_{code}_target'] = target or 0

            # 完成率
            rate = (actual / target * 100) if target and target > 0 else 0
            context[f'kpi_{code}_rate'] = rate

        return context
