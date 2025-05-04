#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Render上用户管理模块的问题
检查并修复用户表中的is_department_manager字段
"""

import os
import sys
import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_users_render.log')
    ]
)
logger = logging.getLogger('用户模块修复')

def parse_db_url(url):
    """解析数据库URL"""
    parsed = urlparse(url)
    
    db_info = {
        'dbname': parsed.path.strip('/'),
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'sslmode': 'require',
        'sslrootcert': 'none'
    }
    
    logger.info(f"数据库信息: 主机:{db_info['host']}, 数据库:{db_info['dbname']}")
    return db_info

def connect_to_db(db_info):
    """连接到数据库"""
    logger.info("正在连接到Render PostgreSQL数据库...")
    try:
        conn = psycopg2.connect(**db_info)
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        logger.info(f"连接成功! PostgreSQL版本: {db_version}")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        sys.exit(1)

def check_users_table(conn):
    """检查用户表结构"""
    cursor = conn.cursor()
    logger.info("检查users表结构...")
    
    # 检查表是否存在
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)
    
    if not cursor.fetchone()[0]:
        logger.error("users表不存在!")
        return False
    
    # 检查字段类型
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    logger.info(f"users表有 {len(columns)} 个字段:")
    
    # 显示字段信息
    for col in columns:
        logger.info(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
    
    # 检查is_department_manager字段
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'is_department_manager';
    """)
    
    result = cursor.fetchone()
    if not result:
        logger.warning("is_department_manager字段不存在，将添加该字段")
        return False
    else:
        logger.info(f"is_department_manager字段存在，类型为: {result[1]}")
        return True

