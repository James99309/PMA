#!/bin/bash

# PMA本地安全启动脚本
# 自动处理端口冲突、关闭旧实例、确保本地数据库连接

echo "🔒 PMA本地安全启动脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查安全锁定文件
check_security_lock() {
    if [ ! -f ".cloud_db_locked" ]; then
        echo -e "${YELLOW}⚠️  安全锁定文件不存在，正在创建...${NC}"
        python3 -c "
import os
from datetime import datetime
with open('.cloud_db_locked', 'w') as f:
    f.write('# 云端数据库安全锁定\\n')
    f.write(f'# 创建时间: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}\\n')
    f.write('# 此文件存在时，系统将拒绝所有云端数据库连接\\n')
    f.write('CLOUD_DB_ACCESS=DISABLED\\n')
    f.write('LOCAL_ONLY_MODE=ENABLED\\n')
"
        echo -e "${GREEN}✅ 安全锁定文件已创建${NC}"
    else
        echo -e "${GREEN}✅ 安全锁定文件已存在${NC}"
    fi
}

# 关闭所有PMA相关进程
kill_existing_processes() {
    echo -e "${BLUE}🔍 检查现有PMA进程...${NC}"
    
    # 查找所有Python进程中包含run.py或PMA的
    PIDS=$(ps aux | grep -E "(run\.py|PMA|flask.*app)" | grep -v grep | awk '{print $2}')
    
    if [ ! -z "$PIDS" ]; then
        echo -e "${YELLOW}⚠️  发现现有PMA进程，正在关闭...${NC}"
        for PID in $PIDS; do
            echo "  关闭进程 PID: $PID"
            kill -TERM $PID 2>/dev/null || kill -KILL $PID 2>/dev/null
        done
        sleep 2
        echo -e "${GREEN}✅ 现有进程已关闭${NC}"
    else
        echo -e "${GREEN}✅ 没有发现现有PMA进程${NC}"
    fi
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # 端口被占用
    else
        return 0  # 端口可用
    fi
}

# 查找可用端口
find_available_port() {
    local start_port=5000
    local max_port=5020
    
    for port in $(seq $start_port $max_port); do
        if check_port $port; then
            echo $port
            return 0
        fi
    done
    
    # 如果5000-5020都被占用，尝试更高的端口
    for port in $(seq 8000 8020); do
        if check_port $port; then
            echo $port
            return 0
        fi
    done
    
    echo "5000"  # 默认返回5000
    return 1
}

# 检查本地数据库连接
check_local_database() {
    echo -e "${BLUE}📊 检查本地数据库连接...${NC}"
    
    # 检查PostgreSQL服务是否运行
    if ! pgrep -x "postgres" > /dev/null; then
        echo -e "${RED}❌ PostgreSQL服务未运行${NC}"
        echo -e "${YELLOW}💡 请先启动PostgreSQL服务：${NC}"
        echo "   brew services start postgresql"
        echo "   或者: pg_ctl -D /usr/local/var/postgres start"
        return 1
    fi
    
    # 测试数据库连接
    python3 -c "
import psycopg2
import os
try:
    # 尝试连接本地数据库
    conn = psycopg2.connect(
        host='localhost',
        database='pma_local',
        user=os.getenv('USER', 'postgres'),
        password='',
        port=5432
    )
    conn.close()
    print('✅ 本地数据库连接正常')
    exit(0)
except Exception as e:
    print(f'❌ 本地数据库连接失败: {e}')
    exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 本地数据库连接正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 本地数据库连接失败${NC}"
        echo -e "${YELLOW}💡 请检查：${NC}"
        echo "   1. PostgreSQL服务是否运行"
        echo "   2. 数据库'pma_local'是否存在"
        echo "   3. 数据库权限是否正确"
        return 1
    fi
}

# 设置环境变量
setup_environment() {
    echo -e "${BLUE}🔧 设置本地环境变量...${NC}"
    
    # 创建.env.local文件
    cat > .env.local << EOF
# PMA本地开发环境配置
# 强制使用本地数据库
DATABASE_URL=postgresql://localhost/pma_local
FLASK_ENV=development
FLASK_DEBUG=1
LOCAL_ONLY_MODE=1
CLOUD_DB_ACCESS=DISABLED

# 清除所有云端数据库变量
CLOUD_DATABASE_URL=
RENDER_DATABASE_URL=
HEROKU_POSTGRESQL_URL=
EOF
    
    # 导出环境变量
    export DATABASE_URL="postgresql://localhost/pma_local"
    export FLASK_ENV="development"
    export FLASK_DEBUG="1"
    export LOCAL_ONLY_MODE="1"
    export CLOUD_DB_ACCESS="DISABLED"
    
    echo -e "${GREEN}✅ 环境变量设置完成${NC}"
}

# 主启动函数
main() {
    echo -e "${BLUE}🚀 开始PMA本地安全启动流程...${NC}"
    
    # 1. 检查安全锁定
    check_security_lock
    
    # 2. 关闭现有进程
    kill_existing_processes
    
    # 3. 检查本地数据库
    if ! check_local_database; then
        echo -e "${RED}❌ 本地数据库检查失败，无法启动${NC}"
        exit 1
    fi
    
    # 4. 设置环境变量
    setup_environment
    
    # 5. 查找可用端口
    echo -e "${BLUE}🔍 查找可用端口...${NC}"
    AVAILABLE_PORT=$(find_available_port)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 找到可用端口: $AVAILABLE_PORT${NC}"
    else
        echo -e "${YELLOW}⚠️  使用默认端口: $AVAILABLE_PORT (可能有冲突)${NC}"
    fi
    
    # 6. 启动应用
    echo -e "${GREEN}🚀 启动PMA本地安全版...${NC}"
    echo -e "${BLUE}📍 访问地址: http://localhost:$AVAILABLE_PORT${NC}"
    echo -e "${YELLOW}💡 按 Ctrl+C 停止服务${NC}"
    echo "================================"
    
    # 启动应用
    python3 run.py --port $AVAILABLE_PORT
}

# 捕获中断信号
trap 'echo -e "\n${YELLOW}🛑 正在停止PMA服务...${NC}"; exit 0' INT TERM

# 执行主函数
main "$@" 