"""跨货币聚合统计服务

统一封装"按货币分组求和 + 换算到目标货币"的逻辑。

核心价值：
- 性能接近原生 SUM 查询（仅多 1-3 次 Python 层转换，而非 N 次逐笔循环）
- 统一使用 Config.DEFAULT_CURRENCY 作为显示货币（SP8D=CNY, OVS=USD）
- 供所有跨单据/跨货币统计点调用，避免重复实现

典型用法：
    # 报价单列表统计
    total = MultiCurrencyAggregationService.sum_converted(
        query, Quotation.amount, Quotation.currency
    )

    # 按状态分组的多个统计
    stats = MultiCurrencyAggregationService.sum_converted_with_conditions(
        query, Quotation.amount, Quotation.currency,
        {
            'total': None,
            'approved': Quotation.approval_status == 'approved',
            'pending': Quotation.approval_status.in_(['pending', 'in_progress']),
            'draft': Quotation.approval_status == 'draft',
        }
    )
    # 返回：{'total': 1200000, 'approved': 800000, 'pending': 300000, 'draft': 100000}
"""

from sqlalchemy import func, case
from app import db
from app.services.exchange_rate_service import exchange_rate_service
from config import Config


class MultiCurrencyAggregationService:
    """跨货币聚合统计服务"""

    @staticmethod
    def get_display_currency():
        """获取统计显示货币 —— 统一使用系统默认货币

        SP8D 环境：CNY
        OVS 环境：USD
        """
        return Config.DEFAULT_CURRENCY

    @staticmethod
    def _convert(amount, from_currency, to_currency):
        """内部换算，处理同货币短路和空值

        Args:
            amount: 金额（可能是 Decimal/float/None）
            from_currency: 源货币（None 时视为目标货币）
            to_currency: 目标货币
        """
        if amount is None:
            return 0.0
        amt = float(amount)
        if amt == 0:
            return 0.0
        src = (from_currency or to_currency).upper()
        dst = to_currency.upper()
        if src == dst:
            return amt
        return float(exchange_rate_service.convert_amount(amt, src, dst))

    @classmethod
    def sum_converted(cls, query, amount_column, currency_column, target_currency=None):
        """跨货币求和 —— 基础方法

        先在数据库层按货币分组聚合，再在 Python 层做 N 次换算（N = 货币种数）。

        Args:
            query: SQLAlchemy Query 对象（已应用 filter，尚未 group/agg）
            amount_column: 金额列（如 Quotation.amount）
            currency_column: 货币列（如 Quotation.currency）
            target_currency: 目标货币（默认 Config.DEFAULT_CURRENCY）

        Returns:
            float: 换算后的总额
        """
        target_currency = (target_currency or Config.DEFAULT_CURRENCY).upper()

        # 按货币分组聚合（数据库层，O(1) I/O）
        rows = query.with_entities(
            currency_column.label('cur'),
            func.coalesce(func.sum(amount_column), 0).label('amt'),
        ).group_by(currency_column).all()

        # Python 层换算合并（O(货币种数) ≈ O(1)）
        total = 0.0
        for row in rows:
            total += cls._convert(row.amt, row.cur, target_currency)
        return total

    @classmethod
    def sum_converted_with_conditions(cls, query, amount_column, currency_column,
                                       conditions, target_currency=None):
        """一次查询返回多个条件聚合 —— 列表页统计卡片专用

        典型场景：报价单列表同时需要 total/approved/pending/draft 四个值。
        为避免 4 次 SQL，在 SELECT 里同时计算所有条件的 SUM，
        按货币分组，Python 层再对每个条件做换算合并。

        Args:
            query: SQLAlchemy Query 对象（已 filter，未 group/agg）
            amount_column: 金额列
            currency_column: 货币列
            conditions: dict[label -> 条件表达式 或 None]
                     None 表示无条件（即 total）
                     示例：{
                         'total': None,
                         'approved': Quotation.approval_status == 'approved',
                     }
            target_currency: 目标货币

        Returns:
            dict[label -> converted_total]
        """
        target_currency = (target_currency or Config.DEFAULT_CURRENCY).upper()

        # 为每个 label 构造条件聚合表达式
        select_cols = [currency_column.label('cur')]
        labels = []
        for label, cond in conditions.items():
            labels.append(label)
            if cond is None:
                # 无条件：直接 SUM
                select_cols.append(
                    func.coalesce(func.sum(amount_column), 0).label(label)
                )
            else:
                # 有条件：case when + sum
                select_cols.append(
                    func.coalesce(
                        func.sum(case((cond, amount_column), else_=0)), 0
                    ).label(label)
                )

        rows = query.with_entities(*select_cols).group_by(currency_column).all()

        # Python 层合并：每个 label 独立累加
        result = {label: 0.0 for label in labels}
        for row in rows:
            cur = row.cur
            for label in labels:
                amt = getattr(row, label, None)
                result[label] += cls._convert(amt, cur, target_currency)
        return result

    @classmethod
    def sum_converted_by_group(cls, query, amount_column, currency_column,
                                group_by_column, target_currency=None):
        """按某维度分组 + 跨货币求和

        典型场景：按销售员分组的销售额，或按产品分类分组的销售额。

        Args:
            query: SQLAlchemy Query 对象
            amount_column: 金额列
            currency_column: 货币列
            group_by_column: 分组维度列（如 QuotationDetail.quotation_id 或 User.id）
            target_currency: 目标货币

        Returns:
            dict[group_value -> converted_total]
        """
        target_currency = (target_currency or Config.DEFAULT_CURRENCY).upper()

        # SQL: GROUP BY (group_column, currency_column)
        rows = query.with_entities(
            group_by_column.label('grp'),
            currency_column.label('cur'),
            func.coalesce(func.sum(amount_column), 0).label('amt'),
        ).group_by(group_by_column, currency_column).all()

        # Python 层换算并合并同组
        result = {}
        for row in rows:
            key = row.grp
            converted = cls._convert(row.amt, row.cur, target_currency)
            result[key] = result.get(key, 0.0) + converted
        return result

    @classmethod
    def convert_single(cls, amount, from_currency, target_currency=None):
        """单个金额换算 —— 用于回写缓存字段等场景

        例如 Project.quotation_customer 的写入点。

        Args:
            amount: 原金额
            from_currency: 源货币
            target_currency: 目标货币（默认系统默认）

        Returns:
            float: 换算后金额
        """
        target_currency = target_currency or Config.DEFAULT_CURRENCY
        return cls._convert(amount, from_currency, target_currency)
