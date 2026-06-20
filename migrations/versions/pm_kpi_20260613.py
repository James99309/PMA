"""产品经理岗位方案指标(2026-06-13 确认:去批价额;研发/质量/支持走手工录入)

pm_implant_amount(已有) + 新增:pm_dev_rate 研发计划达成率(手工,%)/
pm_new_launch 新品上市(自动,个)/ pm_quality_rate 批次质量合格率(手工,%)/
pm_support_count 上市支持(手工,次)

Revision ID: pm_kpi_20260613
Revises: report_bizline_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'pm_kpi_20260613'
down_revision = 'report_bizline_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO performance_metrics_definition
            (metric_code, metric_name, metric_category, data_type, default_unit,
             description, is_system_metric, is_active, created_at)
        VALUES
            ('pm_dev_rate', '研发计划达成', '产品管理', 'percentage', '%',
             '当期研发/迭代里程碑按计划完成率;手工按月录入(完成里程碑÷计划里程碑×100),可附凭证', true, true, NOW()),
            ('pm_new_launch', '新品上市', '产品管理', 'count', '个',
             '负责范围(产品归属人/分类负责人)当期新上市的在产产品数(自动统计)', true, true, NOW()),
            ('pm_quality_rate', '批次质量', '产品管理', 'percentage', '%',
             '生产批次合格率;手工按月录入,可上传质检报告作为凭证', true, true, NOW()),
            ('pm_support_count', '上市支持', '产品管理', 'count', '次',
             '培训/产品资料/技术支持产出次数;手工按月录入', true, true, NOW())
        ON CONFLICT (metric_code) DO NOTHING
    """)


def downgrade():
    op.execute("DELETE FROM performance_metrics_definition WHERE metric_code IN "
               "('pm_dev_rate','pm_new_launch','pm_quality_rate','pm_support_count')")
