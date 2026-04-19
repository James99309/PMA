
"""points_registry_hooks_20260418

Revision ID: 85f238ee3dc3
Revises: 1f3739dded24
Create Date: 2026-04-18 14:35:11.249019

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '85f238ee3dc3'
down_revision = '1f3739dded24'
branch_labels = None
depends_on = None


def upgrade():
    # 新增积分行为注册表中的 3 个 Wiki 钩子（ON CONFLICT 保证幂等）
    op.execute("""
        INSERT INTO points_behavior_config (behavior_code, behavior_name, category, points, daily_cap, is_active)
        VALUES
            ('wiki_create',      '创建知识库文章',   'knowledge', 15, NULL, true),
            ('wiki_cited_qa',    '问答引用我的文章', 'knowledge', 15, 30,   true),
            ('wiki_link_opened', '引用链接被点击',   'knowledge',  5, 20,   true)
        ON CONFLICT (behavior_code) DO NOTHING
    """)


def downgrade():
    op.execute("""
        DELETE FROM points_behavior_config
        WHERE behavior_code IN ('wiki_create', 'wiki_cited_qa', 'wiki_link_opened')
    """)
