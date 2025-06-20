#!/bin/bash
# 容器环境PDF乱码修复脚本（无sudo版本）

set -e  # 遇到错误立即退出

echo "🚀 容器环境PDF乱码修复脚本"
echo "============================"

# 检测环境
detect_environment() {
    echo "📋 环境检测："
    echo "操作系统: $(uname -s)"
    echo "发行版: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"' || echo "未知")"
    echo "当前用户: $(whoami)"
    echo "用户权限: $(id)"
    
    # 检查是否在容器中
    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        echo "🐳 检测到Docker容器环境"
        CONTAINER_ENV=true
    else
        echo "🖥️  检测到主机环境"
        CONTAINER_ENV=false
    fi
    
    # 检查权限
    if [ "$EUID" -eq 0 ]; then
        echo "✅ Root权限，可以直接安装字体"
        USE_SUDO=""
    elif command -v sudo >/dev/null 2>&1; then
        echo "✅ 发现sudo命令，将使用sudo安装"
        USE_SUDO="sudo"
    else
        echo "⚠️  无sudo权限，尝试直接执行或提供替代方案"
        USE_SUDO=""
    fi
    echo ""
}

# 尝试安装字体（适配容器环境）
install_fonts_container() {
    echo "🔧 容器环境字体安装..."
    
    # 方法1：尝试直接安装（如果有权限）
    if command -v apt-get >/dev/null 2>&1; then
        echo "尝试使用 APT 安装字体..."
        
        echo "1. 更新包列表..."
        if $USE_SUDO apt-get update 2>/dev/null; then
            echo "✅ 包列表更新成功"
        else
            echo "❌ 包列表更新失败，可能需要管理员权限"
            return 1
        fi
        
        echo "2. 安装 Noto CJK 字体..."
        if $USE_SUDO apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra 2>/dev/null; then
            echo "✅ Noto CJK 字体安装成功"
        else
            echo "❌ Noto CJK 字体安装失败"
        fi
        
        echo "3. 安装文泉驿字体..."
        if $USE_SUDO apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei 2>/dev/null; then
            echo "✅ 文泉驿字体安装成功"
        else
            echo "❌ 文泉驿字体安装失败"
        fi
        
    elif command -v yum >/dev/null 2>&1; then
        echo "尝试使用 YUM 安装字体..."
        $USE_SUDO yum install -y google-noto-cjk-fonts wqy-microhei-fonts wqy-zenhei-fonts
        
    elif command -v dnf >/dev/null 2>&1; then
        echo "尝试使用 DNF 安装字体..."
        $USE_SUDO dnf install -y google-noto-cjk-fonts wqy-microhei-fonts wqy-zenhei-fonts
        
    else
        echo "❌ 未找到包管理器"
        return 1
    fi
}

# 手动下载字体（备用方案）
download_fonts_manual() {
    echo ""
    echo "🔄 尝试手动下载字体..."
    
    # 创建用户字体目录
    FONT_DIR="$HOME/.local/share/fonts"
    mkdir -p "$FONT_DIR"
    
    echo "字体目录: $FONT_DIR"
    
    # 下载Noto Sans CJK SC字体
    FONT_URL="https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/NotoSansCJK-Regular.ttc"
    FONT_FILE="$FONT_DIR/NotoSansCJK-Regular.ttc"
    
    if [ ! -f "$FONT_FILE" ]; then
        echo "📥 下载 Noto Sans CJK 字体..."
        if command -v wget >/dev/null 2>&1; then
            if wget -O "$FONT_FILE" "$FONT_URL" 2>/dev/null; then
                echo "✅ 字体下载成功: $FONT_FILE"
            else
                echo "❌ wget 下载失败"
                return 1
            fi
        elif command -v curl >/dev/null 2>&1; then
            if curl -L -o "$FONT_FILE" "$FONT_URL" 2>/dev/null; then
                echo "✅ 字体下载成功: $FONT_FILE"
            else
                echo "❌ curl 下载失败"
                return 1
            fi
        else
            echo "❌ 未找到 wget 或 curl 命令"
            return 1
        fi
    else
        echo "✅ 字体文件已存在: $FONT_FILE"
    fi
    
    # 更新字体缓存
    if command -v fc-cache >/dev/null 2>&1; then
        echo "🔄 更新字体缓存..."
        fc-cache -fv "$FONT_DIR" 2>/dev/null || echo "字体缓存更新可能失败"
    fi
    
    return 0
}

