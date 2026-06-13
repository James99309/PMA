"""为缺部门的公司补「销售部」(2026-06-13)

部门字典(Department 表)原只覆盖和源通信(上海);其余有在职账户的公司无任何部门,
导致账户切 Department 源后无部门可选。为每个未覆盖公司补一个「销售部」(现有账户均归此)。

幂等:仅对无部门的公司插入。

Revision ID: dept_seed_companies_20260613
Revises: dept_unify_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'dept_seed_companies_20260613'
down_revision = 'dept_unify_20260613'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    rows = conn.execute(text(
        "SELECT DISTINCT u.company_name FROM users u "
        "WHERE u.is_active=true AND u.company_name IS NOT NULL AND u.company_name<>'' "
        "AND NOT EXISTS (SELECT 1 FROM departments d WHERE d.company_name=u.company_name)"
    )).fetchall()
    for i, (company,) in enumerate(rows, start=1):
        conn.execute(text(
            "INSERT INTO departments (name, code, company_name, is_active, created_at, updated_at) "
            "VALUES ('销售部', :code, :company, true, NOW(), NOW())"),
            {'code': f'SALES_EXT{i}', 'company': company})


def downgrade():
    from sqlalchemy import text
    op.get_bind().execute(text("DELETE FROM departments WHERE code LIKE 'SALES_EXT%'"))
