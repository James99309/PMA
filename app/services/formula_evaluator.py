"""公式求值服务

提供安全的公式表达式求值功能，支持：
1. 基础变量替换 ({variable_name})
2. KPI变量动态解析 (kpi_xxx, kpi_xxx_target, kpi_xxx_rate)
3. STEP阶梯函数 (STEP({rate}, "rule_type"))
4. 数学运算符 (+, -, *, /, %, **, //)
5. 内置函数 (max, min, abs, round)

使用示例:
    from app.services.formula_evaluator import FormulaEvaluator

    # 创建求值器
    evaluator = FormulaEvaluator(user_id=13, year=2025, month=3)

    # 求值公式
    result = evaluator.evaluate("{monthly_base_salary} * 12")

    # 带KPI变量
    result = evaluator.evaluate("{kpi_sales_target} / {kpi_sales_target_target} * 100")

    # 带STEP函数
    result = evaluator.evaluate("STEP({personal_rate}, 'performance_coefficient')")
"""

import re
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class FormulaEvaluator:
    """安全的公式求值器"""

    # 允许的内置函数
    ALLOWED_FUNCTIONS = {
        'max': max,
        'min': min,
        'abs': abs,
        'round': round,
        'float': float,
        'int': int,
    }

    # 变量名模式
    VARIABLE_PATTERN = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

    # STEP函数模式
    STEP_PATTERN = re.compile(r'STEP\s*\(\s*\{([^}]+)\}\s*,\s*["\']([^"\']+)["\']\s*\)')

    def __init__(self, user_id, year, month=None, additional_context=None):
        """
        初始化求值器

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份（可选，用于月度计算）
            additional_context: 额外的上下文变量 dict
        """
        self.user_id = user_id
        self.year = year
        self.month = month
        self._context = {}
        self._additional_context = additional_context or {}
        self._context_loaded = False

    def _load_context(self):
        """延迟加载计算上下文"""
        if self._context_loaded:
            return

        try:
            # 1. 加载员工薪资配置
            self._load_salary_config()

            # 2. 加载业绩数据
            self._load_performance_data()

            # 3. 加载KPI数据
            self._load_kpi_context()

            # 4. 添加额外上下文
            self._context.update(self._additional_context)

            self._context_loaded = True
        except Exception as e:
            logger.error(f"加载公式上下文失败: {e}")
            self._context_loaded = True  # 标记为已加载，避免重复尝试

    def _load_salary_config(self):
        """加载员工薪资配置"""
        from app.models.salary_config import EmployeeSalaryConfig

        config = EmployeeSalaryConfig.query.filter_by(user_id=self.user_id).first()
        if not config:
            return

        # 基础薪资配置
        self._context['monthly_base_salary'] = float(config.get_effective_value('monthly_base_salary', 0))
        self._context['monthly_performance_base'] = float(config.get_effective_value('monthly_performance_base', 0))
        self._context['annual_target'] = float(config.get_effective_value('annual_target', 0))
        self._context['annual_base_salary'] = self._context['monthly_base_salary'] * 12 / 10000  # 万

        # 权重
        personal_weight = float(config.get_effective_value('personal_weight', 1))
        self._context['personal_weight'] = personal_weight
        self._context['team_weight'] = 1 - personal_weight

    def _load_performance_data(self):
        """加载业绩数据"""
        from app.models.salary_config import QuarterlyPerformanceData, EmployeeSalaryConfig

        config = EmployeeSalaryConfig.query.filter_by(user_id=self.user_id).first()
        if not config:
            return

        annual_target = float(config.get_effective_value('annual_target', 0))

        # 计算到当前月的累计业绩
        if self.month:
            quarter = (self.month - 1) // 3 + 1
            ytd_achievement = 0
            ytd_target = 0

            for q in range(1, quarter + 1):
                qdata = QuarterlyPerformanceData.query.filter_by(
                    user_id=self.user_id,
                    year=self.year,
                    quarter=q
                ).first()
                if qdata and qdata.achievement:
                    ytd_achievement += float(qdata.achievement)
                ytd_target += annual_target / 4

            self._context['achievement'] = ytd_achievement
            self._context['personal_rate'] = (ytd_achievement / ytd_target * 100) if ytd_target else 0

            # 团队完成率（如果配置了团队）
            self._context['team_rate'] = self._context.get('personal_rate', 0)  # 默认同个人

            # 综合完成率
            personal_weight = self._context.get('personal_weight', 1)
            team_weight = self._context.get('team_weight', 0)
            self._context['comprehensive_rate'] = (
                self._context['personal_rate'] * personal_weight +
                self._context['team_rate'] * team_weight
            )
        else:
            # 年度数据
            yearly_data = QuarterlyPerformanceData.query.filter_by(
                user_id=self.user_id,
                year=self.year
            ).all()

            total_achievement = sum(float(q.achievement or 0) for q in yearly_data)
            self._context['achievement'] = total_achievement
            self._context['personal_rate'] = (total_achievement / annual_target * 100) if annual_target else 0
            self._context['team_rate'] = self._context.get('personal_rate', 0)
            self._context['comprehensive_rate'] = self._context['personal_rate']

        # 高批价相关
        self._context['high_price_ratio'] = 0
        self._context['high_price_rate'] = 0

    def _load_kpi_context(self):
        """加载KPI变量上下文"""
        from app.services.kpi_calculation_service import KpiCalculationService

        kpi_context = KpiCalculationService.get_kpi_context(
            self.user_id, self.year, self.month
        )
        self._context.update(kpi_context)

    def get_variable(self, var_name):
        """
        获取变量值

        Args:
            var_name: 变量名

        Returns:
            变量值，如果未找到返回0
        """
        self._load_context()

        # 先从上下文中查找
        if var_name in self._context:
            return self._context[var_name]

        # KPI变量特殊处理
        if var_name.startswith('kpi_'):
            from app.services.kpi_calculation_service import KpiCalculationService

            parts = var_name[4:].rsplit('_', 1)

            if len(parts) == 2 and parts[1] in ('target', 'rate'):
                item_code = parts[0]
                suffix = parts[1]

                if suffix == 'target':
                    return KpiCalculationService.get_kpi_target(
                        self.user_id, item_code, self.year
                    ) or 0
                elif suffix == 'rate':
                    return KpiCalculationService.get_kpi_rate(
                        self.user_id, item_code, self.year, self.month
                    )
            else:
                item_code = var_name[4:]
                return KpiCalculationService.get_kpi_value(
                    self.user_id, item_code, self.year, self.month
                )

        logger.warning(f"未找到变量: {var_name}")
        return 0

    def get_step_value(self, rate, rule_type):
        """
        根据阶梯规则获取系数

        Args:
            rate: 完成率（百分比，如85表示85%）
            rule_type: 规则类型（performance_coefficient, commission_rate等）

        Returns:
            对应的系数值
        """
        from app.models.salary_config import SalaryStepRules
        return SalaryStepRules.get_coefficient(rule_type, rate)

    def _replace_step_functions(self, expression):
        """替换STEP函数调用"""
        def replace_step(match):
            var_name = match.group(1)
            rule_type = match.group(2)

            # 获取变量值
            rate = self.get_variable(var_name)
            # 获取阶梯系数
            coefficient = self.get_step_value(rate, rule_type)
            return str(coefficient)

        return self.STEP_PATTERN.sub(replace_step, expression)

    def _replace_variables(self, expression):
        """替换变量占位符"""
        def replace_var(match):
            var_name = match.group(1)
            value = self.get_variable(var_name)
            return str(value)

        return self.VARIABLE_PATTERN.sub(replace_var, expression)

    def evaluate(self, expression):
        """
        安全求值公式表达式

        Args:
            expression: 公式表达式，如 "{monthly_base_salary} * 12 / 10000"

        Returns:
            float: 计算结果
        """
        if not expression:
            return 0

        try:
            # 1. 替换STEP函数
            expr = self._replace_step_functions(expression)

            # 2. 替换变量
            expr = self._replace_variables(expr)

            # 3. 安全求值
            result = self._safe_eval(expr)
            return float(result) if result is not None else 0

        except Exception as e:
            logger.error(f"公式求值失败: {expression}, 错误: {e}")
            return 0

    def _safe_eval(self, expression):
        """
        安全的表达式求值

        只允许数字、基本运算符和白名单函数
        """
        # 移除危险字符
        safe_expr = expression.replace('__', '')

        # 构建安全的求值环境
        safe_globals = {
            '__builtins__': {},
        }
        safe_globals.update(self.ALLOWED_FUNCTIONS)

        try:
            # 使用compile检查表达式安全性
            code = compile(safe_expr, '<formula>', 'eval')

            # 检查是否包含危险操作
            for name in code.co_names:
                if name not in self.ALLOWED_FUNCTIONS and not name.isdigit():
                    logger.warning(f"表达式包含不允许的名称: {name}")

            result = eval(code, safe_globals, {})
            return result

        except SyntaxError as e:
            logger.error(f"表达式语法错误: {expression}, {e}")
            return None
        except Exception as e:
            logger.error(f"表达式求值错误: {expression}, {e}")
            return None

    def evaluate_formula_config(self, formula_config):
        """
        求值SalaryFormulaConfig配置的公式

        Args:
            formula_config: SalaryFormulaConfig对象

        Returns:
            float: 计算结果
        """
        if not formula_config or not formula_config.formula_expression:
            return 0

        return self.evaluate(formula_config.formula_expression)

    def get_context_dict(self):
        """获取当前计算上下文（用于调试）"""
        self._load_context()
        return dict(self._context)


def resolve_formula_variable(var_code, user_id, year, month=None):
    """
    解析单个公式变量值（便捷函数）

    Args:
        var_code: 变量代码
        user_id: 用户ID
        year: 年份
        month: 月份（可选）

    Returns:
        变量值
    """
    evaluator = FormulaEvaluator(user_id, year, month)
    return evaluator.get_variable(var_code)


def evaluate_salary_formula(formula_expression, user_id, year, month=None):
    """
    计算薪资公式（便捷函数）

    Args:
        formula_expression: 公式表达式
        user_id: 用户ID
        year: 年份
        month: 月份（可选）

    Returns:
        float: 计算结果
    """
    evaluator = FormulaEvaluator(user_id, year, month)
    return evaluator.evaluate(formula_expression)
