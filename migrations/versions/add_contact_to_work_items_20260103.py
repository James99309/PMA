# -*- coding: utf-8 -*-
"""add contact_id to work_items

Revision ID: add_contact_20260103
Revises:
Create Date: 2026-01-03

为工作项添加联系人字段，支持关联到具体联系人
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_contact_20260103'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 contact_id 字段到 work_items 表
    op.add_column('work_items', sa.Column('contact_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_work_items_contact', 'work_items', 'contacts', ['contact_id'], ['id'])


def downgrade():
    # 删除外键和字段
    op.drop_constraint('fk_work_items_contact', 'work_items', type_='foreignkey')
    op.drop_column('work_items', 'contact_id')
