#!/bin/bash
# Render PostgreSQL迁移一站式脚本
# 用于将本地SQLite数据库迁移到Render PostgreSQL

# 定义颜色代码
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 输出格式化函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否有必要的Python包
check_dependencies() {
    log_info "检查依赖项..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请安装后再试"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装必要的Python包..."
    pip install sqlalchemy psycopg2-binary pandas python-dotenv
    
    log_success "依赖项检查完成"
}

# 导出SQLite数据库
export_sqlite_data() {
    log_info "开始导出SQLite数据库..."
    
    # 检查SQLite数据库文件
    if [ ! -f "app.db" ]; then
        log_error "未找到app.db文件，请确保它存在于当前目录"
        exit 1
    fi
    
    # 运行导出脚本
    python3 export_sqlite_data.py --db app.db --output db_export_full.json
    
    if [ $? -eq 0 ]; then
        log_success "SQLite数据库导出成功"
    else
        log_error "SQLite数据库导出失败"
        exit 1
    fi
}

# 修复数据库连接URL
fix_database_url() {
    log_info "修复Render数据库连接URL..."
    
    # 检查是否提供了数据库URL
    if [ -z "$RENDER_DB_URL" ]; then
        log_error "未设置RENDER_DB_URL环境变量，请提供Render数据库URL"
        read -p "请输入Render数据库URL: " RENDER_DB_URL
        export RENDER_DB_URL="$RENDER_DB_URL"
    fi
    
    # 运行URL修复工具
    python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --test
    
    if [ $? -eq 0 ]; then
        log_success "数据库连接测试成功"
    else
        log_warning "数据库连接测试失败，尝试修复问题..."
        # 运行更新配置文件的操作
        python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --set-env --update-config
        
        if [ $? -eq 0 ]; then
            log_success "数据库连接已修复并更新配置"
        else
            log_error "无法修复数据库连接问题"
            exit 1
        fi
    fi
}

# 迁移数据到Render
migrate_to_render() {
    log_info "开始迁移数据到Render PostgreSQL..."
    
    # 检查导出文件是否存在
    if [ ! -f "db_export_full.json" ]; then
        log_error "未找到db_export_full.json文件，请先导出SQLite数据"
        exit 1
    fi
    
    # 确保RENDER_DB_URL已经过修复
    if [ -z "$DATABASE_URL" ]; then
        export DATABASE_URL="$RENDER_DB_URL"
    fi
    
    # 运行迁移脚本
    python3 db_migration.py --source db_export_full.json --target "$DATABASE_URL"
    
    if [ $? -eq 0 ]; then
        log_success "数据已成功迁移到Render PostgreSQL!"
    else
        log_error "数据迁移失败"
        exit 1
    fi
}

# 检查迁移结果
verify_migration() {
    log_info "验证迁移结果..."
    
    # 使用一个简单的查询脚本检查数据
    cat > verify_migration.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from sqlalchemy import create_engine, text

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("错误：未设置DATABASE_URL环境变量")
        return 1
        
    print(f"连接到数据库...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 检查用户表
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"用户数量: {user_count}")
            
            # 检查部门表
            result = conn.execute(text("SELECT COUNT(*) FROM departments"))
            dept_count = result.fetchone()[0]
            print(f"部门数量: {dept_count}")
            
            # 获取所有表
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ))
            tables = [row[0] for row in result]
            print(f"数据库包含 {len(tables)} 个表: {', '.join(tables[:5])}...")
            
        print("迁移验证成功!")
        return 0
    except Exception as e:
        print(f"验证失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x verify_migration.py
    python3 verify_migration.py
    
    if [ $? -eq 0 ]; then
        log_success "迁移验证成功!"
    else
        log_warning "迁移验证失败，请手动检查数据库"
    fi
}

