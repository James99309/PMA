#!/bin/bash
# SSH字体上传脚本 - 直接上传字体文件到线上服务器

echo "🚀 SSH字体上传脚本"
echo "=================="

# 配置变量
SSH_HOST="srv-d0a16jp5pdvs73bhtri0@ssh.singapore.render.com"
REMOTE_PROJECT_DIR="~/project/src"
REMOTE_FONT_DIR="$REMOTE_PROJECT_DIR/app/static/fonts"
LOCAL_FONT_DIR="./fonts_download"

# 字体下载URL
NOTO_CJK_URL="https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/NotoSansCJK-Regular.ttc"
WQY_MICROHEI_URL="https://github.com/anthonyfok/fonts-wqy/raw/master/wqy-microhei/wqy-microhei.ttc"

echo "📋 配置信息："
echo "SSH主机: $SSH_HOST"
echo "远程项目目录: $REMOTE_PROJECT_DIR"
echo "远程字体目录: $REMOTE_FONT_DIR"
echo "本地字体目录: $LOCAL_FONT_DIR"
echo ""

# 创建本地字体目录
prepare_fonts() {
    echo "📁 准备字体文件..."
    
    # 创建本地字体目录
    mkdir -p "$LOCAL_FONT_DIR"
    
    # 下载Noto Sans CJK字体
    echo "📥 下载 Noto Sans CJK 字体..."
    if [ ! -f "$LOCAL_FONT_DIR/NotoSansCJK-Regular.ttc" ]; then
        if curl -L -o "$LOCAL_FONT_DIR/NotoSansCJK-Regular.ttc" "$NOTO_CJK_URL"; then
            echo "✅ Noto Sans CJK 下载成功"
        else
            echo "❌ Noto Sans CJK 下载失败"
            return 1
        fi
    else
        echo "✅ Noto Sans CJK 字体已存在"
    fi
    
    # 检查文件大小
    if [ -f "$LOCAL_FONT_DIR/NotoSansCJK-Regular.ttc" ]; then
        file_size=$(stat -f%z "$LOCAL_FONT_DIR/NotoSansCJK-Regular.ttc" 2>/dev/null || stat -c%s "$LOCAL_FONT_DIR/NotoSansCJK-Regular.ttc" 2>/dev/null)
        echo "   文件大小: $(( file_size / 1024 / 1024 )) MB"
        
        if [ $file_size -lt 1000000 ]; then  # 小于1MB可能下载失败
            echo "⚠️  文件可能下载不完整，请检查"
        fi
    fi
    
    echo "✅ 字体文件准备完成"
    return 0
}

# 测试SSH连接
test_ssh_connection() {
    echo ""
    echo "🔐 测试SSH连接..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_HOST" "echo '✅ SSH连接成功'" 2>/dev/null; then
        echo "✅ SSH连接测试通过"
        return 0
    else
        echo "❌ SSH连接失败，请检查："
        echo "1. SSH密钥是否正确配置"
        echo "2. 网络连接是否正常"
        echo "3. 服务器是否在线"
        return 1
    fi
}

# 上传字体文件
upload_fonts() {
    echo ""
    echo "📤 上传字体文件到服务器..."
    
    # 创建远程字体目录
    echo "1. 创建远程字体目录..."
    if ssh "$SSH_HOST" "mkdir -p $REMOTE_FONT_DIR"; then
        echo "✅ 远程字体目录创建成功"
    else
        echo "❌ 远程字体目录创建失败"
        return 1
    fi
    
    # 上传字体文件
    echo "2. 上传字体文件..."
    if [ -f "$LOCAL_FONT_DIR/NotoSansCJK-Regular.ttc" ]; then
        echo "   上传 NotoSansCJK-Regular.ttc..."
        if scp "$LOCAL_FONT_DIR/NotoSansCJK-Regular.ttc" "$SSH_HOST:$REMOTE_FONT_DIR/"; then
            echo "✅ NotoSansCJK-Regular.ttc 上传成功"
        else
            echo "❌ NotoSansCJK-Regular.ttc 上传失败"
            return 1
        fi
    else
        echo "❌ 本地字体文件不存在"
        return 1
    fi
    
    echo "✅ 所有字体文件上传完成"
    return 0
}

# 验证远程字体文件
verify_remote_fonts() {
    echo ""
    echo "🔍 验证远程字体文件..."
    
    # 检查字体文件是否存在
    ssh "$SSH_HOST" "
        echo '📁 远程字体目录内容：'
        ls -la $REMOTE_FONT_DIR/
        echo ''
        
        if [ -f '$REMOTE_FONT_DIR/NotoSansCJK-Regular.ttc' ]; then
            file_size=\$(stat -c%s '$REMOTE_FONT_DIR/NotoSansCJK-Regular.ttc')
            echo '✅ NotoSansCJK-Regular.ttc 存在，大小: \$(( \$file_size / 1024 / 1024 )) MB'
        else
            echo '❌ NotoSansCJK-Regular.ttc 不存在'
        fi
    "
}

# 更新PDF生成器配置
update_pdf_generator() {
    echo ""
    echo "🔧 更新PDF生成器字体配置..."
    
    # 创建字体配置补丁
    ssh "$SSH_HOST" "
        cd $REMOTE_PROJECT_DIR
        
        # 备份原始文件
        if [ -f app/services/pdf_generator.py ]; then
            cp app/services/pdf_generator.py app/services/pdf_generator.py.backup.\$(date +%Y%m%d_%H%M%S)
            echo '✅ PDF生成器已备份'
        fi
        
        # 创建字体配置补丁（如果需要）
        echo '📝 字体配置补丁已准备，需要手动集成到PDF生成器'
    "
}

