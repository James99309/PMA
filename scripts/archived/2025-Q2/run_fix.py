#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成了模板修复、数据库布尔值修复和应用重启功能
"""

import os
import sys
import time
import logging
import re
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix.log')
    ]
)
logger = logging.getLogger('Render修复')

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
        return None

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    if not conn:
        logger.error("数据库连接失败，无法修复布尔值字段")
        return False
        
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    all_succeeded = True
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        # 检查表是否存在
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table}'
            );
        """)
        
        if not cursor.fetchone()[0]:
            logger.warning(f"表 {table} 不存在，跳过")
            continue
        
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
                all_succeeded = False
    
    return all_succeeded

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 1. 修复无名称的endblock
    if "{% endblock %}" in content and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = content.replace("{% endblock %}", "{% endblock content %}")
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 特殊修复: user/list.html中的scripts块
    if "list.html" in file_path and "{% block scripts %}" in content:
        if "{% endblock %}" in content and "{% endblock scripts %}" not in content:
            content = content.replace("{% endblock %}", "{% endblock scripts %}")
            logger.info("已修复scripts块")
    
    # 6. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    fixed_files = []
    for file_path in problem_files:
        if file_path.exists():
            if fix_template(str(file_path)):
                fixed_files.append(file_path.name)
    
    # 返回修复的文件
    if fixed_files:
        logger.info(f"修复了以下文件: {', '.join(fixed_files)}")
    else:
        logger.info("没有文件需要修复")
        
    return True

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

def main():
    """主函数"""
    logger.info("========== Render全面修复工具 ==========")
    
    # 1. 修复模板语法错误
    logger.info("\n------ 步骤1: 修复模板语法错误 ------")
    template_fixed = check_templates()
    
    # 2. 修复数据库布尔值字段
    logger.info("\n------ 步骤2: 修复数据库布尔值字段 ------")
    
    db_fixed = False
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("未找到DATABASE_URL环境变量，跳过数据库修复")
    else:
        # 连接数据库
        db_info = parse_db_url(db_url)
        conn = connect_to_db(db_info)
        
        if conn:
            # 修复布尔值字段
            db_fixed = fix_boolean_fields(conn)
            # 关闭数据库连接
            conn.close()
    
    # 3. 重启应用
    logger.info("\n------ 步骤3: 重启应用 ------")
    restart_success = restart_render_app()
    
    # 总结
    logger.info("\n========== 修复总结 ==========")
    if template_fixed:
        logger.info("✅ 模板修复成功")
    else:
        logger.warning("❌ 模板修复失败")
        
    if db_fixed:
        logger.info("✅ 数据库布尔值字段修复成功")
    else:
        logger.warning("❌ 数据库布尔值字段修复失败或跳过")
        
    if restart_success:
        logger.info("✅ 应用重启触发成功")
    else:
        logger.warning("❌ 应用重启触发失败")
    
    logger.info("\n如果用户管理模块仍然无法访问，请检查日志获取更多信息")
    logger.info("========== 修复完成 ==========")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成了模板修复、数据库布尔值修复和应用重启功能
"""

import os
import sys
import time
import logging
import re
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix.log')
    ]
)
logger = logging.getLogger('Render修复')

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
        return None

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    if not conn:
        logger.error("数据库连接失败，无法修复布尔值字段")
        return False
        
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    all_succeeded = True
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        # 检查表是否存在
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table}'
            );
        """)
        
        if not cursor.fetchone()[0]:
            logger.warning(f"表 {table} 不存在，跳过")
            continue
        
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
                all_succeeded = False
    
    return all_succeeded

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 1. 修复无名称的endblock
    if "{% endblock %}" in content and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = content.replace("{% endblock %}", "{% endblock content %}")
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 特殊修复: user/list.html中的scripts块
    if "list.html" in file_path and "{% block scripts %}" in content:
        if "{% endblock %}" in content and "{% endblock scripts %}" not in content:
            content = content.replace("{% endblock %}", "{% endblock scripts %}")
            logger.info("已修复scripts块")
    
    # 6. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    fixed_files = []
    for file_path in problem_files:
        if file_path.exists():
            if fix_template(str(file_path)):
                fixed_files.append(file_path.name)
    
    # 返回修复的文件
    if fixed_files:
        logger.info(f"修复了以下文件: {', '.join(fixed_files)}")
    else:
        logger.info("没有文件需要修复")
        
    return True

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

