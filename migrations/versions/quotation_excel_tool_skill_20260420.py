# -*- coding: utf-8 -*-
"""Add export_quotation_to_excel as built-in tool skill entry

Revision ID: quotation_excel_tool_skill_20260420
Revises: xlsx_skill_system_20260420
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'quotation_excel_tool_skill_20260420'
down_revision = 'xlsx_skill_system_20260420'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        INSERT INTO cli_skills
            (name, title, skill_type, description, skill_body, parameters, queries,
             scope, is_active, created_at, updated_at)
        VALUES (
            'export_quotation_to_excel',
            '报价单 Excel 导出',
            'tool',
            '内置工具（非 invoke_skill 可调用）。\n'
            '将 PMA 报价单导出为格式化 Excel（「销售报价单」模板样式）。\n\n'
            '触发词：导出报价单 / 生成报价Excel / 导出报价单Excel / 报价单下载\n\n'
            '调用参数：\n'
            '- quotation_number（优先）：报价单编号，如 HY2024001\n'
            '- quotation_id（备选）：报价单 ID（整数）\n\n'
            '注意：调用前必须先确认有效的报价单编号，否则工具将返回错误。',
            NULL,
            '[]',
            '[]',
            'global',
            TRUE,
            NOW(),
            NOW()
        )
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade():
    op.execute("DELETE FROM cli_skills WHERE name = 'export_quotation_to_excel';")
