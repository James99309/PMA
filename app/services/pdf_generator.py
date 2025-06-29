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
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import logging

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class PDFGenerator:
    """PDF生成器"""
    
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'pdf')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
        # 配置字体
        self.font_config = FontConfiguration()
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
    
    def generate_pricing_order_pdf(self, pricing_order):
        """生成批价单PDF"""
        try:
            # 获取当前系统的字体配置
            font_family = self._get_system_font_family()
            
            # 渲染HTML模板
            html_content = render_template(
                'pdf/pricing_order_template.html',
                pricing_order=pricing_order,
                generated_at=datetime.now(),
                font_family=font_family
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
    
    def generate_settlement_order_pdf(self, pricing_order):
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
                font_family=font_family
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
            # 获取当前系统的字体配置
            font_family = self._get_system_font_family()
            
            # 渲染HTML模板
            html_content = render_template(
                'pdf/quotation_template.html',
                quotation=quotation,
                generated_at=datetime.now(),
                font_family=font_family
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