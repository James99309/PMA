"""部门数据归一(2026-06-13):账户部门统一到 Department 表口径

账户旧值「产品和解决方案部」(来自 Dictionary)在 Department 表无对应,归一:
- 刘威 / 蒋隽弘(解决方案经理) → 方案应用部
- 其余(产品经理/工程师/普通) → 产品中心
之后账户部门下拉改用 Department 表(按公司联动),全站部门单一真源。

幂等:仅改剩余的旧值。

Revision ID: dept_unify_20260613
Revises: perm_clean_legacy_features_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'dept_unify_20260613'
down_revision = 'perm_clean_legacy_features_20260613'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    # 解决方案经理 → 方案应用部
    conn.execute(text(
        "UPDATE users SET department='方案应用部' "
        "WHERE department='产品和解决方案部' AND username IN ('liuwei','Michael')"))
    # 其余 → 产品中心
    conn.execute(text(
        "UPDATE users SET department='产品中心' WHERE department='产品和解决方案部'"))


def downgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    conn.execute(text(
        "UPDATE users SET department='产品和解决方案部' "
        "WHERE department IN ('方案应用部','产品中心') AND username IN "
        "('liuwei','Michael','hezy','zhangx','Eric','shiyg','suwen')"))
