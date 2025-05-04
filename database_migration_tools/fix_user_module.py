#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理模块修复工具

专门用于修复用户管理模块，解决在Render上访问/user/list空白的问题
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_fix.log')
    ]
)
logger = logging.getLogger('用户管理模块修复')

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

def examine_user_table(conn):
    """检查用户表结构和数据"""
    try:
        with conn.cursor() as cur:
            # 查询用户表结构
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'user'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            logger.info("用户表结构:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]}" + (f"({col[2]})" if col[2] else ""))
            
            # 查询用户表数据样本
            cur.execute('SELECT id, username, email, role_id, is_active, is_department_manager FROM "user" LIMIT 5;')
            users = cur.fetchall()
            logger.info(f"用户表数据样本({len(users)}条):")
            for user in users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 角色ID: {user[3]}, 活跃: {user[4]}, 部门管理员: {user[5]}")
            
            # 查询用户总数
            cur.execute('SELECT COUNT(*) FROM "user";')
            user_count = cur.fetchone()[0]
            logger.info(f"用户表总记录数: {user_count}")
            
            return True
    except Exception as e:
        logger.error(f"检查用户表时出错: {str(e)}")
        return False

def fix_user_list_template():
    """修复用户列表模板"""
    template_file = Path('app/templates/user/list.html')
    
    if not template_file.exists():
        logger.error(f"用户列表模板文件不存在: {template_file}")
        return False
    
    try:
        # 读取模板内容
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户列表模板总字节数: {len(content)}")
        
        # 检查是否有endblock不匹配问题
        block_count = content.count("{% block")
        endblock_count = content.count("{% endblock")
        
        logger.info(f"模板中block标签数: {block_count}, endblock标签数: {endblock_count}")
        
        if block_count != endblock_count:
            logger.warning(f"模板中block和endblock数量不匹配: {block_count} vs {endblock_count}")
            
            # 查找所有block标签
            import re
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            
            # 查找所有endblock标签
            endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
            endblocks = re.findall(endblock_pattern, content)
            endblocks = [eb for eb in endblocks if eb]  # 过滤掉空值
            
            logger.info(f"Block标签: {blocks}")
            logger.info(f"Endblock标签: {endblocks}")
            
            # 查找缺失的endblock
            missing_endblocks = set(blocks) - set(endblocks)
            if missing_endblocks:
                logger.warning(f"缺失的endblock标签: {missing_endblocks}")
                
                # 为最后一个缺失的block添加endblock标签
                new_content = content
                for block in missing_endblocks:
                    if not new_content.endswith('\n'):
                        new_content += '\n'
                    new_content += f"{{% endblock {block} %}}\n"
                    logger.info(f"添加缺失的endblock标签: {block}")
                
                # 写回文件
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("已修复用户列表模板中的endblock标签")
                return True
        
        return False
    except Exception as e:
        logger.error(f"修复用户列表模板时出错: {str(e)}")
        return False

def fix_user_route():
    """修复用户路由处理"""
    route_file = Path('app/routes/user.py')
    
    if not route_file.exists():
        logger.warning(f"用户路由文件不存在: {route_file}")
        return False
    
    try:
        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户路由文件总字节数: {len(content)}")
        
        # 检查路由处理逻辑
        if 'user_list' in content or 'list_users' in content:
            logger.info("用户路由文件中存在用户列表处理函数")
        else:
            logger.warning("用户路由文件中可能缺少用户列表处理函数")
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户路由时出错: {str(e)}")
        return False

