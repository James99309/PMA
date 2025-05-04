#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库错误修复工具

用于解决PostgreSQL数据库中的类型兼容性问题和其他错误
主要功能：
1. 修复布尔值字段类型问题（SQLite 0/1 -> PostgreSQL true/false）
2. 修复可能的外键约束问题
3. 验证数据库连接和表结构完整性
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

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
    
    logger.info(f"数据库连接信息: host={db_info['host']}, dbname={db_info['dbname']}, user={db_info['user']}")
    return db_info

def connect_to_db(db_url):
    """连接到PostgreSQL数据库"""
    db_info = parse_db_url(db_url)
    
    try:
        conn = psycopg2.connect(**db_info)
        logger.info("成功连接到Render PostgreSQL数据库")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def get_all_tables(conn):
    """获取所有表名"""
    tables = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = [row[0] for row in cur.fetchall()]
        return tables
    except Exception as e:
        logger.error(f"获取表名失败: {str(e)}")
        return []

def fix_boolean_fields(conn):
    """修复布尔值字段类型问题"""
    # 已知的布尔值字段列表
    boolean_fields = {
        'user': ['is_department_manager', 'is_active', 'is_admin'],
        'permission': ['is_menu', 'is_default', 'is_active'],
        'company': ['is_active'],
        'project': ['is_active'],
        'quotation': ['is_active', 'is_draft'],
        # 添加其他表中的布尔字段
    }
    
    count = 0
    try:
        with conn.cursor() as cur:
            for table, fields in boolean_fields.items():
                for field in fields:
                    try:
                        # 检查表和字段是否存在
                        cur.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}');")
                        if not cur.fetchone()[0]:
                            logger.warning(f"表 {table} 中的字段 {field} 不存在，跳过")
                            continue
                        
                        # 获取字段当前类型
                        cur.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}';")
                        data_type = cur.fetchone()[0]
                        
                        if data_type.lower() not in ('boolean', 'bool'):
                            # 修复SQLite的整数布尔值(0/1)为PostgreSQL布尔值
                            logger.info(f"正在修复表 {table} 的布尔字段 {field}，当前类型: {data_type}")
                            
                            # 将0转换为false，其他值转换为true
                            cur.execute(f"ALTER TABLE {table} ALTER COLUMN {field} TYPE boolean USING CASE WHEN {field}='0' THEN FALSE WHEN {field}='1' THEN TRUE ELSE NULL END;")
                            count += 1
                            logger.info(f"成功将表 {table} 的字段 {field} 转换为布尔类型")
                        else:
                            logger.info(f"表 {table} 的字段 {field} 已经是布尔类型，无需修复")
                    except Exception as e:
                        logger.error(f"修复表 {table} 字段 {field} 失败: {str(e)}")
            
            conn.commit()
            logger.info(f"总共修复了 {count} 个布尔字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复布尔字段时发生错误: {str(e)}")

def fix_user_is_department_manager(conn):
    """特别修复user表的is_department_manager字段"""
    try:
        with conn.cursor() as cur:
            # 检查是否存在is_department_manager字段
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("user表中不存在is_department_manager字段，可能已被删除或重命名")
                return
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，无需修复")
                return
            
            # 查看字段中的值
            cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
            values = [row[0] for row in cur.fetchall()]
            logger.info(f"is_department_manager字段中的值: {values}")
            
            # 更新字段为布尔类型
            cur.execute("""
                ALTER TABLE "user" 
                ALTER COLUMN is_department_manager TYPE boolean 
                USING CASE 
                    WHEN is_department_manager='0' THEN FALSE 
                    WHEN is_department_manager='1' THEN TRUE 
                    ELSE NULL 
                END;
            """)
            
            conn.commit()
            logger.info("成功修复user表的is_department_manager字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复is_department_manager字段失败: {str(e)}")

def validate_table_structure(conn):
    """验证表结构完整性"""
    expected_tables = ['user', 'role', 'permission', 'company', 'contact', 'project', 'quotation']
    
    try:
        tables = get_all_tables(conn)
        logger.info(f"数据库中的表: {tables}")
        
        # 检查关键表是否存在
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            logger.warning(f"缺少以下关键表: {missing_tables}")
        else:
            logger.info("所有关键表都存在")
        
        # 检查各表记录数
        with conn.cursor() as cur:
            for table in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}";')
                    count = cur.fetchone()[0]
                    logger.info(f"表 {table} 有 {count} 条记录")
                except Exception as e:
                    logger.error(f"统计表 {table} 记录数时出错: {str(e)}")
    except Exception as e:
        logger.error(f"验证表结构时出错: {str(e)}")