def main():
    """主函数"""
    logger.info("========== Render全面修复工具 ==========")
    
    # 1. 修复模板语法错误
    logger.info("\n------ 步骤1: 修复模板语法错误 ------")
    template_fixed = check_templates()
    
    # 2. 修复数据库布尔值字段
    logger.info("\n------ 步骤2: 修复数据库布尔值字段 ------")
    
    db_fixed = False
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("未找到DATABASE_URL环境变量，跳过数据库修复")
    else:
        # 连接数据库
        db_info = parse_db_url(db_url)
        conn = connect_to_db(db_info)
        
        if conn:
            # 修复布尔值字段
            db_fixed = fix_boolean_fields(conn)
            # 关闭数据库连接
            conn.close()
    
    # 3. 重启应用
    logger.info("\n------ 步骤3: 重启应用 ------")
    restart_success = restart_render_app()
    
    # 总结
    logger.info("\n========== 修复总结 ==========")
    if template_fixed:
        logger.info("✅ 模板修复成功")
    else:
        logger.warning("❌ 模板修复失败")
        
    if db_fixed:
        logger.info("✅ 数据库布尔值字段修复成功")
    else:
        logger.warning("❌ 数据库布尔值字段修复失败或跳过")
        
    if restart_success:
        logger.info("✅ 应用重启触发成功")
    else:
        logger.warning("❌ 应用重启触发失败")
    
    logger.info("\n如果用户管理模块仍然无法访问，请检查日志获取更多信息")
    logger.info("========== 修复完成 ==========")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成了模板修复、数据库布尔值修复和应用重启功能
"""

import os
import sys
import time
import logging
import re
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix.log')
    ]
)
logger = logging.getLogger('Render修复')

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
        return None

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    if not conn:
        logger.error("数据库连接失败，无法修复布尔值字段")
        return False
        
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    all_succeeded = True
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        # 检查表是否存在
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table}'
            );
        """)
        
        if not cursor.fetchone()[0]:
            logger.warning(f"表 {table} 不存在，跳过")
            continue
        
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
                all_succeeded = False
    
    return all_succeeded

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 1. 修复无名称的endblock
    if "{% endblock %}" in content and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = content.replace("{% endblock %}", "{% endblock content %}")
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 特殊修复: user/list.html中的scripts块
    if "list.html" in file_path and "{% block scripts %}" in content:
        if "{% endblock %}" in content and "{% endblock scripts %}" not in content:
            content = content.replace("{% endblock %}", "{% endblock scripts %}")
            logger.info("已修复scripts块")
    
    # 6. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    fixed_files = []
    for file_path in problem_files:
        if file_path.exists():
            if fix_template(str(file_path)):
                fixed_files.append(file_path.name)
    
    # 返回修复的文件
    if fixed_files:
        logger.info(f"修复了以下文件: {', '.join(fixed_files)}")
    else:
        logger.info("没有文件需要修复")
        
    return True

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

def main():
    """主函数"""
    logger.info("========== Render全面修复工具 ==========")
    
    # 1. 修复模板语法错误
    logger.info("\n------ 步骤1: 修复模板语法错误 ------")
    template_fixed = check_templates()
    
    # 2. 修复数据库布尔值字段
    logger.info("\n------ 步骤2: 修复数据库布尔值字段 ------")
    
    db_fixed = False
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("未找到DATABASE_URL环境变量，跳过数据库修复")
    else:
        # 连接数据库
        db_info = parse_db_url(db_url)
        conn = connect_to_db(db_info)
        
        if conn:
            # 修复布尔值字段
            db_fixed = fix_boolean_fields(conn)
            # 关闭数据库连接
            conn.close()
    
    # 3. 重启应用
    logger.info("\n------ 步骤3: 重启应用 ------")
    restart_success = restart_render_app()
    
    # 总结
    logger.info("\n========== 修复总结 ==========")
    if template_fixed:
        logger.info("✅ 模板修复成功")
    else:
        logger.warning("❌ 模板修复失败")
        
    if db_fixed:
        logger.info("✅ 数据库布尔值字段修复成功")
    else:
        logger.warning("❌ 数据库布尔值字段修复失败或跳过")
        
    if restart_success:
        logger.info("✅ 应用重启触发成功")
    else:
        logger.warning("❌ 应用重启触发失败")
    
    logger.info("\n如果用户管理模块仍然无法访问，请检查日志获取更多信息")
    logger.info("========== 修复完成 ==========")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成了模板修复、数据库布尔值修复和应用重启功能
