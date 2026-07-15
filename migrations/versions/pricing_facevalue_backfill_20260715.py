"""回填「价格面议」批价明细:面价缺失但有报价单价 → 面价=报价单价、折扣100%

Revision ID: pricing_facevalue_backfill_20260715
Revises: pricing_quote_unit_price_20260715
Create Date: 2026-07-15

背景:价格面议产品源报价只有报价单价(unit_price)、没有面价(market_price=0)。复制到
批价单后,批价模型「单价=面价×折扣」用面价0把单价冲成0(批价单价列显示0),报价单价快照
(quote_unit_price)却是对的。修复:把报价单价当作批价面价、折扣100%,使 面价=单价=报价单价。

同步修正对应结算明细:面价跟随批价;折扣按业务类型——直销强制=批价、渠道取 min(结算,批价)
(此处批价折扣=1.0,结算原为1.0,结果都是1.0,不产生倒挂),重算单价/小计。

纯数据回填,无 schema 变更。幂等:只命中 面价≤0 且 有报价单价快照 的行,重复执行不再匹配。
"""
from alembic import op
import sqlalchemy as sa

revision = 'pricing_facevalue_backfill_20260715'
down_revision = 'pricing_quote_unit_price_20260715'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # 1) 批价明细:面价缺失但有报价单价快照 → 面价=报价单价、折扣100%、重算单价/小计
    conn.execute(sa.text("""
        UPDATE pricing_order_details
        SET market_price  = quote_unit_price,
            discount_rate = 1.0,
            unit_price    = quote_unit_price,
            total_price   = quote_unit_price * COALESCE(quantity, 0)
        WHERE (market_price IS NULL OR market_price <= 0)
          AND quote_unit_price IS NOT NULL
          AND quote_unit_price > 0
    """))

    # 2) 对应结算明细跟随修正后的批价。effective 折扣:直销=批价折扣;渠道=min(结算,批价)。
    #    只命中「批价已被步骤1修正(面价=报价单价、折扣1.0)、而结算面价仍<=0」的结算行。
    conn.execute(sa.text("""
        UPDATE settlement_order_details sod
        SET market_price  = pod.market_price,
            discount_rate = CASE WHEN po.is_direct_contract
                                 THEN pod.discount_rate
                                 ELSE LEAST(COALESCE(sod.discount_rate, 1.0), pod.discount_rate) END,
            unit_price    = pod.market_price * (CASE WHEN po.is_direct_contract
                                 THEN pod.discount_rate
                                 ELSE LEAST(COALESCE(sod.discount_rate, 1.0), pod.discount_rate) END),
            total_price   = pod.market_price * (CASE WHEN po.is_direct_contract
                                 THEN pod.discount_rate
                                 ELSE LEAST(COALESCE(sod.discount_rate, 1.0), pod.discount_rate) END)
                            * COALESCE(sod.quantity, 0)
        FROM pricing_order_details pod
        JOIN pricing_orders po ON po.id = pod.pricing_order_id
        WHERE sod.pricing_detail_id = pod.id
          AND pod.quote_unit_price IS NOT NULL
          AND pod.quote_unit_price > 0
          AND pod.market_price = pod.quote_unit_price
          AND pod.discount_rate = 1.0
          AND (sod.market_price IS NULL OR sod.market_price <= 0)
    """))


def downgrade():
    # 数据回填不可逆(原始 面价0/单价0 无保留价值);留空。
    pass