# 创建必要的脚本文件
create_necessary_files() {
    log_info "创建必要的工具脚本..."
    
    # 如果导出脚本不存在，创建它
    if [ ! -f "export_sqlite_data.py" ]; then
        cat > export_sqlite_data.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
EOF
        chmod +x export_sqlite_data.py
    fi
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}Render PostgreSQL迁移一站式脚本${NC}"
    echo "这个脚本将帮助您将本地SQLite数据库迁移到Render的PostgreSQL数据库"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "可用命令:"
    echo "  all         - 执行完整的迁移流程"
    echo "  setup       - 安装依赖并创建必要的脚本"
    echo "  export      - 导出SQLite数据库"
    echo "  fix-url     - 修复数据库URL"
    echo "  migrate     - 迁移数据到Render"
    echo "  verify      - 验证迁移结果"
    echo "  help        - 显示此帮助信息"
    echo
    echo "示例:"
    echo "  RENDER_DB_URL=\"您的Render数据库URL\" $0 all"
    echo
}

# 主函数
main() {
    # 获取命令
    command=${1:-"help"}
    
    case $command in
        all)
            check_dependencies
            create_necessary_files
            export_sqlite_data
            fix_database_url
            migrate_to_render
            verify_migration
            log_success "完整迁移流程完成!"
            ;;
        setup)
            check_dependencies
            create_necessary_files
            log_success "安装依赖和创建脚本完成!"
            ;;
        export)
            check_dependencies
            export_sqlite_data
            log_success "导出SQLite数据库完成!"
            ;;
        fix-url)
            check_dependencies
            fix_database_url
            log_success "修复数据库URL完成!"
            ;;
        migrate)
            check_dependencies
            migrate_to_render
            log_success "迁移数据到Render完成!"
            ;;
        verify)
            check_dependencies
            verify_migration
            log_success "验证迁移结果完成!"
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# 执行主函数
main "$@" 
# Render PostgreSQL迁移一站式脚本
# 用于将本地SQLite数据库迁移到Render PostgreSQL

# 定义颜色代码
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 输出格式化函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否有必要的Python包
check_dependencies() {
    log_info "检查依赖项..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请安装后再试"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装必要的Python包..."
    pip install sqlalchemy psycopg2-binary pandas python-dotenv
    
    log_success "依赖项检查完成"
}

# 导出SQLite数据库
export_sqlite_data() {
    log_info "开始导出SQLite数据库..."
    
    # 检查SQLite数据库文件
    if [ ! -f "app.db" ]; then
        log_error "未找到app.db文件，请确保它存在于当前目录"
        exit 1
    fi
    
    # 运行导出脚本
    python3 export_sqlite_data.py --db app.db --output db_export_full.json
    
    if [ $? -eq 0 ]; then
        log_success "SQLite数据库导出成功"
    else
        log_error "SQLite数据库导出失败"
        exit 1
    fi
}

# 修复数据库连接URL
fix_database_url() {
    log_info "修复Render数据库连接URL..."
    
    # 检查是否提供了数据库URL
    if [ -z "$RENDER_DB_URL" ]; then
        log_error "未设置RENDER_DB_URL环境变量，请提供Render数据库URL"
        read -p "请输入Render数据库URL: " RENDER_DB_URL
        export RENDER_DB_URL="$RENDER_DB_URL"
    fi
    
    # 运行URL修复工具
    python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --test
    
    if [ $? -eq 0 ]; then
        log_success "数据库连接测试成功"
    else
        log_warning "数据库连接测试失败，尝试修复问题..."
        # 运行更新配置文件的操作
        python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --set-env --update-config
        
        if [ $? -eq 0 ]; then
            log_success "数据库连接已修复并更新配置"
        else
            log_error "无法修复数据库连接问题"
            exit 1
        fi
    fi
}

# 迁移数据到Render
migrate_to_render() {
    log_info "开始迁移数据到Render PostgreSQL..."
    
    # 检查导出文件是否存在
    if [ ! -f "db_export_full.json" ]; then
        log_error "未找到db_export_full.json文件，请先导出SQLite数据"
        exit 1
    fi
    
    # 确保RENDER_DB_URL已经过修复
    if [ -z "$DATABASE_URL" ]; then
        export DATABASE_URL="$RENDER_DB_URL"
    fi
    
    # 运行迁移脚本
    python3 db_migration.py --source db_export_full.json --target "$DATABASE_URL"
    
    if [ $? -eq 0 ]; then
        log_success "数据已成功迁移到Render PostgreSQL!"
    else
        log_error "数据迁移失败"
        exit 1
    fi
}