def fix_user_view():
    """修复用户视图处理"""
    view_file = Path('app/views/user.py')
    
    if not view_file.exists():
        logger.warning(f"用户视图文件不存在: {view_file}")
        return False
    
    try:
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户视图文件总字节数: {len(content)}")
        
        # 检查视图处理逻辑中常见问题
        if 'render_template("user/list.html"' in content or "render_template('user/list.html'" in content:
            logger.info("用户视图文件中存在用户列表模板渲染")
            
            # 检查错误处理
            has_error_handling = 'try:' in content and 'except' in content
            logger.info(f"用户视图中包含异常处理: {has_error_handling}")
            
            # 如果没有错误处理，可以考虑添加
            if not has_error_handling and 'def list_' in content:
                logger.warning("用户列表视图可能缺少错误处理")
                
                # 分析list_users或类似函数
                import re
                list_func_pattern = r'def\s+(list_\w+).*?:'
                list_func_match = re.search(list_func_pattern, content)
                
                if list_func_match:
                    list_func_name = list_func_match.group(1)
                    logger.info(f"找到列表函数: {list_func_name}")
                    
                    # 检查函数体，看是否需要添加错误处理
                    func_body_pattern = f'def\\s+{list_func_name}.*?\\{{(.*?)\\}}'
                    func_body_match = re.search(func_body_pattern, content, re.DOTALL)
                    
                    # 如果找到函数体且没有错误处理，可以添加
                    # 这部分逻辑比较复杂，暂不实现自动修复
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户视图时出错: {str(e)}")
        return False

def fix_is_department_manager_field(conn):
    """修复is_department_manager字段问题"""
    try:
        with conn.cursor() as cur:
            # 检查字段是否存在
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("is_department_manager字段不存在，无法修复")
                return False
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，检查数据")
                
                # 检查是否有NULL值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager IS NULL;")
                null_count = cur.fetchone()[0]
                logger.info(f"is_department_manager为NULL的记录数: {null_count}")
                
                # 检查是否有布尔值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = true;")
                true_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = false;")
                false_count = cur.fetchone()[0]
                
                logger.info(f"is_department_manager为true的记录数: {true_count}")
                logger.info(f"is_department_manager为false的记录数: {false_count}")
                
                if null_count + true_count + false_count == 0:
                    logger.warning("is_department_manager字段可能存在问题，所有值都为空")
                
                return False  # 无需修复
            else:
                logger.info(f"is_department_manager字段类型为: {data_type}，需要修复为布尔类型")
                
                # 查看字段当前值
                cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
                values = [str(row[0]) for row in cur.fetchall()]
                logger.info(f"is_department_manager字段当前值: {values}")
                
                # 修复字段类型
                try:
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
                    logger.info("成功修复is_department_manager字段类型为布尔类型")
                    return True
                except Exception as e:
                    conn.rollback()
                    logger.error(f"修复is_department_manager字段类型时出错: {str(e)}")
                    return False
    except Exception as e:
        logger.error(f"检查is_department_manager字段时出错: {str(e)}")
        return False

def fix_user_module():
    """修复用户管理模块问题"""
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法修复数据库相关问题")
        db_conn = None
    else:
        # 连接数据库
        db_conn = connect_to_db(db_url)
    
    fixed_something = False
    
    try:
        # 修复文件问题
        template_fixed = fix_user_list_template()
        route_fixed = fix_user_route()
        view_fixed = fix_user_view()
        
        fixed_something = template_fixed or route_fixed or view_fixed
        
        # 修复数据库问题
        if db_conn:
            # 检查用户表
            examine_user_table(db_conn)
            
            # 修复is_department_manager字段
            db_fixed = fix_is_department_manager_field(db_conn)
            fixed_something = fixed_something or db_fixed
        
        logger.info(f"用户管理模块修复{'完成' if fixed_something else '未发现需要修复的问题'}")
        return fixed_something
    except Exception as e:
        logger.error(f"修复用户管理模块时出错: {str(e)}")
        return False
    finally:
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    logger.info("=== 开始修复用户管理模块 ===")
    fix_user_module()
    logger.info("=== 用户管理模块修复完成 ===") 
