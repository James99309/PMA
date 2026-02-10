#!/bin/bash

# ============================================================
# PMA 项目统一启动脚本
# ============================================================
# 功能:
# - 自动检测当前数据库配置
# - 交互式选择文件存储方式（本地/NAS）
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
echo "   [2] 中国NAS存储（SP8D，外网Cloudflare隧道）"
echo "   [3] 新加坡NAS存储（OVS，内网直连）"
echo ""
read -p "请选择 [1-3，默认1]: " storage_choice
storage_choice=${storage_choice:-1}

# 验证输入
if [ "$storage_choice" != "1" ] && [ "$storage_choice" != "2" ] && [ "$storage_choice" != "3" ]; then
    print_error "❌ 无效的选择，使用默认选项 1（本地存储）"
    storage_choice=1
fi

echo ""

# ============================================================
# 3. 加载对应的存储配置
# ============================================================
STORAGE_TYPE=""
STORAGE_LOCATION=""
NAS_ENV_FILE=""

if [ "$storage_choice" = "1" ]; then
    STORAGE_TYPE="本地文件存储"
    STORAGE_LOCATION="本地文件系统"
    print_success "✅ 使用本地文件存储"
elif [ "$storage_choice" = "2" ]; then
    STORAGE_TYPE="中国NAS存储（SP8D）"
    STORAGE_LOCATION="中国NAS WebDAV（Cloudflare隧道）"
    NAS_ENV_FILE=".env.nas.cn"
elif [ "$storage_choice" = "3" ]; then
    STORAGE_TYPE="新加坡NAS存储（OVS）"
    STORAGE_LOCATION="新加坡NAS WebDAV（内网直连）"
    NAS_ENV_FILE=".env.nas"
fi

# NAS 存储通用加载逻辑
if [ ! -z "$NAS_ENV_FILE" ]; then
    # 检查NAS存储配置文件
    if [ ! -f "$NAS_ENV_FILE" ]; then
        print_error "❌ 错误: 未找到NAS存储配置文件 $NAS_ENV_FILE"
        print_warning "💡 请确保文件存在并包含正确的 WebDAV 配置"
        exit 1
    fi

    print_info "🔍 正在加载NAS存储配置（$NAS_ENV_FILE）..."

    # 加载NAS配置
    export $(cat "$NAS_ENV_FILE" | grep -v '^#' | grep -v '^$' | xargs)

    # 设置阻止Supabase自动加载
    export FORCE_LOCAL_STORAGE=true

    # 验证必要的环境变量（至少需要内网或外网地址之一）
    if [ -z "$SYNOLOGY_WEBDAV_EXTERNAL_URL" ] && [ -z "$SYNOLOGY_WEBDAV_INTERNAL_URL" ]; then
        print_error "❌ 错误: SYNOLOGY_WEBDAV_EXTERNAL_URL 和 SYNOLOGY_WEBDAV_INTERNAL_URL 均未设置"
        exit 1
    fi

    if [ -z "$SYNOLOGY_WEBDAV_USER" ]; then
        print_error "❌ 错误: SYNOLOGY_WEBDAV_USER 未设置"
        exit 1
    fi

    # 验证WebDAV地址可达
    print_info "🔍 正在验证NAS WebDAV连接..."
    NAS_VERIFIED=false

    # 优先验证外网地址
    if [ ! -z "$SYNOLOGY_WEBDAV_EXTERNAL_URL" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$SYNOLOGY_WEBDAV_EXTERNAL_URL" 2>/dev/null)
        if [ "$HTTP_CODE" != "000" ]; then
            print_success "✅ NAS WebDAV外网连接验证通过"
            NAS_VERIFIED=true
        else
            print_warning "⚠️  NAS WebDAV外网地址不可达: $SYNOLOGY_WEBDAV_EXTERNAL_URL"
        fi
    fi

    # 如果外网不可达，尝试内网
    if [ "$NAS_VERIFIED" = "false" ] && [ ! -z "$SYNOLOGY_WEBDAV_INTERNAL_URL" ]; then
        HTTP_CODE_INT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$SYNOLOGY_WEBDAV_INTERNAL_URL" 2>/dev/null)
        if [ "$HTTP_CODE_INT" != "000" ]; then
            print_success "✅ NAS WebDAV内网连接验证通过"
            NAS_VERIFIED=true
        else
            print_warning "⚠️  NAS WebDAV内网地址也不可达: $SYNOLOGY_WEBDAV_INTERNAL_URL"
        fi
    fi

    if [ "$NAS_VERIFIED" = "false" ]; then
        print_warning "⚠️  NAS WebDAV地址均不可达，启动后可能无法访问NAS文件"
    fi

    # 显示NAS连接信息
    echo ""
    print_success "✅ NAS存储配置已加载"
    if [ ! -z "$SYNOLOGY_WEBDAV_EXTERNAL_URL" ]; then
        echo "   外网地址: $SYNOLOGY_WEBDAV_EXTERNAL_URL"
    fi
    if [ ! -z "$SYNOLOGY_WEBDAV_INTERNAL_URL" ]; then
        echo "   内网地址: $SYNOLOGY_WEBDAV_INTERNAL_URL"
    fi
    echo "   WebDAV路径: $SYNOLOGY_WEBDAV_PATH"
    echo "   NAS存储启用: $NAS_STORAGE_ENABLED"
    echo "   FORCE_LOCAL_STORAGE: true"
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

if [ "$storage_choice" = "2" ] || [ "$storage_choice" = "3" ]; then
    if [ ! -z "$SYNOLOGY_WEBDAV_EXTERNAL_URL" ]; then
        echo "   WebDAV外网: $SYNOLOGY_WEBDAV_EXTERNAL_URL"
    fi
    if [ ! -z "$SYNOLOGY_WEBDAV_INTERNAL_URL" ]; then
        echo "   WebDAV内网: $SYNOLOGY_WEBDAV_INTERNAL_URL"
    fi
    echo "   路径: $SYNOLOGY_WEBDAV_PATH"
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
    print_warning "   - 当前使用中国NAS WebDAV存储（SP8D）"
    print_warning "   - 文件通过Cloudflare隧道外网传输"
    print_warning "   - 上传/下载速度取决于外网带宽"
    echo ""
elif [ "$storage_choice" = "3" ]; then
    print_warning "⚠️  重要提醒:"
    print_warning "   - 当前使用新加坡NAS WebDAV存储（OVS）"
    print_warning "   - 文件通过内网直连传输"
    print_warning "   - 需要在新加坡局域网内"
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
        echo "   - 使用中国NAS: 重新运行并选择选项 2"
        echo "   - 使用新加坡NAS: 重新运行并选择选项 3"
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
# NAS存储模式下环境变量已通过export设置，直接启动即可
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
