"""SE 确认质量 → 植入品质(2026-06-14)

se_confirm_quality 指标语义改为「植入品质」:本期该 SE 确认的报价单,
每单=出现过的推荐产品(citation_coefficient>0)系数之和(去重不看数量),取平均。
计分=固定档位制(scoring_mode='tiered',阈值写死不可配):
  均值 及格3→达成50% / 良好5→达成100% / 优秀7(封顶100%),两线间线性。
本迁移动指标定义:
  metric_name  '确认质量' → '植入品质'
  data_type    'rate' → 'score'(归入跨期取平均的 level 集)
  default_unit '%' → '分'
  scoring_mode → 'tiered'(固定档位,无目标输入)
  description  → 固定档位口径说明
item_code 保留 se_confirm_quality(避免大面积改键)。幂等。

Revision ID: se_implant_quality_20260614
Revises: scoring_mode_20260614
Create Date: 2026-06-14
"""
from alembic import op
from sqlalchemy import text

revision = 'se_implant_quality_20260614'
down_revision = 'scoring_mode_20260614'
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(text(
        "UPDATE performance_metrics_definition "
        "SET metric_name='植入品质', data_type='score', default_unit='分', "
        "    scoring_mode='tiered', "
        "    description='本期该 SE 确认报价单的植入品质均值:每单=出现过的推荐产品(推荐系数>0)系数之和(去重不看数量)。固定档位:及格3分→达成50%、良好5分→达成100%、优秀7分(封顶100%),阈值写死不可配。', "
        "    updated_at=NOW() "
        "WHERE metric_code='se_confirm_quality'"))


def downgrade():
    op.get_bind().execute(text(
        "UPDATE performance_metrics_definition "
        "SET metric_name='确认质量', data_type='rate', default_unit='%', scoring_mode=NULL "
        "WHERE metric_code='se_confirm_quality'"))