# -*- coding: utf-8 -*-
"""
用户管理模块修复工具

专门用于修复用户管理模块，解决在Render上访问/user/list空白的问题
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_fix.log')
    ]
)
logger = logging.getLogger('用户管理模块修复')

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

def examine_user_table(conn):
    """检查用户表结构和数据"""
    try:
        with conn.cursor() as cur:
            # 查询用户表结构
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'user'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            logger.info("用户表结构:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]}" + (f"({col[2]})" if col[2] else ""))
            
            # 查询用户表数据样本
            cur.execute('SELECT id, username, email, role_id, is_active, is_department_manager FROM "user" LIMIT 5;')
            users = cur.fetchall()
            logger.info(f"用户表数据样本({len(users)}条):")
            for user in users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 角色ID: {user[3]}, 活跃: {user[4]}, 部门管理员: {user[5]}")
            
            # 查询用户总数
            cur.execute('SELECT COUNT(*) FROM "user";')
            user_count = cur.fetchone()[0]
            logger.info(f"用户表总记录数: {user_count}")
            
            return True
    except Exception as e:
        logger.error(f"检查用户表时出错: {str(e)}")
        return False

def fix_user_list_template():
    """修复用户列表模板"""
    template_file = Path('app/templates/user/list.html')
    
    if not template_file.exists():
        logger.error(f"用户列表模板文件不存在: {template_file}")
        return False
    
    try:
        # 读取模板内容
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户列表模板总字节数: {len(content)}")
        
        # 检查是否有endblock不匹配问题
        block_count = content.count("{% block")
        endblock_count = content.count("{% endblock")
        
        logger.info(f"模板中block标签数: {block_count}, endblock标签数: {endblock_count}")
        
        if block_count != endblock_count:
            logger.warning(f"模板中block和endblock数量不匹配: {block_count} vs {endblock_count}")
            
            # 查找所有block标签
            import re
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            
            # 查找所有endblock标签
            endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
            endblocks = re.findall(endblock_pattern, content)
            endblocks = [eb for eb in endblocks if eb]  # 过滤掉空值
            
            logger.info(f"Block标签: {blocks}")
            logger.info(f"Endblock标签: {endblocks}")
            
            # 查找缺失的endblock
            missing_endblocks = set(blocks) - set(endblocks)
            if missing_endblocks:
                logger.warning(f"缺失的endblock标签: {missing_endblocks}")
                
                # 为最后一个缺失的block添加endblock标签
                new_content = content
                for block in missing_endblocks:
                    if not new_content.endswith('\n'):
                        new_content += '\n'
                    new_content += f"{{% endblock {block} %}}\n"
                    logger.info(f"添加缺失的endblock标签: {block}")
                
                # 写回文件
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("已修复用户列表模板中的endblock标签")
                return True
        
        return False
    except Exception as e:
        logger.error(f"修复用户列表模板时出错: {str(e)}")
        return False

def fix_user_route():
    """修复用户路由处理"""
    route_file = Path('app/routes/user.py')
    
    if not route_file.exists():
        logger.warning(f"用户路由文件不存在: {route_file}")
        return False
    
    try:
        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户路由文件总字节数: {len(content)}")
        
        # 检查路由处理逻辑
        if 'user_list' in content or 'list_users' in content:
            logger.info("用户路由文件中存在用户列表处理函数")
        else:
            logger.warning("用户路由文件中可能缺少用户列表处理函数")
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户路由时出错: {str(e)}")
        return False

def fix_user_view():
    """修复用户视图处理"""
    view_file = Path('app/views/user.py')
    
    if not view_file.exists():
        logger.warning(f"用户视图文件不存在: {view_file}")
        return False
    
    try:
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户视图文件总字节数: {len(content)}")
        
        # 检查视图处理逻辑中常见问题
        if 'render_template("user/list.html"' in content or "render_template('user/list.html'" in content:
            logger.info("用户视图文件中存在用户列表模板渲染")
            
            # 检查错误处理
            has_error_handling = 'try:' in content and 'except' in content
            logger.info(f"用户视图中包含异常处理: {has_error_handling}")
            
            # 如果没有错误处理，可以考虑添加
            if not has_error_handling and 'def list_' in content:
                logger.warning("用户列表视图可能缺少错误处理")
                
                # 分析list_users或类似函数
                import re
                list_func_pattern = r'def\s+(list_\w+).*?:'
                list_func_match = re.search(list_func_pattern, content)
                
                if list_func_match:
                    list_func_name = list_func_match.group(1)
                    logger.info(f"找到列表函数: {list_func_name}")
                    
                    # 检查函数体，看是否需要添加错误处理
                    func_body_pattern = f'def\\s+{list_func_name}.*?\\{{(.*?)\\}}'
                    func_body_match = re.search(func_body_pattern, content, re.DOTALL)
                    
                    # 如果找到函数体且没有错误处理，可以添加
                    # 这部分逻辑比较复杂，暂不实现自动修复
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户视图时出错: {str(e)}")
        return False

def fix_is_department_manager_field(conn):
    """修复is_department_manager字段问题"""
    try:
        with conn.cursor() as cur:
            # 检查字段是否存在
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("is_department_manager字段不存在，无法修复")
                return False
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，检查数据")
                
                # 检查是否有NULL值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager IS NULL;")
                null_count = cur.fetchone()[0]
                logger.info(f"is_department_manager为NULL的记录数: {null_count}")
                
                # 检查是否有布尔值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = true;")
                true_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = false;")
                false_count = cur.fetchone()[0]
                
                logger.info(f"is_department_manager为true的记录数: {true_count}")
                logger.info(f"is_department_manager为false的记录数: {false_count}")
                
                if null_count + true_count + false_count == 0:
                    logger.warning("is_department_manager字段可能存在问题，所有值都为空")
                
                return False  # 无需修复
            else:
                logger.info(f"is_department_manager字段类型为: {data_type}，需要修复为布尔类型")
                
                # 查看字段当前值
                cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
                values = [str(row[0]) for row in cur.fetchall()]
                logger.info(f"is_department_manager字段当前值: {values}")
                
                # 修复字段类型
                try:
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
                    logger.info("成功修复is_department_manager字段类型为布尔类型")
                    return True
                except Exception as e:
                    conn.rollback()
                    logger.error(f"修复is_department_manager字段类型时出错: {str(e)}")
                    return False
    except Exception as e:
        logger.error(f"检查is_department_manager字段时出错: {str(e)}")
        return False

def fix_user_module():
    """修复用户管理模块问题"""
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法修复数据库相关问题")
        db_conn = None
    else:
        # 连接数据库
        db_conn = connect_to_db(db_url)
    
    fixed_something = False
    
    try:
        # 修复文件问题
        template_fixed = fix_user_list_template()
        route_fixed = fix_user_route()
        view_fixed = fix_user_view()
        
        fixed_something = template_fixed or route_fixed or view_fixed
        
        # 修复数据库问题
        if db_conn:
            # 检查用户表
            examine_user_table(db_conn)
            
            # 修复is_department_manager字段
            db_fixed = fix_is_department_manager_field(db_conn)
            fixed_something = fixed_something or db_fixed
        
        logger.info(f"用户管理模块修复{'完成' if fixed_something else '未发现需要修复的问题'}")
        return fixed_something
    except Exception as e:
        logger.error(f"修复用户管理模块时出错: {str(e)}")
        return False
    finally:
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    logger.info("=== 开始修复用户管理模块 ===")
    fix_user_module()
    logger.info("=== 用户管理模块修复完成 ===") 
 
 
# -*- coding: utf-8 -*-
"""
用户管理模块修复工具

