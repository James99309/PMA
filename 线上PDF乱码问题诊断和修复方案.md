# 线上PDF乱码问题诊断和修复方案

## 🔍 问题根本原因

### 环境差异导致的字体问题
1. **本地环境（macOS）**：有完整的中文字体支持
2. **线上环境（Linux）**：缺少中文字体或字体路径不同
3. **字体回退机制失效**：WeasyPrint无法找到合适的中文字体

### 当前系统的字体配置逻辑
```python
# app/services/pdf_generator.py 第124-135行
def _get_system_font_family(self):
    system = platform.system()
    
    if system == "Darwin":  # macOS - 本地正常
        return '"Songti TC", "Songti SC", "STSong", "STHeiti Light", "STHeiti", "Helvetica", "Arial", sans-serif'
    elif system == "Windows":  # Windows
        return '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体", "Arial", sans-serif'
    else:  # Linux - 线上环境，可能缺少字体
        return '"Noto Sans CJK SC", "DejaVu Sans", "Liberation Sans", "Arial", sans-serif'
```

## 🚨 问题诊断

### 1. 检查线上环境字体状态

**创建字体检测脚本：**

```bash
#!/bin/bash
# 检查线上环境字体
echo "=== 系统信息 ==="
uname -a
echo ""

echo "=== Python环境 ==="
python3 --version
pip list | grep -i weasyprint
echo ""

echo "=== 字体目录检查 ==="
ls -la /usr/share/fonts/truetype/ 2>/dev/null || echo "字体目录不存在"
ls -la /usr/share/fonts/opentype/ 2>/dev/null || echo "OpenType字体目录不存在"
echo ""

echo "=== 中文字体检查 ==="
find /usr -name "*noto*" -name "*.ttf" -o -name "*.ttc" 2>/dev/null
find /usr -name "*cjk*" -name "*.ttf" -o -name "*.ttc" 2>/dev/null
find /usr -name "*chinese*" -name "*.ttf" -o -name "*.ttc" 2>/dev/null
echo ""

echo "=== 字体缓存 ==="
fc-list | grep -i "noto\|cjk\|chinese" || echo "未找到中文字体"
```

### 2. WeasyPrint字体问题测试

**创建PDF生成测试脚本：**

```python
#!/usr/bin/env python3
import platform
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def test_pdf_generation():
    """测试PDF生成和字体"""
    print(f"操作系统: {platform.system()}")
    print(f"平台: {platform.platform()}")
    
    # 测试HTML内容
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { 
                font-family: "Noto Sans CJK SC", "DejaVu Sans", "Liberation Sans", Arial, sans-serif; 
                font-size: 14px; 
            }
        </style>
    </head>
    <body>
        <h1>批价单测试</h1>
        <p>中文字符测试：和源通信科技有限公司</p>
        <p>数字测试：￥12,345.67</p>
        <table border="1">
            <tr><th>产品名称</th><th>数量</th><th>单价</th></tr>
            <tr><td>测试产品</td><td>10</td><td>￥100.00</td></tr>
        </table>
    </body>
    </html>
    '''
    
    try:
        font_config = FontConfiguration()
        html_doc = HTML(string=html_content)
        
        # 尝试生成PDF
        pdf_content = html_doc.write_pdf(font_config=font_config)
        
        # 保存测试文件
        with open('/tmp/test_pdf.pdf', 'wb') as f:
            f.write(pdf_content)
        
        print("✅ PDF生成成功，保存为 /tmp/test_pdf.pdf")
        return True
        
    except Exception as e:
        print(f"❌ PDF生成失败: {e}")
        return False

if __name__ == '__main__':
    test_pdf_generation()
```

## 🛠️ 修复方案

### 方案1：安装系统字体（推荐）

**在线上服务器安装中文字体：**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra
sudo apt install -y fonts-wqy-microhei fonts-wqy-zenhei
sudo apt install -y fonts-arphic-ukai fonts-arphic-uming

# CentOS/RHEL
sudo yum install -y google-noto-cjk-fonts
sudo yum install -y wqy-microhei-fonts wqy-zenhei-fonts

# 刷新字体缓存
sudo fc-cache -fv
```

### 方案2：项目内嵌字体文件

**在项目中添加字体文件：**

```python
# 1. 下载字体文件到项目
mkdir -p app/static/fonts
# 下载 Noto Sans CJK SC 字体
# wget https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/NotoSansCJK-Regular.ttc

# 2. 修改 PDF 生成器
class PDFGenerator:
    def __init__(self):
        # ... 现有代码 ...
        self._add_custom_fonts()
    
    def _add_custom_fonts(self):
        """添加自定义字体"""
        try:
            custom_font_path = os.path.join(
                current_app.static_folder, 'fonts', 'NotoSansCJK-Regular.ttc'
            )
            if os.path.exists(custom_font_path):
                self.font_config.add_font_file(custom_font_path)
                logger.info(f"✅ 添加自定义字体: {custom_font_path}")
        except Exception as e:
            logger.warning(f"添加自定义字体失败: {e}")
