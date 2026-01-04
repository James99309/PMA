"""add formula builder fields to salary_formula_config

Revision ID: add_formula_builder_20251229
Revises:
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_formula_builder_20251229'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加公式构建器相关字段"""
    # 添加适用职级类型字段 (ALL=全部, L=专业序列, M=管理序列)
    op.add_column('salary_formula_config',
        sa.Column('applicable_grade_type', sa.String(10), nullable=True, server_default='ALL')
    )

    # 添加结构化公式元素字段 (JSON格式存储)
    op.add_column('salary_formula_config',
        sa.Column('formula_elements', sa.JSON(), nullable=True)
    )

    # 更新现有数据的默认值
    op.execute("""
        UPDATE salary_formula_config
        SET applicable_grade_type = 'ALL'
        WHERE applicable_grade_type IS NULL
    """)

    # 特殊处理：综合绩效公式仅适用于M级
    op.execute("""
        UPDATE salary_formula_config
        SET applicable_grade_type = 'M'
        WHERE formula_code = 'comprehensive_rate'
    """)


def downgrade():
    """回滚迁移"""
    op.drop_column('salary_formula_config', 'formula_elements')
    op.drop_column('salary_formula_config', 'applicable_grade_type')
