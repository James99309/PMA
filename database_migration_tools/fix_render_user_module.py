#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render用户管理模块修复工具

此脚本用于修复Render上用户管理模块访问空白的问题:
1. 修复模板语法错误
2. 确保布尔值字段类型正确
"""

import os
import sys
import psycopg2
import logging
import re
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_render_user_module.log')
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

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        for field in fields:
            try:
                # 检查字段类型
                cursor.execute(f"""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}' 
                    AND column_name = '{field}';
                """)
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"字段 {field} 在表 {table} 中不存在，跳过")
                    continue
                
                data_type = result[0]
                logger.info(f"字段 {field} 当前类型为: {data_type}")
                
                if data_type != 'boolean':
                    logger.info(f"将字段 {field} 从 {data_type} 转换为 boolean 类型")
                    
                    # 如果是整数类型，需要转换为布尔型
                    if data_type in ('integer', 'smallint', 'bigint'):
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING CASE WHEN {field} = 0 THEN FALSE 
                                      WHEN {field} = 1 THEN TRUE 
                                      ELSE FALSE END;
                        """)
                    else:
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING {field}::boolean;
                        """)
                    
                    conn.commit()
                    logger.info(f"字段 {field} 类型修改完成")
                else:
                    logger.info(f"字段 {field} 已经是布尔型，无需修改")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"修改字段 {field} 时出错: {str(e)}")
    
    return True

def fix_template_files():
    """修复模板语法错误"""
    template_dir = "app/templates"
    logger.info("开始修复模板文件...")
    
    # 检查模板目录是否存在
    if not os.path.exists(template_dir):
        logger.error(f"模板目录 {template_dir} 不存在")
        return False
    
    # 需要检查的文件列表
    files_to_check = [
        "user/list.html",
        "quotation/list.html",
        "product/list.html"
    ]
    
    for file_name in files_to_check:
        file_path = os.path.join(template_dir, file_name)
        
        if not os.path.exists(file_path):
            logger.warning(f"文件 {file_path} 不存在，跳过")
            continue
        
        logger.info(f"正在处理文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建备份
            with open(f"{file_path}.bak", 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 检查endblock标签是否有名称
            if "{% endblock %}" in content and "{% block content %}" in content:
                logger.info(f"在 {file_path} 中发现无名称的endblock标签，添加名称")
                content = content.replace("{% endblock %}", "{% endblock content %}")
            
            # 检查是否有多个相同类型的block
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            block_counts = {}
            
            for block in blocks:
                if block in block_counts:
                    block_counts[block] += 1
                else:
                    block_counts[block] = 1
            
            # 检查文件末尾是否缺少endblock
            for block, count in block_counts.items():
                endblock_pattern = r'{%\s*endblock\s+' + re.escape(block) + r'\s*%}'
                endblocks = re.findall(endblock_pattern, content)
                
                if len(endblocks) < count:
                    logger.info(f"在 {file_path} 中发现 {block} 块缺少endblock标签，添加")
                    content += f"\n{{% endblock {block} %}}\n"
            
            # 修复scripts块未正确关闭的问题
            if "{% block scripts %}" in content and "{% endblock scripts %}" not in content:
                if content.strip().endswith("{% endblock %}"):
                    content = content.replace("{% endblock %}", "{% endblock scripts %}")
                else:
                    content += "\n{% endblock scripts %}\n"
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"文件 {file_path} 修复完成")
            
        except Exception as e:
            logger.error(f"修复文件 {file_path} 时出错: {str(e)}")
    
    return True

def main():
    """主函数"""
    logger.info("=== 开始修复Render用户管理模块 ===")
    
    # 修复模板语法错误
    logger.info("\n--- 步骤1: 修复模板语法错误 ---")
    template_fixed = fix_template_files()
    
    if not template_fixed:
        logger.error("修复模板文件失败")
    else:
        logger.info("模板文件修复完成")
    
    # 修复数据库布尔值字段
    logger.info("\n--- 步骤2: 修复数据库布尔值字段 ---")
    
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        sys.exit(1)
    
    # 连接数据库
    db_info = parse_db_url(db_url)
    conn = connect_to_db(db_info)
    
    # 修复布尔值字段
    boolean_fixed = fix_boolean_fields(conn)
    
    if not boolean_fixed:
        logger.error("修复布尔值字段失败")
    else:
        logger.info("布尔值字段修复完成")
    
    # 关闭数据库连接
    conn.close()
    
    # 总结
    logger.info("\n=== 修复总结 ===")
    if template_fixed and boolean_fixed:
        logger.info("所有修复成功完成！用户管理模块应该可以正常访问了")
        logger.info("请重启应用以应用更改")
    else:
        logger.warning("部分修复未成功完成，请查看日志了解详情")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render用户管理模块修复工具

此脚本用于修复Render上用户管理模块访问空白的问题:
1. 修复模板语法错误
2. 确保布尔值字段类型正确
"""

