"""添加字典表英文字段和初始化筛选选项数据

Revision ID: add_filter_dictionaries_20251228
Revises:
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_filter_dictionaries_20251228'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加 value_en 字段并初始化筛选选项数据"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. 检查并添加 value_en 字段
    columns = [col['name'] for col in inspector.get_columns('dictionaries')]
    if 'value_en' not in columns:
        op.add_column('dictionaries', sa.Column('value_en', sa.String(100), nullable=True))
        print("✓ 添加字段 dictionaries.value_en")
    else:
        print("- 字段 dictionaries.value_en 已存在，跳过")

    # 2. 插入项目类型选项
    project_types = [
        ('project_type', 'channel_follow', '渠道', 'Channel', 1),
        ('project_type', 'sales_focus', '销售', 'Sales', 2),
        ('project_type', 'business_opportunity', '服务', 'Service', 3),
    ]

    for dtype, key, value, value_en, sort_order in project_types:
        existing = conn.execute(text(
            "SELECT id FROM dictionaries WHERE type = :type AND key = :key"
        ), {'type': dtype, 'key': key}).fetchone()

        if existing:
            conn.execute(text("""
                UPDATE dictionaries
                SET value = :value, value_en = :value_en, sort_order = :sort_order
                WHERE type = :type AND key = :key
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})
        else:
            conn.execute(text("""
                INSERT INTO dictionaries (type, key, value, value_en, is_active, sort_order)
                VALUES (:type, :key, :value, :value_en, true, :sort_order)
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})

    print("✓ 初始化项目类型选项 (3条)")

    # 3. 插入项目阶段选项
    project_stages = [
        ('project_stage', 'discover', '发现', 'Discovery', 1),
        ('project_stage', 'embed', '植入', 'Embedding', 2),
        ('project_stage', 'pre_tender', '标前', 'Pre-tender', 3),
        ('project_stage', 'tendering', '标中', 'Tendering', 4),
        ('project_stage', 'awarded', '中标', 'Awarded', 5),
        ('project_stage', 'quoted', '批价', 'Pricing', 6),
        ('project_stage', 'signed', '签约', 'Contracted', 7),
        ('project_stage', 'lost', '失败', 'Failed', 8),
        ('project_stage', 'paused', '搁置', 'Paused', 9),
    ]

    for dtype, key, value, value_en, sort_order in project_stages:
        existing = conn.execute(text(
            "SELECT id FROM dictionaries WHERE type = :type AND key = :key"
        ), {'type': dtype, 'key': key}).fetchone()

        if existing:
            conn.execute(text("""
                UPDATE dictionaries
                SET value = :value, value_en = :value_en, sort_order = :sort_order
                WHERE type = :type AND key = :key
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})
        else:
            conn.execute(text("""
                INSERT INTO dictionaries (type, key, value, value_en, is_active, sort_order)
                VALUES (:type, :key, :value, :value_en, true, :sort_order)
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})

    print("✓ 初始化项目阶段选项 (9条)")

    # 4. 插入报备来源选项
    report_sources = [
        ('report_source', 'channel', '渠道', 'Channel', 1),
        ('report_source', 'sales', '销售', 'Sales', 2),
        ('report_source', 'marketing', '市场', 'Market', 3),
    ]

    for dtype, key, value, value_en, sort_order in report_sources:
        existing = conn.execute(text(
            "SELECT id FROM dictionaries WHERE type = :type AND key = :key"
        ), {'type': dtype, 'key': key}).fetchone()

        if existing:
            conn.execute(text("""
                UPDATE dictionaries
                SET value = :value, value_en = :value_en, sort_order = :sort_order
                WHERE type = :type AND key = :key
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})
        else:
            conn.execute(text("""
                INSERT INTO dictionaries (type, key, value, value_en, is_active, sort_order)
                VALUES (:type, :key, :value, :value_en, true, :sort_order)
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})

    print("✓ 初始化报备来源选项 (3条)")

    # 5. 插入企业类型选项
    company_types = [
        ('company_type', 'user', '用户', 'User', 1),
        ('company_type', 'designer', '顾问', 'Conslt', 2),
        ('company_type', 'contractor', '总包', 'Contrc', 3),
        ('company_type', 'integrator', '集成', 'Integr', 4),
        ('company_type', 'dealer', '经销', 'Dealer', 5),
        ('company_type', 'distributor', '分销', 'Distri', 6),
        ('company_type', 'partner', '伙伴', 'Partner', 7),
        ('company_type', 'other', '其他', 'Other', 8),
    ]

    for dtype, key, value, value_en, sort_order in company_types:
        existing = conn.execute(text(
            "SELECT id FROM dictionaries WHERE type = :type AND key = :key"
        ), {'type': dtype, 'key': key}).fetchone()

        if existing:
            conn.execute(text("""
                UPDATE dictionaries
                SET value = :value, value_en = :value_en, sort_order = :sort_order
                WHERE type = :type AND key = :key
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})
        else:
            conn.execute(text("""
                INSERT INTO dictionaries (type, key, value, value_en, is_active, sort_order)
                VALUES (:type, :key, :value, :value_en, true, :sort_order)
            """), {'type': dtype, 'key': key, 'value': value, 'value_en': value_en, 'sort_order': sort_order})

    print("✓ 初始化企业类型选项 (8条)")

    print("\n=== 迁移完成 ===")


def downgrade():
    """回滚：删除 value_en 字段（数据保留）"""
    op.drop_column('dictionaries', 'value_en')
    print("✓ 删除字段 dictionaries.value_en")
    # 注意：字典数据不删除，保留在数据库中