专门用于修复用户管理模块，解决在Render上访问/user/list空白的问题
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_fix.log')
    ]
)
logger = logging.getLogger('用户管理模块修复')

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

def examine_user_table(conn):
    """检查用户表结构和数据"""
    try:
        with conn.cursor() as cur:
            # 查询用户表结构
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'user'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            logger.info("用户表结构:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]}" + (f"({col[2]})" if col[2] else ""))
            
            # 查询用户表数据样本
            cur.execute('SELECT id, username, email, role_id, is_active, is_department_manager FROM "user" LIMIT 5;')
            users = cur.fetchall()
            logger.info(f"用户表数据样本({len(users)}条):")
            for user in users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 角色ID: {user[3]}, 活跃: {user[4]}, 部门管理员: {user[5]}")
            
            # 查询用户总数
            cur.execute('SELECT COUNT(*) FROM "user";')
            user_count = cur.fetchone()[0]
            logger.info(f"用户表总记录数: {user_count}")
            
            return True
    except Exception as e:
        logger.error(f"检查用户表时出错: {str(e)}")
        return False

def fix_user_list_template():
    """修复用户列表模板"""
    template_file = Path('app/templates/user/list.html')
    
    if not template_file.exists():
        logger.error(f"用户列表模板文件不存在: {template_file}")
        return False
    
    try:
        # 读取模板内容
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户列表模板总字节数: {len(content)}")
        
        # 检查是否有endblock不匹配问题
        block_count = content.count("{% block")
        endblock_count = content.count("{% endblock")
        
        logger.info(f"模板中block标签数: {block_count}, endblock标签数: {endblock_count}")
        
        if block_count != endblock_count:
            logger.warning(f"模板中block和endblock数量不匹配: {block_count} vs {endblock_count}")
            
            # 查找所有block标签
            import re
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            
            # 查找所有endblock标签
            endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
            endblocks = re.findall(endblock_pattern, content)
            endblocks = [eb for eb in endblocks if eb]  # 过滤掉空值
            
            logger.info(f"Block标签: {blocks}")
            logger.info(f"Endblock标签: {endblocks}")
            
            # 查找缺失的endblock
            missing_endblocks = set(blocks) - set(endblocks)
            if missing_endblocks:
                logger.warning(f"缺失的endblock标签: {missing_endblocks}")
                
                # 为最后一个缺失的block添加endblock标签
                new_content = content
                for block in missing_endblocks:
                    if not new_content.endswith('\n'):
                        new_content += '\n'
                    new_content += f"{{% endblock {block} %}}\n"
                    logger.info(f"添加缺失的endblock标签: {block}")
                
                # 写回文件
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("已修复用户列表模板中的endblock标签")
                return True
        
        return False
    except Exception as e:
        logger.error(f"修复用户列表模板时出错: {str(e)}")
        return False

