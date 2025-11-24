#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研发产品PDF生成器
继承PDFGenerator，自动获得中文字体支持
"""

import os
import base64
import logging
import requests
import re
from datetime import datetime
from flask import render_template, current_app
from app.services.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


class RDProductPDFGenerator(PDFGenerator):
    """研发产品PDF生成器"""

    def generate_rd_product_pdf(self, dev_product):
        """
        生成研发产品PDF

        Args:
            dev_product: DevProduct对象

        Returns:
            dict: {'content': PDF字节内容, 'filename': 文件名}
        """
        try:
            # 1. 准备模板数据
            template_data = self._prepare_template_data(dev_product)

            # 2. 获取Logo（复用父类方法）
            logo_base64 = self._get_company_logo('evertac_logo')

            # 3. 获取字体配置（复用父类方法）
            font_family = self._get_system_font_family()
            font_face_css = self._get_font_face_css()

            # 4. 渲染HTML模板
            html_content = render_template(
                'pdf/rd_product_template.html',
                product=template_data,
                logo_base64=logo_base64,
                font_family=font_family,
                font_face_css=font_face_css,
                generated_at=datetime.now()
            )

            # 5. 生成文件名
            safe_name = self._sanitize_filename(dev_product.model or dev_product.name)
            filename = f"{safe_name} - 产品详情.pdf"

            # 6. 生成PDF（复用父类方法）
            pdf_content = self._generate_pdf_from_html(html_content, filename)

            logger.info(f"成功生成研发产品PDF: {dev_product.name}")

            return {
                'content': pdf_content,
                'filename': filename
            }

        except Exception as e:
            logger.error(f"生成研发产品PDF失败: {str(e)}", exc_info=True)
            raise

    def _prepare_template_data(self, dev_product):
        """准备模板数据"""
        # 处理产品图片
        image_base64 = self._process_product_image(dev_product)

        # 格式化规格数据
        specs = self._format_specs(dev_product)

        return {
            'name': dev_product.name or '未命名产品',
            'model': dev_product.model or '暂无',
            'mn_code': dev_product.mn_code,
            'category': dev_product.category.name if dev_product.category else '暂无',
            'subcategory': dev_product.subcategory.name if dev_product.subcategory else '暂无',
            'region': dev_product.region.name if dev_product.region else '暂无',
            'status': dev_product.current_stage_name if hasattr(dev_product, 'current_stage_name') else (dev_product.status or '暂无'),
            'retail_price': f"{dev_product.retail_price:.2f}" if dev_product.retail_price else '暂无',
            'currency': dev_product.currency or 'CNY',
            'unit': dev_product.unit or '暂无',
            'description': dev_product.description,
            'creator_name': dev_product.creator.username if dev_product.creator else '未知',
            'created_at': dev_product.created_at.strftime('%Y-%m-%d %H:%M') if dev_product.created_at else '未知',
            'image_base64': image_base64,
            'specs': specs
        }

    def _process_product_image(self, dev_product):
        """处理产品图片转Base64"""
        if not dev_product.image_path:
            return None

        try:
            if dev_product.image_path.startswith('http'):
                # Supabase云端图片
                response = requests.get(dev_product.image_path, timeout=10)
                image_data = response.content
            else:
                # 本地图片
                file_path = os.path.join(current_app.static_folder, dev_product.image_path)
                with open(file_path, 'rb') as f:
                    image_data = f.read()

            # 转Base64
            base64_str = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_str}"

        except Exception as e:
            logger.warning(f"处理产品图片失败: {str(e)}")
            return None

    def _format_specs(self, dev_product):
        """格式化规格参数"""
        specs = []
        for spec in dev_product.specs:
            if spec.field_value and spec.field_value.strip():
                specs.append({
                    'field_name': spec.field_name,
                    'field_value': spec.field_value
                })
        return specs

    def _sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        # 移除非法字符，保留中文、英文、数字、短横线、下划线
        safe_name = re.sub(r'[^\w\s\-]', '', filename)
        # 替换空格为下划线
        safe_name = safe_name.replace(' ', '_')
        return safe_name[:50]  # 限制长度


# 便捷函数（供路由直接调用）
def generate_rd_product_pdf(dev_product):
    """生成研发产品PDF的便捷函数"""
    generator = RDProductPDFGenerator()
    return generator.generate_rd_product_pdf(dev_product)
