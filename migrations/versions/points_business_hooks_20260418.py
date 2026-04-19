
"""points_business_hooks_20260418

Revision ID: points_business_hooks_20260418
Revises: 85f238ee3dc3
Create Date: 2026-04-18

新增 5 个业务类积分行为种子：
  project_approved, project_approver_acted, pricing_order_approved,
  contact_create, action_record_create
"""
from alembic import op

revision = 'points_business_hooks_20260418'
down_revision = '85f238ee3dc3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO points_behavior_config
            (behavior_code, behavior_name, category, points, daily_cap, is_active)
        VALUES
            ('project_approved',       '项目审批通过',   'business', 50, NULL, true),
            ('project_approver_acted',        '参与项目审批',   'approval', 20, NULL, true),
            ('pricing_order_approver_acted',  '参与批价单审批', 'approval', 20, NULL, true),
            ('pricing_order_approved', '批价单审批通过', 'business', 40, NULL, true),
            ('contact_create',         '创建联系人',     'business', 10, NULL, true),
            ('action_record_create',   '创建跟进记录',   'business', 10, NULL, true)
        ON CONFLICT (behavior_code) DO NOTHING
    """)


def downgrade():
    op.execute("""
        DELETE FROM points_behavior_config
        WHERE behavior_code IN (
            'project_approved', 'project_approver_acted', 'pricing_order_approved',
            'contact_create', 'action_record_create'
        )
    """)