def fix_foreign_key_constraints(conn):
    """修复外键约束问题"""
    try:
        with conn.cursor() as cur:
            # 检查外键约束
            cur.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'FOREIGN KEY';
            """)
            
            foreign_keys = cur.fetchall()
            logger.info(f"数据库中的外键约束: {foreign_keys}")
            
            # 检查外键约束是否有问题
            for table, column, ref_table, ref_column in foreign_keys:
                try:
                    # 查找违反外键约束的记录
                    cur.execute(f"""
                        SELECT a.{column} 
                        FROM "{table}" a 
                        LEFT JOIN "{ref_table}" b ON a.{column} = b.{ref_column} 
                        WHERE a.{column} IS NOT NULL AND b.{ref_column} IS NULL;
                    """)
                    
                    invalid_keys = cur.fetchall()
                    if invalid_keys:
                        logger.warning(f"表 {table} 中的字段 {column} 有 {len(invalid_keys)} 条记录违反了外键约束")
                        logger.warning(f"违反约束的值: {invalid_keys}")
                    else:
                        logger.info(f"外键约束 {table}.{column} -> {ref_table}.{ref_column} 验证通过")
                except Exception as e:
                    logger.error(f"检查外键约束 {table}.{column} 时出错: {str(e)}")
    except Exception as e:
        logger.error(f"修复外键约束时出错: {str(e)}")

def test_user_module(conn):
    """测试用户模块功能"""
    try:
        with conn.cursor() as cur:
            # 检查user表结构
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user';
            """)
            
            columns = cur.fetchall()
            logger.info(f"user表结构: {columns}")
            
            # 检查user表记录
            cur.execute('SELECT id, username, role_id, is_active, is_department_manager FROM "user" LIMIT 10;')
            users = cur.fetchall()
            logger.info(f"用户数据示例: {users}")
            
            # 特别检查is_department_manager字段
            cur.execute('SELECT id, username, is_department_manager FROM "user" WHERE is_department_manager IS NOT NULL LIMIT 5;')
            dept_managers = cur.fetchall()
            logger.info(f"部门管理员示例: {dept_managers}")
            
    except Exception as e:
        logger.error(f"测试用户模块时出错: {str(e)}")

def main():
    """主函数"""
    logger.info("=== 开始修复Render数据库错误 ===")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法连接数据库")
        return
    
    # 连接数据库
    conn = connect_to_db(db_url)
    if not conn:
        return
    
    try:
        # 验证表结构
        validate_table_structure(conn)
        
        # 修复布尔值字段
        fix_boolean_fields(conn)
        
        # 特别修复user表的is_department_manager字段
        fix_user_is_department_manager(conn)
        
        # 检查外键约束
        fix_foreign_key_constraints(conn)
        
        # 测试用户模块
        test_user_module(conn)
        
        logger.info("=== 数据库修复完成 ===")
    except Exception as e:
        logger.error(f"数据库修复过程中出错: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render数据库错误修复工具

用于解决PostgreSQL数据库中的类型兼容性问题和其他错误
主要功能：
1. 修复布尔值字段类型问题（SQLite 0/1 -> PostgreSQL true/false）
2. 修复可能的外键约束问题
3. 验证数据库连接和表结构完整性
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

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
    
    logger.info(f"数据库连接信息: host={db_info['host']}, dbname={db_info['dbname']}, user={db_info['user']}")
    return db_info

def connect_to_db(db_url):
    """连接到PostgreSQL数据库"""
    db_info = parse_db_url(db_url)
    
    try:
        conn = psycopg2.connect(**db_info)
        logger.info("成功连接到Render PostgreSQL数据库")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def get_all_tables(conn):
    """获取所有表名"""
    tables = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = [row[0] for row in cur.fetchall()]
        return tables
    except Exception as e:
        logger.error(f"获取表名失败: {str(e)}")
        return []

def fix_boolean_fields(conn):
    """修复布尔值字段类型问题"""
    # 已知的布尔值字段列表
    boolean_fields = {
        'user': ['is_department_manager', 'is_active', 'is_admin'],
        'permission': ['is_menu', 'is_default', 'is_active'],
        'company': ['is_active'],
        'project': ['is_active'],
        'quotation': ['is_active', 'is_draft'],
        # 添加其他表中的布尔字段
    }
    
    count = 0
    try:
        with conn.cursor() as cur:
            for table, fields in boolean_fields.items():
                for field in fields:
                    try:
                        # 检查表和字段是否存在
                        cur.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}');")
                        if not cur.fetchone()[0]:
                            logger.warning(f"表 {table} 中的字段 {field} 不存在，跳过")
                            continue
                        
                        # 获取字段当前类型
                        cur.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}';")
                        data_type = cur.fetchone()[0]
                        
                        if data_type.lower() not in ('boolean', 'bool'):
                            # 修复SQLite的整数布尔值(0/1)为PostgreSQL布尔值
                            logger.info(f"正在修复表 {table} 的布尔字段 {field}，当前类型: {data_type}")
                            
                            # 将0转换为false，其他值转换为true
                            cur.execute(f"ALTER TABLE {table} ALTER COLUMN {field} TYPE boolean USING CASE WHEN {field}='0' THEN FALSE WHEN {field}='1' THEN TRUE ELSE NULL END;")
                            count += 1
                            logger.info(f"成功将表 {table} 的字段 {field} 转换为布尔类型")
                        else:
                            logger.info(f"表 {table} 的字段 {field} 已经是布尔类型，无需修复")
                    except Exception as e:
                        logger.error(f"修复表 {table} 字段 {field} 失败: {str(e)}")
            
            conn.commit()
            logger.info(f"总共修复了 {count} 个布尔字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复布尔字段时发生错误: {str(e)}")