import os
import sys
import psycopg2
import logging
import re
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_render_user_module.log')
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

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        for field in fields:
            try:
                # 检查字段类型
                cursor.execute(f"""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}' 
                    AND column_name = '{field}';
                """)
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"字段 {field} 在表 {table} 中不存在，跳过")
                    continue
                
                data_type = result[0]
                logger.info(f"字段 {field} 当前类型为: {data_type}")
                
                if data_type != 'boolean':
                    logger.info(f"将字段 {field} 从 {data_type} 转换为 boolean 类型")
                    
                    # 如果是整数类型，需要转换为布尔型
                    if data_type in ('integer', 'smallint', 'bigint'):
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING CASE WHEN {field} = 0 THEN FALSE 
                                      WHEN {field} = 1 THEN TRUE 
                                      ELSE FALSE END;
                        """)
                    else:
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING {field}::boolean;
                        """)
                    
                    conn.commit()
                    logger.info(f"字段 {field} 类型修改完成")
                else:
                    logger.info(f"字段 {field} 已经是布尔型，无需修改")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"修改字段 {field} 时出错: {str(e)}")
    
    return True

def fix_template_files():
    """修复模板语法错误"""
    template_dir = "app/templates"
    logger.info("开始修复模板文件...")
    
    # 检查模板目录是否存在
    if not os.path.exists(template_dir):
        logger.error(f"模板目录 {template_dir} 不存在")
        return False
    
    # 需要检查的文件列表
    files_to_check = [
        "user/list.html",
        "quotation/list.html",
        "product/list.html"
    ]
    
    for file_name in files_to_check:
        file_path = os.path.join(template_dir, file_name)
        
        if not os.path.exists(file_path):
            logger.warning(f"文件 {file_path} 不存在，跳过")
            continue
        
        logger.info(f"正在处理文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建备份
            with open(f"{file_path}.bak", 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 检查endblock标签是否有名称
            if "{% endblock %}" in content and "{% block content %}" in content:
                logger.info(f"在 {file_path} 中发现无名称的endblock标签，添加名称")
                content = content.replace("{% endblock %}", "{% endblock content %}")
            
            # 检查是否有多个相同类型的block
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            block_counts = {}
            
            for block in blocks:
                if block in block_counts:
                    block_counts[block] += 1
                else:
                    block_counts[block] = 1
            
            # 检查文件末尾是否缺少endblock
            for block, count in block_counts.items():
                endblock_pattern = r'{%\s*endblock\s+' + re.escape(block) + r'\s*%}'
                endblocks = re.findall(endblock_pattern, content)
                
                if len(endblocks) < count:
                    logger.info(f"在 {file_path} 中发现 {block} 块缺少endblock标签，添加")
                    content += f"\n{{% endblock {block} %}}\n"
            
            # 修复scripts块未正确关闭的问题
            if "{% block scripts %}" in content and "{% endblock scripts %}" not in content:
                if content.strip().endswith("{% endblock %}"):
                    content = content.replace("{% endblock %}", "{% endblock scripts %}")
                else:
                    content += "\n{% endblock scripts %}\n"
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"文件 {file_path} 修复完成")
            
        except Exception as e:
            logger.error(f"修复文件 {file_path} 时出错: {str(e)}")
    
    return True

def main():
    """主函数"""
    logger.info("=== 开始修复Render用户管理模块 ===")
    
    # 修复模板语法错误
    logger.info("\n--- 步骤1: 修复模板语法错误 ---")
    template_fixed = fix_template_files()
    
    if not template_fixed:
        logger.error("修复模板文件失败")
    else:
        logger.info("模板文件修复完成")
    
    # 修复数据库布尔值字段
    logger.info("\n--- 步骤2: 修复数据库布尔值字段 ---")
    
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        sys.exit(1)
    
    # 连接数据库
    db_info = parse_db_url(db_url)
    conn = connect_to_db(db_info)
    
    # 修复布尔值字段
    boolean_fixed = fix_boolean_fields(conn)
    
    if not boolean_fixed:
        logger.error("修复布尔值字段失败")
    else:
        logger.info("布尔值字段修复完成")
    
    # 关闭数据库连接
    conn.close()
    
    # 总结
    logger.info("\n=== 修复总结 ===")
    if template_fixed and boolean_fixed:
        logger.info("所有修复成功完成！用户管理模块应该可以正常访问了")
        logger.info("请重启应用以应用更改")
    else:
        logger.warning("部分修复未成功完成，请查看日志了解详情")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render用户管理模块修复工具

此脚本用于修复Render上用户管理模块访问空白的问题:
1. 修复模板语法错误
2. 确保布尔值字段类型正确
"""

import os
import sys
import psycopg2
import logging
import re
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_render_user_module.log')
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

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        for field in fields:
            try:
                # 检查字段类型
                cursor.execute(f"""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}' 
                    AND column_name = '{field}';
                """)
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"字段 {field} 在表 {table} 中不存在，跳过")
                    continue
                
                data_type = result[0]
                logger.info(f"字段 {field} 当前类型为: {data_type}")
                
                if data_type != 'boolean':
                    logger.info(f"将字段 {field} 从 {data_type} 转换为 boolean 类型")
                    
                    # 如果是整数类型，需要转换为布尔型
                    if data_type in ('integer', 'smallint', 'bigint'):
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING CASE WHEN {field} = 0 THEN FALSE 
                                      WHEN {field} = 1 THEN TRUE 
                                      ELSE FALSE END;
                        """)
                    else:
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING {field}::boolean;
                        """)
                    
                    conn.commit()
                    logger.info(f"字段 {field} 类型修改完成")
                else:
                    logger.info(f"字段 {field} 已经是布尔型，无需修改")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"修改字段 {field} 时出错: {str(e)}")
    
    return True

def fix_template_files():
    """修复模板语法错误"""
    template_dir = "app/templates"
    logger.info("开始修复模板文件...")
    
    # 检查模板目录是否存在
    if not os.path.exists(template_dir):
        logger.error(f"模板目录 {template_dir} 不存在")
        return False
    
    # 需要检查的文件列表
    files_to_check = [
        "user/list.html",
        "quotation/list.html",
        "product/list.html"
    ]
    
    for file_name in files_to_check:
        file_path = os.path.join(template_dir, file_name)
        
        if not os.path.exists(file_path):
            logger.warning(f"文件 {file_path} 不存在，跳过")
            continue
        
        logger.info(f"正在处理文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建备份
            with open(f"{file_path}.bak", 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 检查endblock标签是否有名称
            if "{% endblock %}" in content and "{% block content %}" in content:
                logger.info(f"在 {file_path} 中发现无名称的endblock标签，添加名称")
                content = content.replace("{% endblock %}", "{% endblock content %}")
            
            # 检查是否有多个相同类型的block
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            block_counts = {}
            
            for block in blocks:
                if block in block_counts:
                    block_counts[block] += 1
                else:
                    block_counts[block] = 1
            
            # 检查文件末尾是否缺少endblock
            for block, count in block_counts.items():
                endblock_pattern = r'{%\s*endblock\s+' + re.escape(block) + r'\s*%}'
                endblocks = re.findall(endblock_pattern, content)
                
                if len(endblocks) < count:
                    logger.info(f"在 {file_path} 中发现 {block} 块缺少endblock标签，添加")
                    content += f"\n{{% endblock {block} %}}\n"
            
            # 修复scripts块未正确关闭的问题
            if "{% block scripts %}" in content and "{% endblock scripts %}" not in content:
                if content.strip().endswith("{% endblock %}"):
                    content = content.replace("{% endblock %}", "{% endblock scripts %}")
                else:
                    content += "\n{% endblock scripts %}\n"
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"文件 {file_path} 修复完成")
            
        except Exception as e:
            logger.error(f"修复文件 {file_path} 时出错: {str(e)}")
    
    return True

def main():
    """主函数"""
    logger.info("=== 开始修复Render用户管理模块 ===")
    
    # 修复模板语法错误
    logger.info("\n--- 步骤1: 修复模板语法错误 ---")
    template_fixed = fix_template_files()
    
    if not template_fixed:
        logger.error("修复模板文件失败")
    else:
        logger.info("模板文件修复完成")
    
    # 修复数据库布尔值字段
    logger.info("\n--- 步骤2: 修复数据库布尔值字段 ---")
    
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        sys.exit(1)
    
    # 连接数据库
    db_info = parse_db_url(db_url)
    conn = connect_to_db(db_info)
    
    # 修复布尔值字段
    boolean_fixed = fix_boolean_fields(conn)
    
    if not boolean_fixed:
        logger.error("修复布尔值字段失败")
    else:
        logger.info("布尔值字段修复完成")
    
    # 关闭数据库连接
    conn.close()
    
    # 总结
    logger.info("\n=== 修复总结 ===")
    if template_fixed and boolean_fixed:
        logger.info("所有修复成功完成！用户管理模块应该可以正常访问了")
        logger.info("请重启应用以应用更改")
    else:
        logger.warning("部分修复未成功完成，请查看日志了解详情")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render用户管理模块修复工具

此脚本用于修复Render上用户管理模块访问空白的问题:
1. 修复模板语法错误
2. 确保布尔值字段类型正确
"""

