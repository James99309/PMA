#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线上PDF乱码问题 - 字体检测和修复脚本
快速诊断和修复线上环境的PDF导出乱码问题
"""

import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path

def run_command(cmd, shell=True):
    """安全执行命令"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_system_info():
    """检查系统信息"""
    print("🔍 系统环境检测")
    print("=" * 50)
    
    # 基本系统信息
    print(f"操作系统: {platform.system()}")
    print(f"平台: {platform.platform()}")
    print(f"架构: {platform.machine()}")
    print(f"Python版本: {sys.version}")
    print()
    
    # 检查是否为容器环境
    if os.path.exists('/.dockerenv'):
        print("🐳 检测到Docker容器环境")
    elif os.path.exists('/proc/1/cgroup'):
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read():
                print("🐳 检测到Docker容器环境")
    print()

def check_fonts():
    """检查系统字体"""
    print("🔤 字体检查")
    print("=" * 50)
    
    system = platform.system()
    
    if system == 'Linux':
        # 检查字体目录
        font_dirs = [
            '/usr/share/fonts/truetype/',
            '/usr/share/fonts/opentype/',
            '/usr/share/fonts/noto-cjk/',
            '/usr/local/share/fonts/'
        ]
        
        print("📁 字体目录检查:")
        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                print(f"  ✅ {font_dir}")
            else:
                print(f"  ❌ {font_dir}")
        print()
        
        # 检查具体字体文件
        print("📄 中文字体文件检查:")
        font_files = [
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/arphic/ukai.ttc',
            '/usr/share/fonts/truetype/arphic/uming.ttc'
        ]
        
        found_fonts = []
        for font_file in font_files:
            if os.path.exists(font_file):
                print(f"  ✅ {font_file}")
                found_fonts.append(font_file)
            else:
                print(f"  ❌ {font_file}")
        
        print(f"\n找到 {len(found_fonts)} 个中文字体文件")
        
        # 使用fc-list检查系统字体
        print("\n🔍 fc-list字体检查:")
        success, output, error = run_command("fc-list | grep -i 'noto\\|cjk\\|chinese\\|wqy\\|arphic'")
        if success and output:
            print("  ✅ 找到中文字体:")
            for line in output.strip().split('\n')[:10]:  # 只显示前10个
                print(f"    {line}")
            if len(output.strip().split('\n')) > 10:
                print(f"    ... 还有 {len(output.strip().split('\n')) - 10} 个字体")
        else:
            print("  ❌ 未找到中文字体")
        
        return len(found_fonts) > 0
    
    else:
        print(f"当前系统 {system} 不需要检查（非Linux环境）")
        return True

def check_weasyprint():
    """检查WeasyPrint环境"""
    print("\n📚 WeasyPrint环境检查")
    print("=" * 50)
    
    try:
        import weasyprint
        print(f"✅ WeasyPrint版本: {weasyprint.__version__}")
        
        # 检查字体配置
        from weasyprint.text.fonts import FontConfiguration
        font_config = FontConfiguration()
        print("✅ FontConfiguration创建成功")
        
        return True
    except ImportError:
        print("❌ WeasyPrint未安装")
        return False
    except Exception as e:
        print(f"❌ WeasyPrint配置错误: {e}")
        return False

