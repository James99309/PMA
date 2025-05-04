#!/bin/bash
# 用于将本地SQLite数据迁移到Render云端PostgreSQL数据库
# 简化SSL配置并添加更安全的错误处理

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

echo -e "${GREEN}======== Render PostgreSQL迁移工具 ========${NC}"

# 检查Python环境和依赖
echo -e "${GREEN}检查Python环境和依赖...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python 3${NC}"
    echo "请安装Python 3，然后再次运行此脚本"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到pip3，尝试安装必要的依赖...${NC}"
    python3 -m ensurepip --upgrade || {
        echo -e "${RED}错误: 无法安装pip${NC}"
        echo "请手动安装pip，然后再次运行此脚本"
        exit 1
    }
fi

# 安装必要的依赖
echo -e "${GREEN}安装必要的依赖...${NC}"
pip3 install --quiet sqlalchemy psycopg2-binary pandas requests || {
    echo -e "${RED}错误: 安装依赖失败${NC}"
    echo "请手动执行: pip3 install sqlalchemy psycopg2-binary pandas requests"
    exit 1
}

# 检查环境变量
if [ -z "$RENDER_DB_URL" ]; then
    echo -e "${YELLOW}请提供Render PostgreSQL数据库URL${NC}"
    read -p "输入数据库URL (格式: postgresql://user:pass@host:port/database): " RENDER_DB_URL
    
    # 简单验证URL格式
    if [[ ! $RENDER_DB_URL =~ ^postgresql://[^:]+:[^@]+@[^:]+:[0-9]+/[^?]+ ]]; then
        echo -e "${RED}错误: 不是有效的PostgreSQL URL格式${NC}"
        echo "正确格式示例: postgresql://username:password@host:port/database"
        exit 1
    fi
fi

# 检查SQLite数据库路径
if [ -z "$SQLITE_DB" ]; then
    # 查找当前目录下的SQLite数据库
    db_files=$(find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" | head -n 5)
    
    if [ -z "$db_files" ]; then
        echo -e "${YELLOW}在当前目录未找到SQLite数据库文件${NC}"
        read -p "输入SQLite数据库路径: " SQLITE_DB
    else
        echo "发现以下SQLite数据库文件:"
        echo "$db_files"
        read -p "选择要使用的SQLite数据库 (输入完整路径): " SQLITE_DB
    fi
fi

# 确保SQLite数据库文件存在
if [ ! -f "$SQLITE_DB" ]; then
    echo -e "${RED}错误: 找不到SQLite数据库文件: $SQLITE_DB${NC}"
    exit 1
fi

# 确保所需的目录存在
mkdir -p ./ssl_certs
mkdir -p ./backups

# 替换postgres://为postgresql://
if [[ $RENDER_DB_URL == postgres://* ]]; then
    RENDER_DB_URL=${RENDER_DB_URL/postgres:\/\//postgresql:\/\/}
    echo -e "${YELLOW}已将DATABASE_URL从postgres://更改为postgresql://${NC}"
fi

# 添加SSL参数
if [[ $RENDER_DB_URL != *"ssl="* && $RENDER_DB_URL != *"sslmode="* ]]; then
    # 添加SSL参数
    RENDER_DB_URL="${RENDER_DB_URL}?sslmode=require"
    echo -e "${YELLOW}已添加SSL参数: ?sslmode=require${NC}"
fi

# 测试SSL连接
echo -e "${GREEN}测试数据库SSL连接...${NC}"
python3 db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require

# 检查连接测试是否成功
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}简单SSL连接测试失败，尝试具体的SSL模式...${NC}"
    python3 db_migration_ssl.py --db-url "$RENDER_DB_URL"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}所有SSL连接测试都失败，请检查网络和凭据${NC}"
        echo "如果您确定凭据正确，可能需要联系Render支持"
        exit 1
    fi
fi

# 备份本地数据
echo -e "${GREEN}备份本地SQLite数据库...${NC}"
backup_file="./backups/sqlite_backup_$(date +%Y%m%d_%H%M%S).db"
cp "$SQLITE_DB" "$backup_file"
echo "本地数据已备份到: $backup_file"

# 导出SQLite数据
echo -e "${GREEN}正在导出SQLite数据...${NC}"
python3 export_sqlite_data.py --sqlite-db "$SQLITE_DB" --output-dir ./backups

# 检查导出结果
if [ $? -ne 0 ]; then
    echo -e "${RED}SQLite数据导出失败${NC}"
    exit 1
fi

# 迁移数据到Render PostgreSQL
echo -e "${GREEN}开始迁移数据到Render PostgreSQL...${NC}"
python3 db_migration.py --sqlite-db "$SQLITE_DB" --db-url "$RENDER_DB_URL"

# 检查迁移结果
if [ $? -ne 0 ]; then
    echo -e "${RED}数据迁移失败${NC}"
    echo "请检查日志获取详细错误信息"
    exit 1
fi

# 创建管理员用户
echo -e "${GREEN}确保管理员账户存在...${NC}"
python3 create_admin_user.py --db-url "$RENDER_DB_URL"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}数据迁移完成!${NC}"
echo "Render数据库URL: ${RENDER_DB_URL//:\/\/[^:]*:[^@]*@/:\/\/username:password@}"
echo -e "${YELLOW}重要提示: 请更新您的应用程序配置，使用新的数据库URL，确保添加SSL参数${NC}"
echo -e "${GREEN}======================================${NC}" 
# 用于将本地SQLite数据迁移到Render云端PostgreSQL数据库
# 简化SSL配置并添加更安全的错误处理

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

echo -e "${GREEN}======== Render PostgreSQL迁移工具 ========${NC}"

# 检查Python环境和依赖
echo -e "${GREEN}检查Python环境和依赖...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python 3${NC}"
    echo "请安装Python 3，然后再次运行此脚本"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到pip3，尝试安装必要的依赖...${NC}"
    python3 -m ensurepip --upgrade || {
        echo -e "${RED}错误: 无法安装pip${NC}"
        echo "请手动安装pip，然后再次运行此脚本"
        exit 1
    }
fi

# 安装必要的依赖
echo -e "${GREEN}安装必要的依赖...${NC}"
pip3 install --quiet sqlalchemy psycopg2-binary pandas requests || {
    echo -e "${RED}错误: 安装依赖失败${NC}"
    echo "请手动执行: pip3 install sqlalchemy psycopg2-binary pandas requests"
    exit 1
}

# 检查环境变量
if [ -z "$RENDER_DB_URL" ]; then
    echo -e "${YELLOW}请提供Render PostgreSQL数据库URL${NC}"
    read -p "输入数据库URL (格式: postgresql://user:pass@host:port/database): " RENDER_DB_URL
    
    # 简单验证URL格式
    if [[ ! $RENDER_DB_URL =~ ^postgresql://[^:]+:[^@]+@[^:]+:[0-9]+/[^?]+ ]]; then
        echo -e "${RED}错误: 不是有效的PostgreSQL URL格式${NC}"
        echo "正确格式示例: postgresql://username:password@host:port/database"
        exit 1
    fi
fi

# 检查SQLite数据库路径
if [ -z "$SQLITE_DB" ]; then
    # 查找当前目录下的SQLite数据库
    db_files=$(find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" | head -n 5)
    
    if [ -z "$db_files" ]; then
        echo -e "${YELLOW}在当前目录未找到SQLite数据库文件${NC}"
        read -p "输入SQLite数据库路径: " SQLITE_DB
    else
        echo "发现以下SQLite数据库文件:"
        echo "$db_files"
        read -p "选择要使用的SQLite数据库 (输入完整路径): " SQLITE_DB
    fi
fi

# 确保SQLite数据库文件存在
if [ ! -f "$SQLITE_DB" ]; then
    echo -e "${RED}错误: 找不到SQLite数据库文件: $SQLITE_DB${NC}"
    exit 1
fi

# 确保所需的目录存在
mkdir -p ./ssl_certs
mkdir -p ./backups

# 替换postgres://为postgresql://
if [[ $RENDER_DB_URL == postgres://* ]]; then
    RENDER_DB_URL=${RENDER_DB_URL/postgres:\/\//postgresql:\/\/}
    echo -e "${YELLOW}已将DATABASE_URL从postgres://更改为postgresql://${NC}"
fi

# 添加SSL参数
if [[ $RENDER_DB_URL != *"ssl="* && $RENDER_DB_URL != *"sslmode="* ]]; then
    # 添加SSL参数
    RENDER_DB_URL="${RENDER_DB_URL}?sslmode=require"
    echo -e "${YELLOW}已添加SSL参数: ?sslmode=require${NC}"
fi

# 测试SSL连接
echo -e "${GREEN}测试数据库SSL连接...${NC}"
python3 db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require

# 检查连接测试是否成功
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}简单SSL连接测试失败，尝试具体的SSL模式...${NC}"
    python3 db_migration_ssl.py --db-url "$RENDER_DB_URL"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}所有SSL连接测试都失败，请检查网络和凭据${NC}"
        echo "如果您确定凭据正确，可能需要联系Render支持"
        exit 1
    fi
fi

# 备份本地数据
echo -e "${GREEN}备份本地SQLite数据库...${NC}"
backup_file="./backups/sqlite_backup_$(date +%Y%m%d_%H%M%S).db"
cp "$SQLITE_DB" "$backup_file"
echo "本地数据已备份到: $backup_file"

# 导出SQLite数据
echo -e "${GREEN}正在导出SQLite数据...${NC}"
python3 export_sqlite_data.py --sqlite-db "$SQLITE_DB" --output-dir ./backups

# 检查导出结果
if [ $? -ne 0 ]; then
    echo -e "${RED}SQLite数据导出失败${NC}"
    exit 1
fi

# 迁移数据到Render PostgreSQL
echo -e "${GREEN}开始迁移数据到Render PostgreSQL...${NC}"
python3 db_migration.py --sqlite-db "$SQLITE_DB" --db-url "$RENDER_DB_URL"

# 检查迁移结果
if [ $? -ne 0 ]; then
    echo -e "${RED}数据迁移失败${NC}"
    echo "请检查日志获取详细错误信息"
    exit 1
fi

# 创建管理员用户
echo -e "${GREEN}确保管理员账户存在...${NC}"
python3 create_admin_user.py --db-url "$RENDER_DB_URL"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}数据迁移完成!${NC}"
echo "Render数据库URL: ${RENDER_DB_URL//:\/\/[^:]*:[^@]*@/:\/\/username:password@}"
echo -e "${YELLOW}重要提示: 请更新您的应用程序配置，使用新的数据库URL，确保添加SSL参数${NC}"
echo -e "${GREEN}======================================${NC}" 
 
 

# 添加SSL参数
if [[ $RENDER_DB_URL != *"ssl="* && $RENDER_DB_URL != *"sslmode="* ]]; then
    # 添加SSL参数
    RENDER_DB_URL="${RENDER_DB_URL}?sslmode=require"
    echo -e "${YELLOW}已添加SSL参数: ?sslmode=require${NC}"
fi

# 测试SSL连接
echo -e "${GREEN}测试数据库SSL连接...${NC}"
python3 db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require

# 检查连接测试是否成功
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}简单SSL连接测试失败，尝试具体的SSL模式...${NC}"
    python3 db_migration_ssl.py --db-url "$RENDER_DB_URL"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}所有SSL连接测试都失败，请检查网络和凭据${NC}"
        echo "如果您确定凭据正确，可能需要联系Render支持"
        exit 1
    fi
fi

# 备份本地数据
echo -e "${GREEN}备份本地SQLite数据库...${NC}"
backup_file="./backups/sqlite_backup_$(date +%Y%m%d_%H%M%S).db"
cp "$SQLITE_DB" "$backup_file"
echo "本地数据已备份到: $backup_file"

# 导出SQLite数据
echo -e "${GREEN}正在导出SQLite数据...${NC}"
python3 export_sqlite_data.py --sqlite-db "$SQLITE_DB" --output-dir ./backups

# 检查导出结果
if [ $? -ne 0 ]; then
    echo -e "${RED}SQLite数据导出失败${NC}"
    exit 1
fi

# 迁移数据到Render PostgreSQL
echo -e "${GREEN}开始迁移数据到Render PostgreSQL...${NC}"
python3 db_migration.py --sqlite-db "$SQLITE_DB" --db-url "$RENDER_DB_URL"

# 检查迁移结果
if [ $? -ne 0 ]; then
    echo -e "${RED}数据迁移失败${NC}"
    echo "请检查日志获取详细错误信息"
    exit 1
fi

# 创建管理员用户
echo -e "${GREEN}确保管理员账户存在...${NC}"
python3 create_admin_user.py --db-url "$RENDER_DB_URL"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}数据迁移完成!${NC}"
echo "Render数据库URL: ${RENDER_DB_URL//:\/\/[^:]*:[^@]*@/:\/\/username:password@}"
echo -e "${YELLOW}重要提示: 请更新您的应用程序配置，使用新的数据库URL，确保添加SSL参数${NC}"
echo -e "${GREEN}======================================${NC}" 
# 用于将本地SQLite数据迁移到Render云端PostgreSQL数据库
# 简化SSL配置并添加更安全的错误处理

# 设置颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

echo -e "${GREEN}======== Render PostgreSQL迁移工具 ========${NC}"

# 检查Python环境和依赖
echo -e "${GREEN}检查Python环境和依赖...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python 3${NC}"
    echo "请安装Python 3，然后再次运行此脚本"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到pip3，尝试安装必要的依赖...${NC}"
    python3 -m ensurepip --upgrade || {
        echo -e "${RED}错误: 无法安装pip${NC}"
        echo "请手动安装pip，然后再次运行此脚本"
        exit 1
    }
fi

# 安装必要的依赖
echo -e "${GREEN}安装必要的依赖...${NC}"
pip3 install --quiet sqlalchemy psycopg2-binary pandas requests || {
    echo -e "${RED}错误: 安装依赖失败${NC}"
    echo "请手动执行: pip3 install sqlalchemy psycopg2-binary pandas requests"
    exit 1
}

# 检查环境变量
if [ -z "$RENDER_DB_URL" ]; then
    echo -e "${YELLOW}请提供Render PostgreSQL数据库URL${NC}"
    read -p "输入数据库URL (格式: postgresql://user:pass@host:port/database): " RENDER_DB_URL
    
    # 简单验证URL格式
    if [[ ! $RENDER_DB_URL =~ ^postgresql://[^:]+:[^@]+@[^:]+:[0-9]+/[^?]+ ]]; then
        echo -e "${RED}错误: 不是有效的PostgreSQL URL格式${NC}"
        echo "正确格式示例: postgresql://username:password@host:port/database"
        exit 1
    fi
fi

# 检查SQLite数据库路径
if [ -z "$SQLITE_DB" ]; then
    # 查找当前目录下的SQLite数据库
    db_files=$(find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" | head -n 5)
    
    if [ -z "$db_files" ]; then
        echo -e "${YELLOW}在当前目录未找到SQLite数据库文件${NC}"
        read -p "输入SQLite数据库路径: " SQLITE_DB
    else
        echo "发现以下SQLite数据库文件:"
        echo "$db_files"
        read -p "选择要使用的SQLite数据库 (输入完整路径): " SQLITE_DB
    fi
fi

# 确保SQLite数据库文件存在
if [ ! -f "$SQLITE_DB" ]; then
    echo -e "${RED}错误: 找不到SQLite数据库文件: $SQLITE_DB${NC}"
    exit 1
fi

# 确保所需的目录存在
mkdir -p ./ssl_certs
mkdir -p ./backups

# 替换postgres://为postgresql://
if [[ $RENDER_DB_URL == postgres://* ]]; then
    RENDER_DB_URL=${RENDER_DB_URL/postgres:\/\//postgresql:\/\/}
    echo -e "${YELLOW}已将DATABASE_URL从postgres://更改为postgresql://${NC}"
fi

# 添加SSL参数
if [[ $RENDER_DB_URL != *"ssl="* && $RENDER_DB_URL != *"sslmode="* ]]; then
    # 添加SSL参数
    RENDER_DB_URL="${RENDER_DB_URL}?sslmode=require"
    echo -e "${YELLOW}已添加SSL参数: ?sslmode=require${NC}"
fi

# 测试SSL连接
echo -e "${GREEN}测试数据库SSL连接...${NC}"
python3 db_migration_ssl.py --db-url "$RENDER_DB_URL" --ssl-mode require

# 检查连接测试是否成功
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}简单SSL连接测试失败，尝试具体的SSL模式...${NC}"
    python3 db_migration_ssl.py --db-url "$RENDER_DB_URL"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}所有SSL连接测试都失败，请检查网络和凭据${NC}"
        echo "如果您确定凭据正确，可能需要联系Render支持"
        exit 1
    fi
fi

# 备份本地数据
echo -e "${GREEN}备份本地SQLite数据库...${NC}"
backup_file="./backups/sqlite_backup_$(date +%Y%m%d_%H%M%S).db"
cp "$SQLITE_DB" "$backup_file"
echo "本地数据已备份到: $backup_file"

# 导出SQLite数据
echo -e "${GREEN}正在导出SQLite数据...${NC}"
python3 export_sqlite_data.py --sqlite-db "$SQLITE_DB" --output-dir ./backups

# 检查导出结果
if [ $? -ne 0 ]; then
    echo -e "${RED}SQLite数据导出失败${NC}"
    exit 1
fi

# 迁移数据到Render PostgreSQL
echo -e "${GREEN}开始迁移数据到Render PostgreSQL...${NC}"
python3 db_migration.py --sqlite-db "$SQLITE_DB" --db-url "$RENDER_DB_URL"

# 检查迁移结果
if [ $? -ne 0 ]; then
    echo -e "${RED}数据迁移失败${NC}"
    echo "请检查日志获取详细错误信息"
    exit 1
fi

# 创建管理员用户
echo -e "${GREEN}确保管理员账户存在...${NC}"
python3 create_admin_user.py --db-url "$RENDER_DB_URL"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}数据迁移完成!${NC}"
echo "Render数据库URL: ${RENDER_DB_URL//:\/\/[^:]*:[^@]*@/:\/\/username:password@}"
echo -e "${YELLOW}重要提示: 请更新您的应用程序配置，使用新的数据库URL，确保添加SSL参数${NC}"
echo -e "${GREEN}======================================${NC}" 
 
 