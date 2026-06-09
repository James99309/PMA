#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF生成服务
用于生成批价单和结算单的PDF文档
"""

import os
import platform
import tempfile
from datetime import datetime
from flask import render_template, current_app
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except Exception:
    HTML = CSS = FontConfiguration = None
import logging

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class PDFGenerator:
    """PDF生成器"""
    
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'pdf')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
        # 配置字体
        self.font_config = FontConfiguration() if FontConfiguration else None
        # 检查内嵌字体是否可用
        self.embedded_fonts_available = self._check_embedded_fonts()
        
    def _check_embedded_fonts(self):
        """检查项目内嵌字体是否可用"""
        try:
            project_fonts_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts')
            embedded_fonts = [
                'NotoSansCJK-Regular.ttc',  # 主要中文字体
                'SourceHanSansCN-Regular.otf',  # 备用中文字体
            ]
            
            available_fonts = []
            for font_file in embedded_fonts:
                font_path = os.path.join(project_fonts_dir, font_file)
                if os.path.exists(font_path):
                    available_fonts.append({
                        'file': font_file,
                        'path': font_path,
                        'size': os.path.getsize(font_path)
                    })
                    logger.info(f"✅ 找到项目字体: {font_file} ({os.path.getsize(font_path):,} 字节)")
            
            if available_fonts:
                logger.info(f"🎯 项目内嵌字体配置完成，共 {len(available_fonts)} 个字体文件")
                return available_fonts
            else:
                logger.warning("⚠️ 未找到项目内嵌字体，将使用系统字体")
                return []
                
        except Exception as e:
            logger.error(f"💥 检查内嵌字体失败: {e}")
            return []
    
    def _get_font_face_css(self):
        """生成字体CSS规则"""
        if not self.embedded_fonts_available:
            return ""
        
        font_css_rules = []
        
        for font_info in self.embedded_fonts_available:
            font_path = font_info['path']
            font_file = font_info['file']
            
            # 根据字体文件生成字体族名称
            if 'Noto' in font_file:
                font_family_name = 'Noto Sans CJK SC'
            elif 'SourceHan' in font_file:
                font_family_name = 'Source Han Sans CN'
            else:
                font_family_name = 'Custom Font'
            
            # 生成@font-face规则
            font_rule = f'''
            @font-face {{
                font-family: "{font_family_name}";
                src: url("file://{font_path}") format("truetype");
                font-weight: normal;
                font-style: normal;
            }}'''
            
            font_css_rules.append(font_rule)
            logger.debug(f"📝 生成字体CSS规则: {font_family_name}")
        
        return '\n'.join(font_css_rules)
        
    def _get_system_font_family(self):
        """获取优化的字体族配置"""
        # 如果有内嵌字体，优先使用
        if self.embedded_fonts_available:
            embedded_families = []
            for font_info in self.embedded_fonts_available:
                font_file = font_info['file']
                if 'Noto' in font_file:
                    embedded_families.append('"Noto Sans CJK SC"')
                elif 'SourceHan' in font_file:
                    embedded_families.append('"Source Han Sans CN"')
            
            # 项目字体 + 系统字体回退
            font_families = embedded_families + [
                '"Songti TC"', '"Songti SC"', '"STSong"',
                '"Microsoft YaHei"', '"微软雅黑"', '"DengXian"', '"等线"',
                '"DejaVu Sans"', '"Liberation Sans"',
                '"Arial"', '"Helvetica"', 'sans-serif'
            ]
            
            return ', '.join(font_families)
        
        # 原有的系统字体配置（回退）
        system = platform.system()
        if system == "Darwin":  # macOS
            return '"Songti TC", "Songti SC", "STSong", "STHeiti Light", "STHeiti", "Helvetica", "Arial", sans-serif'
        elif system == "Windows":  # Windows
            return '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体", "Arial", sans-serif'
        else:  # Linux
            return '"Noto Sans CJK SC", "DejaVu Sans", "Liberation Sans", "Arial", sans-serif'
    
    def _get_company_logo(self, company_key=None):
        """
        获取公司Logo（优先从企业字典，回退到全局Logo）
        
        Args:
            company_key: 企业字典键名，如果提供则尝试获取企业专属Logo
        """
        try:
            # 优先尝试从企业字典获取Logo
            if company_key:
                from app.models.dictionary import Dictionary
                company = Dictionary.query.filter_by(
                    type='company', 
                    key=company_key,
                    is_active=True
                ).first()
                
                if company and company.logo_content:
                    logger.debug(f"✅ 使用企业字典Logo: {company_key}")
                    return company.logo_data_url
            
            # 回退到全局Logo服务
            from app.services.logo_service import LogoService
            global_logo = LogoService.get_company_logo('evertac_logo')
            if global_logo:
                logger.debug("✅ 使用全局Logo")
                return global_logo
            
            logger.warning("⚠️ 未找到任何Logo")
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取公司Logo失败: {e}")
            return None
    
    def generate_pricing_order_pdf(self, pricing_order, include_notes=False):
        """生成批价单PDF"""
        try:
            # 获取当前系统的字体配置
            font_family = self._get_system_font_family()

            # 渲染HTML模板
            html_content = render_template(
                'pdf/pricing_order_template.html',
                pricing_order=pricing_order,
                generated_at=datetime.now(),
                font_family=font_family,
                include_notes=include_notes
            )
            
            # 生成PDF文件名：批价单编号 & 项目名称
            project_name = pricing_order.project.project_name if pricing_order.project else "未知项目"
            # 清理文件名中的特殊字符
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{pricing_order.order_number} & {safe_project_name}.pdf"
            
            # 生成PDF
            pdf_content = self._generate_pdf_from_html(html_content, filename)
            
            return {
                'content': pdf_content,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"生成批价单PDF失败: {str(e)}")
            raise
    
    def generate_settlement_order_pdf(self, pricing_order, include_notes=False):
        """生成结算单PDF"""
        try:
            # 获取关联的结算单
            from app.models.pricing_order import SettlementOrder
            settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order.id).first()
            
            # 如果结算单不存在，创建一个（兼容性处理）
            if not settlement_order:
                logger.warning(f"批价单 {pricing_order.order_number} 没有关联的结算单，正在创建...")
                from app.services.pricing_order_service import PricingOrderService
                from app import db
                
                # 创建结算单
                settlement_order = PricingOrderService.create_settlement_order(
                    pricing_order, 
                    pricing_order.created_by
                )
                
                # 创建结算单明细
                PricingOrderService.create_settlement_details(pricing_order, settlement_order)
                
                db.session.commit()
                logger.info(f"为批价单 {pricing_order.order_number} 创建了结算单 {settlement_order.order_number}")
            
            # 获取当前系统的字体配置
            font_family = self._get_system_font_family()
            
            # 渲染HTML模板
            html_content = render_template(
                'pdf/settlement_order_template.html',
                pricing_order=pricing_order,
                settlement_order=settlement_order,
                generated_at=datetime.now(),
                font_family=font_family,
                include_notes=include_notes
            )
            
            # 生成PDF文件名：结算单编号 & 项目名称
            order_number = settlement_order.order_number
            project_name = pricing_order.project.project_name if pricing_order.project else "未知项目"
            # 清理文件名中的特殊字符
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{order_number} & {safe_project_name}.pdf"
            
            # 生成PDF
            pdf_content = self._generate_pdf_from_html(html_content, filename)
            
            return {
                'content': pdf_content,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"生成结算单PDF失败: {str(e)}")
            raise
    
    def generate_quotation_pdf(self, quotation):
        """生成报价单PDF"""
        try:
            # 使用简单的Excel样式模板，确保与Excel导出格式一致
            font_family = self._get_system_font_family()
            
            # 获取企业Logo（优先使用报价单关联企业的Logo）
            company_key = None
            # 这里需要根据实际的数据模型来获取企业key
            # 暂时使用默认Logo，后续可以根据用户归属企业来获取
            
            logo_base64 = self._get_company_logo(company_key)
            
            # 渲染HTML模板 - 使用简单的Excel样式模板
            html_content = render_template(
                'pdf/quotation_template_simple.html',
                quotation=quotation,
                generated_at=datetime.now(),
                font_family=font_family,
                logo_base64=logo_base64
            )
            
            # 生成PDF文件名：报价单编号 & 项目名称
            project_name = quotation.project.project_name if quotation.project else "未知项目"
            # 清理文件名中的特殊字符
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{quotation.quotation_number} & {safe_project_name}.pdf"
            
            # 生成PDF
            pdf_content = self._generate_pdf_from_html(html_content, filename)
            
            return {
                'content': pdf_content,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"生成报价单PDF失败: {str(e)}")
            raise
    
    def generate_order_pdf(self, order):
        """生成订单PDF"""
        try:
            # 获取当前系统的字体配置
            font_family = self._get_system_font_family()
            
            # 渲染HTML模板
            html_content = render_template(
                'pdf/order_template.html',
                order=order,
                generated_at=datetime.now(),
                font_family=font_family
            )
            
            # 生成PDF文件名：订单编号 & 供应商名称
            company_name = order.company.company_name if order.company else "未知供应商"
            # 清理文件名中的特殊字符
            safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{order.order_number} & {safe_company_name}.pdf"
            
            # 生成PDF
            pdf_content = self._generate_pdf_from_html(html_content, filename)
            
            return {
                'content': pdf_content,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"生成订单PDF失败: {str(e)}")
            raise
    
    # 报销科目中英标签（数据库 EXPENSE_CATEGORIES 仅有中文，这里补英文）
    EXPENSE_CATEGORY_LABELS = {
        'entertainment':        {'zh': '招待费',   'en': 'Entertainment'},
        'local_transport':      {'zh': '市内交通', 'en': 'Local Transport'},
        'travel_accommodation': {'zh': '差旅住宿', 'en': 'Travel & Accommodation'},
        'office_supplies':      {'zh': '办公用品', 'en': 'Office Supplies'},
        'communication':        {'zh': '通讯费',   'en': 'Communication'},
        'fuel':                 {'zh': '油费',     'en': 'Fuel'},
        'parking':              {'zh': '停车费',   'en': 'Parking'},
        'meals':                {'zh': '餐费',     'en': 'Meals'},
        'other':                {'zh': '其他',     'en': 'Other'},
    }
    EXPENSE_STATUS_LABELS = {
        'draft':            {'zh': '草稿',   'en': 'Draft'},
        'pending':          {'zh': '待审批', 'en': 'Pending'},
        'approved':         {'zh': '已通过', 'en': 'Approved'},
        'rejected':         {'zh': '已驳回', 'en': 'Rejected'},
        'recalled':         {'zh': '已召回', 'en': 'Recalled'},
        'awaiting_payment': {'zh': '待支付', 'en': 'Awaiting Payment'},
        'paid':             {'zh': '已支付', 'en': 'Paid'},
    }

    def _editorial_fontface_css(self):
        """报销单横版 PDF 专用 @font-face（编辑风格品牌字体）。

        Latin: Instrument Serif(标题) / Geist(正文) / Geist Mono(编号·数字)
        CJK:   复用项目内嵌 NotoSansCJK
        全部用绝对 file:// 路径,确保 NAS(Linux) 渲染也能找到。
        """
        fonts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts'))
        edir = os.path.join(fonts_dir, 'editorial')

        def furl(path):
            return 'file://' + path

        faces = [
            ('Instrument Serif', 'InstrumentSerif-Regular.ttf', 'normal', 'normal'),
            ('Geist',            'Geist-Light.ttf',              '300',    'normal'),
            ('Geist',            'Geist-Regular.ttf',            'normal', 'normal'),
            ('Geist',            'Geist-Medium.ttf',             '500',    'normal'),
            ('Geist Mono',       'GeistMono-Regular.ttf',        'normal', 'normal'),
            ('Geist Mono',       'GeistMono-Medium.ttf',         '500',    'normal'),
        ]
        rules = []
        for family, fname, weight, style in faces:
            fpath = os.path.join(edir, fname)
            if os.path.exists(fpath):
                rules.append(
                    f'@font-face {{ font-family: "{family}"; '
                    f'src: url("{furl(fpath)}") format("truetype"); '
                    f'font-weight: {weight}; font-style: {style}; }}'
                )
        # CJK（复用已有内嵌字体）
        cjk = os.path.join(fonts_dir, 'NotoSansCJK-Regular.ttc')
        if os.path.exists(cjk):
            rules.append(
                f'@font-face {{ font-family: "Noto Sans CJK SC"; '
                f'src: url("{furl(cjk)}") format("truetype"); '
                f'font-weight: normal; font-style: normal; }}'
            )
        return '\n'.join(rules)

    def generate_expense_pdf(self, expense):
        """生成报销单 PDF（EVERTAC 品牌横版 A4；基本信息 + 明细 + 签字行；
        不含发票附件、系统审批流、支付信息）。

        语言按数据库类型决定：OVS→英文(EVERTAC SOLUTIONS logo)，
        SP8D/本地→中文(EVERTAC 和源通信 logo)。
        """
        try:
            from app.utils.dictionary_helpers import get_currency_symbol

            lang = 'en' if (current_app and current_app.config.get('IS_OVS', False)) else 'zh'
            currency_sym = get_currency_symbol(expense.currency or 'CNY')

            # 按语言/服务器选 logo
            logo_file = 'evertac_solutions.png' if lang == 'en' else 'evertac_cn.png'
            logo_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__), '..', 'static', 'img', 'company_logos', logo_file))
            logo_url = 'file://' + logo_path if os.path.exists(logo_path) else ''

            def cat_label(code):
                m = self.EXPENSE_CATEGORY_LABELS.get(code)
                return m[lang] if m else (code or '')

            def status_label(code):
                m = self.EXPENSE_STATUS_LABELS.get(code)
                return m[lang] if m else (code or '')

            html_content = render_template(
                'pdf/expense_template.html',
                expense=expense,
                lang=lang,
                currency_sym=currency_sym,
                cur_sym=get_currency_symbol,   # 供明细按各自发票货币取符号
                cat_label=cat_label,
                status_label=status_label,
                generated_at=datetime.now(),
                logo_url=logo_url,
                fontface_css=self._editorial_fontface_css(),
            )

            num = expense.expense_number or str(expense.id)
            filename = f'报销单_{num}.pdf' if lang == 'zh' else f'Expense_{num}.pdf'

            # 专用渲染：样式全在模板内（横版 @page + @font-face），不套用竖版通用 _get_pdf_css
            html_doc = HTML(string=html_content,
                            base_url=(current_app.static_folder if current_app else None))
            pdf_content = html_doc.write_pdf(font_config=self.font_config)
            return {'content': pdf_content, 'filename': filename}

        except Exception as e:
            logger.error(f"生成报销单PDF失败: {str(e)}")
            raise

    def _generate_pdf_from_html(self, html_content, filename):
        """从HTML内容生成PDF文件"""
        try:
            # 获取字体CSS和PDF样式
            font_css = self._get_font_face_css()
            pdf_css = self._get_pdf_css()
            
            # 合并CSS
            combined_css = font_css + "\n" + pdf_css
            
            # 生成PDF内容
            html_doc = HTML(string=html_content, base_url=current_app.static_folder if current_app else None)
            css_doc = CSS(string=combined_css, font_config=self.font_config)
            
            # 直接生成PDF字节内容，使用字体配置
            pdf_content = html_doc.write_pdf(
                stylesheets=[css_doc],
                font_config=self.font_config
            )
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"从HTML生成PDF失败: {str(e)}")
            raise
    
    def _get_pdf_css(self):
        """获取PDF样式"""
        system = platform.system()
        
        # 根据操作系统选择字体
        if system == "Darwin":  # macOS
            font_family = '"Songti TC", "Songti SC", "STSong", "STHeiti Light", "STHeiti", "Helvetica", "Arial", sans-serif'
        elif system == "Windows":  # Windows
            font_family = '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体", "Arial", sans-serif'
        else:  # Linux
            font_family = '"Noto Sans CJK SC", "DejaVu Sans", "Liberation Sans", "Arial", sans-serif'
        
        return f"""
        @page {{
            size: A4;
            margin: 2cm 1.5cm;
            @top-center {{
                content: "";
                font-size: 10px;
                color: #666;
            }}
            @bottom-center {{
                content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
                font-size: 10px;
                color: #666;
            }}
        }}
        
        body {{
            font-family: {font_family};
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        
        .document-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
        }}
        
        .document-title {{
            font-size: 24px;
            font-weight: bold;
            color: #0066cc;
            margin-bottom: 10px;
        }}
        
        .document-subtitle {{
            font-size: 14px;
            color: #666;
        }}
        
        .order-info {{
            margin-bottom: 25px;
        }}
        
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        .info-table td {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            vertical-align: top;
        }}
        
        .info-label {{
            background-color: #f8f9fa;
            font-weight: bold;
            width: 120px;
            color: #495057;
        }}
        
        .info-value {{
            background-color: white;
        }}
        
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #0066cc;
            margin: 25px 0 15px 0;
            padding-bottom: 5px;
        }}
        
        .details-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-size: 11px;
        }}
        
        .details-table th {{
            background-color: #0066cc;
            color: white;
            padding: 10px 6px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #0066cc;
        }}
        
        .details-table td {{
            padding: 8px 6px;
            border: 1px solid #ddd;
            text-align: center;
            vertical-align: middle;
        }}
        
        .details-table .text-left {{
            text-align: left;
        }}
        
        .details-table .text-right {{
            text-align: right;
        }}
        
        .details-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .summary-section {{
            margin-top: 30px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        
        .summary-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .summary-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid #ddd;
        }}
        
        .summary-label {{
            font-weight: bold;
            color: #495057;
            width: 150px;
        }}
        
        .summary-value {{
            color: #333;
        }}
        
        .total-amount {{
            font-size: 18px;
            font-weight: bold;
            color: #0066cc;
            text-align: right;
            margin-top: 15px;
            padding-top: 15px;
        }}
        """

# 创建全局实例
pdf_generator = PDFGenerator()

# 便捷函数
def generate_pricing_order_pdf(pricing_order):
    """生成批价单PDF的便捷函数"""
    result = pdf_generator.generate_pricing_order_pdf(pricing_order)
    return result['content']

def generate_settlement_order_pdf(pricing_order):
    """生成结算单PDF的便捷函数"""
    result = pdf_generator.generate_settlement_order_pdf(pricing_order)
    return result['content']

def generate_quotation_pdf(quotation):
    """生成报价单PDF的便捷函数"""
    result = pdf_generator.generate_quotation_pdf(quotation)
    return result['content']

def generate_order_pdf(order):
    """生成订单PDF的便捷函数"""
    result = pdf_generator.generate_order_pdf(order)
    return result['content'] 


def get_company_logo_base64():
    """获取公司Logo的Base64编码（兼容函数，调用数据库Logo服务）"""
    try:
        from app.services.logo_service import get_company_logo_base64 as get_db_logo
        return get_db_logo('evertac_logo')
    except Exception as e:
        logger.error(f"❌ 获取数据库Logo失败: {e}")
        return None
