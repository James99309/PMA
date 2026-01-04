"""
将编码字段从 SpecDefinition 移动到 SpecTemplateItem

背景：
- 之前错误地将编码字段添加到了 SpecDefinition（全局级）
- 现在移动到 SpecTemplateItem（模板级），以支持同一规格项在不同模板中有不同的编码配置
- 采用简化设计：只需 use_in_code + code_length 两个字段

Revision ID: move_code_fields_20251224
Revises: add_category_to_spec_template_20251224
Create Date: 2025-12-24
"""
from alembic import op
import sqlalchemy as sa


revision = 'move_code_fields_20251224'
down_revision = 'add_category_to_spec_template_20251224'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 从 spec_definitions 表移除编码字段（如果存在）
    try:
        op.drop_column('spec_definitions', 'use_in_code')
    except Exception:
        pass  # 列可能不存在

    try:
        op.drop_column('spec_definitions', 'code_position')
    except Exception:
        pass

    try:
        op.drop_column('spec_definitions', 'code_options')
    except Exception:
        pass

    # 2. 向 spec_template_items 表添加编码字段
    try:
        op.add_column('spec_template_items',
            sa.Column('use_in_code', sa.Boolean(), nullable=True, default=False)
        )
    except Exception:
        pass  # 列可能已存在

    try:
        op.add_column('spec_template_items',
            sa.Column('code_length', sa.Integer(), nullable=True, default=1)
        )
    except Exception:
        pass


def downgrade():
    # 1. 从 spec_template_items 表移除编码字段
    try:
        op.drop_column('spec_template_items', 'use_in_code')
    except Exception:
        pass

    try:
        op.drop_column('spec_template_items', 'code_length')
    except Exception:
        pass

    # 2. 向 spec_definitions 表恢复编码字段
    try:
        op.add_column('spec_definitions',
            sa.Column('use_in_code', sa.Boolean(), nullable=True, default=False)
        )
    except Exception:
        pass

    try:
        op.add_column('spec_definitions',
            sa.Column('code_position', sa.Integer(), nullable=True)
        )
    except Exception:
        pass

    try:
        op.add_column('spec_definitions',
            sa.Column('code_options', sa.JSON(), nullable=True)
        )
    except Exception:
        pass
