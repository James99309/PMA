#!/bin/bash
# 线上PDF乱码问题 - 快速字体检测脚本

echo "🔧 线上PDF字体快速检测"
echo "=========================="

# 检查系统信息
echo "📋 系统信息："
echo "操作系统: $(uname -s)"
echo "发行版: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"' || echo "未知")"
echo "架构: $(uname -m)"
echo ""

# 检查字体目录
echo "📁 字体目录检查："
for dir in "/usr/share/fonts/truetype" "/usr/share/fonts/opentype" "/usr/share/fonts/noto-cjk" "/usr/local/share/fonts"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir"
    fi
done
echo ""

# 检查具体字体文件
echo "📄 中文字体文件检查："
font_files=(
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
    "/usr/share/fonts/truetype/arphic/ukai.ttc"
    "/usr/share/fonts/truetype/arphic/uming.ttc"
)

found_count=0
for font in "${font_files[@]}"; do
    if [ -f "$font" ]; then
        echo "  ✅ $font"
        ((found_count++))
    else
        echo "  ❌ $font"
    fi
done

echo ""
echo "找到 $found_count 个中文字体文件"
echo ""

# 使用fc-list检查字体
echo "🔍 fc-list字体检查："
if command -v fc-list >/dev/null 2>&1; then
    cjk_fonts=$(fc-list | grep -i 'noto\|cjk\|chinese\|wqy\|arphic' | wc -l)
    if [ $cjk_fonts -gt 0 ]; then
        echo "  ✅ 找到 $cjk_fonts 个中文字体"
        echo "  前5个字体："
        fc-list | grep -i 'noto\|cjk\|chinese\|wqy\|arphic' | head -5 | sed 's/^/    /'
    else
        echo "  ❌ 未找到中文字体"
    fi
else
    echo "  ⚠️  fc-list命令不存在"
fi
echo ""

# 检查WeasyPrint
echo "📚 WeasyPrint检查："
if python3 -c "import weasyprint; print(f'✅ WeasyPrint版本: {weasyprint.__version__}')" 2>/dev/null; then
    echo "  WeasyPrint环境正常"
else
    echo "  ❌ WeasyPrint未安装或有问题"
fi
echo ""

# 生成建议
echo "🎯 修复建议："
if [ $found_count -eq 0 ]; then
    echo "❌ 需要立即安装中文字体！"
    echo ""
    echo "立即修复命令（Ubuntu/Debian）："
    echo "  sudo apt update"
    echo "  sudo apt install -y fonts-noto-cjk fonts-noto-cjk-extra"
    echo "  sudo apt install -y fonts-wqy-microhei fonts-wqy-zenhei"
    echo "  sudo fc-cache -fv"
    echo ""
    echo "立即修复命令（CentOS/RHEL）："
    echo "  sudo yum install -y google-noto-cjk-fonts"
    echo "  sudo yum install -y wqy-microhei-fonts wqy-zenhei-fonts"
    echo "  sudo fc-cache -fv"
    echo ""
    echo "修复后重启应用服务"
elif [ $found_count -lt 3 ]; then
    echo "⚠️  字体不完整，建议补充安装"
    echo "执行上述安装命令补充字体"
else
    echo "✅ 字体环境良好"
    echo "如果仍有PDF乱码，请检查："
    echo "1. WeasyPrint版本是否过旧"
    echo "2. 应用日志中的具体错误"
    echo "3. 字体配置是否正确"
fi

echo ""
echo "🔧 检测完成！" 