"""

import os
import sys
import time
import logging
import re
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix.log')
    ]
)
logger = logging.getLogger('Render修复')

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
        return None

def fix_boolean_fields(conn):
    """修复布尔值字段类型"""
    if not conn:
        logger.error("数据库连接失败，无法修复布尔值字段")
        return False
        
    cursor = conn.cursor()
    
    # 需要修复的表和字段列表
    tables_boolean_fields = {
        "users": ["is_active", "is_profile_complete", "is_department_manager"],
        "permissions": ["can_create", "can_read", "can_update", "can_delete"]
    }
    
    all_succeeded = True
    
    for table, fields in tables_boolean_fields.items():
        logger.info(f"检查表 {table} 的布尔值字段...")
        
        # 检查表是否存在
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table}'
            );
        """)
        
        if not cursor.fetchone()[0]:
            logger.warning(f"表 {table} 不存在，跳过")
            continue
        
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
                all_succeeded = False
    
    return all_succeeded

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 1. 修复无名称的endblock
    if "{% endblock %}" in content and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = content.replace("{% endblock %}", "{% endblock content %}")
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 特殊修复: user/list.html中的scripts块
    if "list.html" in file_path and "{% block scripts %}" in content:
        if "{% endblock %}" in content and "{% endblock scripts %}" not in content:
            content = content.replace("{% endblock %}", "{% endblock scripts %}")
            logger.info("已修复scripts块")
    
    # 6. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    fixed_files = []
    for file_path in problem_files:
        if file_path.exists():
            if fix_template(str(file_path)):
                fixed_files.append(file_path.name)
    
    # 返回修复的文件
    if fixed_files:
        logger.info(f"修复了以下文件: {', '.join(fixed_files)}")
    else:
        logger.info("没有文件需要修复")
        
    return True

def restart_render_app():
    """重启Render应用"""
    logger.info("===== 开始重启Render应用 =====")
    
    # 应用根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render重启触发目录
    tmp_dir = os.path.join(base_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        logger.info(f"创建临时目录: {tmp_dir}")
    
    # 创建重启触发文件
    restart_file = os.path.join(tmp_dir, 'restart.txt')
    with open(restart_file, 'w') as f:
        f.write(f"Restart triggered at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info(f"创建重启触发文件: {restart_file}")
    logger.info("Render将检测到此文件并重启应用")
    logger.info("===== 重启触发完成 =====")
    
    return True

def main():
    """主函数"""
    logger.info("========== Render全面修复工具 ==========")
    
    # 1. 修复模板语法错误
    logger.info("\n------ 步骤1: 修复模板语法错误 ------")
    template_fixed = check_templates()
    
    # 2. 修复数据库布尔值字段
    logger.info("\n------ 步骤2: 修复数据库布尔值字段 ------")
    
    db_fixed = False
    # 获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("未找到DATABASE_URL环境变量，跳过数据库修复")
    else:
        # 连接数据库
        db_info = parse_db_url(db_url)
        conn = connect_to_db(db_info)
        
        if conn:
            # 修复布尔值字段
            db_fixed = fix_boolean_fields(conn)
            # 关闭数据库连接
            conn.close()
    
    # 3. 重启应用
    logger.info("\n------ 步骤3: 重启应用 ------")
    restart_success = restart_render_app()
    
    # 总结
    logger.info("\n========== 修复总结 ==========")
    if template_fixed:
        logger.info("✅ 模板修复成功")
    else:
        logger.warning("❌ 模板修复失败")
        
    if db_fixed:
        logger.info("✅ 数据库布尔值字段修复成功")
    else:
        logger.warning("❌ 数据库布尔值字段修复失败或跳过")
        
    if restart_success:
        logger.info("✅ 应用重启触发成功")
    else:
        logger.warning("❌ 应用重启触发失败")
    
    logger.info("\n如果用户管理模块仍然无法访问，请检查日志获取更多信息")
    logger.info("========== 修复完成 ==========")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
 
 