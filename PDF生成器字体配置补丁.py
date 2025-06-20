#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF生成器字体配置补丁
用于修复线上环境缺少中文字体的问题
"""

import os
import platform
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class PDFGeneratorFontPatch:
    """PDF生成器字体配置补丁"""
    
    @staticmethod
    def configure_project_fonts(font_config):
        """配置项目内的字体文件"""
        try:
            # 项目字体目录
            if current_app:
                font_dir = os.path.join(current_app.static_folder, 'fonts')
            else:
                # 备用路径
                font_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts')
                font_dir = os.path.abspath(font_dir)
            
            if not os.path.exists(font_dir):
                logger.warning(f"项目字体目录不存在: {font_dir}")
                return False
            
            # 项目字体文件列表
            project_fonts = [
                'NotoSansCJK-Regular.ttc',
                'wqy-microhei.ttc',
                'wqy-zenhei.ttc',
                'NotoSansCJK-Bold.ttc',
                'NotoSansCJK-Light.ttc'
            ]
            
            font_added = False
            
            # 添加项目字体文件
            for font_file in project_fonts:
                font_path = os.path.join(font_dir, font_file)
                if os.path.exists(font_path):
                    try:
                        font_config.add_font_file(font_path)
                        logger.info(f"✅ 添加项目字体: {font_path}")
                        font_added = True
                    except Exception as e:
                        logger.warning(f"添加字体失败 {font_path}: {e}")
                else:
                    logger.debug(f"字体文件不存在: {font_path}")
            
            return font_added
            
        except Exception as e:
            logger.error(f"配置项目字体失败: {e}")
            return False
    
    @staticmethod
    def get_enhanced_font_family():
        """获取增强的字体族配置（包含项目字体）"""
        system = platform.system()
        
        # 基础字体配置
        if system == "Darwin":  # macOS
            base_fonts = '"Songti TC", "Songti SC", "STSong", "STHeiti Light", "STHeiti"'
        elif system == "Windows":  # Windows
            base_fonts = '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体"'
        else:  # Linux
            base_fonts = '"Noto Sans CJK SC", "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "AR PL UKai CN", "AR PL UMing CN"'
        
        # 通用回退字体
        fallback_fonts = '"DejaVu Sans", "Liberation Sans", "Helvetica", "Arial", sans-serif'
        
        return f'{base_fonts}, {fallback_fonts}'

# 补丁函数：修改现有PDF生成器
def patch_pdf_generator():
    """
    应用字体配置补丁到现有的PDF生成器
    使用方法：在 app/services/pdf_generator.py 的 __init__ 方法中调用
    """
    
    def enhanced_configure_fonts(self):
        """增强的字体配置方法"""
        try:
            # 保留原有的系统字体配置
            original_configure = self._configure_fonts_original if hasattr(self, '_configure_fonts_original') else None
            if original_configure:
                original_configure()
            
            # 添加项目字体配置
            font_added = PDFGeneratorFontPatch.configure_project_fonts(self.font_config)
            
            if font_added:
                logger.info("✅ 项目字体配置成功")
            else:
                logger.warning("⚠️  未找到项目字体文件")
                
        except Exception as e:
            logger.error(f"增强字体配置失败: {e}")
    
    def enhanced_get_system_font_family(self):
        """增强的系统字体族获取方法"""
        return PDFGeneratorFontPatch.get_enhanced_font_family()
    
    # 返回补丁方法
    return enhanced_configure_fonts, enhanced_get_system_font_family

# 完整的PDF生成器配置示例
SAMPLE_PDF_GENERATOR_PATCH = '''
# 在 app/services/pdf_generator.py 的 PDFGenerator 类中应用此补丁

class PDFGenerator:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'pdf')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
        # 配置字体
        self.font_config = FontConfiguration()
        
        # 【补丁】添加项目字体配置
        self._configure_fonts_enhanced()
        
    def _configure_fonts_enhanced(self):
        """增强的字体配置（包含项目字体）"""
        try:
            # 保留原有系统字体配置
            self._configure_fonts_original()
            
            # 添加项目字体
            from PDF生成器字体配置补丁 import PDFGeneratorFontPatch
            PDFGeneratorFontPatch.configure_project_fonts(self.font_config)
            
        except Exception as e:
            logger.error(f"增强字体配置失败: {e}")
    
    def _configure_fonts_original(self):
        """原始的字体配置方法（重命名）"""
        # ... 保留原有的 _configure_fonts 方法内容 ...
        
    def _get_system_font_family(self):
        """获取系统字体族（使用增强配置）"""
        from PDF生成器字体配置补丁 import PDFGeneratorFontPatch
        return PDFGeneratorFontPatch.get_enhanced_font_family()
'''

if __name__ == '__main__':
    print("PDF生成器字体配置补丁")
    print("====================")
    print()
    print("使用方法：")
    print("1. 将此文件放置到项目根目录")
    print("2. 在 app/services/pdf_generator.py 中导入并使用")
    print("3. 确保 app/static/fonts/ 目录中有字体文件")
    print()
    print("示例代码：")
    print(SAMPLE_PDF_GENERATOR_PATCH) 