```

### 方案3：改进字体检测和回退机制

**增强字体检测逻辑：**

```python
def _configure_fonts(self):
    """改进的字体配置"""
    try:
        system = platform.system()
        
        if system == 'Linux':
            # Linux环境的字体检测
            linux_font_paths = [
                # Noto CJK 字体
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
                
                # WQY字体
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                
                # 文泉驿字体
                '/usr/share/fonts/truetype/arphic/ukai.ttc',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
                
                # 自定义字体路径
                os.path.join(current_app.static_folder, 'fonts', 'NotoSansCJK-Regular.ttc'),
            ]
            
            available_fonts = []
            for font_path in linux_font_paths:
                if os.path.exists(font_path):
                    logger.info(f"✅ Linux找到字体: {font_path}")
                    available_fonts.append(font_path)
                    # 添加到字体配置
                    self.font_config.add_font_file(font_path)
            
            if not available_fonts:
                logger.error("⚠️ Linux系统未找到任何中文字体！PDF可能出现乱码")
                # 发送告警通知
                self._send_font_alert()
        
        # ... 其他系统的配置 ...
    except Exception as e:
        logger.error(f"字体配置失败: {e}")
```

### 方案4：使用Docker确保字体一致性

**创建包含字体的Docker镜像：**

```dockerfile
FROM python:3.9-slim

# 安装字体
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# ... 其他Docker配置 ...
```

## 🔧 立即修复脚本

**创建可直接运行的修复脚本：**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线上PDF乱码修复脚本
"""

import os
import platform
import requests
import tempfile
from pathlib import Path

def download_font():
    """下载Noto Sans CJK字体"""
    font_url = "https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/NotoSansCJK-Regular.ttc"
    font_dir = Path("app/static/fonts")
    font_path = font_dir / "NotoSansCJK-Regular.ttc"
    
    if font_path.exists():
        print(f"✅ 字体文件已存在: {font_path}")
        return str(font_path)
    
    print(f"📥 下载字体文件到: {font_path}")
    font_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(font_url, stream=True)
        response.raise_for_status()
        
        with open(font_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 字体下载完成: {font_path}")
        return str(font_path)
        
    except Exception as e:
        print(f"❌ 字体下载失败: {e}")
        return None

def install_system_fonts():
    """安装系统字体"""
    system = platform.system()
    
    if system == 'Linux':
        print("🔧 检测到Linux系统，尝试安装中文字体...")
        
        # 检测包管理器并安装字体
        if os.path.exists('/usr/bin/apt'):
            # Ubuntu/Debian
            commands = [
                'sudo apt update',
                'sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra',
                'sudo apt install -y fonts-wqy-microhei fonts-wqy-zenhei',
                'sudo fc-cache -fv'
            ]
        elif os.path.exists('/usr/bin/yum'):
            # CentOS/RHEL
            commands = [
                'sudo yum install -y google-noto-cjk-fonts',
                'sudo yum install -y wqy-microhei-fonts wqy-zenhei-fonts',
                'sudo fc-cache -fv'
            ]
        else:
            print("❌ 未知的Linux发行版，请手动安装字体")
            return False
        
        print("请运行以下命令安装字体：")
        for cmd in commands:
            print(f"  {cmd}")
        
        return True
    else:
        print(f"当前系统 {system} 不需要额外安装字体")
        return True

def create_font_patch():
    """创建字体补丁"""
    patch_content = '''
# PDF字体修复补丁
# 添加到 app/services/pdf_generator.py

def _get_system_font_family_fixed(self):
    """修复后的字体配置"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return '"Songti TC", "Songti SC", "STSong", "STHeiti Light", "STHeiti", "Helvetica", "Arial", sans-serif'
    elif system == "Windows":  # Windows
        return '"Microsoft YaHei", "微软雅黑", "DengXian", "等线", "SimSun", "宋体", "Arial", sans-serif'
    else:  # Linux - 增强版
        # 检查可用字体
        possible_fonts = [
            '"Noto Sans CJK SC"',
            '"WenQuanYi Micro Hei"',
            '"WenQuanYi Zen Hei"',
            '"AR PL UKai CN"',
            '"AR PL UMing CN"',
            '"DejaVu Sans"',
            '"Liberation Sans"',
            '"Arial"',
            'sans-serif'
        ]
        
        return ', '.join(possible_fonts)
'''
    
    with open('font_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("✅ 字体补丁已创建: font_patch.py")

if __name__ == '__main__':
    print("🔧 线上PDF乱码修复脚本")
    print("=" * 50)
    
    # 1. 下载字体文件
    font_path = download_font()
    
    # 2. 安装系统字体
    install_system_fonts()
    
    # 3. 创建补丁
    create_font_patch()
    
    print("\n✅ 修复脚本执行完成！")
    print("\n📋 后续步骤：")
    print("1. 重启应用服务")
    print("2. 测试PDF导出功能")
    print("3. 检查字体显示效果")
```

## 📋 验证步骤

### 1. 检查字体安装
```bash
fc-list | grep -i "noto\|cjk\|chinese"
```

### 2. 测试PDF生成
```python
# 运行测试脚本验证PDF生成
python3 test_pdf_generation.py
```

### 3. 检查日志
```bash
# 查看应用日志中的字体相关信息
tail -f /path/to/app.log | grep -i "font\|pdf"
```

## 🎯 推荐解决方案

**立即可用的解决方案（优先级排序）：**

1. **【立即执行】** 在线上服务器安装Noto CJK字体
2. **【备用方案】** 下载字体文件到项目static目录
3. **【长期方案】** 使用Docker确保环境一致性
4. **【监控方案】** 添加字体检测和告警机制

这样可以快速解决线上PDF乱码问题，确保批价单和结算单正常导出！ 