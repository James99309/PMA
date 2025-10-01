#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体检测脚本
用于检查服务器上的字体配置，诊断PDF乱码问题
"""

import os
import platform
import sys

def check_windows_fonts():
    """检查Windows系统字体"""
    print("🖥️ Windows 字体检测")
    print("=" * 50)
    
    windows_fonts = {
        # 微软雅黑系列
        'C:/Windows/Fonts/msyh.ttc': '微软雅黑 (推荐)',
        'C:/Windows/Fonts/msyhbd.ttc': '微软雅黑粗体',
        'C:/Windows/Fonts/msyhl.ttc': '微软雅黑细体',
        
        # 等线系列 (Windows 10+)
        'C:/Windows/Fonts/DengXian.ttf': '等线',
        'C:/Windows/Fonts/DengXianBold.ttf': '等线粗体',
        'C:/Windows/Fonts/DengXianLight.ttf': '等线细体',
        
        # 传统中文字体
        'C:/Windows/Fonts/simsun.ttc': '宋体',
        'C:/Windows/Fonts/NSimSun.ttf': '新宋体',
        'C:/Windows/Fonts/simhei.ttf': '黑体',
        'C:/Windows/Fonts/simkai.ttf': '楷体',
        'C:/Windows/Fonts/simfang.ttf': '仿宋',
        
        # 英文字体
        'C:/Windows/Fonts/arial.ttf': 'Arial',
        'C:/Windows/Fonts/arialbd.ttf': 'Arial Bold',
        'C:/Windows/Fonts/times.ttf': 'Times New Roman',
        'C:/Windows/Fonts/calibri.ttf': 'Calibri',
    }
    
    available_fonts = []
    missing_fonts = []
    
    for font_path, font_name in windows_fonts.items():
        if os.path.exists(font_path):
            print(f"✅ {font_name}: {font_path}")
            available_fonts.append((font_path, font_name))
        else:
            print(f"❌ {font_name}: {font_path} (不存在)")
            missing_fonts.append((font_path, font_name))
    
    print(f"\n📊 统计结果:")
    print(f"可用字体: {len(available_fonts)} 个")
    print(f"缺失字体: {len(missing_fonts)} 个")
    
    # 检查关键字体
    critical_fonts = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simsun.ttc',
        'C:/Windows/Fonts/arial.ttf'
    ]
    
    print(f"\n🔍 关键字体检查:")
    all_critical_available = True
    for font_path in critical_fonts:
        if os.path.exists(font_path):
            print(f"✅ {font_path}")
        else:
            print(f"❌ {font_path} (关键字体缺失)")
            all_critical_available = False
    
    if all_critical_available:
        print("\n🎉 所有关键字体都可用，PDF生成应该正常")
    else:
        print("\n⚠️ 部分关键字体缺失，可能导致PDF乱码")
    
    return available_fonts, missing_fonts

def check_macos_fonts():
    """检查macOS系统字体"""
    print("🍎 macOS 字体检测")
    print("=" * 50)
    
    macos_fonts = {
        # 中文字体
        '/System/Library/Fonts/Supplemental/Songti.ttc': '宋体',
        '/System/Library/Fonts/STHeiti Light.ttc': '黑体-简 细体',
        '/System/Library/Fonts/STHeiti Medium.ttc': '黑体-简 中等',
        '/System/Library/PrivateFrameworks/FontServices.framework/Versions/A/Resources/Reserved/PingFangUI.ttc': '苹方',
        
        # 英文字体
        '/System/Library/Fonts/Helvetica.ttc': 'Helvetica',
        '/System/Library/Fonts/Times.ttc': 'Times',
        '/System/Library/Fonts/Arial.ttf': 'Arial',
    }
    
    available_fonts = []
    missing_fonts = []
    
    for font_path, font_name in macos_fonts.items():
        if os.path.exists(font_path):
            print(f"✅ {font_name}: {font_path}")
            available_fonts.append((font_path, font_name))
        else:
            print(f"❌ {font_name}: {font_path} (不存在)")
            missing_fonts.append((font_path, font_name))
    
    print(f"\n📊 统计结果:")
    print(f"可用字体: {len(available_fonts)} 个")
    print(f"缺失字体: {len(missing_fonts)} 个")
    
    return available_fonts, missing_fonts

def check_linux_fonts():
    """检查Linux系统字体"""
    print("🐧 Linux 字体检测")
    print("=" * 50)
    
    linux_fonts = {
        # Noto字体系列
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc': 'Noto Sans CJK',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc': 'Noto Sans CJK (OpenType)',
        
        # DejaVu字体系列
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf': 'DejaVu Sans',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf': 'DejaVu Sans Bold',
        
        # Liberation字体系列
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf': 'Liberation Sans',
    }
    
    available_fonts = []
    missing_fonts = []
    
    for font_path, font_name in linux_fonts.items():
        if os.path.exists(font_path):
            print(f"✅ {font_name}: {font_path}")
            available_fonts.append((font_path, font_name))
        else:
            print(f"❌ {font_name}: {font_path} (不存在)")
            missing_fonts.append((font_path, font_name))
    
    print(f"\n📊 统计结果:")
    print(f"可用字体: {len(available_fonts)} 个")
    print(f"缺失字体: {len(missing_fonts)} 个")
    
    return available_fonts, missing_fonts

def generate_font_css(available_fonts):
    """根据可用字体生成CSS字体族"""
    system = platform.system()
    
    if system == "Windows":
        if any('msyh.ttc' in font[0] for font in available_fonts):
            return '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体", "Arial", sans-serif'
        elif any('simsun.ttc' in font[0] for font in available_fonts):
            return '"SimSun", "宋体", "DengXian", "等线", "Arial", sans-serif'
        else:
            return '"Arial", sans-serif'
    
    elif system == "Darwin":
        return '"Songti SC", "STHeiti Light", "PingFang SC", "Helvetica", "Arial", sans-serif'
    
    else:  # Linux
        if any('Noto' in font[1] for font in available_fonts):
            return '"Noto Sans CJK SC", "DejaVu Sans", "Liberation Sans", "Arial", sans-serif'
        else:
            return '"DejaVu Sans", "Liberation Sans", "Arial", sans-serif'

def main():
    """主函数"""
    print("🔍 PDF字体检测工具")
    print("=" * 60)
    print(f"系统类型: {platform.system()}")
    print(f"系统版本: {platform.release()}")
    print(f"Python版本: {sys.version}")
    print("=" * 60)
    
    system = platform.system()
    
    if system == "Windows":
        available_fonts, missing_fonts = check_windows_fonts()
    elif system == "Darwin":
        available_fonts, missing_fonts = check_macos_fonts()
    elif system == "Linux":
        available_fonts, missing_fonts = check_linux_fonts()
    else:
        print(f"❌ 不支持的操作系统: {system}")
        return
    
    # 生成推荐的字体CSS
    font_css = generate_font_css(available_fonts)
    print(f"\n💡 推荐的CSS字体配置:")
    print(f"font-family: {font_css};")
    
    # 给出建议
    print(f"\n📝 建议:")
    if len(available_fonts) >= 3:
        print("✅ 字体配置良好，PDF生成应该正常工作")
    elif len(available_fonts) >= 1:
        print("⚠️ 字体配置基本可用，但建议安装更多中文字体")
    else:
        print("❌ 字体配置不足，强烈建议安装中文字体包")
    
    # Windows特殊建议
    if system == "Windows" and not any('msyh.ttc' in font[0] for font in available_fonts):
        print("💡 Windows建议: 安装微软雅黑字体以获得最佳显示效果")
    
    print(f"\n🔧 如需安装字体，请参考系统文档或联系系统管理员")

if __name__ == "__main__":
    main() 