# -*- coding: utf-8 -*-
"""
export_quotation_to_excel 工具：按模板格式生成报价单 Excel。

直接在 Flask 上下文内查询数据库，使用 openpyxl 生成 .xlsx，
样式严格对照「销售报价单表模版.xlsx」。
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)

_STORAGE_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', 'storage', 'exports'
))

# ── 大写金额转换 ─────────────────────────────────────────────────────────────

_CN_DIGITS = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
_CN_UPPER  = ['', '万', '亿']


def _num_to_chinese(amount: float) -> str:
    """将金额（元）转换为人民币大写，如 12345.60 → 壹万贰仟叁佰肆拾伍元陆角整"""
    if not amount or amount == 0:
        return '零元整'
    negative = amount < 0
    amount = abs(amount)
    int_part = int(amount)
    dec = round((amount - int_part) * 100)
    jiao, fen = dec // 10, dec % 10

    def _group(n: int) -> str:
        if n == 0:
            return ''
        q, r3 = divmod(n, 1000)
        r2, r1 = divmod(r3, 100)
        r1d, r1u = divmod(r1, 10)
        s = ''
        if q:   s += _CN_DIGITS[q] + '仟'
        if r2:  s += _CN_DIGITS[r2] + '佰'
        elif q and (r1d or r1u): s += '零'
        if r1d: s += _CN_DIGITS[r1d] + '拾'
        elif r2 and r1u: s += '零'
        if r1u: s += _CN_DIGITS[r1u]
        return s

    groups, n = [], int_part
    while n > 0:
        groups.append(n % 10000)
        n //= 10000
    if not groups:
        groups = [0]

    result = ''
    for i, g in enumerate(reversed(groups)):
        seg = _group(g)
        idx = len(groups) - 1 - i
        if seg:
            result += seg + _CN_UPPER[idx]
        elif result and not result.endswith('零'):
            result += '零'
    result = result.rstrip('零') or '零'

    result = ('负' if negative else '') + result + '元'
    if jiao == 0 and fen == 0:
        result += '整'
    elif jiao == 0:
        result += '零' + _CN_DIGITS[fen] + '分'
    elif fen == 0:
        result += _CN_DIGITS[jiao] + '角整'
    else:
        result += _CN_DIGITS[jiao] + '角' + _CN_DIGITS[fen] + '分'
    return result


# ── Excel 样式常量 ───────────────────────────────────────────────────────────

_HEADER_BG  = 'F3F3F3'   # 表头灰底（来自模板）
_BORDER_CLR = '000000'

_SP8D_HEADER = '和源通信(上海)股份有限公司\n上海市普陀区武威路88弄中鑫企业广场 19号楼6层\n021-62596028'
_OVS_HEADER  = 'Evertac Solutions\nSingapore'

# 列宽（按模板原值）
_COL_WIDTHS = {
    'A': 5.5,   'B': 5.0,   'C': 15.5,  'D': 10.33,
    'E': 34.5,  'F': 8.16,  'G': 6.33,  'H': 5.33,
    'I': 7.5,   'J': 8.0,   'K': 9.83,  'L': 12.66,
}


def _thin(color=_BORDER_CLR):
    from openpyxl.styles import Border, Side
    s = Side(style='thin', color=color)
    return Border(left=s, right=s, top=s, bottom=s)


def _fill_borders(ws, r1, c1, r2, c2):
    """对范围内每个单元格都设置细边框（修复合并单元格外框缺失问题）。"""
    b = _thin()
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(row=r, column=c).border = b


def _set_cell(ws, row, col, value, *, font_name='微软雅黑', font_size=8,
              bold=False, color=None, h_align=None, v_align='center',
              wrap=False, fill_color=None, num_format=None):
    from openpyxl.styles import Font, Alignment, PatternFill
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = Font(name=font_name, size=font_size, bold=bold,
                     color=color or '000000')
    cell.alignment = Alignment(horizontal=h_align, vertical=v_align,
                                wrap_text=wrap)
    if fill_color:
        cell.fill = PatternFill(start_color=fill_color, end_color=fill_color,
                                fill_type='solid')
    if num_format:
        cell.number_format = num_format
    return cell


def _merge(ws, r1, c1, r2, c2):
    ws.merge_cells(start_row=r1, start_column=c1, end_row=r2, end_column=c2)


def _row_h(ws, row, height):
    ws.row_dimensions[row].height = height


# ── 主生成函数 ───────────────────────────────────────────────────────────────

def _build_excel(quotation, db_type: str) -> bytes:
    """根据 Quotation ORM 对象生成 Excel bytes。"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO

    wb = Workbook()
    ws = wb.active
    ws.title = '销售报价单'

    # 列宽
    for col_letter, width in _COL_WIDTHS.items():
        ws.column_dimensions[col_letter].width = width

    # ── Row 1: 公司抬头 ──────────────────────────────────────────────────────
    _row_h(ws, 1, 50.25)
    # B1:E1 — 公司名称大标题
    _merge(ws, 1, 2, 1, 5)   # B1:E1
    c_logo = ws.cell(row=1, column=2, value='和源通信')
    c_logo.font = Font(name='微软雅黑', size=22, bold=True)
    c_logo.alignment = Alignment(horizontal='center', vertical='center')
    # G1:L1 — 公司信息
    _merge(ws, 1, 7, 1, 12)  # G1:L1
    header_text = _SP8D_HEADER if db_type.upper() != 'OVS' else _OVS_HEADER
    c = ws.cell(row=1, column=7, value=header_text)
    c.font = Font(name='微软雅黑', size=8)
    c.alignment = Alignment(horizontal='right', vertical='center', wrap_text=True)

    # ── Row 2: 标题 ──────────────────────────────────────────────────────────
    _row_h(ws, 2, 53.25)
    _merge(ws, 2, 2, 2, 12)  # B2:L2
    c = ws.cell(row=2, column=2, value='销 售 报 价 单')
    c.font = Font(name='微软雅黑', size=16)
    c.alignment = Alignment(horizontal='center', vertical='center')

    # ── Row 3: 空白分隔 ──────────────────────────────────────────────────────
    _row_h(ws, 3, 19.5)
    _merge(ws, 3, 2, 3, 12)  # B3:L3

    # ── Row 4: 报价主题 ──────────────────────────────────────────────────────
    _row_h(ws, 4, 21.0)
    _merge(ws, 4, 2, 4, 3)   # B4:C4
    _merge(ws, 4, 4, 4, 12)  # D4:L4
    _set_cell(ws, 4, 2, '报价主题', h_align='left')
    project_name = (quotation.project.project_name if quotation.project else '')
    _set_cell(ws, 4, 4, project_name, h_align='left')

    # ── Row 5: 公司 / 接收人 ─────────────────────────────────────────────────
    _row_h(ws, 5, 21.0)
    _merge(ws, 5, 2, 5, 3)   # B5:C5
    _merge(ws, 5, 4, 5, 5)   # D5:E5
    _merge(ws, 5, 7, 5, 12)  # G5:L5
    _set_cell(ws, 5, 2, '公司', h_align='left')
    company_name = (quotation.customer.company_name if quotation.customer else '')
    _set_cell(ws, 5, 4, company_name, h_align='left')
    _set_cell(ws, 5, 6, '接收人', h_align='left')
    contact_name = (quotation.contact.name if quotation.contact else '')
    _set_cell(ws, 5, 7, contact_name, h_align='left')

    # ── Row 6: 联系方式 / 报价日期 ────────────────────────────────────────────
    _row_h(ws, 6, 21.0)
    _merge(ws, 6, 2, 6, 3)   # B6:C6
    _merge(ws, 6, 4, 6, 5)   # D6:E6
    _merge(ws, 6, 7, 6, 12)  # G6:L6
    _set_cell(ws, 6, 2, '联系方式', h_align='left')
    contact_phone = (quotation.contact.phone if quotation.contact else '')
    _set_cell(ws, 6, 4, contact_phone, h_align='left')
    _set_cell(ws, 6, 6, '报价日期', h_align='left')
    quote_date = quotation.created_at.strftime('%Y-%m-%d') if quotation.created_at else ''
    _set_cell(ws, 6, 7, quote_date, h_align='center')

    # ── Row 7: 报价明细标题 ──────────────────────────────────────────────────
    _row_h(ws, 7, 21.75)
    _merge(ws, 7, 2, 7, 12)  # B7:L7
    _set_cell(ws, 7, 2, '报 价 明 细', bold=False, h_align='center')

    # ── Row 8: 表头 ──────────────────────────────────────────────────────────
    _row_h(ws, 8, 21.75)
    headers = ['ID', '产品名称', '产品型号', '产品规格', '产品品牌',
               '产品单位', '数量', '折扣', '单价', '小计']
    for ci, h in enumerate(headers):
        _set_cell(ws, 8, ci + 2, h, bold=True, h_align='center',
                  fill_color=_HEADER_BG)

    # ── 明细行 ───────────────────────────────────────────────────────────────
    details = [d for d in quotation.details if not d.is_accessory]
    data_start = 9
    currency_sym = quotation.currency_symbol if hasattr(quotation, 'currency_symbol') else '¥'

    for i, d in enumerate(details):
        r = data_start + i
        _row_h(ws, r, 21.75)
        discount_pct = f'{int((d.discount or 1) * 100)}%' if d.discount else '100%'
        unit_price = d.unit_price or 0
        total = d.total_price or 0
        row_vals = [
            i + 1,
            d.product_name or '',
            d.product_model or '',
            d.product_desc or '',
            d.brand or '',
            d.unit or '',
            d.quantity or 0,
            discount_pct,
            unit_price,
            total,
        ]
        for ci, val in enumerate(row_vals):
            col = ci + 2
            if col in (9, 10):   # 单价、小计 — 数字格式
                _set_cell(ws, r, col, val, h_align='right', num_format='#,##0.00')
            elif col == 7:       # 数量 — 居中
                _set_cell(ws, r, col, val, h_align='center')
            elif col == 2:       # ID — 居中
                _set_cell(ws, r, col, val, h_align='center')
            else:
                _set_cell(ws, r, col, val, h_align='left')

    # ── 小计行 ───────────────────────────────────────────────────────────────
    subtotal_row = data_start + len(details)
    _row_h(ws, subtotal_row, 22.5)
    _merge(ws, subtotal_row, 10, subtotal_row, 11)  # J:K merged
    _set_cell(ws, subtotal_row, 3, '小计', h_align='center',
              fill_color=_HEADER_BG)
    total_amount = quotation.amount or sum(d.total_price or 0 for d in details)
    _set_cell(ws, subtotal_row, 10, total_amount, h_align='center',
              fill_color=_HEADER_BG, num_format='#,##0.00')

    # ── 金额说明 ──────────────────────────────────────────────────────────────
    note_row = subtotal_row + 1
    _row_h(ws, note_row, 22.5)
    _merge(ws, note_row, 2, note_row, 12)
    _set_cell(ws, note_row, 2,
              '金额计算说明：本单总金额 = 产品报价金额 * 优惠折扣 - 抹零金额',
              v_align='center')

    # ── 空行分隔 ──────────────────────────────────────────────────────────────
    sep_row = note_row + 1
    _row_h(ws, sep_row, 22.5)
    _merge(ws, sep_row, 2, sep_row, 12)

    # ── 报价总额行 ────────────────────────────────────────────────────────────
    total_row = sep_row + 1
    _row_h(ws, total_row, 22.5)
    _merge(ws, total_row, 4, total_row, 5)   # D:E 小写金额
    _merge(ws, total_row, 8, total_row, 12)  # H:L 大写金额
    _set_cell(ws, total_row, 2, '一', h_align='left')
    _set_cell(ws, total_row, 3, '报价总额【小写】', h_align='left')
    _set_cell(ws, total_row, 4, total_amount, bold=True, h_align='left',
              num_format='#,##0.00')
    _set_cell(ws, total_row, 6, '报价总额【大写】', h_align='left')
    _set_cell(ws, total_row, 8, _num_to_chinese(total_amount),
              bold=True, h_align='left')

    # ── 付款方式 / 交付说明 / 备注 ────────────────────────────────────────────
    extra_rows = [('二', '付款方式'), ('三', '交付说明'), ('四', '备注')]
    for idx, (num, label) in enumerate(extra_rows):
        r = total_row + 1 + idx
        _row_h(ws, r, 21.75)
        _merge(ws, r, 4, r, 12)
        _set_cell(ws, r, 2, num, h_align='left')
        _set_cell(ws, r, 3, label, h_align='left')
        _set_cell(ws, r, 4, '', h_align='left')   # 留空供手动填写

    # ── 签章行（统一微软雅黑）────────────────────────────────────────────────
    sig_row = total_row + len(extra_rows) + 3
    _row_h(ws, sig_row, 21.75)
    _merge(ws, sig_row, 7, sig_row, 10)
    _set_cell(ws, sig_row, 4, '盖章', bold=True, h_align='center')
    owner_name = ''
    if quotation.owner:
        owner_name = (getattr(quotation.owner, 'real_name', '')
                      or getattr(quotation.owner, 'username', ''))
    _set_cell(ws, sig_row, 6, f'报价人：{owner_name}', bold=True)
    _set_cell(ws, sig_row, 7, f'日期：{quote_date}', bold=True)

    # ── 边框：只到"备注"行，签章区（空行+盖章行）不加边框 ──────────────────────
    last_footer_row = total_row + len(extra_rows)   # "备注"所在行
    _fill_borders(ws, 4, 2, last_footer_row, 12)    # B4:L[备注行]

    # ── 打印设置：适应页宽，水平居中，两侧各留约半列 ─────────────────────────
    ws.print_area = f'A1:L{sig_row}'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.5
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── 工具类 ────────────────────────────────────────────────────────────────────

