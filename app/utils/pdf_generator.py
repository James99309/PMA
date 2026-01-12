"""
订单PDF生成器
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging
from config import Config

logger = logging.getLogger(__name__)

def generate_order_pdf(order):
    """
    生成订单PDF
    
    Args:
        order: PurchaseOrder对象
        
    Returns:
        BytesIO: PDF文件流
    """
    try:
        buffer = io.BytesIO()
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        # 注册中文字体
        chinese_font_name = 'Helvetica'  # 默认字体
        try:
            import os
            # 按优先级排序的字体路径（兼容reportlab的字体）
            font_paths_to_try = [
                # macOS系统字体（兼容性最好）
                '/System/Library/Fonts/STHeiti Medium.ttc',
                '/System/Library/Fonts/PingFang.ttc', 
                '/System/Library/Fonts/Hiragino Sans GB.ttc',
                '/Library/Fonts/Arial Unicode MS.ttf',
                # Linux字体
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                # Windows字体
                'C:\\Windows\\Fonts\\simsun.ttc',
                'C:\\Windows\\Fonts\\msyh.ttc',
                'C:\\Windows\\Fonts\\Arial.ttf',
            ]
            
            for font_path in font_paths_to_try:
                try:
                    if os.path.exists(font_path):
                        # 尝试注册字体
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        chinese_font_name = 'ChineseFont'
                        logger.info(f"✅ 成功注册中文字体: {font_path}")
                        break
                except Exception as e:
                    logger.warning(f"字体注册失败 {font_path}: {e}")
                    continue
            else:
                # 如果所有字体都失败，使用reportlab内置字体
                try:
                    from reportlab.lib.fonts import addMapping
                    chinese_font_name = 'Helvetica'
                    logger.warning("❌ 未找到兼容的中文字体，使用默认字体（中文可能显示为方块）")
                except:
                    logger.warning("❌ 字体注册完全失败")
        except Exception as e:
            logger.warning(f"字体注册过程失败: {e}")
        
        # 定义样式
        styles = getSampleStyleSheet()
        
        # 标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=chinese_font_name,
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # 居中
            textColor=colors.black
        )
        
        # 普通文本样式
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=chinese_font_name,
            fontSize=10,
            spaceAfter=6
        )
        
        # 构建PDF内容
        story = []
        
        # 标题
        title = Paragraph("采购订单", title_style)
        story.append(title)
        story.append(Spacer(1, 10))
        
        # 获取厂商信息
        vendor_names = set()
        for detail in order.details:
            # 从订单明细的brand字段获取品牌，然后查找对应的厂商公司
            brand = detail.brand or (detail.product.brand if detail.product else '')
            if brand:
                # 根据品牌查找厂商公司全称
                from app.models.dictionary import Dictionary
                vendor_dict = Dictionary.query.filter_by(
                    type='company',
                    is_active=True,
                    is_vendor=True
                ).filter(
                    # 尝试匹配value字段中包含brand的记录
                    Dictionary.value.ilike(f'%{brand}%')
                ).first()
                
                if vendor_dict:
                    vendor_names.add(vendor_dict.value)
                else:
                    # 如果没有找到厂商字典，也可以尝试通过key匹配
                    vendor_dict_by_key = Dictionary.query.filter_by(
                        type='company',
                        key=brand,
                        is_active=True,
                        is_vendor=True
                    ).first()
                    if vendor_dict_by_key:
                        vendor_names.add(vendor_dict_by_key.value)
                    else:
                        # 最后直接使用品牌名
                        vendor_names.add(brand)
        
        # 厂商信息行
        if vendor_names:
            vendor_text = "厂商：" + "、".join(vendor_names)
            vendor_style = ParagraphStyle(
                'VendorStyle',
                parent=styles['Normal'],
                fontName=chinese_font_name,
                fontSize=12,  # 比标题小几号
                alignment=1,  # 居中
                textColor=colors.black,
                spaceAfter=15
            )
            vendor_para = Paragraph(vendor_text, vendor_style)
            story.append(vendor_para)
        
        story.append(Spacer(1, 10))
        
        # 订单基本信息
        order_info_data = [
            ['订单编号:', order.order_number or ''],
            ['采购商:', order.company.company_name if order.company else ''],
            ['版本号:', order.revision or '-'],
            ['创建时间:', order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else ''],
            ['订单状态:', get_status_text(order.status)],
            ['创建人:', order.created_by.real_name or order.created_by.username if order.created_by else ''],
            ['订单总额:', f'{Config.CURRENCY_SYMBOL}{order.total_amount:.2f}' if order.total_amount else f'{Config.CURRENCY_SYMBOL}0.00'],
        ]

        # 贸易术语
        if order.incoterms:
            order_info_data.append(['贸易术语:', get_incoterms_text(order.incoterms)])

        # 如果有备注
        if order.description:
            order_info_data.append(['备注:', order.description])

        # 创建订单信息表格
        order_info_table = Table(order_info_data, colWidths=[2*inch, 4*inch])
        order_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), chinese_font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(order_info_table)
        story.append(Spacer(1, 15))

        # 交货信息段（如果有交货相关数据）
        has_delivery_info = order.required_date or order.confirmed_date or order.ship_to or order.shipping_method
        if has_delivery_info:
            delivery_title = Paragraph("交货信息", ParagraphStyle(
                'DeliveryTitle',
                parent=styles['Heading2'],
                fontName=chinese_font_name,
                fontSize=12,
                spaceAfter=8
            ))
            story.append(delivery_title)

            delivery_data = []
            if order.required_date:
                delivery_data.append(['需求日期:', order.required_date.strftime('%Y-%m-%d')])
            if order.confirmed_date:
                delivery_data.append(['确认交期:', order.confirmed_date.strftime('%Y-%m-%d')])
            if order.shipping_method:
                delivery_data.append(['运输方式:', get_shipping_method_text(order.shipping_method)])
            if order.freight_terms:
                delivery_data.append(['运费承担:', get_freight_terms_text(order.freight_terms)])
            if order.ship_to:
                delivery_data.append(['交货地点:', order.ship_to])

            if delivery_data:
                delivery_table = Table(delivery_data, colWidths=[2*inch, 4*inch])
                delivery_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(delivery_table)
            story.append(Spacer(1, 15))

        # 生产与测试状态（仅在确认后显示）
        if order.status in ['confirmed', 'producing', 'tested', 'shipped', 'stored', 'completed']:
            progress_title = Paragraph("生产与测试状态", ParagraphStyle(
                'ProgressTitle',
                parent=styles['Heading2'],
                fontName=chinese_font_name,
                fontSize=12,
                spaceAfter=8
            ))
            story.append(progress_title)

            progress_data = [
                ['生产状态:', get_production_status_text(order.production_status)],
                ['生产进度:', f'{order.production_progress or 0}%'],
                ['工厂测试:', get_test_status_text(order.factory_test_status)],
            ]
            if order.verification_test_type:
                test_type_text = '现场FAT' if order.verification_test_type == 'site_fat' else '到货测试'
                progress_data.append(['验证测试:', f'{test_type_text} - {get_test_status_text(order.verification_test_status)}'])
            if order.estimated_completion_date:
                progress_data.append(['预计完成:', order.estimated_completion_date.strftime('%Y-%m-%d')])
            if order.production_notes:
                progress_data.append(['生产备注:', order.production_notes])

            progress_table = Table(progress_data, colWidths=[2*inch, 4*inch])
            progress_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(progress_table)
            story.append(Spacer(1, 15))

        # 物流信息（如果已发货）
        if order.status in ['shipped', 'stored', 'completed'] and (order.carrier or order.tracking_number or order.ship_date):
            logistics_title = Paragraph("物流信息", ParagraphStyle(
                'LogisticsTitle',
                parent=styles['Heading2'],
                fontName=chinese_font_name,
                fontSize=12,
                spaceAfter=8
            ))
            story.append(logistics_title)

            logistics_data = []
            if order.carrier:
                logistics_data.append(['承运商:', order.carrier])
            if order.tracking_number:
                logistics_data.append(['运单号:', order.tracking_number])
            if order.ship_date:
                logistics_data.append(['发货日期:', order.ship_date.strftime('%Y-%m-%d')])
            if order.arrival_date:
                logistics_data.append(['预计到达:', order.arrival_date.strftime('%Y-%m-%d')])
            if order.actual_arrival_date:
                logistics_data.append(['实际到达:', order.actual_arrival_date.strftime('%Y-%m-%d')])

            if logistics_data:
                logistics_table = Table(logistics_data, colWidths=[2*inch, 4*inch])
                logistics_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font_name),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(logistics_table)
            story.append(Spacer(1, 15))

        story.append(Spacer(1, 5))
        
        # 订单明细标题
        details_title_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontName=chinese_font_name,
            fontSize=14
        )
        details_title = Paragraph("订单明细", details_title_style)
        story.append(details_title)
        story.append(Spacer(1, 10))
        
        # 订单明细表格
        if order.details:
            # 表头
            details_data = [
                ['序号', '产品名称', '型号', '品牌', '数量', '单位', '单价', '小计']
            ]
            
            # 明细数据
            for i, detail in enumerate(order.details, 1):
                subtotal = (detail.quantity or 0) * (detail.unit_price or 0)
                details_data.append([
                    str(i),
                    detail.product_name or '',
                    detail.product_model or '',
                    detail.brand or '',
                    str(detail.quantity or 0),
                    detail.unit or '件',
                    f'{Config.CURRENCY_SYMBOL}{detail.unit_price:.2f}' if detail.unit_price else f'{Config.CURRENCY_SYMBOL}0.00',
                    f'{Config.CURRENCY_SYMBOL}{subtotal:.2f}'
                ])
            
            # 创建明细表格
            details_table = Table(details_data, colWidths=[
                0.5*inch,  # 序号
                2*inch,    # 产品名称
                1.2*inch,  # 型号
                1*inch,    # 品牌
                0.8*inch,  # 数量
                0.6*inch,  # 单位
                0.8*inch,  # 单价
                0.8*inch   # 小计
            ])
            
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # 表头背景
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # 产品名称左对齐
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                # 数值右对齐
                ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ]))
            
            story.append(details_table)
        else:
            story.append(Paragraph("暂无订单明细", normal_style))
        
        story.append(Spacer(1, 30))
        
        # 页脚信息
        footer_info = [
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "此订单由PMA业务机会管理系统生成"
        ]
        
        for info in footer_info:
            footer_para = Paragraph(info, ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontName=chinese_font_name,
                fontSize=8,
                textColor=colors.grey,
                alignment=1  # 居中
            ))
            story.append(footer_para)
        
        # 生成PDF
        doc.build(story)
        
        # 重置buffer位置
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"生成订单PDF失败: {e}")
        raise

def get_status_text(status):
    """获取状态的中文显示文本"""
    status_map = {
        'draft': '草稿',
        'pending': '审批中',
        'approved': '已审批',
        'confirmed': '已确认',
        'rejected': '已拒绝',
        'shipped': '已发货',
        'completed': '已完成',
        'cancelled': '已取消',
        'producing': '生产中',
        'tested': '已测试',
        'stored': '已入库'
    }
    return status_map.get(status, status)

def get_production_status_text(status):
    """获取生产状态的中文显示文本"""
    status_map = {
        'not_started': '未开始',
        'preparing': '备料中',
        'producing': '生产中',
        'testing': '测试中',
        'packaging': '包装中',
        'ready': '已完成'
    }
    return status_map.get(status, status or '未开始')

def get_test_status_text(status):
    """获取测试状态的中文显示文本"""
    status_map = {
        'pending': '待测试',
        'passed': '已通过',
        'failed': '未通过',
        'not_required': '无需测试'
    }
    return status_map.get(status, status or '待测试')

def get_incoterms_text(incoterm):
    """获取贸易术语的显示文本"""
    incoterms_map = {
        'DDP': 'DDP (完税后交货)',
        'FOB': 'FOB (装运港船上交货)',
        'CIF': 'CIF (成本加运费保险费)',
        'EXW': 'EXW (工厂交货)',
        'CFR': 'CFR (成本加运费)',
        'DAP': 'DAP (目的地交货)'
    }
    return incoterms_map.get(incoterm, incoterm or '-')

def get_shipping_method_text(method):
    """获取运输方式的中文显示文本"""
    method_map = {
        'truck': '陆运',
        'air': '空运',
        'express': '快递',
        'self_pickup': '自提',
        'sea': '海运'
    }
    return method_map.get(method, method or '-')

def get_freight_terms_text(terms):
    """获取运费承担方式的中文显示文本"""
    terms_map = {
        'supplier': '供应商承担',
        'buyer': '采购方承担'
    }
    return terms_map.get(terms, terms or '-')