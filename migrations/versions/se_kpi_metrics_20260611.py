"""seed solution_manager KPI metrics (报价确认量/销售配合广度/确认质量)

解决方案经理写死考核方案(role_kpi_schemes.py)的 3 个新指标定义。
算法在 PerformanceService.calculate_se_yearly_statistics_batch(confirmed_by 口径),
此处仅登记指标元数据(配置页池子显示名称/单位用)。幂等:ON CONFLICT DO NOTHING。

Revision ID: se_kpi_metrics_20260611
Revises: project_attachments_20260611
Create Date: 2026-06-11

"""
from alembic import op

revision = 'se_kpi_metrics_20260611'
down_revision = 'project_attachments_20260611'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO performance_metrics_definition
            (metric_code, metric_name, metric_category, data_type, default_unit,
             description, is_system_metric, is_active, entry_frequency,
             created_at, updated_at)
        VALUES
            ('se_confirm_count', '报价确认量', '技术支持', 'count', '个',
             '解决方案经理确认的报价单数量(confirmed_by,按确认时间归月)',
             true, true, 'monthly', NOW(), NOW()),
            ('se_sales_support', '销售配合广度', '技术支持', 'count', '人',
             '当月确认报价覆盖的销售人数(COUNT DISTINCT owner)',
             true, true, 'monthly', NOW(), NOW()),
            ('se_confirm_quality', '确认质量', '技术支持', 'rate', '%',
             '确认报价中所属项目进入中标/批价/签约的占比',
             true, true, 'monthly', NOW(), NOW())
        ON CONFLICT (metric_code) DO NOTHING
    """)


def downgrade():
    op.execute("""
        DELETE FROM performance_metrics_definition
        WHERE metric_code IN ('se_confirm_count', 'se_sales_support', 'se_confirm_quality')
    """)