def fix_user_route():
    """修复用户路由处理"""
    route_file = Path('app/routes/user.py')
    
    if not route_file.exists():
        logger.warning(f"用户路由文件不存在: {route_file}")
        return False
    
    try:
        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户路由文件总字节数: {len(content)}")
        
        # 检查路由处理逻辑
        if 'user_list' in content or 'list_users' in content:
            logger.info("用户路由文件中存在用户列表处理函数")
        else:
            logger.warning("用户路由文件中可能缺少用户列表处理函数")
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户路由时出错: {str(e)}")
        return False

def fix_user_view():
    """修复用户视图处理"""
    view_file = Path('app/views/user.py')
    
    if not view_file.exists():
        logger.warning(f"用户视图文件不存在: {view_file}")
        return False
    
    try:
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户视图文件总字节数: {len(content)}")
        
        # 检查视图处理逻辑中常见问题
        if 'render_template("user/list.html"' in content or "render_template('user/list.html'" in content:
            logger.info("用户视图文件中存在用户列表模板渲染")
            
            # 检查错误处理
            has_error_handling = 'try:' in content and 'except' in content
            logger.info(f"用户视图中包含异常处理: {has_error_handling}")
            
            # 如果没有错误处理，可以考虑添加
            if not has_error_handling and 'def list_' in content:
                logger.warning("用户列表视图可能缺少错误处理")
                
                # 分析list_users或类似函数
                import re
                list_func_pattern = r'def\s+(list_\w+).*?:'
                list_func_match = re.search(list_func_pattern, content)
                
                if list_func_match:
                    list_func_name = list_func_match.group(1)
                    logger.info(f"找到列表函数: {list_func_name}")
                    
                    # 检查函数体，看是否需要添加错误处理
                    func_body_pattern = f'def\\s+{list_func_name}.*?\\{{(.*?)\\}}'
                    func_body_match = re.search(func_body_pattern, content, re.DOTALL)
                    
                    # 如果找到函数体且没有错误处理，可以添加
                    # 这部分逻辑比较复杂，暂不实现自动修复
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户视图时出错: {str(e)}")
        return False

