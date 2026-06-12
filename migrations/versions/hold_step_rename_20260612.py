"""项目失败/搁置审核第一步改名:部门经理审批 → 业务线经理审批

第一步审批人按业务线分流:渠道(report_source=channel)→渠道经理(缺位营销总监代理);
服务类(负责人属服务部门)→服务经理(缺位直达总经理);其余→营销总监(缺位直达总经理)。

Revision ID: hold_step_rename_20260612
Revises: channel_kpi_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'hold_step_rename_20260612'
down_revision = 'channel_kpi_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE approval_step SET step_name='业务线经理审批'
        WHERE step_order=1 AND step_name='部门经理审批'
          AND process_id IN (SELECT id FROM approval_process_template WHERE object_type='project_hold')
    """)


def downgrade():
    op.execute("""
        UPDATE approval_step SET step_name='部门经理审批'
        WHERE step_order=1 AND step_name='业务线经理审批'
          AND process_id IN (SELECT id FROM approval_process_template WHERE object_type='project_hold')
    """)
