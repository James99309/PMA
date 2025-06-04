"""product_analysis_module_deployment_marker_may_2025

Revision ID: product_analysis_2025
Revises: 302d37d8a408
Create Date: 2025-05-26 08:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'product_analysis_2025'
down_revision = '302d37d8a408'
branch_labels = None
depends_on = None


def upgrade():
    # 产品分析模块部署标记 - 无数据库结构变更
    # 该模块复用现有的Product、Quotation、QuotationDetail、Project等表
    pass


def downgrade():
    # 产品分析模块回滚标记
    pass 