"""freeze terminal stage projects activity status

Revision ID: freeze_terminal_stage_projects_20260207
Revises: add_project_activity_status_20260205
Create Date: 2026-02-07

将所有终态阶段(signed/lost/paused)的项目活跃度设为 frozen
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'freeze_terminal_stage_projects_20260207'
down_revision = 'add_project_activity_status_20260205'
branch_labels = None
depends_on = None


def upgrade():
    # 将所有终态阶段项目的活跃度设为 frozen
    op.execute("""
        UPDATE projects
        SET activity_status = 'frozen',
            is_active = false,
            activity_reason = CASE current_stage
                WHEN 'signed' THEN '项目已签约，活跃度已冻结'
                WHEN 'lost' THEN '项目已失败，活跃度已冻结'
                WHEN 'paused' THEN '项目已搁置，活跃度已冻结'
            END
        WHERE current_stage IN ('signed', 'lost', 'paused')
    """)


def downgrade():
    # 回滚：将 frozen 状态重置为 churned
    op.execute("""
        UPDATE projects
        SET activity_status = 'churned',
            is_active = false,
            activity_reason = '从冻结状态回滚'
        WHERE activity_status = 'frozen'
    """)
