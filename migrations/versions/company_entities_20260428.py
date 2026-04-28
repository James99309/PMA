"""add company_entities table for multi-company quotation header

Revision ID: company_entities_20260428
Revises: quotation_excel_editor_20260428
Create Date: 2026-04-28 14:00:00.000000

新表 company_entities：报价单"主体"配置（多公司/多地区共用同一系统）
  - region: CN / SG / MY ...
  - tax_mode: inclusive (价内税，如中国增值税) / exclusive (价外税，如 GST)
  - language: zh / en — 决定编辑器和 PDF 的语言
  - logo_url: NAS WebDAV 上的 logo
  - line1/2/3: 公司名 / 地址 / UEN/网站
  - currency_code, tax_label

quotations 加 entity_id 引用，向后兼容 NULL（历史报价单走默认 entity）
"""
from alembic import op
import sqlalchemy as sa


revision = 'company_entities_20260428'
down_revision = '3db17b0942a6'
branch_labels = None
depends_on = None


def upgrade():
    # 用 raw SQL CREATE TABLE IF NOT EXISTS 避免与 db.create_all() 冲突
    op.execute("""
        CREATE TABLE IF NOT EXISTS company_entities (
            id SERIAL PRIMARY KEY,
            code VARCHAR(32) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            region VARCHAR(8) NOT NULL,
            language VARCHAR(8) NOT NULL DEFAULT 'en',
            tax_mode VARCHAR(16) NOT NULL DEFAULT 'exclusive',
            tax_label VARCHAR(32),
            currency_code VARCHAR(8) NOT NULL DEFAULT 'CNY',
            logo_url VARCHAR(512),
            line1 VARCHAR(255),
            line2 VARCHAR(255),
            line3 VARCHAR(255),
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_default BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    # 初始化数据：根据当前 DB 类型注入 CN 或 SG/MY
    # CN 库默认主体
    op.execute("""
        INSERT INTO company_entities (code, name, region, language, tax_mode, tax_label, currency_code, line1, line2, line3, sort_order, is_default)
        VALUES (
            'CN_DEFAULT', '中国默认主体', 'CN', 'zh', 'inclusive', '增值税', 'CNY',
            '上海和源通信科技有限公司',
            '上海市闵行区紫月路 999 号',
            '电话: 021-xxxx-xxxx  网址: www.evertac.cn',
            10, true
        )
        ON CONFLICT (code) DO NOTHING
    """)
    # SG 主体
    op.execute("""
        INSERT INTO company_entities (code, name, region, language, tax_mode, tax_label, currency_code, line1, line2, line3, sort_order, is_default)
        VALUES (
            'SG_DEFAULT', 'Evertac Singapore', 'SG', 'en', 'exclusive', 'GST', 'SGD',
            'EVERTAC SOLUTIONS SINGAPORE PTE. LTD.',
            '18 Boon Lay Way, #03-117 Tradehub 21, Singapore 609966',
            'UEN No/GST Reg. No.: 202230146C    Website: www.evertac-solutions.com',
            20, false
        )
        ON CONFLICT (code) DO NOTHING
    """)
    # MY 主体
    op.execute("""
        INSERT INTO company_entities (code, name, region, language, tax_mode, tax_label, currency_code, line1, line2, line3, sort_order, is_default)
        VALUES (
            'MY_DEFAULT', 'Evertac Malaysia', 'MY', 'en', 'exclusive', 'SST', 'MYR',
            'EVERTAC SOLUTIONS MALAYSIA SDN. BHD.',
            'Kuala Lumpur, Malaysia',
            'Reg. No.: 1234567-X    Website: www.evertac-solutions.com',
            30, false
        )
        ON CONFLICT (code) DO NOTHING
    """)

    # quotations 加 entity_id（同样用 raw SQL 避免冲突；ALTER ADD COLUMN IF NOT EXISTS 是 PG 9.6+ 支持）
    op.execute("""
        ALTER TABLE quotations ADD COLUMN IF NOT EXISTS entity_id INTEGER REFERENCES company_entities(id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_quotations_entity_id ON quotations(entity_id)
    """)


def downgrade():
    op.drop_index('ix_quotations_entity_id', table_name='quotations')
    with op.batch_alter_table('quotations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_quotations_entity', type_='foreignkey')
        batch_op.drop_column('entity_id')
    op.drop_table('company_entities')