# 创建项目内字体文件（最后备用方案）
create_project_font() {
    echo ""
    echo "🔧 创建项目内字体解决方案..."
    
    # 在项目中创建字体目录
    PROJECT_FONT_DIR="app/static/fonts"
    mkdir -p "$PROJECT_FONT_DIR"
    
    # 创建字体配置说明
    cat > "$PROJECT_FONT_DIR/README.md" << 'EOF'
# 项目字体文件

## 问题说明
线上环境缺少中文字体，导致PDF导出乱码。

## 解决方案
1. 手动上传中文字体文件到此目录
2. 修改PDF生成器加载项目内字体

## 推荐字体
- NotoSansCJK-Regular.ttc (推荐)
- wqy-microhei.ttc
- wqy-zenhei.ttc

## 下载地址
- Noto CJK: https://github.com/googlefonts/noto-cjk/releases
- 文泉驿: http://wenq.org/wqy2/

## 使用方法
下载字体文件后放置到此目录，重启应用即可。
EOF

    echo "✅ 已创建项目字体目录: $PROJECT_FONT_DIR"
    echo "📄 已创建字体说明文件: $PROJECT_FONT_DIR/README.md"
}

# 检测字体状态
check_fonts() {
    echo ""
    echo "🔍 检测字体状态..."
    
    # 检查系统字体
    system_fonts=(
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
    )
    
    system_font_count=0
    for font in "${system_fonts[@]}"; do
        if [ -f "$font" ]; then
            echo "  ✅ 系统字体: $font"
            ((system_font_count++))
        fi
    done
    
    # 检查用户字体
    user_fonts=(
        "$HOME/.local/share/fonts/NotoSansCJK-Regular.ttc"
        "$HOME/.fonts/NotoSansCJK-Regular.ttc"
    )
    
    user_font_count=0
    for font in "${user_fonts[@]}"; do
        if [ -f "$font" ]; then
            echo "  ✅ 用户字体: $font"
            ((user_font_count++))
        fi
    done
    
    # 检查项目字体
    project_fonts=(
        "app/static/fonts/NotoSansCJK-Regular.ttc"
        "app/static/fonts/wqy-microhei.ttc"
    )
    
    project_font_count=0
    for font in "${project_fonts[@]}"; do
        if [ -f "$font" ]; then
            echo "  ✅ 项目字体: $font"
            ((project_font_count++))
        fi
    done
    
    total_fonts=$((system_font_count + user_font_count + project_font_count))
    echo ""
    echo "📊 字体统计: 系统($system_font_count) + 用户($user_font_count) + 项目($project_font_count) = 总计($total_fonts)"
    
    return $total_fonts
}