def fix_user_is_department_manager(conn):
    """特别修复user表的is_department_manager字段"""
    try:
        with conn.cursor() as cur:
            # 检查是否存在is_department_manager字段
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("user表中不存在is_department_manager字段，可能已被删除或重命名")
                return
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，无需修复")
                return
            
            # 查看字段中的值
            cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
            values = [row[0] for row in cur.fetchall()]
            logger.info(f"is_department_manager字段中的值: {values}")
            
            # 更新字段为布尔类型
            cur.execute("""
                ALTER TABLE "user" 
                ALTER COLUMN is_department_manager TYPE boolean 
                USING CASE 
                    WHEN is_department_manager='0' THEN FALSE 
                    WHEN is_department_manager='1' THEN TRUE 
                    ELSE NULL 
                END;
            """)
            
            conn.commit()
            logger.info("成功修复user表的is_department_manager字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复is_department_manager字段失败: {str(e)}")

def validate_table_structure(conn):
    """验证表结构完整性"""
    expected_tables = ['user', 'role', 'permission', 'company', 'contact', 'project', 'quotation']
    
    try:
        tables = get_all_tables(conn)
        logger.info(f"数据库中的表: {tables}")
        
        # 检查关键表是否存在
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            logger.warning(f"缺少以下关键表: {missing_tables}")
        else:
            logger.info("所有关键表都存在")
        
        # 检查各表记录数
        with conn.cursor() as cur:
            for table in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}";')
                    count = cur.fetchone()[0]
                    logger.info(f"表 {table} 有 {count} 条记录")
                except Exception as e:
                    logger.error(f"统计表 {table} 记录数时出错: {str(e)}")
    except Exception as e:
        logger.error(f"验证表结构时出错: {str(e)}")