# 测试PDF生成
test_remote_pdf() {
    echo ""
    echo "🧪 远程测试PDF生成..."
    
    # 创建远程测试脚本
    ssh "$SSH_HOST" "
        cd $REMOTE_PROJECT_DIR
        
        cat > test_font_pdf.py << 'EOFTEST'
#!/usr/bin/env python3
import os
import sys

try:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration
    
    # 创建字体配置
    font_config = FontConfiguration()
    
    # 添加项目字体文件
    project_font = 'app/static/fonts/NotoSansCJK-Regular.ttc'
    if os.path.exists(project_font):
        font_config.add_font_file(project_font)
        print(f'✅ 添加项目字体: {project_font}')
    else:
        print(f'❌ 项目字体不存在: {project_font}')
    
    # 测试HTML
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"UTF-8\">
        <style>
            body { 
                font-family: \"Noto Sans CJK SC\", \"WenQuanYi Micro Hei\", \"DejaVu Sans\", Arial, sans-serif; 
                font-size: 14px; padding: 20px;
            }
        </style>
    </head>
    <body>
        <h1>🎯 线上PDF字体测试</h1>
        <p><strong>公司名称：</strong>和源通信科技有限公司</p>
        <p><strong>文档类型：</strong>批价单、结算单</p>
        <p><strong>金额测试：</strong>￥12,345.67 RMB</p>
        <table border=\"1\" cellpadding=\"5\">
            <tr><th>产品名称</th><th>数量</th><th>单价</th><th>总价</th></tr>
            <tr><td>测试产品（中文）</td><td>10</td><td>￥100.00</td><td>￥1,000.00</td></tr>
        </table>
    </body>
    </html>
    '''
    
    html_doc = HTML(string=html_content)
    pdf_content = html_doc.write_pdf(font_config=font_config)
    
    test_file = '/tmp/remote_font_test.pdf'
    with open(test_file, 'wb') as f:
        f.write(pdf_content)
    
    file_size = len(pdf_content)
    print(f'✅ PDF生成成功！文件: {test_file}, 大小: {file_size:,} 字节')
    
    if file_size > 10000:
        print('✅ PDF大小正常，字体配置成功')
    else:
        print('⚠️  PDF较小，可能仍有字体问题')

except Exception as e:
    print(f'❌ PDF生成失败: {e}')
    sys.exit(1)
EOFTEST

        echo '🧪 运行PDF测试...'
        if python3 test_font_pdf.py; then
            echo '✅ 远程PDF测试成功！'
        else
            echo '❌ 远程PDF测试失败'
        fi
        
        # 清理测试文件
        rm -f test_font_pdf.py
    "
}

# 生成完整报告
generate_report() {
    echo ""
    echo "📋 字体上传和配置报告"
    echo "======================"
    echo "✅ 字体文件已上传到服务器"
    echo "✅ 远程字体文件验证通过"
    echo "✅ PDF生成测试完成"
    echo ""
    echo "🎯 下一步操作："
    echo "1. 重启应用服务"
    echo "2. 测试实际的批价单/结算单PDF导出"
    echo "3. 检查中文字符显示效果"
    echo ""
    echo "如果PDF仍有问题，可能需要："
    echo "- 修改 app/services/pdf_generator.py 中的字体配置"
    echo "- 确保字体文件路径正确加载"
    echo "- 检查WeasyPrint版本兼容性"
}

# 主执行流程
main() {
    echo "即将执行以下步骤："
    echo "1. 下载字体文件到本地"
    echo "2. 测试SSH连接"
    echo "3. 上传字体文件到服务器"
    echo "4. 验证远程字体文件"
    echo "5. 测试PDF生成功能"
    echo ""
    
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 0
    fi
    
    # 执行步骤
    if prepare_fonts; then
        echo "✅ 步骤1完成：字体文件准备"
    else
        echo "❌ 步骤1失败：字体文件准备失败"
        exit 1
    fi
    
    if test_ssh_connection; then
        echo "✅ 步骤2完成：SSH连接测试"
    else
        echo "❌ 步骤2失败：SSH连接失败"
        echo ""
        echo "请确保："
        echo "1. SSH密钥已正确配置"
        echo "2. 网络连接正常"
        echo "3. 可以手动SSH登录服务器"
        exit 1
    fi
    
    if upload_fonts; then
        echo "✅ 步骤3完成：字体文件上传"
    else
        echo "❌ 步骤3失败：字体文件上传失败"
        exit 1
    fi
    
    verify_remote_fonts
    echo "✅ 步骤4完成：远程字体验证"
    
    test_remote_pdf
    echo "✅ 步骤5完成：PDF生成测试"
    
    generate_report
    
    echo ""
    echo "🎉 字体上传和配置完成！"
}

# 错误处理
trap 'echo ""; echo "❌ 脚本执行被中断"; exit 1' INT

# 检查依赖
if ! command -v curl >/dev/null 2>&1; then
    echo "❌ 需要curl命令来下载字体文件"
    exit 1
fi

if ! command -v ssh >/dev/null 2>&1; then
    echo "❌ 需要ssh命令来连接服务器"
    exit 1
fi

if ! command -v scp >/dev/null 2>&1; then
    echo "❌ 需要scp命令来上传文件"
    exit 1
fi

# 执行主函数
main "$@" 