"""项目报备审批切换业务线路由:停用旧 project 模板

新模板「项目报备审批(业务线)」由代码 get-or-create(两步:业务线经理→总经理,
缺位跳级);授权编号在整条通过时按项目类型自动生成(CPJ/SPJ/APJ)。
进行中的旧实例按各自模板快照走完,不受影响。

Revision ID: report_bizline_20260613
Revises: dealer_apply_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'report_bizline_20260613'
down_revision = 'dealer_apply_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE approval_process_template SET is_active = false
        WHERE object_type = 'project' AND is_active = true
          AND name != '项目报备审批(业务线)'
    """)


def downgrade():
    # 恢复旧默认模板「审批」(若存在)
    op.execute("UPDATE approval_process_template SET is_active = true "
               "WHERE object_type='project' AND name='审批'")
    op.execute("UPDATE approval_process_template SET is_active = false "
               "WHERE object_type='project' AND name='项目报备审批(业务线)'")