def fix_foreign_key_constraints(conn):
    """修复外键约束问题"""
    try:
        with conn.cursor() as cur:
            # 检查外键约束
            cur.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'FOREIGN KEY';
            """)
            
            foreign_keys = cur.fetchall()
            logger.info(f"数据库中的外键约束: {foreign_keys}")
            
            # 检查外键约束是否有问题
            for table, column, ref_table, ref_column in foreign_keys:
                try:
                    # 查找违反外键约束的记录
                    cur.execute(f"""
                        SELECT a.{column} 
                        FROM "{table}" a 
                        LEFT JOIN "{ref_table}" b ON a.{column} = b.{ref_column} 
                        WHERE a.{column} IS NOT NULL AND b.{ref_column} IS NULL;
                    """)
                    
                    invalid_keys = cur.fetchall()
                    if invalid_keys:
                        logger.warning(f"表 {table} 中的字段 {column} 有 {len(invalid_keys)} 条记录违反了外键约束")
                        logger.warning(f"违反约束的值: {invalid_keys}")
                    else:
                        logger.info(f"外键约束 {table}.{column} -> {ref_table}.{ref_column} 验证通过")
                except Exception as e:
                    logger.error(f"检查外键约束 {table}.{column} 时出错: {str(e)}")
    except Exception as e:
        logger.error(f"修复外键约束时出错: {str(e)}")

def test_user_module(conn):
    """测试用户模块功能"""
    try:
        with conn.cursor() as cur:
            # 检查user表结构
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user';
            """)
            
            columns = cur.fetchall()
            logger.info(f"user表结构: {columns}")
            
            # 检查user表记录
            cur.execute('SELECT id, username, role_id, is_active, is_department_manager FROM "user" LIMIT 10;')
            users = cur.fetchall()
            logger.info(f"用户数据示例: {users}")
            
            # 特别检查is_department_manager字段
            cur.execute('SELECT id, username, is_department_manager FROM "user" WHERE is_department_manager IS NOT NULL LIMIT 5;')
            dept_managers = cur.fetchall()
            logger.info(f"部门管理员示例: {dept_managers}")
            
    except Exception as e:
        logger.error(f"测试用户模块时出错: {str(e)}")

def main():
    """主函数"""
    logger.info("=== 开始修复Render数据库错误 ===")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法连接数据库")
        return
    
    # 连接数据库
    conn = connect_to_db(db_url)
    if not conn:
        return
    
    try:
        # 验证表结构
        validate_table_structure(conn)
        
        # 修复布尔值字段
        fix_boolean_fields(conn)
        
        # 特别修复user表的is_department_manager字段
        fix_user_is_department_manager(conn)
        
        # 检查外键约束
        fix_foreign_key_constraints(conn)
        
        # 测试用户模块
        test_user_module(conn)
        
        logger.info("=== 数据库修复完成 ===")
    except Exception as e:
        logger.error(f"数据库修复过程中出错: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Render数据库错误修复工具

用于解决PostgreSQL数据库中的类型兼容性问题和其他错误
主要功能：
1. 修复布尔值字段类型问题（SQLite 0/1 -> PostgreSQL true/false）
2. 修复可能的外键约束问题
3. 验证数据库连接和表结构完整性
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

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
    
    logger.info(f"数据库连接信息: host={db_info['host']}, dbname={db_info['dbname']}, user={db_info['user']}")
    return db_info

def connect_to_db(db_url):
    """连接到PostgreSQL数据库"""
    db_info = parse_db_url(db_url)
    
    try:
        conn = psycopg2.connect(**db_info)
        logger.info("成功连接到Render PostgreSQL数据库")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def get_all_tables(conn):
    """获取所有表名"""
    tables = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = [row[0] for row in cur.fetchall()]
        return tables
    except Exception as e:
        logger.error(f"获取表名失败: {str(e)}")
        return []

def fix_boolean_fields(conn):
    """修复布尔值字段类型问题"""
    # 已知的布尔值字段列表
    boolean_fields = {
        'user': ['is_department_manager', 'is_active', 'is_admin'],
        'permission': ['is_menu', 'is_default', 'is_active'],
        'company': ['is_active'],
        'project': ['is_active'],
        'quotation': ['is_active', 'is_draft'],
        # 添加其他表中的布尔字段
    }
    
    count = 0
    try:
        with conn.cursor() as cur:
            for table, fields in boolean_fields.items():
                for field in fields:
                    try:
                        # 检查表和字段是否存在
                        cur.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}');")
                        if not cur.fetchone()[0]:
                            logger.warning(f"表 {table} 中的字段 {field} 不存在，跳过")
                            continue
                        
                        # 获取字段当前类型
                        cur.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}';")
                        data_type = cur.fetchone()[0]
                        
                        if data_type.lower() not in ('boolean', 'bool'):
                            # 修复SQLite的整数布尔值(0/1)为PostgreSQL布尔值
                            logger.info(f"正在修复表 {table} 的布尔字段 {field}，当前类型: {data_type}")
                            
                            # 将0转换为false，其他值转换为true
                            cur.execute(f"ALTER TABLE {table} ALTER COLUMN {field} TYPE boolean USING CASE WHEN {field}='0' THEN FALSE WHEN {field}='1' THEN TRUE ELSE NULL END;")
                            count += 1
                            logger.info(f"成功将表 {table} 的字段 {field} 转换为布尔类型")
                        else:
                            logger.info(f"表 {table} 的字段 {field} 已经是布尔类型，无需修复")
                    except Exception as e:
                        logger.error(f"修复表 {table} 字段 {field} 失败: {str(e)}")
            
            conn.commit()
            logger.info(f"总共修复了 {count} 个布尔字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复布尔字段时发生错误: {str(e)}")

