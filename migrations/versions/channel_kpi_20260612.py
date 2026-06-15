"""渠道经理考核指标集(渠道=全量 report_source/source='channel' 业务,不限负责人)

结构对齐销售方案;渠道失败率=当年失败的渠道项目 ÷ 渠道项目总数(整体渠道质量,
不带个人归因维度)。率类角色默认目标随迁移 seed。

Revision ID: channel_kpi_20260612
Revises: role_scheme_alias_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'channel_kpi_20260612'
down_revision = 'role_scheme_alias_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO performance_metrics_definition
            (metric_code, metric_name, metric_category, data_type, default_unit,
             description, is_system_metric, is_active, created_at)
        VALUES
            ('channel_sales_amount', '渠道销售目标', '渠道管理', 'amount', '',
             '渠道报备项目(report_source=channel)每月批价单审批金额合计(全量,不限负责人)', true, true, NOW()),
            ('channel_implant_amount', '渠道植入额', '渠道管理', 'amount', '',
             '渠道报备项目关联报价单植入额合计(全量)', true, true, NOW()),
            ('channel_new_projects', '渠道新增项目', '渠道管理', 'count', '个',
             '每月新建的渠道报备项目数(全量)', true, true, NOW()),
            ('channel_new_customers', '渠道新增客户', '渠道管理', 'count', '个',
             '代理商(dealer)账户名下每月新建客户数(客户不分渠道,按创建账户归属)', true, true, NOW()),
            ('channel_customer_activity_rate', '渠道客户活跃度', '渠道管理', 'percentage', '%',
             '代理商账户名下客户中 高度活跃/活跃/正常 的占比(快照)', true, true, NOW()),
            ('channel_project_activity_rate', '渠道项目活跃度', '渠道管理', 'percentage', '%',
             '渠道报备项目(排除签约/失败/搁置)跟进未超 20 天的占比(快照,全量)', true, true, NOW()),
            ('channel_fail_rate', '渠道失败率', '渠道管理', 'percentage', '%',
             '当年进入失败阶段的渠道项目数 ÷ 渠道项目总数;反向指标,实际 ≤ 目标为达标', true, true, NOW()),
            ('channel_new_dealers', '渠道发展', '渠道管理', 'count', '个',
             '每月新增的代理商/分销商客户数(company_type=dealer/distributor)', true, true, NOW())
        ON CONFLICT (metric_code) DO NOTHING
    """)
    op.execute("""
        INSERT INTO role_performance_targets (role_code, year, item_code, annual_target, created_at, updated_at)
        SELECT r.role_code, 2026, r.item_code, r.annual_target, NOW(), NOW()
        FROM (VALUES
            ('channel_manager', 'channel_customer_activity_rate', 100.0),
            ('channel_manager', 'channel_project_activity_rate',  90.0)
        ) AS r(role_code, item_code, annual_target)
        WHERE NOT EXISTS (
            SELECT 1 FROM role_performance_targets t
            WHERE t.role_code = r.role_code AND t.year = 2026 AND t.item_code = r.item_code)
    """)


def downgrade():
    op.execute("DELETE FROM role_performance_targets WHERE role_code='channel_manager' AND item_code LIKE 'channel_%'")
    op.execute("DELETE FROM performance_metrics_definition WHERE metric_code LIKE 'channel_%'")
