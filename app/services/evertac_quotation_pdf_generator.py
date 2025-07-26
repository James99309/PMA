#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVERTAC报价单PDF生成器
基于真实Excel模板的精确PDF生成系统
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from flask import render_template_string
from app.services.logo_service import LogoService
from app.services.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)

class EvertacQuotationPDFGenerator(PDFGenerator):
    """基于EVERTAC Excel模板的精确PDF生成器"""
    
    def __init__(self):
        super().__init__()
        self.template_config = self._load_excel_template_config()
        self.field_mapping = self._load_field_mapping()
        
    def _load_excel_template_config(self):
        """加载Excel模板配置"""
        try:
            # 从处理后的Excel配置文件加载
            config_path = Path(__file__).parent.parent.parent / "Downloads" / "template_output" / "optimized_field_mapping.json"
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("✅ Excel模板配置加载成功")
                return config
            else:
                logger.warning("⚠️ Excel模板配置文件不存在，使用默认配置")
                return self._get_default_template_config()
                
        except Exception as e:
            logger.error(f"❌ 加载Excel模板配置失败: {e}")
            return self._get_default_template_config()
    
    def _get_default_template_config(self):
        """获取默认模板配置"""
        return {
            "字段映射": {
                "E3": "quotation.quotation_number",
                "B7": "quotation.project.company.company_name",
                "H8": "quotation.created_at",
                "H32": "quotation.subtotal",
                "H33": "quotation.total_amount"
            },
            "样式配置": {
                "logo_position": "A1:D5",
                "title_position": "E2"
            }
        }
    
    def _load_field_mapping(self):
        """加载字段映射"""
        return self.template_config.get("字段映射", {})
    
    def generate_quotation_pdf(self, quotation, export_info=None):
        """生成EVERTAC报价单PDF"""
        try:
            logger.info(f"🔄 开始生成EVERTAC报价单PDF: {quotation.quotation_number}")
            logger.info(f"📦 收到的导出信息: {export_info}")
            
            # 准备模板数据
            template_data = self._prepare_template_data(quotation, export_info)
            
            # 获取Logo - 优先从用户所属企业字典获取
            logo_base64 = self._get_user_company_logo(quotation.owner)
            
            # 渲染HTML模板
            html_content = self._render_evertac_template(template_data, logo_base64)
            
            # 生成PDF文件名
            project_name = quotation.project.project_name if quotation.project else "Unknown Project"
            safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{quotation.quotation_number} - {safe_project_name}.pdf"
            
            # 生成PDF
            pdf_content = self._generate_pdf_from_html(html_content, filename)
            
            logger.info(f"✅ EVERTAC报价单PDF生成成功: {filename}")
            
            return {
                'content': pdf_content,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"❌ 生成EVERTAC报价单PDF失败: {e}")
            raise
    
    def _prepare_template_data(self, quotation, export_info=None):
        """准备模板数据"""
        # 格式化日期
        created_date = quotation.created_at.strftime('%m.%d.%Y') if quotation.created_at else datetime.now().strftime('%m.%d.%Y')
        
        # 计算有效期（通常是30天后）
        from datetime import timedelta
        valid_until = quotation.created_at + timedelta(days=30) if quotation.created_at else datetime.now() + timedelta(days=30)
        valid_until_str = valid_until.strftime('%m.%d.%Y')
        
        # 获取用户所属企业信息
        company_info = self._get_user_company_info(quotation.owner)
        
        # 确定货币符号和显示名称
        currency = quotation.currency or 'CNY'
        currency_symbol = '¥' if currency == 'CNY' else '$'
        currency_display = '人民币' if currency == 'CNY' else '美元' if currency == 'USD' else currency
        
        # 准备产品明细
        details = []
        for i, detail in enumerate(quotation.details, 1):
            formatted_detail = {
                'item_number': i,
                'product_name': str(detail.product_name) if detail.product_name else '',
                'product_description': str(detail.product_desc) if detail.product_desc else '',
                'specifications': str(detail.product_model) if detail.product_model else '',
                'detailed_description': self._format_detailed_description(detail),
                'brand': str(getattr(detail, 'brand', '')) if getattr(detail, 'brand', '') else '',
                'quantity': detail.quantity or 0,
                'unit_price': detail.unit_price or 0,
                'total_price': detail.total_price or 0,
                'unit_price_formatted': f"{currency_symbol}{detail.unit_price:,.2f}" if detail.unit_price else f"{currency_symbol}0.00",
                'total_price_formatted': f"{currency_symbol}{detail.total_price:,.2f}" if detail.total_price else f"{currency_symbol}0.00",
                'product_mn': str(getattr(detail, 'product_mn', '')) if getattr(detail, 'product_mn', '') else ''
            }
            details.append(formatted_detail)
        
        # 计算总计
        subtotal = sum(detail.total_price or 0 for detail in quotation.details)
        
        # 确定当前语言环境
        from flask import session, g
        try:
            current_language = getattr(g, 'current_language', 'zh') or session.get('language', 'zh')
        except:
            current_language = 'zh'
        
        # 准备国际化文本
        i18n_texts = self._get_i18n_texts(current_language)
        
        template_data = {
            'quotation': {
                'quotation_number': quotation.quotation_number,
                'version': '1.0',
                'created_at': created_date,
                'valid_until': valid_until_str,
                'currency': currency,
                'currency_display': currency_display,
                'payment_terms': '30 days',
                'subtotal': subtotal,
                'total_amount': quotation.amount or subtotal,
                
                # 添加owner信息
                'owner': quotation.owner,
                
                # 添加国际化文本
                'i18n': i18n_texts,
                
                'subtotal_formatted': f"{currency_symbol}{subtotal:,.2f}",
                'total_amount_formatted': f"{currency_symbol}{(quotation.amount or subtotal):,.2f}",
                
                'project': {
                    'project_name': quotation.project.project_name if quotation.project else '',
                    'location': self._get_customer_address(quotation, export_info),  # 使用客户地址方法
                    'description': self._get_project_description(quotation),
                    'company': {
                        'company_name': self._get_company_name(quotation, export_info),
                        'contact_person': self._get_contact_person(quotation, export_info),
                        'contact_phone': self._get_contact_phone(quotation, export_info)  # 添加联系电话
                    }
                },
                
                'details': details,
                
                'notes': self._prepare_notes_data(quotation, export_info, current_language),
                
                'prepared_by': {
                    'name': quotation.owner.real_name if quotation.owner else 'EVERTAC Solutions'
                },
                
                'company_info': company_info
            }
        }
        
        return template_data
    
    def _format_detailed_description(self, detail):
        """格式化详细描述"""
        desc_parts = []
        
        if detail.product_desc:
            desc_parts.append(str(detail.product_desc))
        
        if detail.product_model:
            desc_parts.append(f"型号: {str(detail.product_model)}")
        
        if hasattr(detail, 'brand') and detail.brand:
            desc_parts.append(f"品牌: {str(detail.brand)}")
        
        return " | ".join(desc_parts) if desc_parts else ""
    
    def _get_project_location(self, quotation, export_info=None):
        """获取项目地点"""
        if not quotation or not quotation.project:
            return ""
        
        # 优先使用导出信息中的客户地址
        if export_info and export_info.get('customer'):
            customer_info = export_info['customer']
            if customer_info and customer_info.get('address'):
                return str(customer_info['address']).strip()
            
        if hasattr(quotation.project, 'location') and quotation.project.location:
            location = str(quotation.project.location).strip()
            if location and location != "" and location.lower() != "none":
                return location
                
        # 如果没有有效的项目地点，返回空字符串
        return ""
    
    def _get_project_description(self, quotation):
        """获取项目描述"""
        if quotation.project and hasattr(quotation.project, 'description'):
            return quotation.project.description
        return f"{quotation.project.project_name} - 设备供应及安装" if quotation.project else "设备供应项目"
    
    def _get_company_name(self, quotation, export_info=None):
        """获取公司名称"""
        if not quotation or not quotation.project:
            logger.warning("⚠️ 无法获取报价单或项目信息")
            return ""
        
        logger.info(f"🔍 获取公司名称 - export_info: {export_info}")
        
        # 优先使用导出信息中的客户
        if export_info and export_info.get('customer'):
            customer_info = export_info['customer']
            logger.info(f"📋 导出信息中的客户数据: {customer_info}")
            if customer_info and customer_info.get('company_name'):
                logger.info(f"✅ 使用导出信息中的客户: {customer_info['company_name']}")
                return str(customer_info['company_name']).strip()
        else:
            logger.warning("⚠️ 导出信息中没有客户数据，使用原始数据")
            
        project = quotation.project
        
        # 尝试从quotation_customer获取
        if hasattr(project, 'quotation_customer') and project.quotation_customer is not None:
            customer_raw = project.quotation_customer
            # 检查是否是数字类型（可能错误地获取了价格字段）
            if isinstance(customer_raw, (int, float)):
                logger.error(f"❌ quotation_customer 字段包含数字值: {customer_raw} - 可能是字段映射错误")
                # 继续尝试其他字段
            else:
                customer = str(customer_raw).strip()
                if customer and customer != "" and customer.lower() != "none":
                    logger.info(f"✅ 从 quotation_customer 获取公司名称: {customer}")
                    return customer
                
        # 尝试从end_user获取  
        if hasattr(project, 'end_user') and project.end_user is not None:
            end_user_raw = project.end_user
            if isinstance(end_user_raw, (int, float)):
                logger.error(f"❌ end_user 字段包含数字值: {end_user_raw} - 可能是字段映射错误")
            else:
                end_user = str(end_user_raw).strip()
                if end_user and end_user != "" and end_user.lower() != "none":
                    logger.info(f"✅ 从 end_user 获取公司名称: {end_user}")
                    return end_user
                
        # 尝试从contractor获取
        if hasattr(project, 'contractor') and project.contractor is not None:
            contractor_raw = project.contractor
            if isinstance(contractor_raw, (int, float)):
                logger.error(f"❌ contractor 字段包含数字值: {contractor_raw} - 可能是字段映射错误")
            else:
                contractor = str(contractor_raw).strip()
                if contractor and contractor != "" and contractor.lower() != "none":
                    logger.info(f"✅ 从 contractor 获取公司名称: {contractor}")
                    return contractor
                
        # 如果都没有有效值，返回空字符串
        logger.warning("⚠️ 无法获取有效的公司名称")
        return ""
    
    def _get_i18n_texts(self, language='zh'):
        """获取国际化文本"""
        if language == 'en':
            return {
                # 地址标签
                'address_label': 'Address',
                'phone_label': 'Phone',
                'website_label': 'Website',
                
                # 报价单标题
                'quotation_title': 'QUOTATION',
                
                # 信息表格标签
                'project_label': 'Project',
                'company_label': 'Company',
                'address_info_label': 'Address',
                'date_label': 'Date',
                'contact_label': 'Contact',
                'responsible_label': 'Responsible',
                'contact_info_label': 'Contact Info',
                'currency_label': 'Currency',
                'number_label': 'Number',
                'version_label': 'Version',
                
                # 产品表格标签
                'item_label': 'Item',
                'description_label': 'Description',
                'qty_label': 'Qty',
                'unit_price_label': 'Unit Price',
                'total_price_label': 'Total Price',
                'subtotal_label': 'Subtotal',
                'total_label': 'Total',
                
                # 备注标签
                'notes_title': 'Terms and Conditions',
                'delivery_clause': 'Delivery Terms: On-site delivery',
                'delivery_time': 'Delivery Time: 4-6 weeks after contract signing',
                'warranty': 'Warranty: 24 months after goods handover',
                'payment_terms': 'Payment Terms: Payment within 30 days after contract signing',
                'others': 'Others: Price valid for 30 days',
                
                # 签名标签
                'signature_title': 'Confirmation',
                'supplier_signature': 'Supplier Signature',
                'customer_signature': 'Customer Signature',
                'signature_note': 'This quotation will be valid upon signature confirmation by both parties.'
            }
        else:
            return {
                # 地址标签
                'address_label': '地址',
                'phone_label': '电话',
                'website_label': '网址',
                
                # 报价单标题
                'quotation_title': '报价单',
                
                # 信息表格标签
                'project_label': '项目',
                'company_label': '公司',
                'address_info_label': '公司地址',
                'date_label': '日期',
                'contact_label': '联系人',
                'responsible_label': '报价负责人',
                'contact_info_label': '联系方式',
                'currency_label': '货币',
                'number_label': '编号',
                'version_label': '版本',
                
                # 产品表格标签
                'item_label': '项目',
                'description_label': '描述',
                'qty_label': '数量',
                'unit_price_label': '单价',
                'total_price_label': '总价',
                'subtotal_label': '小计',
                'total_label': '总计',
                
                # 备注标签
                'notes_title': '条款和条件',
                'delivery_clause': '交付条款：项目现场交付',
                'delivery_time': '交付时间：合同签订后 4-6 周',
                'warranty': '质保：货物移交后24个月',
                'payment_terms': '付款条款：合同签订后30天内付款',
                'others': '其他：价格有效期30天',
                
                # 签名标签
                'signature_title': '签字确认',
                'supplier_signature': '供方签字',
                'customer_signature': '客户签字',
                'signature_note': '此报价单经双方签字确认后生效。'
            }
    
    def _prepare_notes_data(self, quotation, export_info=None, language='zh'):
        """准备备注数据"""
        # 如果导出信息中包含自定义备注，使用自定义备注
        if export_info and export_info.get('notes'):
            custom_notes = export_info['notes'].strip()
            if custom_notes:
                # 将自定义备注按行分割并格式化
                notes_lines = custom_notes.split('\n')
                formatted_notes = {}
                
                for i, line in enumerate(notes_lines):
                    line = line.strip()
                    if line:
                        key = f"note_{i+1}"
                        formatted_notes[key] = line
                
                # 添加常用的备注字段映射
                if len(notes_lines) >= 1 and notes_lines[0].strip():
                    formatted_notes['delivery_note'] = notes_lines[0].strip()
                if len(notes_lines) >= 2 and notes_lines[1].strip():
                    formatted_notes['delivery_time'] = notes_lines[1].strip()
                if len(notes_lines) >= 3 and notes_lines[2].strip():
                    formatted_notes['warranty'] = notes_lines[2].strip()
                if len(notes_lines) >= 4 and notes_lines[3].strip():
                    formatted_notes['payment_terms_detail'] = notes_lines[3].strip()
                if len(notes_lines) >= 5 and notes_lines[4].strip():
                    formatted_notes['additional_info'] = notes_lines[4].strip()
                
                # 添加完整的自定义备注内容
                formatted_notes['custom_content'] = custom_notes
                
                return formatted_notes
        
        # 使用默认备注
        i18n = self._get_i18n_texts(language)
        return {
            'delivery_note': i18n['delivery_clause'],
            'delivery_time': i18n['delivery_time'],
            'warranty': i18n['warranty'],
            'payment_terms_detail': i18n['payment_terms'],
            'additional_info': i18n['others'],
            'custom_content': f"{i18n['delivery_clause']}\n{i18n['delivery_time']}\n{i18n['warranty']}\n{i18n['payment_terms']}\n{i18n['others']}"
        }
    
    def _get_contact_person(self, quotation, export_info=None):
        """获取联系人"""
        if not quotation:
            return ""
        
        # 优先使用导出信息中的联系人
        if export_info and export_info.get('contact'):
            contact_info = export_info['contact']
            if contact_info and contact_info.get('name'):
                return str(contact_info['name']).strip()
            
        # 首先尝试从报价单直接获取联系人信息
        if hasattr(quotation, 'contact_person') and quotation.contact_person:
            contact = str(quotation.contact_person).strip()
            if contact and contact != "" and contact.lower() != "none":
                return contact
        
        # 然后尝试从项目获取
        if quotation.project and hasattr(quotation.project, 'contact_person') and quotation.project.contact_person:
            contact = str(quotation.project.contact_person).strip()
            if contact and contact != "" and contact.lower() != "none":
                return contact
        
        # 如果都没有有效值，返回空字符串
        return ""
    
    def _get_customer_address(self, quotation, export_info=None):
        """获取客户地址"""
        if not quotation:
            return ""
        
        # 优先使用导出信息中的客户地址
        if export_info and export_info.get('customer'):
            customer_info = export_info['customer']
            if customer_info and customer_info.get('address'):
                return str(customer_info['address']).strip()
        
        # 尝试从项目location获取
        if quotation.project and hasattr(quotation.project, 'location') and quotation.project.location:
            address = str(quotation.project.location).strip()
            if address and address != "" and address.lower() != "none":
                return address
        
        # 如果都没有有效值，返回空字符串
        return ""
    
    def _get_contact_phone(self, quotation, export_info=None):
        """获取联系人电话"""
        if not quotation:
            return ""
        
        # 优先使用导出信息中的联系人电话
        if export_info and export_info.get('contact'):
            contact_info = export_info['contact']
            if contact_info and contact_info.get('phone'):
                return str(contact_info['phone']).strip()
        
        # 如果没有导出信息，返回空字符串（可以根据需要扩展）
        return ""
    
    def _get_user_company_logo(self, user):
        """获取用户所属企业的Logo"""
        if not user or not user.company_name:
            # 如果用户没有企业归属，使用默认EVERTAC logo
            return LogoService.get_company_logo('evertac_logo')
        
        try:
            from app.models.dictionary import Dictionary
            
            # 查找用户所属企业的字典记录
            company_dict = Dictionary.query.filter_by(
                type='company',
                value=user.company_name,
                is_active=True
            ).first()
            
            if company_dict and company_dict.logo_content:
                # 如果找到企业字典记录且有logo，返回logo的data URL
                return company_dict.logo_data_url
            else:
                # 如果没有找到或没有logo，使用默认EVERTAC logo
                logger.info(f"⚠️ 用户 {user.username} 的企业 {user.company_name} 没有设置Logo，使用默认Logo")
                return LogoService.get_company_logo('evertac_logo')
                
        except Exception as e:
            logger.error(f"❌ 获取用户企业Logo失败: {e}")
            # 出错时使用默认logo
            return LogoService.get_company_logo('evertac_logo')
    
    def _get_user_company_info(self, user):
        """获取用户所属企业的信息"""
        # 默认企业信息（EVERTAC）
        default_info = {
            'name': 'EVERTAC SOLUTIONS',
            'contact_person': user.real_name if user else 'Sales Team',
            'address': '武威路88号19楼6楼, 普陀区 上海市, 中国 (200335)',
            'phone': '021-62596028',
            'email': 'info@evertac.net',
            'website': 'www.evertac.net'
        }
        
        if not user or not user.company_name:
            return default_info
        
        try:
            from app.models.dictionary import Dictionary
            
            # 查找用户所属企业的字典记录
            company_dict = Dictionary.query.filter_by(
                type='company',
                value=user.company_name,
                is_active=True
            ).first()
            
            if company_dict:
                # 如果找到企业字典记录，使用字典中的企业信息
                company_info = {
                    'name': company_dict.value,  # 企业名称
                    'contact_person': user.real_name if user else 'Sales Team',
                    'address': company_dict.address or default_info['address'],
                    'phone': company_dict.phone or default_info['phone'],
                    'email': company_dict.email or default_info['email'],
                    'website': company_dict.website or default_info['website']
                }
                
                logger.info(f"✅ 使用企业字典中的企业信息: {user.company_name}")
                return company_info
            else:
                # 如果没有找到企业字典记录，使用默认信息但更新企业名称
                logger.info(f"⚠️ 用户 {user.username} 的企业 {user.company_name} 在字典中未找到，使用默认信息")
                default_info['name'] = user.company_name
                return default_info
                
        except Exception as e:
            logger.error(f"❌ 获取用户企业信息失败: {e}")
            # 出错时使用默认信息
            return default_info
    
    def _render_evertac_template(self, template_data, logo_base64):
        """渲染EVERTAC模板"""
        
        # 获取系统字体配置
        font_family = self._get_system_font_family()
        font_face_css = self._get_font_face_css()
        
        # 按照要求设计的报价单HTML模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>报价单 - {{ quotation.quotation_number }}</title>
    <style>
        """ + font_face_css + """
        
        @page {
            size: A4;
            margin: 1.5cm 1cm;
        }
        
        body {
            font-family: """ + font_family + """;
            font-size: 9pt;  /* 减少2号：从11pt减少到9pt */
            line-height: 1.3;
            margin: 0;
            padding: 0;
            color: #000;
        }
        
        .quotation-container {
            width: 100%;
            margin: 0 auto;
        }
        
        /* 表格样式 */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 0;  /* 移除默认的表格间距 */
        }
        
        .border-table {
            border: 1px solid #000;
        }
        
        .border-table td, .border-table th {
            border: 1px solid #000;
            padding: 6pt;
            vertical-align: top;
        }
        
        /* 确保所有表格边框粗细一致 */
        .header-table, .info-table, .product-table {
            border: 1px solid #000;
        }
        
        .header-table td, .info-table td, .product-table td, .product-table th {
            border: 1px solid #000;
        }
        
        /* 头部表格 - Logo和公司信息 */
        .header-table td {
            vertical-align: top;
            padding: 8pt;
        }
        
        .logo-cell {
            width: 32%;  /* 缩小20%：从40%减少到32% */
            text-align: center;
        }
        
        .logo-cell img {
            max-width: 134px;  /* 再缩小20%：从168px到134px (168 * 0.8 = 134.4) */
            max-height: 54px;   /* 再缩小20%：从67px到54px (67 * 0.8 = 53.6) */
            width: 134px !important;      /* 强制设置宽度 */
            height: auto !important;      /* 保持比例 */
        }
        
        .company-info-cell {
            width: 68%;  /* 相应增加到68% */
            vertical-align: middle;  /* 改为中间对齐 */
            text-align: center;  /* 公司名称居中 */
        }
        
        /* Logo右侧两行比例控制 */
        .company-name-row {
            height: 2em;  /* 2/3高度 */
            vertical-align: middle;
        }
        
        .company-details-row {
            height: 1em;  /* 1/3高度 */
            vertical-align: middle;
        }
        
        .company-name {
            font-size: 14pt;
            font-weight: bold;
            margin: 0;  /* 移除边距，减少预留空间 */
            padding: 2pt 0;  /* 少量内边距保持合理空间 */
        }
        
        .company-details {
            font-size: 6pt;  /* 从5pt增加到6pt */
            line-height: 1.2;
            text-align: left;  /* 地址等信息左对齐 */
            margin: 0;  /* 移除边距，减少预留空间 */
            padding: 1pt 0;  /* 少量内边距保持合理空间 */
        }
        
        /* 报价单标题 */
        .title-row {
            text-align: center;
            font-size: 14pt;  /* 与公司名称一样大 */
            font-weight: bold;
            padding: 6pt;  /* 减少上下间距 */
        }
        
        /* 信息表格 */
        .info-table td {
            padding: 6pt;
            font-size: 8pt;  /* 减少2号：从10pt减少到8pt */
        }
        
        .label-col {
            font-weight: bold;
            background-color: #f0f0f0;
        }
        
        /* 列宽比例 - 确保信息表格和产品表格列对齐 */
        .col-20 { width: 20%; }
        .col-40 { width: 40%; }
        .col-2 { width: 2%; }
        .col-4 { width: 4%; }
        .col-6 { width: 6%; }
        .col-8 { width: 8%; }
        .col-10 { width: 10%; }
        .col-12 { width: 12%; }
        .col-15 { width: 15%; }
        .col-18 { width: 18%; }
        .col-25 { width: 25%; }
        
        /* 信息表格列宽：精确对齐产品表格分割线 */
        .info-table .col-info-1 { width: 20%; }    /* 对应左侧标签列 */
        .info-table .col-info-2 { width: 40%; }    /* 对应主要内容列 */
        .info-table .col-info-3 { width: 20%; }    /* 对应右侧标签列 */
        .info-table .col-info-4 { width: 20%; }    /* 对应右侧内容列 */
        
        /* 产品表格 */
        .product-table th {
            background-color: #f0f0f0;
            font-weight: bold;
            text-align: center;
            padding: 6pt 4pt;
            font-size: 8pt;  /* 减少2号：从10pt减少到8pt */
        }
        
        .product-table td {
            padding: 4pt;
            font-size: 8pt;  /* 减少2号：从10pt减少到8pt */
            vertical-align: top;
        }
        
        /* 金额字段样式 - 参考列表模板 */
        .amount-cell {
            font-size: 7pt;  /* 比普通字体小1号 */
            font-weight: 500;
            text-align: right;
        }
        
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .text-left { text-align: left; }
        
        /* 总计行 */
        .total-row {
            font-weight: bold;
            background-color: #f0f0f0;
        }
        
        /* 备注区域 */
        .notes-section {
            margin-top: 15pt;
            margin-bottom: 15pt;
        }
        
        .notes-content {
            font-size: 8pt;  /* 减少2号：从10pt减少到8pt */
            line-height: 1.4;
        }
        
        /* 签字区域 */
        .signature-section {
            margin-top: 20pt;
        }
        
        .signature-row {
            text-align: right;
            font-weight: bold;
            margin-bottom: 40pt;
            font-size: 8pt;  /* 减少2号 */
        }
        
        .signature-table {
            width: 100%;
        }
        
        .signature-table td {
            text-align: center;
            padding: 8pt;
            border: none;
        }
        
        .signature-line {
            border-bottom: 1px solid #000;
            height: 30pt;
            margin-bottom: 5pt;
        }
        
        .signature-label {
            font-size: 8pt;  /* 减少2号：从10pt减少到8pt */
        }
    </style>