def fix_user_is_department_manager(conn):
    """特别修复user表的is_department_manager字段"""
    try:
        with conn.cursor() as cur:
            # 检查是否存在is_department_manager字段
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("user表中不存在is_department_manager字段，可能已被删除或重命名")
                return
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，无需修复")
                return
            
            # 查看字段中的值
            cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
            values = [row[0] for row in cur.fetchall()]
            logger.info(f"is_department_manager字段中的值: {values}")
            
            # 更新字段为布尔类型
            cur.execute("""
                ALTER TABLE "user" 
                ALTER COLUMN is_department_manager TYPE boolean 
                USING CASE 
                    WHEN is_department_manager='0' THEN FALSE 
                    WHEN is_department_manager='1' THEN TRUE 
                    ELSE NULL 
                END;
            """)
            
            conn.commit()
            logger.info("成功修复user表的is_department_manager字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复is_department_manager字段失败: {str(e)}")

def validate_table_structure(conn):
    """验证表结构完整性"""
    expected_tables = ['user', 'role', 'permission', 'company', 'contact', 'project', 'quotation']
    
    try:
        tables = get_all_tables(conn)
        logger.info(f"数据库中的表: {tables}")
        
        # 检查关键表是否存在
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            logger.warning(f"缺少以下关键表: {missing_tables}")
        else:
            logger.info("所有关键表都存在")
        
        # 检查各表记录数
        with conn.cursor() as cur:
            for table in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}";')
                    count = cur.fetchone()[0]
                    logger.info(f"表 {table} 有 {count} 条记录")
                except Exception as e:
                    logger.error(f"统计表 {table} 记录数时出错: {str(e)}")
    except Exception as e:
        logger.error(f"验证表结构时出错: {str(e)}")

def fix_foreign_key_constraints(conn):
    """修复外键约束问题"""
    try:
        with conn.cursor() as cur:
            # 检查外键约束
            cur.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'FOREIGN KEY';
            """)
            
            foreign_keys = cur.fetchall()
            logger.info(f"数据库中的外键约束: {foreign_keys}")
            
            # 检查外键约束是否有问题
            for table, column, ref_table, ref_column in foreign_keys:
                try:
                    # 查找违反外键约束的记录
                    cur.execute(f"""
                        SELECT a.{column} 
                        FROM "{table}" a 
                        LEFT JOIN "{ref_table}" b ON a.{column} = b.{ref_column} 
                        WHERE a.{column} IS NOT NULL AND b.{ref_column} IS NULL;
                    """)
                    
                    invalid_keys = cur.fetchall()
                    if invalid_keys:
                        logger.warning(f"表 {table} 中的字段 {column} 有 {len(invalid_keys)} 条记录违反了外键约束")
                        logger.warning(f"违反约束的值: {invalid_keys}")
                    else:
                        logger.info(f"外键约束 {table}.{column} -> {ref_table}.{ref_column} 验证通过")
                except Exception as e:
                    logger.error(f"检查外键约束 {table}.{column} 时出错: {str(e)}")
    except Exception as e:
        logger.error(f"修复外键约束时出错: {str(e)}")

def test_user_module(conn):
    """测试用户模块功能"""
    try:
        with conn.cursor() as cur:
            # 检查user表结构
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user';
            """)
            
            columns = cur.fetchall()
            logger.info(f"user表结构: {columns}")
            
            # 检查user表记录
            cur.execute('SELECT id, username, role_id, is_active, is_department_manager FROM "user" LIMIT 10;')
            users = cur.fetchall()
            logger.info(f"用户数据示例: {users}")
            
            # 特别检查is_department_manager字段
            cur.execute('SELECT id, username, is_department_manager FROM "user" WHERE is_department_manager IS NOT NULL LIMIT 5;')
            dept_managers = cur.fetchall()
            logger.info(f"部门管理员示例: {dept_managers}")
            
    except Exception as e:
        logger.error(f"测试用户模块时出错: {str(e)}")