def fix_is_department_manager_field(conn):
    """修复is_department_manager字段问题"""
    try:
        with conn.cursor() as cur:
            # 检查字段是否存在
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("is_department_manager字段不存在，无法修复")
                return False
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，检查数据")
                
                # 检查是否有NULL值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager IS NULL;")
                null_count = cur.fetchone()[0]
                logger.info(f"is_department_manager为NULL的记录数: {null_count}")
                
                # 检查是否有布尔值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = true;")
                true_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = false;")
                false_count = cur.fetchone()[0]
                
                logger.info(f"is_department_manager为true的记录数: {true_count}")
                logger.info(f"is_department_manager为false的记录数: {false_count}")
                
                if null_count + true_count + false_count == 0:
                    logger.warning("is_department_manager字段可能存在问题，所有值都为空")
                
                return False  # 无需修复
            else:
                logger.info(f"is_department_manager字段类型为: {data_type}，需要修复为布尔类型")
                
                # 查看字段当前值
                cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
                values = [str(row[0]) for row in cur.fetchall()]
                logger.info(f"is_department_manager字段当前值: {values}")
                
                # 修复字段类型
                try:
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
                    logger.info("成功修复is_department_manager字段类型为布尔类型")
                    return True
                except Exception as e:
                    conn.rollback()
                    logger.error(f"修复is_department_manager字段类型时出错: {str(e)}")
                    return False
    except Exception as e:
        logger.error(f"检查is_department_manager字段时出错: {str(e)}")
        return False

def fix_user_module():
    """修复用户管理模块问题"""
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法修复数据库相关问题")
        db_conn = None
    else:
        # 连接数据库
        db_conn = connect_to_db(db_url)
    
    fixed_something = False
    
    try:
        # 修复文件问题
        template_fixed = fix_user_list_template()
        route_fixed = fix_user_route()
        view_fixed = fix_user_view()
        
        fixed_something = template_fixed or route_fixed or view_fixed
        
        # 修复数据库问题
        if db_conn:
            # 检查用户表
            examine_user_table(db_conn)
            
            # 修复is_department_manager字段
            db_fixed = fix_is_department_manager_field(db_conn)
            fixed_something = fixed_something or db_fixed
        
        logger.info(f"用户管理模块修复{'完成' if fixed_something else '未发现需要修复的问题'}")
        return fixed_something
    except Exception as e:
        logger.error(f"修复用户管理模块时出错: {str(e)}")
        return False
    finally:
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    logger.info("=== 开始修复用户管理模块 ===")
    fix_user_module()
    logger.info("=== 用户管理模块修复完成 ===") 
