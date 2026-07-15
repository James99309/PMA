"""批价单明细报价单价快照 quote_unit_price + 回填历史数据

Revision ID: pricing_quote_unit_price_20260715
Revises: user_favorites_20260715
Create Date: 2026-07-15

背景:批价单"报价单价"列原先靠 pricing_order_details.source_quotation_detail_id 实时反查
报价单明细。报价单一旦被编辑,旧明细行被删除重建(新 id),该外键悬空 → 报价单价列空白。
改为创建时把报价单价抄成快照列 quote_unit_price,不再受报价单后续编辑影响。

回填两步:
  1) 引用仍有效(source_quotation_detail_id 能查到)→ quote_unit_price = 该报价明细 unit_price
  2) 引用悬空 → 按 批价单.quotation_id + product_mn 匹配报价单现有明细取 unit_price
     (报价单改过价时这是当前最佳可得值,与页面"按型号一对就对上"一致)

幂等:app 启动 create_all 只建表不加列,加列前先探测列是否存在。
"""
from alembic import op
import sqlalchemy as sa

revision = 'pricing_quote_unit_price_20260715'
down_revision = 'user_favorites_20260715'
branch_labels = None
depends_on = None


def _has_column(table, col):
    return col in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade():
    if not _has_column('pricing_order_details', 'quote_unit_price'):
        op.add_column('pricing_order_details',
                      sa.Column('quote_unit_price', sa.Float(), nullable=True))

    conn = op.get_bind()
    # 步骤1:引用仍有效 → 直接抄源报价明细单价
    conn.execute(sa.text("""
        UPDATE pricing_order_details pod
        SET quote_unit_price = qd.unit_price
        FROM quotation_details qd
        WHERE pod.source_quotation_detail_id = qd.id
          AND pod.quote_unit_price IS NULL
    """))
    # 步骤2:引用悬空(原本有 source_quotation_detail_id 但已查不到)→ 按 批价单.quotation_id
    #   + product_mn 匹配报价单现有明细取价。只补"本来就该有报价单价、只是引用断了"的行;
    #   从无源引用的手工行(source_quotation_detail_id IS NULL)保持空,显示"—"不误导。
    conn.execute(sa.text("""
        UPDATE pricing_order_details pod
        SET quote_unit_price = sub.unit_price
        FROM (
            SELECT DISTINCT ON (po.id, qd.product_mn)
                   po.id AS pricing_order_id, qd.product_mn, qd.unit_price
            FROM pricing_orders po
            JOIN quotation_details qd ON qd.quotation_id = po.quotation_id
            WHERE qd.product_mn IS NOT NULL AND qd.product_mn <> ''
            ORDER BY po.id, qd.product_mn, qd.id DESC
        ) sub
        WHERE pod.pricing_order_id = sub.pricing_order_id
          AND pod.product_mn = sub.product_mn
          AND pod.quote_unit_price IS NULL
          AND pod.source_quotation_detail_id IS NOT NULL
    """))


def downgrade():
    if _has_column('pricing_order_details', 'quote_unit_price'):
        op.drop_column('pricing_order_details', 'quote_unit_price')
