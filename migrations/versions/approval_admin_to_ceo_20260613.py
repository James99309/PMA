"""审批流程不再让 admin 参与:静态模板里 admin 审批人 → 总经理(ceo)(2026-06-13)

用户规则:所有审批流程都不应让 admin 参与。当前仅批价单模板 step「二审」写死 admin,
统一迁移到 ceo(按角色动态解析,兼容各 NAS 不同 user id)。配套代码改动:
get_next_level_approver/get_authorization_approver_by_project_type 去 admin 回退;
ceo 发起的上级审批步自动跳过。

幂等:仅改仍指向 admin 的步骤;无 ceo 时不动(避免置空)。

Revision ID: approval_admin_to_ceo_20260613
Revises: salary_run_20260613
Create Date: 2026-06-13
"""
from alembic import op
from sqlalchemy import text

revision = 'approval_admin_to_ceo_20260613'
down_revision = 'salary_run_20260613'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    admin_id = conn.execute(text("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1")).scalar()
    ceo_id = conn.execute(text("SELECT id FROM users WHERE role='ceo' ORDER BY id LIMIT 1")).scalar()
    if not admin_id or not ceo_id:
        return  # 缺 admin 或 ceo → 不动
    conn.execute(text(
        "UPDATE approval_step SET approver_user_id = :ceo "
        "WHERE approver_type = 'user' AND approver_user_id = :admin"),
        {'ceo': ceo_id, 'admin': admin_id})


def downgrade():
    # 不可靠回滚(无法区分历史上本就指向 ceo 的步骤),留空
    pass
