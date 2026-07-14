# -*- coding: utf-8 -*-
"""价格三元组(面价 / 折扣 / 单价)的一致性归一。

背景 —— 一条真实的三层漏斗(PO202607-006):
  报价单把 discount 和 unit_price 当两个独立字段分别存,谁也不校验谁,于是库里
  出现了「面价 354 × 折扣 1 ≠ 单价 600」这种自相矛盾的数据。批价单生成时只信
  discount、用 `单价 = 面价 × 折扣` 重算,报价的 600 就被面价 354 冲掉了
  (调试开通更夸张:报价 4000 → 面价 30000)。人只好把折扣一行行手改回去,而
  结算单停在创建时复制的面价 → 结算 40,219 > 批价 16,665,倒挂。

约定:**面价是基准,单价是事实,折扣是导出量**。
  折扣 = 单价 / 面价 —— 只要单价是人真正认可的那个数,折扣就永远自洽。
  折扣 > 1(单价高于面价)是合法的:工程项目加价、面价数据本身偏低都会出现,
  故不设上限,只挡负数。
"""


def normalize_discount(market_price, unit_price, fallback_discount=1.0):
    """由面价与单价反算折扣率(小数,1.0 = 100%)。

    面价缺失/为 0(如价格面议的临时产品)时无从反算,原样返回 fallback。
    """
    try:
        mp = float(market_price or 0)
        up = float(unit_price or 0)
    except (TypeError, ValueError):
        return _sanitize(fallback_discount)

    if mp <= 0:
        return _sanitize(fallback_discount)
    return _sanitize(up / mp)


def _sanitize(discount):
    try:
        d = float(discount)
    except (TypeError, ValueError):
        return 1.0
    return d if d >= 0 else 0.0