def test_pdf_generation():
    """测试PDF生成"""
    print("\n🧪 PDF生成测试")
    print("=" * 50)
    
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # 测试HTML内容
        html_content = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", 
                                 "AR PL UKai CN", "AR PL UMing CN", "DejaVu Sans", "Liberation Sans", 
                                 Arial, sans-serif; 
                    font-size: 14px; 
                    padding: 20px;
                }
                .test-section {
                    margin: 20px 0;
                    padding: 10px;
                    border: 1px solid #ccc;
                }
            </style>
        </head>
        <body>
            <div class="test-section">
                <h1>📋 PDF字体测试</h1>
                <p><strong>公司名称：</strong>和源通信科技有限公司</p>
                <p><strong>文档类型：</strong>批价单 / 结算单</p>
                <p><strong>金额测试：</strong>￥12,345.67 RMB</p>
            </div>
            
            <div class="test-section">
                <h2>📊 表格测试</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr>
                        <th>产品名称</th>
                        <th>数量</th>
                        <th>单价</th>
                        <th>总价</th>
                    </tr>
                    <tr>
                        <td>测试产品（中文）</td>
                        <td>10</td>
                        <td>￥100.00</td>
                        <td>￥1,000.00</td>
                    </tr>
                </table>
            </div>
            
            <div class="test-section">
                <h2>🔤 字符测试</h2>
                <p>中文字符：批价单、结算单、审批、经销商、分销商</p>
                <p>标点符号：，。！？：；""''（）【】</p>
                <p>数字符号：￥ $ € ¥ % ‰</p>
            </div>
        </body>
        </html>
        '''
        
        font_config = FontConfiguration()
        html_doc = HTML(string=html_content)
        
        # 尝试生成PDF
        test_file = '/tmp/pdf_font_test.pdf'
        pdf_content = html_doc.write_pdf(font_config=font_config)
        
        # 保存测试文件
        with open(test_file, 'wb') as f:
            f.write(pdf_content)
        
        file_size = os.path.getsize(test_file)
        print(f"✅ PDF生成成功！")
        print(f"   文件路径: {test_file}")
        print(f"   文件大小: {file_size:,} 字节")
        
        # 简单检查PDF内容
        if file_size > 1000:  # 至少1KB
            print("✅ PDF文件大小正常")
        else:
            print("⚠️  PDF文件可能过小，请检查内容")
        
        return True, test_file
        
    except Exception as e:
        print(f"❌ PDF生成失败: {e}")
        return False, None

def install_fonts():
    """安装中文字体"""
    print("\n🔧 字体安装")
    print("=" * 50)
    
    system = platform.system()
    
    if system != 'Linux':
        print(f"当前系统 {system} 不需要安装字体")
        return True
    
    # 检测包管理器
    if os.path.exists('/usr/bin/apt-get'):
        package_manager = 'apt'
        install_commands = [
            'apt update',
            'apt install -y fonts-noto-cjk fonts-noto-cjk-extra',
            'apt install -y fonts-wqy-microhei fonts-wqy-zenhei',
            'apt install -y fonts-arphic-ukai fonts-arphic-uming'
        ]
    elif os.path.exists('/usr/bin/yum'):
        package_manager = 'yum'
        install_commands = [
            'yum install -y google-noto-cjk-fonts',
            'yum install -y wqy-microhei-fonts wqy-zenhei-fonts'
        ]
    elif os.path.exists('/usr/bin/dnf'):
        package_manager = 'dnf'
        install_commands = [
            'dnf install -y google-noto-cjk-fonts',
            'dnf install -y wqy-microhei-fonts wqy-zenhei-fonts'
        ]
    else:
        print("❌ 未知的包管理器，无法自动安装字体")
        return False
    
    print(f"检测到包管理器: {package_manager}")
    print(f"将要执行以下安装命令:")
    for cmd in install_commands:
        print(f"  sudo {cmd}")
    
    # 询问是否执行
    response = input("\n是否立即执行字体安装？(y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("跳过字体安装")
        return False
    
    # 执行安装
    success_count = 0
    for cmd in install_commands:
        print(f"\n执行: sudo {cmd}")
        success, output, error = run_command(f"sudo {cmd}")
        if success:
            print(f"✅ 执行成功")
            success_count += 1
        else:
            print(f"❌ 执行失败: {error}")
    
    # 更新字体缓存
    print(f"\n更新字体缓存...")
    success, output, error = run_command("sudo fc-cache -fv")
    if success:
        print("✅ 字体缓存更新成功")
    else:
        print(f"❌ 字体缓存更新失败: {error}")
    
    return success_count > 0

def generate_fix_report(has_fonts, pdf_test_success, test_file_path):
    """生成修复报告"""
    print("\n📋 修复报告")
    print("=" * 50)
    
    if has_fonts and pdf_test_success:
        print("✅ 系统状态：正常")
        print("✅ 字体检查：通过")
        print("✅ PDF生成：成功")
        print("\n🎉 恭喜！您的系统已经可以正常生成中文PDF了！")
        if test_file_path:
            print(f"📁 测试文件：{test_file_path}")
    
    elif has_fonts and not pdf_test_success:
        print("⚠️  系统状态：部分异常")
        print("✅ 字体检查：通过")
        print("❌ PDF生成：失败")
        print("\n🔧 建议修复步骤：")
        print("1. 检查WeasyPrint版本是否过旧")
        print("2. 重新安装WeasyPrint: pip install --upgrade weasyprint")
        print("3. 检查应用日志中的具体错误信息")
    
    elif not has_fonts:
        print("❌ 系统状态：需要修复")
        print("❌ 字体检查：失败")
        print("❌ PDF生成：预期失败")
        print("\n🔧 立即修复步骤：")
        print("1. 运行本脚本的字体安装功能")
        print("2. 或手动执行以下命令：")
        print("   sudo apt update")
        print("   sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra")
        print("   sudo fc-cache -fv")
        print("3. 重启应用服务")
        print("4. 重新测试PDF导出功能")
    
    # 应用层面的建议
    print("\n🎯 应用层面优化建议：")
    print("1. 在app/services/pdf_generator.py中添加字体检测日志")
    print("2. 考虑在项目中内嵌字体文件作为备用方案")
    print("3. 添加PDF生成错误的监控和告警")
    print("4. 定期检查线上环境的字体状态")

def main():
    """主函数"""
    print("🔧 线上PDF乱码问题 - 字体检测和修复脚本")
    print("=" * 60)
    print("本脚本将检测系统字体环境并尝试修复PDF乱码问题")
    print()
    
    # 1. 检查系统信息
    check_system_info()
    
    # 2. 检查字体
    has_fonts = check_fonts()
    
    # 3. 检查WeasyPrint
    weasyprint_ok = check_weasyprint()
    
    if not weasyprint_ok:
        print("\n❌ WeasyPrint环境异常，无法继续测试")
        return
    
    # 4. 测试PDF生成
    pdf_test_success, test_file_path = test_pdf_generation()
    
    # 5. 如果没有字体，尝试安装
    if not has_fonts:
        print("\n⚠️  检测到字体缺失，是否安装中文字体？")
        install_fonts()
        
        # 重新检查字体
        print("\n🔄 重新检查字体状态...")
        has_fonts = check_fonts()
        
        if has_fonts:
            # 重新测试PDF生成
            print("\n🔄 重新测试PDF生成...")
            pdf_test_success, test_file_path = test_pdf_generation()
    
    # 6. 生成修复报告
    generate_fix_report(has_fonts, pdf_test_success, test_file_path)
    
    print("\n🎯 脚本执行完成！")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断执行")
    except Exception as e:
        print(f"\n❌ 脚本执行出错: {e}")
        import traceback
        traceback.print_exc() 