# 检查迁移结果
verify_migration() {
    log_info "验证迁移结果..."
    
    # 使用一个简单的查询脚本检查数据
    cat > verify_migration.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from sqlalchemy import create_engine, text

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("错误：未设置DATABASE_URL环境变量")
        return 1
        
    print(f"连接到数据库...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 检查用户表
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"用户数量: {user_count}")
            
            # 检查部门表
            result = conn.execute(text("SELECT COUNT(*) FROM departments"))
            dept_count = result.fetchone()[0]
            print(f"部门数量: {dept_count}")
            
            # 获取所有表
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ))
            tables = [row[0] for row in result]
            print(f"数据库包含 {len(tables)} 个表: {', '.join(tables[:5])}...")
            
        print("迁移验证成功!")
        return 0
    except Exception as e:
        print(f"验证失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x verify_migration.py
    python3 verify_migration.py
    
    if [ $? -eq 0 ]; then
        log_success "迁移验证成功!"
    else
        log_warning "迁移验证失败，请手动检查数据库"
    fi
}

# 创建必要的脚本文件
create_necessary_files() {
    log_info "创建必要的工具脚本..."
    
    # 如果导出脚本不存在，创建它
    if [ ! -f "export_sqlite_data.py" ]; then
        cat > export_sqlite_data.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
EOF
        chmod +x export_sqlite_data.py
    fi
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}Render PostgreSQL迁移一站式脚本${NC}"
    echo "这个脚本将帮助您将本地SQLite数据库迁移到Render的PostgreSQL数据库"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "可用命令:"
    echo "  all         - 执行完整的迁移流程"
    echo "  setup       - 安装依赖并创建必要的脚本"
    echo "  export      - 导出SQLite数据库"
    echo "  fix-url     - 修复数据库URL"
    echo "  migrate     - 迁移数据到Render"
    echo "  verify      - 验证迁移结果"
    echo "  help        - 显示此帮助信息"
    echo
    echo "示例:"
    echo "  RENDER_DB_URL=\"您的Render数据库URL\" $0 all"
    echo
}

# 主函数
main() {
    # 获取命令
    command=${1:-"help"}
    
    case $command in
        all)
            check_dependencies
            create_necessary_files
            export_sqlite_data
            fix_database_url
            migrate_to_render
            verify_migration
            log_success "完整迁移流程完成!"
            ;;
        setup)
            check_dependencies
            create_necessary_files
            log_success "安装依赖和创建脚本完成!"
            ;;
        export)
            check_dependencies
            export_sqlite_data
            log_success "导出SQLite数据库完成!"
            ;;
        fix-url)
            check_dependencies
            fix_database_url
            log_success "修复数据库URL完成!"
            ;;
        migrate)
            check_dependencies
            migrate_to_render
            log_success "迁移数据到Render完成!"
            ;;
        verify)
            check_dependencies
            verify_migration
            log_success "验证迁移结果完成!"
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# 执行主函数
main "$@" 
 
 
# Render PostgreSQL迁移一站式脚本
# 用于将本地SQLite数据库迁移到Render PostgreSQL

# 定义颜色代码
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 输出格式化函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否有必要的Python包
check_dependencies() {
    log_info "检查依赖项..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请安装后再试"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装必要的Python包..."
    pip install sqlalchemy psycopg2-binary pandas python-dotenv
    
    log_success "依赖项检查完成"
}

# 导出SQLite数据库
export_sqlite_data() {
    log_info "开始导出SQLite数据库..."
    
    # 检查SQLite数据库文件
    if [ ! -f "app.db" ]; then
        log_error "未找到app.db文件，请确保它存在于当前目录"
        exit 1
    fi
    
    # 运行导出脚本
    python3 export_sqlite_data.py --db app.db --output db_export_full.json
    
    if [ $? -eq 0 ]; then
        log_success "SQLite数据库导出成功"
    else
        log_error "SQLite数据库导出失败"
        exit 1
    fi
}

