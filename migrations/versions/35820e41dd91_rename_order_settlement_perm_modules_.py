
"""rename order-settlement perm modules + add sales_order

Revision ID: 35820e41dd91
Revises: spec_item_include_in_desc_20260609
Create Date: 2026-06-09 23:27:13.505151

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35820e41dd91'
down_revision = 'spec_item_include_in_desc_20260609'
branch_labels = None
depends_on = None


def upgrade():
    """订单结算组权限模块重整(纯数据,幂等):
       客户订单(新增) → 采购订单(order改名) → 批价单(pricing_order改名)
       → 结算单(settlement改名) → 库存管理;停用死模块 settlement_order。
       角色↔模块的授权由用户在权限配置页操作,本迁移不动 role_permissions。"""
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE permission_modules SET name='采购订单', name_en='Purchase Order', sort_order=8 WHERE module_id='order'"))
    conn.execute(sa.text("UPDATE permission_modules SET name='批价单', name_en='Pricing Order', sort_order=9 WHERE module_id='pricing_order'"))
    conn.execute(sa.text("UPDATE permission_modules SET name='结算单', name_en='Settlement Order', sort_order=10 WHERE module_id='settlement'"))
    conn.execute(sa.text("UPDATE permission_modules SET sort_order=11 WHERE module_id='inventory'"))
    conn.execute(sa.text("UPDATE permission_modules SET is_active=false WHERE module_id='settlement_order'"))
    conn.execute(sa.text("""
        INSERT INTO permission_modules
          (module_id, name, name_en, icon, description, group_name, group_name_en, sort_order,
           supports_discount, supports_owner_change, supports_affiliation, supports_content_filter, is_active)
        SELECT 'sales_order','客户订单','Sales Order','shopping_cart','管理客户订单','订单结算','Order',7,
               false, false, false, false, true
        WHERE NOT EXISTS (SELECT 1 FROM permission_modules WHERE module_id='sales_order')
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE permission_modules SET name='订单管理', name_en='Order', sort_order=7 WHERE module_id='order'"))
    conn.execute(sa.text("UPDATE permission_modules SET name='批价单管理', name_en='Pricing Order', sort_order=10 WHERE module_id='pricing_order'"))
    conn.execute(sa.text("UPDATE permission_modules SET name='结算管理', name_en='Settlement', sort_order=8 WHERE module_id='settlement'"))
    conn.execute(sa.text("UPDATE permission_modules SET sort_order=9 WHERE module_id='inventory'"))
    conn.execute(sa.text("UPDATE permission_modules SET is_active=true WHERE module_id='settlement_order'"))
    conn.execute(sa.text("DELETE FROM permission_modules WHERE module_id='sales_order'"))