def main():
    """主函数"""
    logger.info("=== 开始修复Render数据库错误 ===")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法连接数据库")
        return
    
    # 连接数据库
    conn = connect_to_db(db_url)
    if not conn:
        return
    
    try:
        # 验证表结构
        validate_table_structure(conn)
        
        # 修复布尔值字段
        fix_boolean_fields(conn)
        
        # 特别修复user表的is_department_manager字段
        fix_user_is_department_manager(conn)
        
        # 检查外键约束
        fix_foreign_key_constraints(conn)
        
        # 测试用户模块
        test_user_module(conn)
        
        logger.info("=== 数据库修复完成 ===")
    except Exception as e:
        logger.error(f"数据库修复过程中出错: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render数据库错误修复工具

用于解决PostgreSQL数据库中的类型兼容性问题和其他错误
主要功能：
1. 修复布尔值字段类型问题（SQLite 0/1 -> PostgreSQL true/false）
2. 修复可能的外键约束问题
3. 验证数据库连接和表结构完整性
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_db_fix.log')
    ]
)
logger = logging.getLogger('Render数据库修复')

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
    
    logger.info(f"数据库连接信息: host={db_info['host']}, dbname={db_info['dbname']}, user={db_info['user']}")
    return db_info

def connect_to_db(db_url):
    """连接到PostgreSQL数据库"""
    db_info = parse_db_url(db_url)
    
    try:
        conn = psycopg2.connect(**db_info)
        logger.info("成功连接到Render PostgreSQL数据库")
        return conn
    except Exception as e:
        logger.error(f"连接数据库失败: {str(e)}")
        return None

def get_all_tables(conn):
    """获取所有表名"""
    tables = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = [row[0] for row in cur.fetchall()]
        return tables
    except Exception as e:
        logger.error(f"获取表名失败: {str(e)}")
        return []

def fix_boolean_fields(conn):
    """修复布尔值字段类型问题"""
    # 已知的布尔值字段列表
    boolean_fields = {
        'user': ['is_department_manager', 'is_active', 'is_admin'],
        'permission': ['is_menu', 'is_default', 'is_active'],
        'company': ['is_active'],
        'project': ['is_active'],
        'quotation': ['is_active', 'is_draft'],
        # 添加其他表中的布尔字段
    }
    
    count = 0
    try:
        with conn.cursor() as cur:
            for table, fields in boolean_fields.items():
                for field in fields:
                    try:
                        # 检查表和字段是否存在
                        cur.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}');")
                        if not cur.fetchone()[0]:
                            logger.warning(f"表 {table} 中的字段 {field} 不存在，跳过")
                            continue
                        
                        # 获取字段当前类型
                        cur.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{field}';")
                        data_type = cur.fetchone()[0]
                        
                        if data_type.lower() not in ('boolean', 'bool'):
                            # 修复SQLite的整数布尔值(0/1)为PostgreSQL布尔值
                            logger.info(f"正在修复表 {table} 的布尔字段 {field}，当前类型: {data_type}")
                            
                            # 将0转换为false，其他值转换为true
                            cur.execute(f"ALTER TABLE {table} ALTER COLUMN {field} TYPE boolean USING CASE WHEN {field}='0' THEN FALSE WHEN {field}='1' THEN TRUE ELSE NULL END;")
                            count += 1
                            logger.info(f"成功将表 {table} 的字段 {field} 转换为布尔类型")
                        else:
                            logger.info(f"表 {table} 的字段 {field} 已经是布尔类型，无需修复")
                    except Exception as e:
                        logger.error(f"修复表 {table} 字段 {field} 失败: {str(e)}")
            
            conn.commit()
            logger.info(f"总共修复了 {count} 个布尔字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复布尔字段时发生错误: {str(e)}")