# 修复数据库连接URL
fix_database_url() {
    log_info "修复Render数据库连接URL..."
    
    # 检查是否提供了数据库URL
    if [ -z "$RENDER_DB_URL" ]; then
        log_error "未设置RENDER_DB_URL环境变量，请提供Render数据库URL"
        read -p "请输入Render数据库URL: " RENDER_DB_URL
        export RENDER_DB_URL="$RENDER_DB_URL"
    fi
    
    # 运行URL修复工具
    python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --test
    
    if [ $? -eq 0 ]; then
        log_success "数据库连接测试成功"
    else
        log_warning "数据库连接测试失败，尝试修复问题..."
        # 运行更新配置文件的操作
        python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --set-env --update-config
        
        if [ $? -eq 0 ]; then
            log_success "数据库连接已修复并更新配置"
        else
            log_error "无法修复数据库连接问题"
            exit 1
        fi
    fi
}

# 迁移数据到Render
migrate_to_render() {
    log_info "开始迁移数据到Render PostgreSQL..."
    
    # 检查导出文件是否存在
    if [ ! -f "db_export_full.json" ]; then
        log_error "未找到db_export_full.json文件，请先导出SQLite数据"
        exit 1
    fi
    
    # 确保RENDER_DB_URL已经过修复
    if [ -z "$DATABASE_URL" ]; then
        export DATABASE_URL="$RENDER_DB_URL"
    fi
    
    # 运行迁移脚本
    python3 db_migration.py --source db_export_full.json --target "$DATABASE_URL"
    
    if [ $? -eq 0 ]; then
        log_success "数据已成功迁移到Render PostgreSQL!"
    else
        log_error "数据迁移失败"
        exit 1
    fi
}

# 检查迁移结果
verify_migration() {
    log_info "验证迁移结果..."
    
    # 使用一个简单的查询脚本检查数据
    cat > verify_migration.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from sqlalchemy import create_engine, text

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("错误：未设置DATABASE_URL环境变量")
        return 1
        
    print(f"连接到数据库...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 检查用户表
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"用户数量: {user_count}")
            
            # 检查部门表
            result = conn.execute(text("SELECT COUNT(*) FROM departments"))
            dept_count = result.fetchone()[0]
            print(f"部门数量: {dept_count}")
            
            # 获取所有表
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ))
            tables = [row[0] for row in result]
            print(f"数据库包含 {len(tables)} 个表: {', '.join(tables[:5])}...")
            
        print("迁移验证成功!")
        return 0
    except Exception as e:
        print(f"验证失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x verify_migration.py
    python3 verify_migration.py
    
    if [ $? -eq 0 ]; then
        log_success "迁移验证成功!"
    else
        log_warning "迁移验证失败，请手动检查数据库"
    fi
}

# 创建必要的脚本文件
create_necessary_files() {
    log_info "创建必要的工具脚本..."
    
    # 如果导出脚本不存在，创建它
    if [ ! -f "export_sqlite_data.py" ]; then
        cat > export_sqlite_data.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
EOF
        chmod +x export_sqlite_data.py
    fi
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}Render PostgreSQL迁移一站式脚本${NC}"
    echo "这个脚本将帮助您将本地SQLite数据库迁移到Render的PostgreSQL数据库"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "可用命令:"
    echo "  all         - 执行完整的迁移流程"
    echo "  setup       - 安装依赖并创建必要的脚本"
    echo "  export      - 导出SQLite数据库"
    echo "  fix-url     - 修复数据库URL"
    echo "  migrate     - 迁移数据到Render"
    echo "  verify      - 验证迁移结果"
    echo "  help        - 显示此帮助信息"
    echo
    echo "示例:"
    echo "  RENDER_DB_URL=\"您的Render数据库URL\" $0 all"
    echo
}