def fix_is_department_manager(conn):
    """修复is_department_manager字段"""
    cursor = conn.cursor()
    
    try:
        # 检查字段是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users' 
                AND column_name = 'is_department_manager'
            );
        """)
        
        if not cursor.fetchone()[0]:
            # 字段不存在，添加字段
            logger.info("添加 is_department_manager 字段...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN is_department_manager BOOLEAN DEFAULT FALSE;
            """)
            conn.commit()
            logger.info("is_department_manager 字段添加成功!")
        else:
            # 字段存在，检查类型
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users' 
                AND column_name = 'is_department_manager';
            """)
            
            data_type = cursor.fetchone()[0]
            if data_type != 'boolean':
                # 类型不是布尔型，修改字段类型
                logger.info(f"修改 is_department_manager 字段类型 (当前: {data_type})...")
                
                # 如果字段是整数类型，需要转换为布尔型
                if data_type in ('integer', 'smallint', 'bigint'):
                    cursor.execute("""
                        ALTER TABLE users 
                        ALTER COLUMN is_department_manager TYPE BOOLEAN 
                        USING CASE WHEN is_department_manager = 0 THEN FALSE 
                                    WHEN is_department_manager = 1 THEN TRUE 
                                    ELSE FALSE END;
                    """)
                else:
                    cursor.execute("""
                        ALTER TABLE users 
                        ALTER COLUMN is_department_manager TYPE BOOLEAN 
                        USING is_department_manager::boolean;
                    """)
                
                conn.commit()
                logger.info("is_department_manager 字段类型修改成功!")
            else:
                logger.info("is_department_manager 字段已经是布尔型，无需修改")
        
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"修复 is_department_manager 字段失败: {str(e)}")
        return False

def check_permissions_tables(conn):
    """检查权限表结构"""
    cursor = conn.cursor()
    logger.info("检查permissions表结构...")
    
    # 检查表是否存在
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'permissions'
        );
    """)
    
    if not cursor.fetchone()[0]:
        logger.error("permissions表不存在!")
        return False
    
    # 检查字段类型
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'permissions'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    logger.info(f"permissions表有 {len(columns)} 个字段:")
    
    # 显示字段信息
    for col in columns:
        logger.info(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
    
    # 检查can_create字段
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'permissions' 
        AND column_name = 'can_create';
    """)
    
    result = cursor.fetchone()
    if not result:
        logger.warning("can_create字段不存在，将添加该字段")
        return False
    
    # 检查can_view, can_edit, can_delete字段
    boolean_fields = ['can_view', 'can_create', 'can_edit', 'can_delete']
    for field in boolean_fields:
        cursor.execute(f"""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'permissions' 
            AND column_name = '{field}';
        """)
        
        result = cursor.fetchone()
        if result and result[0] != 'boolean':
            logger.warning(f"{field}字段类型不是boolean，当前是{result[0]}")
            return False
    
    return True

def fix_permissions_table(conn):
    """修复permissions表"""
    cursor = conn.cursor()
    
    try:
        # 检查can_create字段是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'permissions' 
                AND column_name = 'can_create'
            );
        """)
        
        if not cursor.fetchone()[0]:
            # 字段不存在，添加字段
            logger.info("添加 can_create 字段...")
            cursor.execute("""
                ALTER TABLE permissions 
                ADD COLUMN can_create BOOLEAN DEFAULT FALSE;
            """)
            conn.commit()
            logger.info("can_create 字段添加成功!")
        
        # 检查并修复所有布尔字段
        boolean_fields = ['can_view', 'can_create', 'can_edit', 'can_delete']
        for field in boolean_fields:
            cursor.execute(f"""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'permissions' 
                AND column_name = '{field}';
            """)
            
            result = cursor.fetchone()
            if result and result[0] != 'boolean':
                # 类型不是布尔型，修改字段类型
                logger.info(f"修改 {field} 字段类型 (当前: {result[0]})...")
                
                # 如果字段是整数类型，需要转换为布尔型
                if result[0] in ('integer', 'smallint', 'bigint'):
                    cursor.execute(f"""
                        ALTER TABLE permissions 
                        ALTER COLUMN {field} TYPE BOOLEAN 
                        USING CASE WHEN {field} = 0 THEN FALSE 
                                    WHEN {field} = 1 THEN TRUE 
                                    ELSE FALSE END;
                    """)
                else:
                    cursor.execute(f"""
                        ALTER TABLE permissions 
                        ALTER COLUMN {field} TYPE BOOLEAN 
                        USING {field}::boolean;
                    """)
                
                conn.commit()
                logger.info(f"{field} 字段类型修改成功!")
        
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"修复permissions表失败: {str(e)}")
        return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python fix_users_render.py <db_url>")
        print("示例: python fix_users_render.py \"postgresql://user:pass@host:port/dbname?sslmode=require&sslrootcert=none\"")
        sys.exit(1)
    
    db_url = sys.argv[1]
    
    # 解析数据库URL
    db_info = parse_db_url(db_url)
    
    # 连接数据库
    conn = connect_to_db(db_info)
    
    try:
        # 检查用户表
        users_ok = check_users_table(conn)
        if not users_ok:
            logger.info("尝试修复用户表...")
            fix_result = fix_is_department_manager(conn)
            if fix_result:
                logger.info("用户表修复成功!")
            else:
                logger.error("用户表修复失败!")
        
        # 检查权限表
        permissions_ok = check_permissions_tables(conn)
        if not permissions_ok:
            logger.info("尝试修复权限表...")
            fix_result = fix_permissions_table(conn)
            if fix_result:
                logger.info("权限表修复成功!")
            else:
                logger.error("权限表修复失败!")
        
        if users_ok and permissions_ok:
            logger.info("用户管理模块数据库结构正常!")
        
        # 检查用户数据
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        logger.info(f"users表中有 {user_count} 条记录")
        
        # 检查权限数据
        cursor.execute("SELECT COUNT(*) FROM permissions;")
        permission_count = cursor.fetchone()[0]
        logger.info(f"permissions表中有 {permission_count} 条记录")
        
    finally:
        # 关闭连接
        conn.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main() 