def fix_user_is_department_manager(conn):
    """特别修复user表的is_department_manager字段"""
    try:
        with conn.cursor() as cur:
            # 检查是否存在is_department_manager字段
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("user表中不存在is_department_manager字段，可能已被删除或重命名")
                return
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，无需修复")
                return
            
            # 查看字段中的值
            cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
            values = [row[0] for row in cur.fetchall()]
            logger.info(f"is_department_manager字段中的值: {values}")
            
            # 更新字段为布尔类型
            cur.execute("""
                ALTER TABLE "user" 
                ALTER COLUMN is_department_manager TYPE boolean 
                USING CASE 
                    WHEN is_department_manager='0' THEN FALSE 
                    WHEN is_department_manager='1' THEN TRUE 
                    ELSE NULL 
                END;
            """)
            
            conn.commit()
            logger.info("成功修复user表的is_department_manager字段")
    except Exception as e:
        conn.rollback()
        logger.error(f"修复is_department_manager字段失败: {str(e)}")

def validate_table_structure(conn):
    """验证表结构完整性"""
    expected_tables = ['user', 'role', 'permission', 'company', 'contact', 'project', 'quotation']
    
    try:
        tables = get_all_tables(conn)
        logger.info(f"数据库中的表: {tables}")
        
        # 检查关键表是否存在
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            logger.warning(f"缺少以下关键表: {missing_tables}")
        else:
            logger.info("所有关键表都存在")
        
        # 检查各表记录数
        with conn.cursor() as cur:
            for table in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table}";')
                    count = cur.fetchone()[0]
                    logger.info(f"表 {table} 有 {count} 条记录")
                except Exception as e:
                    logger.error(f"统计表 {table} 记录数时出错: {str(e)}")
    except Exception as e:
        logger.error(f"验证表结构时出错: {str(e)}")

def fix_foreign_key_constraints(conn):
    """修复外键约束问题"""
    try:
        with conn.cursor() as cur:
            # 检查外键约束
            cur.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE constraint_type = 'FOREIGN KEY';
            """)
            
            foreign_keys = cur.fetchall()
            logger.info(f"数据库中的外键约束: {foreign_keys}")
            
            # 检查外键约束是否有问题
            for table, column, ref_table, ref_column in foreign_keys:
                try:
                    # 查找违反外键约束的记录
                    cur.execute(f"""
                        SELECT a.{column} 
                        FROM "{table}" a 
                        LEFT JOIN "{ref_table}" b ON a.{column} = b.{ref_column} 
                        WHERE a.{column} IS NOT NULL AND b.{ref_column} IS NULL;
                    """)
                    
                    invalid_keys = cur.fetchall()
                    if invalid_keys:
                        logger.warning(f"表 {table} 中的字段 {column} 有 {len(invalid_keys)} 条记录违反了外键约束")
                        logger.warning(f"违反约束的值: {invalid_keys}")
                    else:
                        logger.info(f"外键约束 {table}.{column} -> {ref_table}.{ref_column} 验证通过")
                except Exception as e:
                    logger.error(f"检查外键约束 {table}.{column} 时出错: {str(e)}")
    except Exception as e:
        logger.error(f"修复外键约束时出错: {str(e)}")

def test_user_module(conn):
    """测试用户模块功能"""
    try:
        with conn.cursor() as cur:
            # 检查user表结构
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user';
            """)
            
            columns = cur.fetchall()
            logger.info(f"user表结构: {columns}")
            
            # 检查user表记录
            cur.execute('SELECT id, username, role_id, is_active, is_department_manager FROM "user" LIMIT 10;')
            users = cur.fetchall()
            logger.info(f"用户数据示例: {users}")
            
            # 特别检查is_department_manager字段
            cur.execute('SELECT id, username, is_department_manager FROM "user" WHERE is_department_manager IS NOT NULL LIMIT 5;')
            dept_managers = cur.fetchall()
            logger.info(f"部门管理员示例: {dept_managers}")
            
    except Exception as e:
        logger.error(f"测试用户模块时出错: {str(e)}")

def main():
    """主函数"""
    logger.info("=== 开始修复Render数据库错误 ===")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法连接数据库")
        return
    
    # 连接数据库
    conn = connect_to_db(db_url)
    if not conn:
        return
    
    try:
        # 验证表结构
        validate_table_structure(conn)
        
        # 修复布尔值字段
        fix_boolean_fields(conn)
        
        # 特别修复user表的is_department_manager字段
        fix_user_is_department_manager(conn)
        
        # 检查外键约束
        fix_foreign_key_constraints(conn)
        
        # 测试用户模块
        test_user_module(conn)
        
        logger.info("=== 数据库修复完成 ===")
    except Exception as e:
        logger.error(f"数据库修复过程中出错: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
 
 