# 主函数
main() {
    # 获取命令
    command=${1:-"help"}
    
    case $command in
        all)
            check_dependencies
            create_necessary_files
            export_sqlite_data
            fix_database_url
            migrate_to_render
            verify_migration
            log_success "完整迁移流程完成!"
            ;;
        setup)
            check_dependencies
            create_necessary_files
            log_success "安装依赖和创建脚本完成!"
            ;;
        export)
            check_dependencies
            export_sqlite_data
            log_success "导出SQLite数据库完成!"
            ;;
        fix-url)
            check_dependencies
            fix_database_url
            log_success "修复数据库URL完成!"
            ;;
        migrate)
            check_dependencies
            migrate_to_render
            log_success "迁移数据到Render完成!"
            ;;
        verify)
            check_dependencies
            verify_migration
            log_success "验证迁移结果完成!"
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# 执行主函数
main "$@" 
# Render PostgreSQL迁移一站式脚本
# 用于将本地SQLite数据库迁移到Render PostgreSQL

# 定义颜色代码
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 输出格式化函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查是否有必要的Python包
check_dependencies() {
    log_info "检查依赖项..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请安装后再试"
        exit 1
    fi
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装必要的Python包..."
    pip install sqlalchemy psycopg2-binary pandas python-dotenv
    
    log_success "依赖项检查完成"
}

# 导出SQLite数据库
export_sqlite_data() {
    log_info "开始导出SQLite数据库..."
    
    # 检查SQLite数据库文件
    if [ ! -f "app.db" ]; then
        log_error "未找到app.db文件，请确保它存在于当前目录"
        exit 1
    fi
    
    # 运行导出脚本
    python3 export_sqlite_data.py --db app.db --output db_export_full.json
    
    if [ $? -eq 0 ]; then
        log_success "SQLite数据库导出成功"
    else
        log_error "SQLite数据库导出失败"
        exit 1
    fi
}

# 修复数据库连接URL
fix_database_url() {
    log_info "修复Render数据库连接URL..."
    
    # 检查是否提供了数据库URL
    if [ -z "$RENDER_DB_URL" ]; then
        log_error "未设置RENDER_DB_URL环境变量，请提供Render数据库URL"
        read -p "请输入Render数据库URL: " RENDER_DB_URL
        export RENDER_DB_URL="$RENDER_DB_URL"
    fi
    
    # 运行URL修复工具
    python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --test
    
    if [ $? -eq 0 ]; then
        log_success "数据库连接测试成功"
    else
        log_warning "数据库连接测试失败，尝试修复问题..."
        # 运行更新配置文件的操作
        python3 render_db_connect_fix.py --db-url "$RENDER_DB_URL" --set-env --update-config
        
        if [ $? -eq 0 ]; then
            log_success "数据库连接已修复并更新配置"
        else
            log_error "无法修复数据库连接问题"
            exit 1
        fi
    fi
}

# 迁移数据到Render
migrate_to_render() {
    log_info "开始迁移数据到Render PostgreSQL..."
    
    # 检查导出文件是否存在
    if [ ! -f "db_export_full.json" ]; then
        log_error "未找到db_export_full.json文件，请先导出SQLite数据"
        exit 1
    fi
    
    # 确保RENDER_DB_URL已经过修复
    if [ -z "$DATABASE_URL" ]; then
        export DATABASE_URL="$RENDER_DB_URL"
    fi
    
    # 运行迁移脚本
    python3 db_migration.py --source db_export_full.json --target "$DATABASE_URL"
    
    if [ $? -eq 0 ]; then
        log_success "数据已成功迁移到Render PostgreSQL!"
    else
        log_error "数据迁移失败"
        exit 1
    fi
}

# 检查迁移结果
verify_migration() {
    log_info "验证迁移结果..."
    
    # 使用一个简单的查询脚本检查数据
    cat > verify_migration.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from sqlalchemy import create_engine, text

def main():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("错误：未设置DATABASE_URL环境变量")
        return 1
        
    print(f"连接到数据库...")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 检查用户表
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"用户数量: {user_count}")
            
            # 检查部门表
            result = conn.execute(text("SELECT COUNT(*) FROM departments"))
            dept_count = result.fetchone()[0]
            print(f"部门数量: {dept_count}")
            
            # 获取所有表
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ))
            tables = [row[0] for row in result]
            print(f"数据库包含 {len(tables)} 个表: {', '.join(tables[:5])}...")
            
        print("迁移验证成功!")
        return 0
    except Exception as e:
        print(f"验证失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x verify_migration.py
    python3 verify_migration.py
    
    if [ $? -eq 0 ]; then
        log_success "迁移验证成功!"
    else
        log_warning "迁移验证失败，请手动检查数据库"
    fi
}