class ExportQuotationToExcelTool(BaseTool):
    name = 'export_quotation_to_excel'
    description = (
        '将 PMA 系统中的报价单导出为格式化 Excel 文件（.xlsx）。\n'
        '当用户说"导出报价单"、"导出报价单Excel"、"生成报价Excel"时使用。\n\n'
        '参数：\n'
        '- quotation_number（优先）：报价单编号，如 "HY2024001"\n'
        '- quotation_id（备选）：报价单 ID（整数）\n\n'
        '返回结果包含 download_url，回复"报价单Excel已生成"即可。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'quotation_number': {
                'type': 'string',
                'description': '报价单编号，如 HY2024001',
            },
            'quotation_id': {
                'type': 'integer',
                'description': '报价单 ID（整数）',
            },
        },
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        tool_input = tool_input or {}
        qnum = tool_input.get('quotation_number', '').strip()
        qid  = tool_input.get('quotation_id')
        user = context.get('user')

        if not qnum and not qid:
            return {'error': '请提供 quotation_number 或 quotation_id'}

        # ── 查询报价单 ────────────────────────────────────────────────────────
        try:
            from app.models.quotation import Quotation
            if qnum:
                q = Quotation.query.filter_by(quotation_number=qnum).first()
            else:
                q = Quotation.query.get(qid)
        except Exception as e:
            logger.exception('[export_quotation_to_excel] DB 查询异常')
            return {'error': f'查询报价单失败: {e}'}

        if not q:
            ident = qnum or str(qid)
            return {'error': f'未找到报价单 {ident}'}

        # ── 权限检查 ──────────────────────────────────────────────────────────
        try:
            from app.utils.access_control import get_viewable_data
            from app.models.quotation import Quotation as Q
            accessible = get_viewable_data(Q, user, [Q.id == q.id]).first()
            if not accessible:
                return {'error': f'您没有权限查看报价单 {q.quotation_number}'}
        except Exception as e:
            logger.warning(f'[export_quotation_to_excel] 权限检查跳过: {e}')

        # ── 生成 Excel ────────────────────────────────────────────────────────
        from flask import current_app
        db_type = 'OVS' if current_app.config.get('IS_OVS') else 'SP8D'

        try:
            xlsx_bytes = _build_excel(q, db_type)
        except Exception as e:
            logger.exception('[export_quotation_to_excel] 生成 Excel 异常')
            return {'error': f'Excel 生成失败: {e}'}

        # ── 保存文件 ──────────────────────────────────────────────────────────
        os.makedirs(_STORAGE_DIR, exist_ok=True)
        safe_num = re.sub(r'[^\w\u4e00-\u9fff]+', '_', q.quotation_number)
        date_str = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f'报价单_{safe_num}_{date_str}.xlsx'
        file_path = os.path.join(_STORAGE_DIR, filename)

        Path(file_path).write_bytes(xlsx_bytes)
        self._try_upload_nas(file_path, filename, user)

        logger.info(f'[export_quotation_to_excel] 生成: {filename}')
        return {
            'success': True,
            'filename': filename,
            'quotation_number': q.quotation_number,
            'download_url': f'/cli/api/exports/{filename}',
            'note': '下载按钮已显示在终端中，只需简短回复"报价单Excel已生成"即可。',
        }

    @staticmethod
    def _try_upload_nas(file_path: str, filename: str, user) -> None:
        try:
            from app.utils.synology_webdav_client import get_synology_webdav_client, is_nas_available
            if not is_nas_available():
                return
            client = get_synology_webdav_client()
            remote_dir = f'/exports/cli/{datetime.now().strftime("%Y/%m")}'
            client.ensure_directory(remote_dir)
            with open(file_path, 'rb') as f:
                client.upload(f'{remote_dir}/{filename}', f.read())
        except Exception as e:
            logger.debug(f'[export_quotation_to_excel] NAS 上传跳过: {e}')