# 测试PDF生成
test_pdf() {
    echo ""
    echo "🧪 测试PDF生成..."
    
    cat > /tmp/container_pdf_test.py << 'EOF'
#!/usr/bin/env python3
import sys
import os

try:
    from weasyprint import HTML
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
                             "DejaVu Sans", "Liberation Sans", Arial, sans-serif; 
                font-size: 14px; 
                padding: 20px;
            }
        </style>
    </head>
    <body>
        <h1>🧪 容器环境PDF测试</h1>
        <p><strong>公司名称：</strong>和源通信科技有限公司</p>
        <p><strong>测试内容：</strong>批价单、结算单PDF导出</p>
        <p><strong>金额测试：</strong>￥12,345.67 RMB</p>
        <table border="1" cellpadding="5">
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
    </body>
    </html>
    '''
    
    font_config = FontConfiguration()
    html_doc = HTML(string=html_content)
    pdf_content = html_doc.write_pdf(font_config=font_config)
    
    test_file = '/tmp/container_font_test.pdf'
    with open(test_file, 'wb') as f:
        f.write(pdf_content)
    
    file_size = len(pdf_content)
    print(f"✅ PDF生成成功！")
    print(f"   文件: {test_file}")
    print(f"   大小: {file_size:,} 字节")
    
    if file_size > 5000:
        print("✅ PDF大小正常，字体可能工作正常")
    else:
        print("⚠️  PDF较小，可能仍有字体问题")
    
except Exception as e:
    print(f"❌ PDF生成失败: {e}")
    sys.exit(1)
EOF

    if python3 /tmp/container_pdf_test.py 2>/dev/null; then
        echo "✅ PDF测试成功！"
        return 0
    else
        echo "❌ PDF测试失败"
        return 1
    fi
    
    # 清理
    rm -f /tmp/container_pdf_test.py
}

# 生成解决方案报告
generate_solution_report() {
    local font_count=$1
    local pdf_success=$2
    
    echo ""
    echo "📋 容器环境解决方案报告"
    echo "========================"
    
    if [ $font_count -gt 0 ] && [ $pdf_success -eq 0 ]; then
        echo "✅ 状态：问题已解决"
        echo "✅ 字体：已安装 ($font_count 个字体文件)"
        echo "✅ PDF：生成测试通过"
        echo ""
        echo "🎉 恭喜！PDF乱码问题已修复，请重启应用测试实际功能。"
        
    elif [ $font_count -gt 0 ] && [ $pdf_success -ne 0 ]; then
        echo "⚠️  状态：部分解决"
        echo "✅ 字体：已安装 ($font_count 个字体文件)"
        echo "❌ PDF：测试失败"
        echo ""
        echo "🔧 建议："
        echo "1. 重启应用服务"
        echo "2. 检查WeasyPrint版本"
        echo "3. 查看应用日志"
        
    else
        echo "❌ 状态：需要手动处理"
        echo "❌ 字体：安装失败"
        echo "❌ PDF：无法测试"
        echo ""
        echo "🔧 手动解决方案："
        echo ""
        echo "方案1：联系系统管理员安装字体"
        echo "sudo apt update"
        echo "sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra"
        echo "sudo fc-cache -fv"
        echo ""
        echo "方案2：下载字体到项目目录"
        echo "mkdir -p app/static/fonts"
        echo "wget -O app/static/fonts/NotoSansCJK-Regular.ttc \\"
        echo "  https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/NotoSansCJK-Regular.ttc"
        echo ""
        echo "方案3：修改Dockerfile添加字体"
        echo "# 在Dockerfile中添加："
        echo "RUN apt-get update && apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra"
        echo ""
    fi
    
    echo "📄 详细说明请查看：线上PDF乱码问题诊断和修复方案.md"
}

# 主执行流程
main() {
    detect_environment
    
    echo "即将尝试以下修复方案："
    echo "1. 尝试使用包管理器安装字体"
    echo "2. 如果失败，尝试手动下载字体"
    echo "3. 创建项目字体目录作为备用"
    echo "4. 测试PDF生成功能"
    echo ""
    
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 0
    fi
    
    # 尝试安装字体
    if install_fonts_container; then
        echo "✅ 包管理器安装成功"
    else
        echo "⚠️  包管理器安装失败，尝试备用方案..."
        if download_fonts_manual; then
            echo "✅ 手动下载安装成功"
        else
            echo "⚠️  手动下载失败，创建项目字体目录..."
            create_project_font
        fi
    fi
    
    # 检测字体状态
    check_fonts
    font_count=$?
    
    # 测试PDF
    test_pdf
    pdf_result=$?
    
    # 生成报告
    generate_solution_report $font_count $pdf_result
    
    echo ""
    echo "🎯 修复脚本执行完成！"
}

# 错误处理
trap 'echo ""; echo "❌ 脚本执行被中断"; exit 1' INT

# 执行主函数
main "$@" 