# 创建必要的脚本文件
create_necessary_files() {
    log_info "创建必要的工具脚本..."
    
    # 如果导出脚本不存在，创建它
    if [ ! -f "export_sqlite_data.py" ]; then
        cat > export_sqlite_data.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据导出工具: 导出数据库中的所有表结构和数据
"""

import os
import sys
import json
import sqlite3
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('数据导出')

def get_tables(conn):
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    cursor.close()
    return tables

def get_table_schema(conn, table_name):
    """获取表结构"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = cursor.fetchall()
    cursor.close()
    
    columns = []
    for col in schema:
        columns.append({
            'cid': col[0],
            'name': col[1],
            'type': col[2],
            'notnull': col[3],
            'default': col[4],
            'pk': col[5]
        })
    
    return columns

def get_table_data(conn, table_name):
    """获取表数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(columns, row)))
    
    cursor.close()
    return data

def export_database(db_path, output_file):
    """导出整个数据库"""
    try:
        conn = sqlite3.connect(db_path)
        
        # 获取所有表
        tables = get_tables(conn)
        logger.info(f"找到 {len(tables)} 个表")
        
        # 导出结果
        db_export = {}
        
        # 导出表结构和数据
        for table_name in tables:
            logger.info(f"导出表 {table_name}")
            
            # 获取表结构
            schema = get_table_schema(conn, table_name)
            
            # 获取表数据
            data = get_table_data(conn, table_name)
            
            # 添加到导出结果
            db_export[table_name] = data
            
            logger.info(f"表 {table_name} 导出完成，共 {len(data)} 条记录")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(db_export, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"数据库导出完成，已保存到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"导出数据库失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='SQLite数据导出工具')
    parser.add_argument('--db', default='app.db', help='SQLite数据库文件路径')
    parser.add_argument('--output', default='db_export.json', help='导出的JSON文件路径')
    args = parser.parse_args()
    
    logger.info("=== 开始导出数据库 ===")
    
    # 检查数据库文件是否存在
    if not os.path.exists(args.db):
        logger.error(f"数据库文件 {args.db} 不存在")
        return 1
    
    # 导出数据库
    success = export_database(args.db, args.output)
    
    logger.info("=== 数据库导出结束 ===")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
EOF
        chmod +x export_sqlite_data.py
    fi
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}Render PostgreSQL迁移一站式脚本${NC}"
    echo "这个脚本将帮助您将本地SQLite数据库迁移到Render的PostgreSQL数据库"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "可用命令:"
    echo "  all         - 执行完整的迁移流程"
    echo "  setup       - 安装依赖并创建必要的脚本"
    echo "  export      - 导出SQLite数据库"
    echo "  fix-url     - 修复数据库URL"
    echo "  migrate     - 迁移数据到Render"
    echo "  verify      - 验证迁移结果"
    echo "  help        - 显示此帮助信息"
    echo
    echo "示例:"
    echo "  RENDER_DB_URL=\"您的Render数据库URL\" $0 all"
    echo
}

# 主函数
main() {
    # 获取命令
    command=${1:-"help"}
    
    case $command in
        all)
            check_dependencies
            create_necessary_files
            export_sqlite_data
            fix_database_url
            migrate_to_render
            verify_migration
            log_success "完整迁移流程完成!"
            ;;
        setup)
            check_dependencies
            create_necessary_files
            log_success "安装依赖和创建脚本完成!"
            ;;
        export)
            check_dependencies
            export_sqlite_data
            log_success "导出SQLite数据库完成!"
            ;;
        fix-url)
            check_dependencies
            fix_database_url
            log_success "修复数据库URL完成!"
            ;;
        migrate)
            check_dependencies
            migrate_to_render
            log_success "迁移数据到Render完成!"
            ;;
        verify)
            check_dependencies
            verify_migration
            log_success "验证迁移结果完成!"
            ;;
        help|*)
            show_usage
            ;;
    esac
}

# 执行主函数
main "$@" 
 
 