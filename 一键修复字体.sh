#!/bin/bash
# 线上PDF乱码问题 - 一键修复脚本

set -e  # 遇到错误立即退出

echo "🚀 线上PDF乱码一键修复脚本"
echo "============================="

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    SUDO=""
else
    SUDO="sudo"
fi

# 检测操作系统和包管理器
detect_system() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    echo "检测到系统: $OS $VER"
}

# 安装字体包
install_fonts() {
    echo ""
    echo "🔧 开始安装中文字体..."
    
    if command -v apt-get >/dev/null 2>&1; then
        echo "使用 APT 包管理器..."
        
        echo "1. 更新包列表..."
        $SUDO apt-get update
        
        echo "2. 安装 Noto CJK 字体..."
        $SUDO apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra
        
        echo "3. 安装文泉驿字体..."
        $SUDO apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei
        
        echo "4. 安装文鼎字体..."
        $SUDO apt-get install -y fonts-arphic-ukai fonts-arphic-uming || echo "文鼎字体安装失败，继续..."
        
    elif command -v yum >/dev/null 2>&1; then
        echo "使用 YUM 包管理器..."
        
        echo "1. 安装 Noto CJK 字体..."
        $SUDO yum install -y google-noto-cjk-fonts
        
        echo "2. 安装文泉驿字体..."
        $SUDO yum install -y wqy-microhei-fonts wqy-zenhei-fonts
        
    elif command -v dnf >/dev/null 2>&1; then
        echo "使用 DNF 包管理器..."
        
        echo "1. 安装 Noto CJK 字体..."
        $SUDO dnf install -y google-noto-cjk-fonts
        
        echo "2. 安装文泉驿字体..."
        $SUDO dnf install -y wqy-microhei-fonts wqy-zenhei-fonts
        
    else
        echo "❌ 未知的包管理器，无法自动安装字体"
        echo "请手动安装中文字体包"
        exit 1
    fi
}

# 更新字体缓存
update_font_cache() {
    echo ""
    echo "🔄 更新字体缓存..."
    
    if command -v fc-cache >/dev/null 2>&1; then
        $SUDO fc-cache -fv
        echo "✅ 字体缓存更新完成"
    else
        echo "⚠️  fc-cache 命令不存在，请手动更新字体缓存"
    fi
}

# 验证字体安装
verify_fonts() {
    echo ""
    echo "🔍 验证字体安装..."
    
    # 检查字体文件
    font_files=(
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
    )
    
    found_count=0
    for font in "${font_files[@]}"; do
        if [ -f "$font" ]; then
            echo "  ✅ $font"
            ((found_count++))
        fi
    done
    
    if [ $found_count -gt 0 ]; then
        echo "✅ 找到 $found_count 个中文字体文件"
    else
        echo "❌ 未找到中文字体文件"
        return 1
    fi
    
    # 使用fc-list验证
    if command -v fc-list >/dev/null 2>&1; then
        cjk_fonts=$(fc-list | grep -i 'noto\|cjk\|chinese\|wqy\|arphic' | wc -l)
        if [ $cjk_fonts -gt 0 ]; then
            echo "✅ fc-list 发现 $cjk_fonts 个中文字体"
        else
            echo "⚠️  fc-list 未发现中文字体"
        fi
    fi
}

# 创建测试PDF
test_pdf_generation() {
    echo ""
    echo "🧪 测试PDF生成..."
    
    # 创建测试脚本
    cat > /tmp/test_pdf.py << 'EOF'
#!/usr/bin/env python3
import sys
try:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { 
                font-family: "Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans", Arial, sans-serif; 
                font-size: 14px; padding: 20px;
            }
        </style>
    </head>
    <body>
        <h1>PDF字体测试</h1>
        <p>中文字符测试：和源通信科技有限公司</p>
        <p>批价单、结算单、审批流程</p>
        <p>金额：￥12,345.67 RMB</p>
        <table border="1">
            <tr><th>产品名称</th><th>数量</th><th>单价</th></tr>
            <tr><td>测试产品</td><td>10</td><td>￥100.00</td></tr>
        </table>
    </body>
    </html>
    '''
    
    font_config = FontConfiguration()
    html_doc = HTML(string=html_content)
    pdf_content = html_doc.write_pdf(font_config=font_config)
    
    with open('/tmp/font_test.pdf', 'wb') as f:
        f.write(pdf_content)
    
    print("PDF测试文件已生成: /tmp/font_test.pdf")
    print("文件大小:", len(pdf_content), "字节")
    
except Exception as e:
    print(f"PDF生成失败: {e}")
    sys.exit(1)
EOF

    if python3 /tmp/test_pdf.py; then
        echo "✅ PDF生成测试成功！"
        if [ -f /tmp/font_test.pdf ]; then
            file_size=$(stat -c%s /tmp/font_test.pdf 2>/dev/null || echo "0")
            echo "   测试文件: /tmp/font_test.pdf (${file_size} 字节)"
        fi
    else
        echo "❌ PDF生成测试失败"
        return 1
    fi
    
    # 清理测试文件
    rm -f /tmp/test_pdf.py
}

# 生成修复报告
generate_report() {
    echo ""
    echo "📋 修复报告"
    echo "============"
    echo "✅ 中文字体安装完成"
    echo "✅ 字体缓存已更新"
    echo "✅ PDF生成测试通过"
    echo ""
    echo "🎯 后续步骤："
    echo "1. 重启应用服务（如 systemctl restart your-app）"
    echo "2. 测试实际的批价单/结算单PDF导出功能"
    echo "3. 检查PDF中的中文字符是否正常显示"
}

# 主执行流程
main() {
    detect_system
    
    echo ""
    echo "即将执行以下操作："
    echo "1. 安装中文字体包"
    echo "2. 更新字体缓存"
    echo "3. 验证字体安装"
    echo "4. 测试PDF生成"
    echo ""
    
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 0
    fi
    
    install_fonts
    update_font_cache
    
    if verify_fonts; then
        if test_pdf_generation; then
            generate_report
            echo "🎉 修复完成！PDF乱码问题应该已经解决。"
        else
            echo "⚠️  字体安装成功，但PDF生成测试失败"
            echo "请检查WeasyPrint环境或查看应用日志"
        fi
    else
        echo "❌ 字体安装可能失败，请检查错误信息"
        exit 1
    fi
}

# 错误处理
trap 'echo ""; echo "❌ 脚本执行被中断"; exit 1' INT

# 执行主函数
main "$@" 