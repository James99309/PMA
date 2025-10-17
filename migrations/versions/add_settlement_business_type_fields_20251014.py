"""添加结算单业务类型标记字段

Revision ID: add_settlement_business_type_20251014
Revises:
Create Date: 2025-10-14 18:00:00.000000

说明：
1. 在settlement_orders表添加is_direct_contract和is_factory_pickup字段
2. 从关联的pricing_orders表同步业务类型标记
3. 清洗不合理的数据（例如：厂商直签的结算单不应该有distributor_id）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_settlement_business_type_20251014'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加字段并迁移数据"""

    # 步骤0: 修改 distributor_id 约束为可空
    print("=" * 80)
    print("步骤0: 修改 distributor_id 约束为可空...")
    print("=" * 80)

    connection = op.get_bind()
    connection.execute(text("""
        ALTER TABLE settlement_orders
        ALTER COLUMN distributor_id DROP NOT NULL
    """))
    print("✓ distributor_id 约束已修改为可空")

    # 步骤1: 添加新字段（默认值为False）
    print("\n" + "=" * 80)
    print("步骤1: 添加业务类型标记字段...")
    print("=" * 80)

    op.add_column('settlement_orders',
        sa.Column('is_direct_contract', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('settlement_orders',
        sa.Column('is_factory_pickup', sa.Boolean(), server_default='false', nullable=False))

    # 步骤2: 从批价单同步业务类型标记
    print("\n" + "=" * 80)
    print("步骤2: 从批价单同步业务类型标记...")
    print("=" * 80)

    connection = op.get_bind()

    # 查询需要同步的结算单数量
    result = connection.execute(text("""
        SELECT COUNT(*) FROM settlement_orders
    """))
    total_count = result.scalar()
    print(f"\n总结算单数: {total_count}")

    # 同步标记字段
    connection.execute(text("""
        UPDATE settlement_orders s
        SET
            is_direct_contract = p.is_direct_contract,
            is_factory_pickup = p.is_factory_pickup
        FROM pricing_orders p
        WHERE s.pricing_order_id = p.id
    """))

    # 验证同步结果
    result = connection.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE is_direct_contract = true) as direct_count,
            COUNT(*) FILTER (WHERE is_factory_pickup = true) as pickup_count,
            COUNT(*) FILTER (WHERE is_direct_contract = false AND is_factory_pickup = false) as channel_count
        FROM settlement_orders
    """))
    row = result.fetchone()
    print(f"\n同步结果:")
    print(f"  - 厂商直签: {row[0]} 条")
    print(f"  - 厂家提货: {row[1]} 条")
    print(f"  - 常规渠道: {row[2]} 条")

    # 步骤3: 清洗不合理的数据
    print("\n" + "=" * 80)
    print("步骤3: 清洗不合理的数据...")
    print("=" * 80)

    # 3.1: 厂商直签的结算单应该没有dealer_id和distributor_id
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM settlement_orders
        WHERE is_direct_contract = true
        AND (dealer_id IS NOT NULL OR distributor_id IS NOT NULL)
    """))
    direct_dirty_count = result.scalar()

    if direct_dirty_count > 0:
        print(f"\n发现 {direct_dirty_count} 条厂商直签结算单有不合理的客户ID，清洗中...")

        # 显示详情
        result = connection.execute(text("""
            SELECT id, order_number, dealer_id, distributor_id
            FROM settlement_orders
            WHERE is_direct_contract = true
            AND (dealer_id IS NOT NULL OR distributor_id IS NOT NULL)
            LIMIT 10
        """))

        print("\n示例记录（前10条）:")
        for row in result:
            print(f"  结算单 {row[1]}: dealer_id={row[2]}, distributor_id={row[3]}")

        # 清洗：将客户ID设置为NULL
        connection.execute(text("""
            UPDATE settlement_orders
            SET dealer_id = NULL, distributor_id = NULL
            WHERE is_direct_contract = true
        """))
        print(f"✓ 已清洗 {direct_dirty_count} 条厂商直签结算单的客户ID")
    else:
        print("\n✓ 所有厂商直签结算单的客户ID都正确")

    # 3.2: 厂家提货的结算单应该没有distributor_id
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM settlement_orders
        WHERE is_factory_pickup = true
        AND distributor_id IS NOT NULL
    """))
    pickup_dirty_count = result.scalar()

    if pickup_dirty_count > 0:
        print(f"\n发现 {pickup_dirty_count} 条厂家提货结算单有不合理的distributor_id，清洗中...")

        # 清洗：将distributor_id设置为NULL
        connection.execute(text("""
            UPDATE settlement_orders
            SET distributor_id = NULL
            WHERE is_factory_pickup = true
        """))
        print(f"✓ 已清洗 {pickup_dirty_count} 条厂家提货结算单的distributor_id")
    else:
        print("\n✓ 所有厂家提货结算单的distributor_id都正确")

    # 步骤4: 最终验证
    print("\n" + "=" * 80)
    print("步骤4: 最终验证...")
    print("=" * 80)

    result = connection.execute(text("""
        SELECT
            is_direct_contract,
            is_factory_pickup,
            COUNT(*) as count,
            COUNT(*) FILTER (WHERE dealer_id IS NULL) as dealer_null_count,
            COUNT(*) FILTER (WHERE distributor_id IS NULL) as distributor_null_count
        FROM settlement_orders
        GROUP BY is_direct_contract, is_factory_pickup
        ORDER BY is_direct_contract DESC, is_factory_pickup DESC
    """))

    print("\n结算单数据验证:")
    print(f"{'类型':15s} {'数量':8s} {'dealer=NULL':15s} {'distributor=NULL':20s}")
    print("-" * 65)
    for row in result:
        if row[0]:
            type_label = "厂商直签"
        elif row[1]:
            type_label = "厂家提货"
        else:
            type_label = "常规渠道"

        print(f"{type_label:15s} {row[2]:8d} {row[3]:15d} {row[4]:20d}")

    print("\n" + "=" * 80)
    print("✅ 迁移和清洗完成！")
    print("=" * 80)


def downgrade():
    """回滚：删除新增字段"""
    print("回滚：删除业务类型标记字段...")

    op.drop_column('settlement_orders', 'is_factory_pickup')
    op.drop_column('settlement_orders', 'is_direct_contract')

    print("✓ 回滚完成")
