#!/bin/bash

# ============================================================
# PMA 项目统一启动脚本
# ============================================================
# 功能:
# - 自动检测当前数据库配置
# - 交互式选择文件存储方式（本地/云端）
# - 显示完整配置摘要
# - 提供确认步骤，避免误操作
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${CYAN}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# 清屏并显示标题
clear
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🚀 PMA 项目启动器${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    print_error "❌ 错误: 未找到 .env 配置文件"
    print_warning "💡 请先创建 .env 文件或从示例复制：cp .env.example .env"
    exit 1
fi

# ============================================================
# 1. 检测数据库配置
# ============================================================
print_info "📊 正在检测当前配置..."
echo ""

# 读取DATABASE_URL
DB_URL=$(grep "^DATABASE_URL=" .env | cut -d '=' -f2- | tr -d '"' | tr -d "'")

if [ -z "$DB_URL" ]; then
    print_error "❌ 错误: .env 中未找到 DATABASE_URL 配置"
    exit 1
fi

# 解析数据库信息
if [[ $DB_URL == *"localhost"* ]] || [[ $DB_URL == *"127.0.0.1"* ]]; then
    DB_TYPE="本地PostgreSQL"
    DB_HOST=$(echo "$DB_URL" | sed -n 's|.*@\([^:]*\).*|\1|p')
    DB_PORT=$(echo "$DB_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME=$(echo "$DB_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
    DB_USER=$(echo "$DB_URL" | sed -n 's|.*://\([^:@]*\).*|\1|p')
    DB_LOCATION="本地"
elif [[ $DB_URL == *"supabase.com"* ]]; then
    DB_TYPE="云端Supabase"
    DB_HOST=$(echo "$DB_URL" | sed -n 's|.*@\([^:]*\).*|\1|p')
    DB_PORT=$(echo "$DB_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
    DB_NAME=$(echo "$DB_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
    DB_LOCATION="云端"
else
    DB_TYPE="未知数据库"
    DB_HOST="未知"
    DB_LOCATION="未知"
fi

# 读取端口配置
PORT=$(grep "^PORT=" .env | cut -d '=' -f2- | tr -d ' ')
PORT=${PORT:-5011}

# 显示数据库配置
echo -e "${CYAN}📊 当前数据库配置:${NC}"
echo "   类型: $DB_TYPE"
echo "   主机: $DB_HOST"
if [ ! -z "$DB_PORT" ]; then
    echo "   端口: $DB_PORT"
fi
if [ ! -z "$DB_NAME" ]; then
    echo "   数据库: $DB_NAME"
fi
if [ ! -z "$DB_USER" ]; then
    echo "   用户: $DB_USER"
fi
echo ""

# ============================================================
# 2. 询问文件存储方式
# ============================================================
echo -e "${CYAN}📁 选择文件存储方式:${NC}"
echo "   [1] 本地文件存储（开发推荐）"
echo "   [2] 云端Supabase存储（生产环境测试）"
echo ""
read -p "请选择 [1-2，默认1]: " storage_choice
storage_choice=${storage_choice:-1}

# 验证输入
if [ "$storage_choice" != "1" ] && [ "$storage_choice" != "2" ]; then
    print_error "❌ 无效的选择，使用默认选项 1（本地存储）"
    storage_choice=1
fi

echo ""

# ============================================================
# 3. 加载对应的存储配置
# ============================================================
STORAGE_TYPE=""
STORAGE_LOCATION=""

if [ "$storage_choice" = "1" ]; then
    STORAGE_TYPE="本地文件存储"
    STORAGE_LOCATION="本地文件系统"
    print_success "✅ 使用本地文件存储"
else
    STORAGE_TYPE="云端Supabase存储"
    STORAGE_LOCATION="生产环境Supabase"

    # 检查云端存储配置文件
    if [ ! -f ".env.supabase.prod" ]; then
        print_error "❌ 错误: 未找到云端存储配置文件 .env.supabase.prod"
        print_warning "💡 请确保文件存在并包含正确的 Supabase 配置"
        exit 1
    fi

    print_info "🔍 正在加载云端存储配置..."

    # 加载Supabase配置
    export $(cat .env.supabase.prod | grep -v '^#' | grep -v '^$' | xargs)

    # 验证必要的环境变量
    if [ -z "$SUPABASE_URL" ]; then
        print_error "❌ 错误: SUPABASE_URL 未设置"
        exit 1
    fi

    if [ -z "$SUPABASE_KEY" ]; then
        print_error "❌ 错误: SUPABASE_KEY 未设置"
        exit 1
    fi

    # 显示存储桶信息
    echo ""
    print_success "✅ 云端存储配置验证通过"
    echo "   URL: ${SUPABASE_URL:0:40}..."

    if [ ! -z "$SUPABASE_BUCKET_INVOICE" ]; then
        echo "   发票存储桶: $SUPABASE_BUCKET_INVOICE"
    fi

    if [ ! -z "$SUPABASE_BUCKET_PRODUCT" ]; then
        echo "   产品存储桶: $SUPABASE_BUCKET_PRODUCT"
    fi

    if [ ! -z "$SUPABASE_BUCKET_RD_PRODUCT" ]; then
        echo "   研发产品存储桶: $SUPABASE_BUCKET_RD_PRODUCT"
    fi

    if [ ! -z "$FORCE_CLOUD_UPLOAD" ]; then
        echo "   强制云端上传: $FORCE_CLOUD_UPLOAD"
    fi
fi

echo ""

# ============================================================
# 4. 显示最终配置摘要
# ============================================================
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📋 最终启动配置${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "${CYAN}🗄️  数据库配置:${NC}"
echo "   类型: $DB_TYPE"
echo "   位置: $DB_LOCATION"
echo "   主机: $DB_HOST"
if [ ! -z "$DB_PORT" ]; then
    echo "   端口: $DB_PORT"
fi
if [ ! -z "$DB_NAME" ]; then
    echo "   数据库名: $DB_NAME"
fi
echo ""

echo -e "${CYAN}📁 文件存储配置:${NC}"
echo "   类型: $STORAGE_TYPE"
echo "   位置: $STORAGE_LOCATION"

if [ "$storage_choice" = "2" ]; then
    echo "   URL: ${SUPABASE_URL:0:40}..."
    if [ ! -z "$SUPABASE_BUCKET_INVOICE" ]; then
        echo "   存储桶: $SUPABASE_BUCKET_INVOICE, $SUPABASE_BUCKET_PRODUCT, $SUPABASE_BUCKET_RD_PRODUCT"
    fi
fi
echo ""

echo -e "${CYAN}🌐 应用信息:${NC}"
echo "   端口: $PORT"
echo "   访问地址: http://localhost:$PORT"
echo "   环境: 开发环境"
echo ""

echo -e "${BLUE}============================================================${NC}"
echo ""

# ============================================================
# 5. 显示警告（如果使用云端存储）
# ============================================================
if [ "$storage_choice" = "2" ]; then
    print_warning "⚠️  重要提醒:"
    print_warning "   - 当前使用生产环境 Supabase 存储"
    print_warning "   - 所有文件上传将直接保存到生产环境"
    print_warning "   - 请谨慎操作，避免上传测试数据到生产存储"
    print_warning "   - 下载功能测试将使用真实生产数据"
    echo ""
fi

# ============================================================
# 6. 用户确认
# ============================================================
read -p "是否继续启动应用？[Y/n]: " confirm
case $confirm in
    [nN]|[nN][oO])
        echo ""
        print_warning "🛑 启动已取消"
        echo ""
        print_info "💡 提示:"
        echo "   - 修改数据库配置: 编辑 .env 文件"
        echo "   - 使用本地存储: 重新运行并选择选项 1"
        echo "   - 使用云端存储: 重新运行并选择选项 2"
        echo ""
        exit 0
        ;;
    *)
        echo ""
        print_success "🎉 启动 PMA 应用..."
        echo ""
        ;;
esac

# ============================================================
# 7. 启动应用
# ============================================================

# 检查Python
if ! command -v python3 &> /dev/null; then
    print_error "❌ 错误: 未找到 python3"
    print_info "💡 请先安装 Python 3"
    exit 1
fi

# 检查run.py
if [ ! -f "run.py" ]; then
    print_error "❌ 错误: 未找到 run.py 启动文件"
    exit 1
fi

# 设置动态库搜索路径（WeasyPrint PDF生成所需）
# macOS Homebrew库路径
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}

# 启动Flask应用
python3 run.py

# ============================================================
# 8. 启动后清理（可选）
# ============================================================
# 应用退出后的处理
exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    print_success "✅ 应用已正常退出"
else
    print_error "❌ 应用异常退出（退出码: $exit_code）"
fi

exit $exit_code
