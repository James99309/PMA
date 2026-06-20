
"""seed product status content_filters defaults

Revision ID: 7aeb7caaae8c
Revises: 35820e41dd91
Create Date: 2026-06-10 08:24:09.748623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7aeb7caaae8c'
down_revision = '35820e41dd91'
branch_labels = None
depends_on = None


def upgrade():
    """给各角色 product 模块的 content_filters 种默认产品状态可见性(保持原行为):
       admin/产品经理/解决方案经理 → 看全部状态;其余角色 → 仅生产中。
       仅更新当前为 NULL 的行(幂等,不覆盖已配置的)。个人权限 content_filters 为空时自动回退角色配置,故不种个人级。"""
    conn = op.get_bind()
    # content_filters 可能是 SQL NULL 或 JSON null/空对象 —— 三种都视为"未配置",一并种子
    conn.execute(sa.text("""
        UPDATE role_permissions
        SET content_filters = '{"status": ["active", "upcoming", "discontinued"]}'::json
        WHERE module='product'
          AND (content_filters IS NULL OR content_filters::jsonb IN ('null'::jsonb, '{}'::jsonb))
          AND role IN ('admin', 'product_manager', 'solution_manager')
    """))
    conn.execute(sa.text("""
        UPDATE role_permissions
        SET content_filters = '{"status": ["active"]}'::json
        WHERE module='product'
          AND (content_filters IS NULL OR content_filters::jsonb IN ('null'::jsonb, '{}'::jsonb))
          AND role NOT IN ('admin', 'product_manager', 'solution_manager')
    """))


def downgrade():
    conn = op.get_bind()
    # 仅回退本迁移种下的两种默认值(jsonb 语义比较,忽略空白/顺序),不动手工改过的
    conn.execute(sa.text("""
        UPDATE role_permissions SET content_filters = NULL
        WHERE module='product' AND content_filters::jsonb IN (
            '{"status": ["active", "upcoming", "discontinued"]}'::jsonb,
            '{"status": ["active"]}'::jsonb
        )
    """))