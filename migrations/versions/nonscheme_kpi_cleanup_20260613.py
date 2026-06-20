"""清理非方案角色的遗留个人考核目标行(2026-06-13 用户确认:没有固化方案的角色先挪走已有考核项,等进一步固定)

岗位方案已固化的角色:solution_manager / sales_manager / customer_sales /
sales_director / service_manager / channel_manager / product_manager。
其余角色(engineer / hr_manager / user / business_admin 等)在旧版页面配出的
user_performance_targets 个人行一并删除 → 仪表盘回到「KPI 未设定」占位,
待这些岗位的方案固化后重新配置。方案角色的个人覆盖行不动。

幂等:重复执行无副作用。

Revision ID: nonscheme_kpi_cleanup_20260613
Revises: pm_kpi_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'nonscheme_kpi_cleanup_20260613'
down_revision = 'pm_kpi_20260613'
branch_labels = None
depends_on = None

# 与 app/services/role_kpi_schemes.py ROLE_KPI_SCHEMES 保持一致
SCHEME_ROLES = ('solution_manager', 'sales_manager', 'customer_sales',
                'sales_director', 'service_manager', 'channel_manager',
                'product_manager')


def upgrade():
    op.execute(f"""
        DELETE FROM user_performance_targets t
        USING users u
        WHERE t.user_id = u.id
          AND (u.role IS NULL OR u.role NOT IN {SCHEME_ROLES!r})
    """)


def downgrade():
    pass  # 遗留脏数据清理,不可逆(原始值已无业务意义)