# -*- coding: utf-8 -*-
"""
用户管理模块修复工具

专门用于修复用户管理模块，解决在Render上访问/user/list空白的问题
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_fix.log')
    ]
)
logger = logging.getLogger('用户管理模块修复')

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

def examine_user_table(conn):
    """检查用户表结构和数据"""
    try:
        with conn.cursor() as cur:
            # 查询用户表结构
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'user'
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            logger.info("用户表结构:")
            for col in columns:
                logger.info(f"  - {col[0]}: {col[1]}" + (f"({col[2]})" if col[2] else ""))
            
            # 查询用户表数据样本
            cur.execute('SELECT id, username, email, role_id, is_active, is_department_manager FROM "user" LIMIT 5;')
            users = cur.fetchall()
            logger.info(f"用户表数据样本({len(users)}条):")
            for user in users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 角色ID: {user[3]}, 活跃: {user[4]}, 部门管理员: {user[5]}")
            
            # 查询用户总数
            cur.execute('SELECT COUNT(*) FROM "user";')
            user_count = cur.fetchone()[0]
            logger.info(f"用户表总记录数: {user_count}")
            
            return True
    except Exception as e:
        logger.error(f"检查用户表时出错: {str(e)}")
        return False

def fix_user_list_template():
    """修复用户列表模板"""
    template_file = Path('app/templates/user/list.html')
    
    if not template_file.exists():
        logger.error(f"用户列表模板文件不存在: {template_file}")
        return False
    
    try:
        # 读取模板内容
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户列表模板总字节数: {len(content)}")
        
        # 检查是否有endblock不匹配问题
        block_count = content.count("{% block")
        endblock_count = content.count("{% endblock")
        
        logger.info(f"模板中block标签数: {block_count}, endblock标签数: {endblock_count}")
        
        if block_count != endblock_count:
            logger.warning(f"模板中block和endblock数量不匹配: {block_count} vs {endblock_count}")
            
            # 查找所有block标签
            import re
            block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            blocks = re.findall(block_pattern, content)
            
            # 查找所有endblock标签
            endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
            endblocks = re.findall(endblock_pattern, content)
            endblocks = [eb for eb in endblocks if eb]  # 过滤掉空值
            
            logger.info(f"Block标签: {blocks}")
            logger.info(f"Endblock标签: {endblocks}")
            
            # 查找缺失的endblock
            missing_endblocks = set(blocks) - set(endblocks)
            if missing_endblocks:
                logger.warning(f"缺失的endblock标签: {missing_endblocks}")
                
                # 为最后一个缺失的block添加endblock标签
                new_content = content
                for block in missing_endblocks:
                    if not new_content.endswith('\n'):
                        new_content += '\n'
                    new_content += f"{{% endblock {block} %}}\n"
                    logger.info(f"添加缺失的endblock标签: {block}")
                
                # 写回文件
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("已修复用户列表模板中的endblock标签")
                return True
        
        return False
    except Exception as e:
        logger.error(f"修复用户列表模板时出错: {str(e)}")
        return False

def fix_user_route():
    """修复用户路由处理"""
    route_file = Path('app/routes/user.py')
    
    if not route_file.exists():
        logger.warning(f"用户路由文件不存在: {route_file}")
        return False
    
    try:
        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户路由文件总字节数: {len(content)}")
        
        # 检查路由处理逻辑
        if 'user_list' in content or 'list_users' in content:
            logger.info("用户路由文件中存在用户列表处理函数")
        else:
            logger.warning("用户路由文件中可能缺少用户列表处理函数")
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户路由时出错: {str(e)}")
        return False

def fix_user_view():
    """修复用户视图处理"""
    view_file = Path('app/views/user.py')
    
    if not view_file.exists():
        logger.warning(f"用户视图文件不存在: {view_file}")
        return False
    
    try:
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"用户视图文件总字节数: {len(content)}")
        
        # 检查视图处理逻辑中常见问题
        if 'render_template("user/list.html"' in content or "render_template('user/list.html'" in content:
            logger.info("用户视图文件中存在用户列表模板渲染")
            
            # 检查错误处理
            has_error_handling = 'try:' in content and 'except' in content
            logger.info(f"用户视图中包含异常处理: {has_error_handling}")
            
            # 如果没有错误处理，可以考虑添加
            if not has_error_handling and 'def list_' in content:
                logger.warning("用户列表视图可能缺少错误处理")
                
                # 分析list_users或类似函数
                import re
                list_func_pattern = r'def\s+(list_\w+).*?:'
                list_func_match = re.search(list_func_pattern, content)
                
                if list_func_match:
                    list_func_name = list_func_match.group(1)
                    logger.info(f"找到列表函数: {list_func_name}")
                    
                    # 检查函数体，看是否需要添加错误处理
                    func_body_pattern = f'def\\s+{list_func_name}.*?\\{{(.*?)\\}}'
                    func_body_match = re.search(func_body_pattern, content, re.DOTALL)
                    
                    # 如果找到函数体且没有错误处理，可以添加
                    # 这部分逻辑比较复杂，暂不实现自动修复
        
        return False  # 无需修复
    except Exception as e:
        logger.error(f"检查用户视图时出错: {str(e)}")
        return False

def fix_is_department_manager_field(conn):
    """修复is_department_manager字段问题"""
    try:
        with conn.cursor() as cur:
            # 检查字段是否存在
            cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager');")
            if not cur.fetchone()[0]:
                logger.warning("is_department_manager字段不存在，无法修复")
                return False
            
            # 获取字段类型
            cur.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'user' AND column_name = 'is_department_manager';")
            data_type = cur.fetchone()[0]
            
            if data_type.lower() == 'boolean':
                logger.info("is_department_manager字段已经是布尔类型，检查数据")
                
                # 检查是否有NULL值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager IS NULL;")
                null_count = cur.fetchone()[0]
                logger.info(f"is_department_manager为NULL的记录数: {null_count}")
                
                # 检查是否有布尔值
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = true;")
                true_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM \"user\" WHERE is_department_manager = false;")
                false_count = cur.fetchone()[0]
                
                logger.info(f"is_department_manager为true的记录数: {true_count}")
                logger.info(f"is_department_manager为false的记录数: {false_count}")
                
                if null_count + true_count + false_count == 0:
                    logger.warning("is_department_manager字段可能存在问题，所有值都为空")
                
                return False  # 无需修复
            else:
                logger.info(f"is_department_manager字段类型为: {data_type}，需要修复为布尔类型")
                
                # 查看字段当前值
                cur.execute("SELECT DISTINCT is_department_manager FROM \"user\";")
                values = [str(row[0]) for row in cur.fetchall()]
                logger.info(f"is_department_manager字段当前值: {values}")
                
                # 修复字段类型
                try:
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
                    logger.info("成功修复is_department_manager字段类型为布尔类型")
                    return True
                except Exception as e:
                    conn.rollback()
                    logger.error(f"修复is_department_manager字段类型时出错: {str(e)}")
                    return False
    except Exception as e:
        logger.error(f"检查is_department_manager字段时出错: {str(e)}")
        return False

def fix_user_module():
    """修复用户管理模块问题"""
    # 从环境变量获取数据库URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("环境变量DATABASE_URL未设置，无法修复数据库相关问题")
        db_conn = None
    else:
        # 连接数据库
        db_conn = connect_to_db(db_url)
    
    fixed_something = False
    
    try:
        # 修复文件问题
        template_fixed = fix_user_list_template()
        route_fixed = fix_user_route()
        view_fixed = fix_user_view()
        
        fixed_something = template_fixed or route_fixed or view_fixed
        
        # 修复数据库问题
        if db_conn:
            # 检查用户表
            examine_user_table(db_conn)
            
            # 修复is_department_manager字段
            db_fixed = fix_is_department_manager_field(db_conn)
            fixed_something = fixed_something or db_fixed
        
        logger.info(f"用户管理模块修复{'完成' if fixed_something else '未发现需要修复的问题'}")
        return fixed_something
    except Exception as e:
        logger.error(f"修复用户管理模块时出错: {str(e)}")
        return False
    finally:
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    logger.info("=== 开始修复用户管理模块 ===")
    fix_user_module()
    logger.info("=== 用户管理模块修复完成 ===") 
 
 