</head>
<body>
    <div class="quotation-container">
        <!-- 头部：Logo和公司信息表格 -->
        <table class="border-table header-table">
            <tr>
                <!-- Logo区域 (32%) -->
                <td rowspan="2" class="logo-cell">
                    {% if logo_base64 %}
                        <img src="{{ logo_base64 }}" alt="{{ quotation.company_info.name }}">
                    {% else %}
                        <div style="font-size: 14pt; font-weight: bold;">{{ quotation.company_info.name }}</div>
                    {% endif %}
                </td>
                <!-- 公司名称 (68%) - 2/3高度 -->
                <td class="company-info-cell company-name-row">
                    <div class="company-name">{{ quotation.company_info.name }}</div>
                </td>
            </tr>
            <tr>
                <!-- 公司地址和联系方式 - 1/3高度 -->
                <td class="company-info-cell company-details-row">
                    <div class="company-details">
                        {% if quotation.company_info.address %}
                        <div>{{ quotation.i18n.address_label }}：{{ quotation.company_info.address }}</div>
                        {% endif %}
                        {% if quotation.company_info.phone %}
                        <div>{{ quotation.i18n.phone_label }}：{{ quotation.company_info.phone }}</div>
                        {% endif %}
                        {% if quotation.company_info.website %}
                        <div>{{ quotation.i18n.website_label }}：{{ quotation.company_info.website }}</div>
                        {% endif %}
                    </div>
                </td>
            </tr>
        </table>
        
        <!-- 报价单标题 -->
        <table class="border-table">
            <tr>
                <td class="title-row">{{ quotation.i18n.quotation_title }}</td>
            </tr>
        </table>
        
        <!-- 基本信息表格 -->
        <table class="border-table info-table">
            <!-- 第一行: 公司名称 | 客户 | 编号 | 编号字段 (2/4/2/2) -->
            <tr>
                <td class="label-col col-info-1">{{ quotation.i18n.company_label }}</td>
                <td class="col-info-2">{{ quotation.project.company.company_name }}</td>
                <td class="label-col col-info-3">{{ quotation.i18n.number_label }}</td>
                <td class="col-info-4">{{ quotation.quotation_number }}</td>
            </tr>
            <!-- 第二行: 公司地址 | 客户地址 | 日期 | 当天日期 -->
            <tr>
                <td class="label-col col-info-1">{{ quotation.i18n.address_info_label }}</td>
                <td class="col-info-2">{{ quotation.project.location }}</td>
                <td class="label-col col-info-3">{{ quotation.i18n.date_label }}</td>
                <td class="col-info-4">{{ quotation.created_at }}</td>
            </tr>
            <!-- 第三行: 联系人 | 客户联系人 | 报价负责人 | 负责人姓名 -->
            <tr>
                <td class="label-col col-info-1">{{ quotation.i18n.contact_label }}</td>
                <td class="col-info-2">{{ quotation.project.company.contact_person }}</td>
                <td class="label-col col-info-3">{{ quotation.i18n.responsible_label }}</td>
                <td class="col-info-4">{{ quotation.owner.real_name or quotation.owner.username }}</td>
            </tr>
            <!-- 第四行: 联系方式 | 联系人电话 | 货币 | 报价单货币 -->
            <tr>
                <td class="label-col col-info-1">{{ quotation.i18n.contact_info_label }}</td>
                <td class="col-info-2">{% if quotation.project.company.contact_phone %}{{ quotation.project.company.contact_phone }}{% endif %}</td>
                <td class="label-col col-info-3">{{ quotation.i18n.currency_label }}</td>
                <td class="col-info-4">{{ quotation.currency_display }}</td>
            </tr>
        </table>
        
        <!-- 产品明细表 -->
        <table class="border-table product-table">
            <thead>
                <tr>
                    <th class="col-6">{{ quotation.i18n.item_label }}</th>
                    <th class="col-15">产品名称</th>
                    <th class="col-12">产品型号</th>
                    <th class="col-18">{{ quotation.i18n.description_label }}</th>
                    <th class="col-8">品牌</th>
                    <th class="col-6">{{ quotation.i18n.qty_label }}</th>
                    <th class="col-10">{{ quotation.i18n.unit_price_label }}</th>
                    <th class="col-10">{{ quotation.i18n.total_price_label }}</th>
                    <th class="col-15">MN</th>
                </tr>
            </thead>
            <tbody>
                {% for detail in quotation.details %}
                <tr>
                    <td class="text-center">{{ detail.item_number }}</td>
                    <td>{{ detail.product_name or '-' }}</td>
                    <td>{{ detail.specifications or detail.product_model or '-' }}</td>
                    <td>{{ detail.product_description or '-' }}</td>
                    <td>{{ detail.brand or '-' }}</td>
                    <td class="text-center">{{ detail.quantity or 1 }}</td>
                    <td class="amount-cell">{{ detail.unit_price_formatted }}</td>
                    <td class="amount-cell">{{ detail.total_price_formatted }}</td>
                    <td>{{ detail.product_mn or '-' }}</td>
                </tr>
                {% endfor %}
                
                <!-- 总计行 (比例6/4) -->
                <tr class="total-row">
                    <td colspan="6" class="text-right">{{ quotation.i18n.total_label }}</td>
                    <td colspan="3" class="amount-cell">{{ quotation.total_amount_formatted }}</td>
                </tr>
            </tbody>
        </table>
        
        <!-- 空行 -->
        <div style="height: 15pt;"></div>
        
        <!-- 备注区域 -->
        <div class="notes-section">
            <div style="font-weight: bold; margin-bottom: 8pt;">{{ quotation.i18n.notes_title }}:</div>
            <div class="notes-content">
                {% if quotation.notes.custom_content %}
                    {% for line in quotation.notes.custom_content.split('\n') %}
                        {% if line.strip() %}
                            {{ line.strip() }}<br>
                        {% endif %}
                    {% endfor %}
                {% else %}
                    交付条款: {{ quotation.notes.delivery_note }}<br>
                    交付时间: {{ quotation.notes.delivery_time }}<br>
                    质保条款: {{ quotation.notes.warranty }}<br>
                    付款条款: {{ quotation.notes.payment_terms_detail }}<br>
                    其他说明: {{ quotation.notes.additional_info }}
                {% endif %}
            </div>
        </div>
        
        <!-- 空5行 -->
        <div style="height: 50pt;"></div>
        
        <!-- 签字确认 -->
        <div class="signature-section">
            <div class="signature-row">{{ quotation.i18n.signature_title }}</div>
            
            <!-- 空3行 -->
            <div style="height: 30pt;"></div>
            
            <!-- 签字表格 -->
            <table class="signature-table">
                <tr>
                    <td style="width: 33.33%;">
                        <div class="signature-line"></div>
                        <div class="signature-label">{{ quotation.company_info.name }}</div>
                    </td>
                    <td style="width: 33.33%;">&nbsp;</td>
                    <td style="width: 33.33%;">
                        <div class="signature-line"></div>
                        <div class="signature-label">{{ quotation.project.company.company_name }}</div>
                    </td>
                </tr>
            </table>
        </div>
    </div>
</body>
</html>
        """
        
        # 使用Jinja2渲染模板
        try:
            rendered_html = render_template_string(
                html_template, 
                quotation=template_data['quotation'],
                logo_base64=logo_base64
            )
            return rendered_html
        except Exception as e:
            logger.error(f"❌ 模板渲染失败: {e}")
            raise

# 便捷函数
def generate_evertac_quotation_pdf(quotation):
    """生成EVERTAC报价单PDF的便捷函数"""
    generator = EvertacQuotationPDFGenerator()
    result = generator.generate_quotation_pdf(quotation)
    return result['content']