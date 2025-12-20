#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档模板生成服务
用于使用Word/Excel模板生成批价单、结算单和报价单

策略：
- Word: 使用 python-docx 直接操作 Word 文档，替换文本并动态添加表格行
- Excel: 使用 openpyxl 操作 Excel 文档，替换单元格并动态添加行
"""

import os
import subprocess
import platform
import tempfile
from datetime import datetime, timedelta
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, Cm, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy
import logging
import openpyxl
from openpyxl.styles import Alignment, Font, Border, Side

logger = logging.getLogger(__name__)


class WordGenerator:
    """Word文档生成器"""

    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'word')

    def _get_template_path(self, template_name):
        """获取模板文件路径"""
        return os.path.join(self.template_dir, template_name)

    def _get_currency_symbol(self, currency='CNY'):
        """获取货币符号"""
        from app.utils.dictionary_helpers import get_currency_symbol
        return get_currency_symbol(currency)

    def _format_discount_rate(self, rate):
        """格式化折扣率为百分比，保留2位小数"""
        return f"{rate * 100:.2f}%"

    def _get_project_type_label(self, project_type):
        """获取项目类型标签"""
        type_map = {
            'channel_follow': '渠道跟进',
            'sales_key': '销售重点',
            'sales_opportunity': '销售机会',
        }
        return type_map.get(project_type, project_type or '未知')

    def _get_status_label(self, status):
        """获取状态标签"""
        status_map = {
            'draft': '草稿',
            'pending': '审批中',
            'approved': '已批准',
            'rejected': '已拒绝',
        }
        return status_map.get(status, status or '未知')

    def _replace_text_in_cell(self, cell, old_text, new_text):
        """替换单元格中的文本，保持格式"""
        for paragraph in cell.paragraphs:
            if old_text in paragraph.text:
                # 保持原有格式，只替换文本
                for run in paragraph.runs:
                    if old_text in run.text:
                        run.text = run.text.replace(old_text, new_text)

    def _replace_text_in_table(self, table, replacements):
        """替换表格中的所有文本"""
        for row in table.rows:
            for cell in row.cells:
                for old_text, new_text in replacements.items():
                    if old_text in cell.text:
                        self._replace_text_in_cell(cell, old_text, new_text)

    def _copy_row(self, table, row_idx):
        """复制表格行"""
        row = table.rows[row_idx]
        tr = row._tr
        new_tr = deepcopy(tr)
        table._tbl.append(new_tr)
        return table.rows[-1]

    def _set_cell_text(self, cell, text, font_size=9, align='center'):
        """设置单元格文本

        Args:
            cell: 单元格对象
            text: 文本内容
            font_size: 字体大小，默认9
            align: 对齐方式，'left'/'center'/'right'，默认'center'
        """
        cell.text = str(text)
        alignment_map = {
            'left': WD_ALIGN_PARAGRAPH.LEFT,
            'center': WD_ALIGN_PARAGRAPH.CENTER,
            'right': WD_ALIGN_PARAGRAPH.RIGHT
        }
        for paragraph in cell.paragraphs:
            paragraph.alignment = alignment_map.get(align, WD_ALIGN_PARAGRAPH.CENTER)
            for run in paragraph.runs:
                run.font.size = Pt(font_size)

    def generate_pricing_order_word(self, pricing_order):
        """
        生成批价单Word文档

        Args:
            pricing_order: PricingOrder 对象

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        try:
            template_path = self._get_template_path('pricing_order_template.docx')
            doc = Document(template_path)

            # 准备基本数据
            currency = pricing_order.currency or 'CNY'
            currency_symbol = self._get_currency_symbol(currency)

            # 计算有效期（默认审批日期起60天）
            valid_from = pricing_order.approved_at or pricing_order.created_at
            valid_to = valid_from + timedelta(days=60) if valid_from else None

            # 计算市场价总计
            market_total = sum(d.market_price * d.quantity for d in pricing_order.pricing_details)

            # 表格0: 基本信息
            table0 = doc.tables[0]
            replacements0 = {
                'PO202512-003': pricing_order.order_number,
                '2025年12月18日': (pricing_order.approved_at or pricing_order.created_at).strftime('%Y年%m月%d日') if (pricing_order.approved_at or pricing_order.created_at) else '',
                '上海东方枢纽': pricing_order.project.project_name if pricing_order.project else '',
                '渠道跟进': self._get_project_type_label(pricing_order.approval_flow_type),
                '已批准': self._get_status_label(pricing_order.status),
                '45%': self._format_discount_rate(pricing_order.pricing_total_discount_rate or 1.0),
            }
            self._replace_text_in_table(table0, replacements0)

            # 表格1: 有效期
            table1 = doc.tables[1]
            valid_from_str = valid_from.strftime('%Y年%m月%d日') if valid_from else ''
            valid_to_str = valid_to.strftime('%Y年%m月%d日') if valid_to else ''
            replacements1 = {
                '2025年12月18日 至 2026年 2月18日': f'{valid_from_str} 至 {valid_to_str}',
                '【上海东方枢纽】': f'【{pricing_order.project.project_name if pricing_order.project else ""}】',
            }
            self._replace_text_in_table(table1, replacements1)

            # 表格2: 渠道信息
            table2 = doc.tables[2]
            dealer_name = pricing_order.dealer.company_name if pricing_order.dealer else '（厂商直签）'
            distributor_name = pricing_order.distributor.company_name if pricing_order.distributor else '（无分销商）'
            project_manager = pricing_order.project.owner.real_name if pricing_order.project and pricing_order.project.owner else ''
            sales_manager = ''
            if pricing_order.project and hasattr(pricing_order.project, 'vendor_sales_manager') and pricing_order.project.vendor_sales_manager:
                sales_manager = pricing_order.project.vendor_sales_manager.real_name

            replacements2 = {
                '上海瑞康通信科技有限公司': dealer_name,
                '上海淳泊信息科技有限公司': distributor_name,
            }
            self._replace_text_in_table(table2, replacements2)

            # 表格3: 明细表格 - 动态处理
            detail_table = doc.tables[3]

            # 删除示例数据行（保留表头）
            while len(detail_table.rows) > 1:
                tr = detail_table.rows[-1]._tr
                detail_table._tbl.remove(tr)

            # 添加实际明细数据
            for idx, detail in enumerate(pricing_order.pricing_details, 1):
                row = detail_table.add_row()
                cells = row.cells

                # 设置各列数据
                self._set_cell_text(cells[0], idx)  # 序号
                self._set_cell_text(cells[1], detail.product_name or '')  # 产品名称
                self._set_cell_text(cells[2], detail.product_model or '')  # 型号
                # 规格参数（截断长文本）
                desc = detail.product_desc or ''
                if len(desc) > 40:
                    desc = desc[:40] + '...'
                self._set_cell_text(cells[3], desc)
                self._set_cell_text(cells[4], detail.brand or '和源')  # 品牌
                self._set_cell_text(cells[5], detail.quantity)  # 数量
                self._set_cell_text(cells[6], f'{currency_symbol}{detail.market_price:,.2f}')  # 零售单价
                self._set_cell_text(cells[7], self._format_discount_rate(detail.discount_rate))  # 折扣率
                self._set_cell_text(cells[8], f'{currency_symbol}{detail.unit_price:,.2f}')  # 批准单价

            # 表格4: 总金额
            table4 = doc.tables[4]
            replacements4 = {
                '¥ 63,196.20': f'{currency_symbol} {pricing_order.pricing_total_amount:,.2f}',
            }
            self._replace_text_in_table(table4, replacements4)

            # 保存到内存
            output = BytesIO()
            doc.save(output)
            output.seek(0)

            # 生成文件名
            project_name = pricing_order.project.project_name if pricing_order.project else "未知项目"
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_', '（', '）', '【', '】')).rstrip()
            filename = f"{pricing_order.order_number} & {safe_project_name}.docx"

            logger.info(f"成功生成批价单Word文档: {filename}")

            return {
                'content': output.getvalue(),
                'filename': filename
            }

        except Exception as e:
            logger.error(f"生成批价单Word文档失败: {str(e)}")
            raise

    def generate_settlement_order_word(self, pricing_order):
        """
        生成结算单Word文档

        Args:
            pricing_order: PricingOrder 对象

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        try:
            # 获取关联的结算单
            from app.models.pricing_order import SettlementOrder
            settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order.id).first()

            # 如果结算单不存在，创建一个
            if not settlement_order:
                logger.warning(f"批价单 {pricing_order.order_number} 没有关联的结算单，正在创建...")
                from app.services.pricing_order_service import PricingOrderService
                from app import db

                settlement_order = PricingOrderService.create_settlement_order(
                    pricing_order,
                    pricing_order.created_by
                )
                PricingOrderService.create_settlement_details(pricing_order, settlement_order)
                db.session.commit()

            template_path = self._get_template_path('settlement_order_template.docx')
            doc = Document(template_path)

            # 准备基本数据
            currency = pricing_order.currency or 'CNY'
            currency_symbol = self._get_currency_symbol(currency)

            # 表格0: 基本信息
            table0 = doc.tables[0]
            replacements0 = {
                'SO202512-003': settlement_order.order_number,
                '2025年12月18日': (pricing_order.approved_at or pricing_order.created_at).strftime('%Y年%m月%d日') if (pricing_order.approved_at or pricing_order.created_at) else '',
                '上海东方枢纽': pricing_order.project.project_name if pricing_order.project else '',
                '渠道跟进': self._get_project_type_label(pricing_order.approval_flow_type),
                'PO202512-003': pricing_order.order_number,
                '40.50%': self._format_discount_rate(pricing_order.settlement_total_discount_rate or 1.0),
            }
            self._replace_text_in_table(table0, replacements0)

            # 表格1: 结算对象
            table1 = doc.tables[1]
            distributor_name = pricing_order.distributor.company_name if pricing_order.distributor else '（无分销商）'
            replacements1 = {
                '上海淳泊信息科技有限公司': distributor_name,
            }
            self._replace_text_in_table(table1, replacements1)

            # 表格2: 渠道信息
            table2 = doc.tables[2]
            dealer_name = pricing_order.dealer.company_name if pricing_order.dealer else '（厂商直签）'
            replacements2 = {
                '上海瑞康通信科技有限公司': dealer_name,
                '上海淳泊信息科技有限公司': distributor_name,
            }
            self._replace_text_in_table(table2, replacements2)

            # 表格3: 明细表格 - 动态处理
            detail_table = doc.tables[3]

            # 删除示例数据行（保留表头）
            while len(detail_table.rows) > 1:
                tr = detail_table.rows[-1]._tr
                detail_table._tbl.remove(tr)

            # 添加实际明细数据
            for idx, detail in enumerate(pricing_order.settlement_details, 1):
                row = detail_table.add_row()
                cells = row.cells

                # 设置各列数据
                self._set_cell_text(cells[0], idx)  # 序号
                self._set_cell_text(cells[1], detail.product_name or '')  # 产品名称
                self._set_cell_text(cells[2], detail.product_model or '')  # 型号
                # 规格参数（截断长文本）
                desc = detail.product_desc or ''
                if len(desc) > 40:
                    desc = desc[:40] + '...'
                self._set_cell_text(cells[3], desc)
                self._set_cell_text(cells[4], detail.brand or '和源')  # 品牌
                self._set_cell_text(cells[5], detail.quantity)  # 数量
                self._set_cell_text(cells[6], f'{currency_symbol}{detail.market_price:,.2f}')  # 零售单价
                self._set_cell_text(cells[7], self._format_discount_rate(detail.discount_rate))  # 折扣率
                self._set_cell_text(cells[8], f'{currency_symbol}{detail.unit_price:,.2f}')  # 结算单价

            # 表格4: 总金额
            table4 = doc.tables[4]
            replacements4 = {
                '¥ 56,876.58': f'{currency_symbol} {pricing_order.settlement_total_amount:,.2f}',
            }
            self._replace_text_in_table(table4, replacements4)

            # 保存到内存
            output = BytesIO()
            doc.save(output)
            output.seek(0)

            # 生成文件名
            project_name = pricing_order.project.project_name if pricing_order.project else "未知项目"
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_', '（', '）', '【', '】')).rstrip()
            filename = f"{settlement_order.order_number} & {safe_project_name}.docx"

            logger.info(f"成功生成结算单Word文档: {filename}")

            return {
                'content': output.getvalue(),
                'filename': filename
            }

        except Exception as e:
            logger.error(f"生成结算单Word文档失败: {str(e)}")
            raise

    def convert_word_to_pdf(self, word_content, filename):
        """
        将Word文档转换为PDF

        Args:
            word_content: Word文档的字节内容
            filename: 原始文件名

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
                tmp_docx.write(word_content)
                tmp_docx_path = tmp_docx.name

            # PDF输出路径
            tmp_pdf_path = tmp_docx_path.replace('.docx', '.pdf')

            system = platform.system()

            if system == "Darwin":  # macOS
                # 尝试使用 LibreOffice
                libreoffice_paths = [
                    '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                    '/usr/local/bin/soffice',
                    'soffice'
                ]

                soffice_path = None
                for path in libreoffice_paths:
                    if os.path.exists(path) or path == 'soffice':
                        soffice_path = path
                        break

                if soffice_path:
                    cmd = [
                        soffice_path,
                        '--headless',
                        '--convert-to', 'pdf',
                        '--outdir', os.path.dirname(tmp_docx_path),
                        tmp_docx_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                    if result.returncode != 0:
                        logger.warning(f"LibreOffice转换失败: {result.stderr}")
                        raise Exception("LibreOffice转换失败")
                else:
                    # 尝试使用 docx2pdf (需要 Microsoft Word)
                    try:
                        from docx2pdf import convert
                        convert(tmp_docx_path, tmp_pdf_path)
                    except ImportError:
                        raise Exception("未找到PDF转换工具，请安装LibreOffice或docx2pdf")

            elif system == "Linux":
                # Linux 使用 LibreOffice
                cmd = [
                    'libreoffice',
                    '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', os.path.dirname(tmp_docx_path),
                    tmp_docx_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode != 0:
                    logger.error(f"LibreOffice转换失败: {result.stderr}")
                    raise Exception("LibreOffice转换失败")

            elif system == "Windows":
                # Windows 使用 docx2pdf
                try:
                    from docx2pdf import convert
                    convert(tmp_docx_path, tmp_pdf_path)
                except ImportError:
                    raise Exception("请安装docx2pdf: pip install docx2pdf")

            # 读取PDF内容
            if os.path.exists(tmp_pdf_path):
                with open(tmp_pdf_path, 'rb') as pdf_file:
                    pdf_content = pdf_file.read()

                # 清理临时文件
                os.unlink(tmp_docx_path)
                os.unlink(tmp_pdf_path)

                # 生成PDF文件名
                pdf_filename = filename.replace('.docx', '.pdf')

                return {
                    'content': pdf_content,
                    'filename': pdf_filename
                }
            else:
                raise Exception(f"PDF文件未生成: {tmp_pdf_path}")

        except subprocess.TimeoutExpired:
            logger.error("PDF转换超时")
            raise Exception("PDF转换超时")
        except Exception as e:
            logger.error(f"Word转PDF失败: {str(e)}")
            # 清理临时文件
            if 'tmp_docx_path' in locals() and os.path.exists(tmp_docx_path):
                os.unlink(tmp_docx_path)
            if 'tmp_pdf_path' in locals() and os.path.exists(tmp_pdf_path):
                os.unlink(tmp_pdf_path)
            raise

    def generate_pricing_order_pdf(self, pricing_order):
        """
        使用Word模板生成批价单PDF

        Args:
            pricing_order: PricingOrder 对象

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        # 先生成Word
        word_result = self.generate_pricing_order_word(pricing_order)

        # 转换为PDF
        pdf_result = self.convert_word_to_pdf(
            word_result['content'],
            word_result['filename']
        )

        return pdf_result

    def generate_settlement_order_pdf(self, pricing_order):
        """
        使用Word模板生成结算单PDF

        Args:
            pricing_order: PricingOrder 对象

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        # 先生成Word
        word_result = self.generate_settlement_order_word(pricing_order)

        # 转换为PDF
        pdf_result = self.convert_word_to_pdf(
            word_result['content'],
            word_result['filename']
        )

        return pdf_result


    def generate_quotation_word(self, quotation):
        """
        生成报价单Word文档

        Args:
            quotation: Quotation 对象

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        try:
            template_path = self._get_template_path('quotation_template.docx')
            doc = Document(template_path)

            # 准备基本数据
            currency = quotation.currency or 'CNY'
            currency_symbol = self._get_currency_symbol(currency)

            # 表格0: 客户信息
            table0 = doc.tables[0]
            customer_name = quotation.customer.company_name if quotation.customer else ''
            contact_name = quotation.contact.name if quotation.contact else ''
            quotation_date = quotation.created_at.strftime('%Y年%m月%d日') if quotation.created_at else ''

            replacements0 = {
                '上海市长宁区新泾镇人民政府': customer_name,
                '包惠青': contact_name,
            }
            self._replace_text_in_table(table0, replacements0)

            # 表格1: 明细表格 - 动态处理
            detail_table = doc.tables[1]

            # 删除示例数据行（保留表头）
            while len(detail_table.rows) > 1:
                tr = detail_table.rows[-1]._tr
                detail_table._tbl.remove(tr)

            # 添加实际明细数据（包括父子关系）
            idx = 0
            for detail in quotation.details:
                # 跳过配置产品（子产品会在父产品后面输出）
                if detail.is_accessory:
                    continue

                idx += 1
                row = detail_table.add_row()
                cells = row.cells

                # 设置父产品数据（序号居中，名称/型号/规格左对齐，数量居中，单价/金额右对齐）
                self._set_cell_text(cells[0], idx, align='center')  # 序号
                self._set_cell_text(cells[1], detail.product_name or '', align='left')  # 产品名称
                self._set_cell_text(cells[2], detail.product_model or '', align='left')  # 型号
                # 规格参数（截断长文本）
                desc = detail.product_desc or ''
                if len(desc) > 50:
                    desc = desc[:50] + '...'
                self._set_cell_text(cells[3], desc, align='left')  # 规格
                self._set_cell_text(cells[4], detail.quantity, align='center')  # 数量
                self._set_cell_text(cells[5], f'{currency_symbol}{detail.unit_price:,.2f}', align='right')  # 单价
                self._set_cell_text(cells[6], f'{currency_symbol}{detail.total_price:,.2f}', align='right')  # 金额

                # 输出子产品（配置产品）
                if detail.configurations:
                    for child in detail.configurations:
                        idx += 1
                        child_row = detail_table.add_row()
                        child_cells = child_row.cells

                        self._set_cell_text(child_cells[0], idx, align='center')  # 子产品也有序号
                        self._set_cell_text(child_cells[1], child.product_name or '', align='left')  # 产品名称
                        self._set_cell_text(child_cells[2], child.product_model or '', align='left')  # 型号
                        child_desc = child.product_desc or ''
                        if len(child_desc) > 50:
                            child_desc = child_desc[:50] + '...'
                        self._set_cell_text(child_cells[3], child_desc, align='left')  # 规格
                        self._set_cell_text(child_cells[4], child.quantity, align='center')  # 数量
                        self._set_cell_text(child_cells[5], f'{currency_symbol}{child.unit_price:,.2f}', align='right')  # 单价
                        self._set_cell_text(child_cells[6], f'{currency_symbol}{child.total_price:,.2f}', align='right')  # 金额

            # 表格2: 汇总金额
            table2 = doc.tables[2]
            # 计算小计（包含所有明细，含子产品）
            subtotal = quotation.amount or sum(d.total_price or 0 for d in quotation.details)
            vat_rate = 0  # 税率，默认0%
            vat_amount = subtotal * vat_rate
            total_amount = subtotal + vat_amount

            replacements2 = {
                '¥140,436': f'{currency_symbol}{subtotal:,.2f}',
                '¥0': f'{currency_symbol}{vat_amount:,.2f}',
                '¥140,436.00': f'{currency_symbol}{total_amount:,.2f}',
            }
            self._replace_text_in_table(table2, replacements2)

            # 保存到内存
            output = BytesIO()
            doc.save(output)
            output.seek(0)

            # 生成文件名
            project_name = quotation.project.project_name if quotation.project else "未知项目"
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_', '（', '）', '【', '】')).rstrip()
            filename = f"{quotation.quotation_number} & {safe_project_name}.docx"

            logger.info(f"成功生成报价单Word文档: {filename}")

            return {
                'content': output.getvalue(),
                'filename': filename
            }

        except Exception as e:
            logger.error(f"生成报价单Word文档失败: {str(e)}")
            raise

    def generate_quotation_pdf(self, quotation):
        """
        使用Word模板生成报价单PDF

        Args:
            quotation: Quotation 对象

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        # 先生成Word
        word_result = self.generate_quotation_word(quotation)

        # 转换为PDF
        pdf_result = self.convert_word_to_pdf(
            word_result['content'],
            word_result['filename']
        )

        return pdf_result

    def generate_quotation_excel(self, quotation):
        """
        使用Excel模板生成报价单Excel文档

        Args:
            quotation: Quotation 对象

        Returns:
            dict: {'content': bytes, 'filename': str}
        """
        try:
            template_path = self._get_template_path('quotation_template.xlsx')
            wb = openpyxl.load_workbook(template_path)
            ws = wb.active

            # 准备基本数据
            currency = quotation.currency or 'CNY'
            currency_symbol = self._get_currency_symbol(currency)

            # 货币显示名称
            currency_names = {
                'CNY': 'CNY (人民币)',
                'USD': 'USD (美元)',
                'EUR': 'EUR (欧元)',
            }
            currency_display = currency_names.get(currency, currency)

            # 替换基本信息
            customer_name = quotation.customer.company_name if quotation.customer else ''
            contact_name = quotation.contact.name if quotation.contact else ''
            quotation_date = quotation.created_at.strftime('%Y-%m-%d') if quotation.created_at else ''
            valid_until = (quotation.created_at + timedelta(days=30)).strftime('%Y-%m-%d') if quotation.created_at else ''
            prepared_by = quotation.owner.real_name if quotation.owner else ''

            # 替换单元格值
            ws['A7'] = customer_name  # 客户名称
            ws['B9'] = contact_name  # 联系人
            ws['F6'] = quotation.quotation_number  # 报价编号
            ws['F7'] = quotation_date  # 日期
            ws['F8'] = valid_until  # 有效期
            ws['F9'] = prepared_by  # 报价人
            ws['F10'] = currency_display  # 货币

            # 明细起始行
            detail_start_row = 14
            template_row = 14  # 模板中的示例行

            # 收集所有明细（包括子产品）
            all_details = []
            for detail in quotation.details:
                if detail.is_accessory:
                    continue
                all_details.append(detail)
                if detail.configurations:
                    for child in detail.configurations:
                        all_details.append(child)

            # 如果明细数量超过模板示例行数，需要插入新行
            template_detail_count = 5  # 模板中有5行示例数据
            if len(all_details) > template_detail_count:
                # 插入额外的行
                extra_rows = len(all_details) - template_detail_count
                ws.insert_rows(detail_start_row + template_detail_count, extra_rows)

            # 填充明细数据
            for idx, detail in enumerate(all_details):
                row = detail_start_row + idx
                ws[f'A{row}'] = idx + 1  # 序号
                ws[f'B{row}'] = detail.product_name or ''  # 产品名称
                ws[f'C{row}'] = detail.product_model or ''  # 型号
                # 规格参数
                desc = detail.product_desc or ''
                if len(desc) > 80:
                    desc = desc[:80] + '...'
                ws[f'D{row}'] = desc  # 规格
                ws[f'E{row}'] = detail.quantity or 0  # 数量
                ws[f'F{row}'] = detail.unit_price or 0  # 单价
                ws[f'G{row}'] = f'=E{row}*F{row}'  # 金额公式

            # 清除多余的模板行
            if len(all_details) < template_detail_count:
                for idx in range(len(all_details), template_detail_count):
                    row = detail_start_row + idx
                    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
                        ws[f'{col}{row}'] = ''

            # 更新汇总行位置
            summary_row = detail_start_row + max(len(all_details), template_detail_count) + 1
            # 小计
            ws[f'G{summary_row}'] = f'=SUM(G{detail_start_row}:G{summary_row - 1})'
            # 税费
            ws[f'G{summary_row + 1}'] = 0
            # 总计
            ws[f'G{summary_row + 2}'] = f'=G{summary_row}+G{summary_row + 1}'

            # 保存到内存
            output = BytesIO()
            wb.save(output)
            output.seek(0)

            # 生成文件名
            project_name = quotation.project.project_name if quotation.project else "未知项目"
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_', '（', '）', '【', '】')).rstrip()
            filename = f"{quotation.quotation_number} & {safe_project_name}.xlsx"

            logger.info(f"成功生成报价单Excel文档: {filename}")

            return {
                'content': output.getvalue(),
                'filename': filename
            }

        except Exception as e:
            logger.error(f"生成报价单Excel文档失败: {str(e)}")
            raise


# 创建全局实例
word_generator = WordGenerator()


# 便捷函数
def generate_pricing_order_word(pricing_order):
    """生成批价单Word文档的便捷函数"""
    return word_generator.generate_pricing_order_word(pricing_order)


def generate_settlement_order_word(pricing_order):
    """生成结算单Word文档的便捷函数"""
    return word_generator.generate_settlement_order_word(pricing_order)


def generate_pricing_order_pdf_from_word(pricing_order):
    """使用Word模板生成批价单PDF的便捷函数"""
    return word_generator.generate_pricing_order_pdf(pricing_order)


def generate_settlement_order_pdf_from_word(pricing_order):
    """使用Word模板生成结算单PDF的便捷函数"""
    return word_generator.generate_settlement_order_pdf(pricing_order)


def generate_quotation_word(quotation):
    """生成报价单Word文档的便捷函数"""
    return word_generator.generate_quotation_word(quotation)


def generate_quotation_pdf_from_word(quotation):
    """使用Word模板生成报价单PDF的便捷函数"""
    return word_generator.generate_quotation_pdf(quotation)
