# -*- coding: utf-8 -*-
"""add business_card_image_url + ocr_json_data to contacts

Revision ID: business_card_fields_20260508
Revises: cross_team_mirror_20260505
Create Date: 2026-05-08

拍照扫名片自动录入联系人功能配套字段:
- business_card_image_url: 名片图 (裁剪后干净矩形) 在 NAS 的下载 URL
- ocr_json_data: Claude vision 返回的原始 JSON, 用于后续审计/调试
两字段都可空, 兼容历史 Contact 记录。
"""
from alembic import op
import sqlalchemy as sa


revision = 'business_card_fields_20260508'
down_revision = 'cross_team_mirror_20260505'
branch_labels = None
depends_on = None


def upgrade():
    # idempotent: 已存在则跳过
    bind = op.get_bind()
    cols = {row[0] for row in bind.execute(sa.text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'contacts'"
    ))}
    if 'business_card_image_url' not in cols:
        op.add_column('contacts', sa.Column('business_card_image_url', sa.String(500), nullable=True))
    if 'ocr_json_data' not in cols:
        op.add_column('contacts', sa.Column('ocr_json_data', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('contacts', 'ocr_json_data')
    op.drop_column('contacts', 'business_card_image_url')
