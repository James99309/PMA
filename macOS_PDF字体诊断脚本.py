#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS PDF字体诊断脚本
用于检测和诊断PDF生成中的字体问题
"""

import os
import platform
import logging
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def check_system_fonts():
    """检查系统字体"""
    print("=" * 60)
    print("系统字体检查")
    print("=" * 60)
    
    system = platform.system()
    print(f"操作系统: {system}")
    
    if system == "Darwin":  # macOS
        font_paths = [
            # 宋体系列
            '/System/Library/Fonts/Supplemental/Songti.ttc',
            # 黑体系列
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            # 苹方系列
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/PingFang SC.ttc',
            # 英文字体
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/Times.ttc',
            '/System/Library/Fonts/Arial.ttf',
        ]
        
        print("\nmacOS字体检查:")
        available_fonts = []
        for font_path in font_paths:
            if os.path.exists(font_path):
                print(f"✅ {font_path}")
                available_fonts.append(font_path)
            else:
                print(f"❌ {font_path}")
        
        print(f"\n共找到 {len(available_fonts)} 个可用字体")
        
        # 检查字体目录
        font_dirs = [
            '/System/Library/Fonts/',
            '/System/Library/Fonts/Supplemental/',
            '/Library/Fonts/',
            '~/Library/Fonts/'
        ]
        
        print("\n字体目录检查:")
        for font_dir in font_dirs:
            expanded_dir = os.path.expanduser(font_dir)
            if os.path.exists(expanded_dir):
                try:
                    font_files = [f for f in os.listdir(expanded_dir) 
                                if f.lower().endswith(('.ttf', '.ttc', '.otf'))]
                    chinese_fonts = [f for f in font_files 
                                   if any(keyword in f.lower() for keyword in 
                                        ['songti', 'heiti', 'pingfang', 'stfang', 'stsong'])]
                    print(f"✅ {font_dir}: {len(font_files)} 个字体文件")
                    if chinese_fonts:
                        print(f"   中文字体: {chinese_fonts[:5]}")  # 只显示前5个
                except Exception as e:
                    print(f"❌ {font_dir}: 无法读取 - {e}")
            else:
                print(f"❌ {font_dir}: 目录不存在")
    
    elif system == "Windows":
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/arial.ttf',
        ]
        
        print("\nWindows字体检查:")
        available_fonts = []
        for font_path in font_paths:
            if os.path.exists(font_path):
                print(f"✅ {font_path}")
                available_fonts.append(font_path)
            else:
                print(f"❌ {font_path}")
        
        print(f"\n共找到 {len(available_fonts)} 个可用字体")
    
    return available_fonts

def test_weasyprint_fonts():
    """测试WeasyPrint字体配置"""
    print("\n" + "=" * 60)
    print("WeasyPrint字体配置测试")
    print("=" * 60)
    
    try:
        # 创建FontConfiguration
        font_config = FontConfiguration()
        
        # 添加系统字体
        system = platform.system()
        if system == "Darwin":
            font_paths = [
                '/System/Library/Fonts/Supplemental/Songti.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
            ]
        elif system == "Windows":
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc',
                'C:/Windows/Fonts/simhei.ttf',
            ]
        else:
            font_paths = []
        
        added_fonts = []
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_config.add_font_face(font_path)
                    added_fonts.append(font_path)
                    print(f"✅ 成功添加字体: {font_path}")
                except Exception as e:
                    print(f"❌ 添加字体失败 {font_path}: {e}")
        
        print(f"\n成功添加 {len(added_fonts)} 个字体到WeasyPrint配置")
        
        return font_config
        
    except Exception as e:
        print(f"❌ WeasyPrint字体配置失败: {e}")
        return None

def test_pdf_generation():
    """测试PDF生成"""
    print("\n" + "=" * 60)
    print("PDF生成测试")
    print("=" * 60)
    
    # 创建测试HTML
    system = platform.system()
    if system == "Darwin":
        font_family = '"Songti TC", "Songti SC", "STSong", "STHeiti Light", "STHeiti", "Helvetica", "Arial", sans-serif'
    elif system == "Windows":
        font_family = '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体", "Arial", sans-serif'
    else:
        font_family = '"Noto Sans CJK SC", "DejaVu Sans", "Liberation Sans", "Arial", sans-serif'
    
    test_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>字体测试</title>
        <style>
            body {{
                font-family: {font_family};
                font-size: 14px;
                line-height: 1.6;
                margin: 20px;
            }}
            .test-section {{
                margin-bottom: 20px;
                padding: 10px;
                border: 1px solid #ccc;
            }}
        </style>
    </head>
    <body>
        <div class="test-section">
            <h1>中文字体测试</h1>
            <p>这是一段中文测试文本，包含常用汉字：你好世界！</p>
            <p>数字测试：1234567890</p>
            <p>英文测试：Hello World! ABCDEFGHIJKLMNOPQRSTUVWXYZ</p>
        </div>
        
        <div class="test-section">
            <h2>特殊字符测试</h2>
            <p>符号：！@#￥%……&*（）——+</p>
            <p>标点：，。？；：""''【】《》</p>
        </div>
        
        <div class="test-section">
            <h2>表格测试</h2>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th>产品名称</th>
                    <th>数量</th>
                    <th>单价</th>
                    <th>总价</th>
                </tr>
                <tr>
                    <td>测试产品A</td>
                    <td>10</td>
                    <td>100.00</td>
                    <td>1,000.00</td>
                </tr>
                <tr>
                    <td>测试产品B</td>
                    <td>5</td>
                    <td>200.00</td>
                    <td>1,000.00</td>
                </tr>
            </table>
        </div>
        
        <div class="test-section">
            <h2>系统信息</h2>
            <p>操作系统: {system}</p>
            <p>字体配置: {font_family}</p>
        </div>
    </body>
    </html>
    """
    
    try:
        # 配置字体
        font_config = test_weasyprint_fonts()
        
        # 生成PDF
        html_doc = HTML(string=test_html)
        
        # 生成PDF内容
        if font_config:
            pdf_content = html_doc.write_pdf(font_config=font_config)
            print("✅ 使用自定义字体配置生成PDF成功")
        else:
            pdf_content = html_doc.write_pdf()
            print("✅ 使用默认字体配置生成PDF成功")
        
        # 保存测试PDF
        test_pdf_path = f"字体测试_{system}.pdf"
        with open(test_pdf_path, 'wb') as f:
            f.write(pdf_content)
        
        print(f"✅ 测试PDF已保存: {test_pdf_path}")
        print(f"   文件大小: {len(pdf_content)} 字节")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("macOS PDF字体诊断脚本")
    print("=" * 60)
    
    # 检查系统字体
    available_fonts = check_system_fonts()
    
    # 测试WeasyPrint
    font_config = test_weasyprint_fonts()
    
    # 测试PDF生成
    pdf_success = test_pdf_generation()
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    print(f"系统字体: 找到 {len(available_fonts)} 个可用字体")
    print(f"WeasyPrint配置: {'成功' if font_config else '失败'}")
    print(f"PDF生成测试: {'成功' if pdf_success else '失败'}")
    
    if pdf_success:
        print("\n✅ 字体配置正常，请检查生成的测试PDF文件")
    else:
        print("\n❌ 存在字体问题，需要进一步排查")
    
    print("\n建议:")
    print("1. 检查生成的测试PDF文件中的中文显示是否正常")
    print("2. 如果仍有乱码，可能需要安装额外的中文字体")
    print("3. 确保WeasyPrint版本与系统兼容")

if __name__ == "__main__":
    main() 