import os
import sys
import psycopg2
import logging
import re
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_render_user_module.log')
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

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        for field in fields:
            try:
                # 检查字段类型
                cursor.execute(f"""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}' 
                    AND column_name = '{field}';
                """)
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"字段 {field} 在表 {table} 中不存在，跳过")
                    continue
                
                data_type = result[0]
                logger.info(f"字段 {field} 当前类型为: {data_type}")
                
                if data_type != 'boolean':
                    logger.info(f"将字段 {field} 从 {data_type} 转换为 boolean 类型")
                    
                    # 如果是整数类型，需要转换为布尔型
                    if data_type in ('integer', 'smallint', 'bigint'):
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING CASE WHEN {field} = 0 THEN FALSE 
                                      WHEN {field} = 1 THEN TRUE 
                                      ELSE FALSE END;
                        """)
                    else:
                        cursor.execute(f"""
                            ALTER TABLE {table} 
                            ALTER COLUMN {field} TYPE BOOLEAN 
                            USING {field}::boolean;
                        """)
                    
                    conn.commit()
                    logger.info(f"字段 {field} 类型修改完成")
                else:
                    logger.info(f"字段 {field} 已经是布尔型，无需修改")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"修改字段 {field} 时出错: {str(e)}")
    
    return True

def fix_template_files():
    """修复模板语法错误"""
    template_dir = "app/templates"
    logger.info("开始修复模板文件...")
    
    # 检查模板目录是否存在
    if not os.path.exists(template_dir):
        logger.error(f"模板目录 {template_dir} 不存在")
        return False
    
    # 需要检查的文件列表
    files_to_check = [
        "user/list.html",
        "quotation/list.html",
        "product/list.html"
    ]
    
    for file_name in files_to_check:
        file_path = os.path.join(template_dir, file_name)
        
        if not os.path.exists(file_path):
            logger.warning(f"文件 {file_path} 不存在，跳过")
            continue
        
        logger.info(f"正在处理文件: {file_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建备份
            with open(f"{file_path}.bak", 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 检查endblock标签是否有名称
            if "{% endblock %}" in content and "{% block content %}" in content:
                logger.info(f"在 {file_path} 中发现无名称的endblock标签，添加名称")
                content = content.replace("{% endblock %}", "{% endblock content %}")
            
            # 检查是否有多个相同类型的block
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            block_counts = {}
            
            for block in blocks:
                if block in block_counts:
                    block_counts[block] += 1
                else:
                    block_counts[block] = 1
            
            # 检查文件末尾是否缺少endblock
            for block, count in block_counts.items():
                endblock_pattern = r'{%\s*endblock\s+' + re.escape(block) + r'\s*%}'
                endblocks = re.findall(endblock_pattern, content)
                
                if len(endblocks) < count:
                    logger.info(f"在 {file_path} 中发现 {block} 块缺少endblock标签，添加")
                    content += f"\n{{% endblock {block} %}}\n"
            
            # 修复scripts块未正确关闭的问题
            if "{% block scripts %}" in content and "{% endblock scripts %}" not in content:
                if content.strip().endswith("{% endblock %}"):
                    content = content.replace("{% endblock %}", "{% endblock scripts %}")
                else:
                    content += "\n{% endblock scripts %}\n"
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"文件 {file_path} 修复完成")
            
        except Exception as e:
            logger.error(f"修复文件 {file_path} 时出错: {str(e)}")
    
    return True

def main():
    """主函数"""
    logger.info("=== 开始修复Render用户管理模块 ===")
    
    # 修复模板语法错误
    logger.info("\n--- 步骤1: 修复模板语法错误 ---")
    template_fixed = fix_template_files()
    
    if not template_fixed:
        logger.error("修复模板文件失败")
    else:
        logger.info("模板文件修复完成")
    
    # 修复数据库布尔值字段
    logger.info("\n--- 步骤2: 修复数据库布尔值字段 ---")
    
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("未找到DATABASE_URL环境变量")
        sys.exit(1)
    
    # 连接数据库
    db_info = parse_db_url(db_url)
    conn = connect_to_db(db_info)
    
    # 修复布尔值字段
    boolean_fixed = fix_boolean_fields(conn)
    
    if not boolean_fixed:
        logger.error("修复布尔值字段失败")
    else:
        logger.info("布尔值字段修复完成")
    
    # 关闭数据库连接
    conn.close()
    
    # 总结
    logger.info("\n=== 修复总结 ===")
    if template_fixed and boolean_fixed:
        logger.info("所有修复成功完成！用户管理模块应该可以正常访问了")
        logger.info("请重启应用以应用更改")
    else:
        logger.warning("部分修复未成功完成，请查看日志了解详情")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
 
 