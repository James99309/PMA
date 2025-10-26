#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断WeasyPrint PDF生成问题"""
import sys

print("=" * 80)
print("WeasyPrint 诊断")
print("=" * 80)

# 1. 检查WeasyPrint是否安装
print("\n【1. 检查WeasyPrint安装】")
try:
    import weasyprint
    print(f"✅ WeasyPrint已安装")
    print(f"   版本: {weasyprint.__version__}")
except ImportError as e:
    print(f"❌ WeasyPrint未安装: {e}")
    print("\n解决方案:")
    print("  pip install weasyprint==65.1")
    sys.exit(1)

# 2. 检查WeasyPrint依赖
print("\n【2. 检查WeasyPrint依赖】")
dependencies = {
    'cairocffi': 'Cairo图形库绑定',
    'cffi': 'C外部函数接口',
    'pydyf': 'PDF生成库',
    'pyphen': '断字库',
    'cssselect2': 'CSS选择器',
    'tinycss2': 'CSS解析器',
    'Pillow': '图片处理库'
}

missing_deps = []
for dep_name, dep_desc in dependencies.items():
    try:
        __import__(dep_name.replace('-', '_'))
        print(f"  ✅ {dep_name}: {dep_desc}")
    except ImportError:
        print(f"  ❌ {dep_name}: {dep_desc} - 未安装")
        missing_deps.append(dep_name)

if missing_deps:
    print(f"\n⚠️  缺少依赖: {', '.join(missing_deps)}")
    print("\n解决方案:")
    print(f"  pip install {' '.join(missing_deps)}")

# 3. 测试简单的HTML转PDF
print("\n【3. 测试HTML转PDF功能】")
try:
    from weasyprint import HTML, CSS

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>WeasyPrint 测试</h1>
        <p>这是一个测试PDF文档。</p>
        <p>中文测试：批价单导出功能</p>
    </body>
    </html>
    """

    # 尝试生成PDF
    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf()

    print(f"  ✅ HTML转PDF成功")
    print(f"  生成的PDF大小: {len(pdf_bytes)} 字节")

except Exception as e:
    print(f"  ❌ HTML转PDF失败: {e}")
    print(f"\n错误类型: {type(e).__name__}")
    print(f"错误详情: {str(e)}")

    # 提供常见问题的解决方案
    print("\n常见问题解决方案:")
    if 'cairo' in str(e).lower():
        print("  1. Cairo库未安装或配置错误")
        print("     macOS: brew install cairo pango gdk-pixbuf libffi")
        print("     Linux: sudo apt-get install libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0")
    elif 'font' in str(e).lower():
        print("  2. 字体问题")
        print("     确保系统有可用的字体文件")
    else:
        print("  3. 其他问题")
        print("     检查WeasyPrint文档: https://doc.courtbouillon.org/weasyprint/")

# 4. 检查系统字体
print("\n【4. 检查系统字体】")
try:
    import os
    import platform

    system = platform.system()
    print(f"  操作系统: {system}")

    # 查找常见字体目录
    if system == 'Darwin':  # macOS
        font_dirs = [
            '/System/Library/Fonts',
            '/Library/Fonts',
            os.path.expanduser('~/Library/Fonts')
        ]
    elif system == 'Linux':
        font_dirs = [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            os.path.expanduser('~/.fonts')
        ]
    else:  # Windows
        font_dirs = [
            'C:\\Windows\\Fonts'
        ]

    font_count = 0
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            fonts = [f for f in os.listdir(font_dir) if f.endswith(('.ttf', '.otf', '.ttc'))]
            font_count += len(fonts)
            print(f"  {font_dir}: {len(fonts)} 个字体")

    print(f"\n  总共找到 {font_count} 个字体文件")

except Exception as e:
    print(f"  ⚠️  检查字体时出错: {e}")

# 5. 检查项目字体
print("\n【5. 检查项目内嵌字体】")
try:
    import os
    project_fonts_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'static', 'fonts')
    project_fonts_dir = os.path.abspath(project_fonts_dir)

    print(f"  字体目录: {project_fonts_dir}")

    if os.path.exists(project_fonts_dir):
        fonts = [f for f in os.listdir(project_fonts_dir) if f.endswith(('.ttf', '.otf', '.ttc'))]
        if fonts:
            print(f"  ✅ 找到 {len(fonts)} 个项目字体:")
            for font in fonts:
                font_path = os.path.join(project_fonts_dir, font)
                size = os.path.getsize(font_path)
                print(f"     - {font} ({size:,} 字节)")
        else:
            print(f"  ⚠️  字体目录存在但为空")
    else:
        print(f"  ❌ 字体目录不存在")
        print(f"\n  建议创建字体目录并放入中文字体文件:")
        print(f"     mkdir -p {project_fonts_dir}")
        print(f"     # 下载并放入字体文件，如 NotoSansCJK-Regular.ttc")

except Exception as e:
    print(f"  ⚠️  检查项目字体时出错: {e}")

print("\n" + "=" * 80)
print("【诊断结论】")
print("=" * 80)

if not missing_deps:
    print("\n✅ WeasyPrint环境基本正常")
    print("\n下一步:")
    print("  1. 取消注释 pricing_order_routes.py 第9行的 PDFGenerator 导入")
    print("  2. 恢复 export_pdf 函数的完整实现")
    print("  3. 测试PDF导出功能")
else:
    print(f"\n❌ 需要安装缺失的依赖")
    print(f"\n解决命令:")
    print(f"  pip install {' '.join(missing_deps)}")

print("\n" + "=" * 80)
