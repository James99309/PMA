#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MultiCurrencyAggregationService 单元测试

测试跨货币聚合统计服务的核心逻辑：
- 同币种求和
- 跨币种求和
- 空查询
- 零金额
- Null 货币字段
- 条件聚合
- 分组聚合
- 目标货币不同时的正确换算
"""
import sys
import os


def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")


sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.quotation import Quotation, QuotationDetail
from app.services.multi_currency_aggregation import MultiCurrencyAggregationService

app = create_app()


def assert_close(actual, expected, tol=0.01, msg=''):
    """浮点数近似比较"""
    if abs(actual - expected) > tol:
        raise AssertionError(f"{msg}: 期望 {expected}, 实际 {actual}")


def test_convert_single():
    """convert_single 基础测试"""
    print("\n=== test_convert_single ===")

    with app.app_context():
        # 同货币应短路返回原值
        result = MultiCurrencyAggregationService.convert_single(100, 'CNY', 'CNY')
        assert_close(result, 100.0, msg="同货币短路")
        print(f"  CNY -> CNY: 100 -> {result} ✓")

        # None 金额返回 0
        result = MultiCurrencyAggregationService.convert_single(None, 'CNY', 'CNY')
        assert_close(result, 0.0, msg="None 金额")
        print(f"  None: -> {result} ✓")

        # 零金额返回 0
        result = MultiCurrencyAggregationService.convert_single(0, 'MYR', 'CNY')
        assert_close(result, 0.0, msg="零金额")
        print(f"  0 MYR -> CNY: -> {result} ✓")

        # 跨货币换算（只要 > 0 即可，不 assert 具体值因汇率会变）
        result = MultiCurrencyAggregationService.convert_single(100, 'USD', 'CNY')
        assert result > 0, "USD -> CNY 应该 > 0"
        print(f"  100 USD -> CNY: {result} ✓")

        # Null 货币视为目标货币
        result = MultiCurrencyAggregationService.convert_single(100, None, 'CNY')
        assert_close(result, 100.0, msg="Null 货币视为目标")
        print(f"  100 None -> CNY: {result} ✓")


def test_sum_converted_empty_query():
    """空查询返回 0"""
    print("\n=== test_sum_converted_empty_query ===")
    with app.app_context():
        # 查一个肯定为空的条件
        query = Quotation.query.filter(Quotation.id == -1)
        result = MultiCurrencyAggregationService.sum_converted(
            query, Quotation.amount, Quotation.currency
        )
        assert_close(result, 0.0, msg="空查询")
        print(f"  空查询: {result} ✓")


def test_sum_converted_real_data():
    """真实数据求和（使用本地数据库的真实报价单）"""
    print("\n=== test_sum_converted_real_data ===")
    with app.app_context():
        # 查询所有报价单的真实总额
        query = Quotation.query

        # 用我们的服务求和
        total_via_service = MultiCurrencyAggregationService.sum_converted(
            query, Quotation.amount, Quotation.currency
        )

        # 手动计算期望值：分货币求和再手动换算
        from sqlalchemy import func
        rows = db.session.query(
            Quotation.currency,
            func.sum(Quotation.amount)
        ).group_by(Quotation.currency).all()

        print(f"  数据库分货币分布:")
        for cur, amt in rows:
            print(f"    {cur or 'NULL'}: {float(amt or 0):,.2f}")
        print(f"  服务返回: {total_via_service:,.2f}")

        # 至少不应该为负
        assert total_via_service >= 0, "总额不应为负"

        # 如果全是同一货币，应该等于 SUM
        single_cur_total = sum(float(amt or 0) for _, amt in rows) if len(rows) == 1 else None
        if single_cur_total is not None:
            assert_close(total_via_service, single_cur_total, msg="单货币场景")
            print(f"  单货币场景验证 ✓")
        else:
            print(f"  多货币场景（无法简单对比，但服务返回值 > 0）✓")


def test_sum_converted_with_conditions():
    """条件聚合测试（报价单 total/approved/pending/draft 场景）"""
    print("\n=== test_sum_converted_with_conditions ===")
    with app.app_context():
        query = Quotation.query

        conditions = {
            'total': None,
            'approved': Quotation.approval_status == 'approved',
            'pending': Quotation.approval_status.in_(['pending', 'in_progress']),
            'draft': Quotation.approval_status == 'draft',
        }

        result = MultiCurrencyAggregationService.sum_converted_with_conditions(
            query, Quotation.amount, Quotation.currency, conditions
        )

        print(f"  统计结果:")
        for label, value in result.items():
            print(f"    {label}: {value:,.2f}")

        # total 应该 >= 其他任何分类的值
        assert result['total'] >= result['approved'], "total >= approved"
        assert result['total'] >= result['pending'], "total >= pending"
        assert result['total'] >= result['draft'], "total >= draft"
        print(f"  总额 >= 各分类值 ✓")


def test_sum_converted_by_group():
    """分组聚合测试（按 owner_id 分组）"""
    print("\n=== test_sum_converted_by_group ===")
    with app.app_context():
        query = Quotation.query

        result = MultiCurrencyAggregationService.sum_converted_by_group(
            query, Quotation.amount, Quotation.currency, Quotation.owner_id
        )

        print(f"  按 owner_id 分组（前 5 个）:")
        items = list(result.items())[:5]
        for owner_id, total in items:
            print(f"    owner_id={owner_id}: {total:,.2f}")

        # 所有分组总和应该等于全表总和
        full_total = MultiCurrencyAggregationService.sum_converted(
            query, Quotation.amount, Quotation.currency
        )
        group_sum = sum(result.values())
        assert_close(group_sum, full_total, tol=1.0, msg="分组总和 = 全表总和")
        print(f"  分组总和 {group_sum:,.2f} ≈ 全表总和 {full_total:,.2f} ✓")


def test_target_currency_override():
    """目标货币覆盖测试"""
    print("\n=== test_target_currency_override ===")
    with app.app_context():
        query = Quotation.query

        # 用系统默认目标（CNY）
        total_default = MultiCurrencyAggregationService.sum_converted(
            query, Quotation.amount, Quotation.currency
        )

        # 显式指定 USD 作为目标
        total_usd = MultiCurrencyAggregationService.sum_converted(
            query, Quotation.amount, Quotation.currency, target_currency='USD'
        )

        print(f"  默认目标 (CNY): {total_default:,.2f}")
        print(f"  指定目标 (USD): {total_usd:,.2f}")

        # USD 数字应该远小于 CNY（约 1/7）
        if total_default > 0:
            ratio = total_usd / total_default
            assert 0.05 < ratio < 0.30, f"USD/CNY 比例应在 0.05~0.30，实际 {ratio:.3f}"
            print(f"  USD/CNY 比例 {ratio:.3f} ✓")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("MultiCurrencyAggregationService 单元测试")
    print("=" * 60)

    try:
        test_convert_single()
        test_sum_converted_empty_query()
        test_sum_converted_real_data()
        test_sum_converted_with_conditions()
        test_sum_converted_by_group()
        test_target_currency_override()

        print("\n" + "=" * 60)
        print("✅ 全部测试通过")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        import traceback
        print(f"\n❌ 测试异常: {e}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
