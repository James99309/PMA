"""解决方案经理指标重定义(2026-06-14)

方案 4 项:植入额 / 确认质量(仅签约) / 销售配合广度(项目参与) / 技术培训(任务计数)。
本迁移只动指标定义表(口径在代码层 role_kpi_schemes + performance_service):
  1) se_training_count 改名「培训次数」→「技术培训」(改为任务驱动,语义统一)
  2) 停用 se_confirm_count(报价确认量)、se_sales_amount(方案批价额)—— 已移出方案,
     从配置池隐藏(幂等;历史目标记录保留不动)
全部幂等 UPDATE,可重复执行。

Revision ID: se_metric_redefine_20260614
Revises: hr_metric_attrition_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'se_metric_redefine_20260614'
down_revision = 'hr_metric_attrition_20260614'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # 1) 指标定义:改名 + 停用已移出方案的两项
    bind.execute(text(
        "UPDATE performance_metrics_definition SET metric_name='技术培训', updated_at=NOW() "
        "WHERE metric_code='se_training_count'"))
    bind.execute(text(
        "UPDATE performance_metrics_definition SET is_active=false, updated_at=NOW() "
        "WHERE metric_code IN ('se_confirm_count','se_sales_amount')"))
    # 2) 清理孤儿目标行(已从方案移除的两项,角色级 + 个人级)
    bind.execute(text(
        "DELETE FROM role_performance_targets WHERE item_code IN ('se_confirm_count','se_sales_amount')"))
    bind.execute(text(
        "DELETE FROM user_performance_targets WHERE item_code IN ('se_confirm_count','se_sales_amount')"))
    # 3) 对齐 solution_manager 角色级权重覆盖到确认方案(35/30/20;技术培训无覆盖→走方案默认 15)
    for code, w in (('se_implant_amount', 35), ('se_confirm_quality', 30), ('se_sales_support', 20)):
        bind.execute(text(
            "UPDATE role_performance_targets SET weight=:w, updated_at=NOW() "
            "WHERE role_code='solution_manager' AND item_code=:c"), {'w': w, 'c': code})


def downgrade():
    bind = op.get_bind()
    bind.execute(text(
        "UPDATE performance_metrics_definition SET metric_name='培训次数' "
        "WHERE metric_code='se_training_count'"))
    bind.execute(text(
        "UPDATE performance_metrics_definition SET is_active=true "
        "WHERE metric_code IN ('se_confirm_count','se_sales_amount')"))
    # 孤儿行删除与权重对齐不可逆(原始值已无法精确还原),downgrade 不恢复
