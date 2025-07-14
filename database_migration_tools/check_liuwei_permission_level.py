#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查liuwei用户的权限级别和数据访问逻辑
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('权限级别检查')

def check_liuwei_permission_logic():
    local_db_url = "postgresql://nijie@localhost:5432/pma_local"
    
    def parse_db_url(db_url):
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    params = parse_db_url(local_db_url)
    conn = psycopg2.connect(**params)
    cursor = conn.cursor()
    
    # 1. 获取liuwei用户信息
    logger.info("🔍 获取liuwei用户信息...")
    cursor.execute("""
        SELECT id, username, role, company_name, department
        FROM users 
        WHERE username = 'liuwei'
    """)
    
    user_info = cursor.fetchone()
    if not user_info:
        logger.error("❌ 未找到liuwei用户")
        return
    
    user_id, username, role, company_name, department = user_info
    logger.info(f"👤 用户: {username} (ID: {user_id})")
    logger.info(f"  - 角色: {role}")
    logger.info(f"  - 公司: {company_name}")
    logger.info(f"  - 部门: {department}")
    
    # 2. 检查权限级别配置
    logger.info(f"\n🔍 检查{role}角色的权限级别...")
    cursor.execute("""
        SELECT module, permission_level, can_view, can_create, can_edit, can_delete
        FROM role_permissions 
        WHERE role = %s
        AND module IN ('project', 'quotation', 'customer')
        ORDER BY module
    """, (role,))
    
    role_permissions = cursor.fetchall()
    system_modules = []
    
    for perm in role_permissions:
        module, perm_level, can_view, can_create, can_edit, can_delete = perm
        logger.info(f"📋 {module}模块:")
        logger.info(f"  - 权限级别: {perm_level}")
        logger.info(f"  - 权限: 查看={can_view}, 创建={can_create}, 编辑={can_edit}, 删除={can_delete}")
        
        if perm_level == 'system':
            system_modules.append(module)
    
    logger.info(f"\n✅ 系统级权限模块: {system_modules}")
    
    # 3. 检查同公司用户
    logger.info(f"\n🔍 检查同公司用户...")
    cursor.execute("""
        SELECT id, username, role
        FROM users 
        WHERE company_name = %s
        AND id != %s
        ORDER BY id
    """, (company_name, user_id))
    
    company_users = cursor.fetchall()
    logger.info(f"📋 同公司用户 ({len(company_users)} 个):")
    company_user_ids = []
    for user in company_users:
        other_id, other_username, other_role = user
        company_user_ids.append(other_id)
        logger.info(f"  - {other_username} (ID: {other_id}, 角色: {other_role})")
    
    # 4. 检查项目数据访问逻辑
    logger.info(f"\n🔍 分析项目数据访问...")
    
    # 检查liuwei作为owner的项目
    cursor.execute("""
        SELECT COUNT(*)
        FROM projects 
        WHERE owner_id = %s
    """, (user_id,))
    owned_projects = cursor.fetchone()[0]
    
    # 检查总项目数
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]
    
    # 检查同公司用户的项目
    if company_user_ids:
        cursor.execute("""
            SELECT COUNT(*)
            FROM projects 
            WHERE owner_id = ANY(%s)
        """, (company_user_ids,))
        company_projects = cursor.fetchone()[0]
    else:
        company_projects = 0
    
    logger.info(f"📊 项目数据统计:")
    logger.info(f"  - 总项目数: {total_projects}")
    logger.info(f"  - liuwei拥有的项目: {owned_projects}")
    logger.info(f"  - 同公司用户项目: {company_projects}")
    logger.info(f"  - 系统级权限应该看到: {total_projects} (所有项目)")
    
    # 5. 检查报价单数据访问逻辑
    logger.info(f"\n🔍 分析报价单数据访问...")
    
    # 获取同公司用户的项目ID
    if company_user_ids:
        cursor.execute("""
            SELECT id
            FROM projects 
            WHERE owner_id = ANY(%s)
        """, (company_user_ids,))
        company_project_ids = [row[0] for row in cursor.fetchall()]
    else:
        company_project_ids = []
    
    # 检查总报价单数
    cursor.execute("SELECT COUNT(*) FROM quotations")
    total_quotations = cursor.fetchone()[0]
    
    # 检查liuwei拥有的报价单
    cursor.execute("""
        SELECT COUNT(*)
        FROM quotations 
        WHERE owner_id = %s
    """, (user_id,))
    owned_quotations = cursor.fetchone()[0]
    
    # 检查基于项目的报价单访问
    if company_project_ids:
        cursor.execute("""
            SELECT COUNT(*)
            FROM quotations 
            WHERE project_id = ANY(%s)
        """, (company_project_ids,))
        company_quotations = cursor.fetchone()[0]
    else:
        company_quotations = 0
    
    logger.info(f"📊 报价单数据统计:")
    logger.info(f"  - 总报价单数: {total_quotations}")
    logger.info(f"  - liuwei拥有的报价单: {owned_quotations}")
    logger.info(f"  - 同公司项目的报价单: {company_quotations}")
    logger.info(f"  - 系统级权限应该看到: {total_quotations} (所有报价单)")
    
    # 6. 分析问题
    logger.info(f"\n🎯 问题分析:")
    if 'project' in system_modules:
        logger.info("✅ project模块确实是系统级权限")
        if owned_projects + company_projects < total_projects:
            logger.warning("⚠️ 但用户可能看不到所有项目数据")
            logger.warning("可能原因:")
            logger.warning("1. 应用代码中有额外的过滤逻辑")
            logger.warning("2. 前端实现与权限配置不一致")
            logger.warning("3. 缓存或会话状态问题")
    
    if 'quotation' in system_modules:
        logger.info("✅ quotation模块确实是系统级权限")
        if owned_quotations + company_quotations < total_quotations:
            logger.warning("⚠️ 但用户可能看不到所有报价单数据")
    
    # 7. 建议检查
    logger.info(f"\n💡 建议检查:")
    logger.info("1. 检查项目列表页面的数据库查询日志")
    logger.info("2. 确认前端是否有额外的过滤参数")
    logger.info("3. 检查用户会话中的权限缓存")
    logger.info("4. 验证get_viewable_data函数的实际执行逻辑")
    logger.info("5. 检查是否有中间件过滤数据")
    
    conn.close()

if __name__ == "__main__":
    check_liuwei_permission_logic()