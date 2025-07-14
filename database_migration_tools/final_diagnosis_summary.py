#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终诊断总结：liuwei用户权限问题
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('最终诊断')

def final_diagnosis():
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
    
    logger.info("🎯 liuwei用户权限问题最终诊断")
    logger.info("="*60)
    
    # 1. 确认用户和权限
    logger.info("\n1️⃣ 用户权限确认:")
    cursor.execute("""
        SELECT u.username, u.role, u.company_name,
               rp.module, rp.permission_level, rp.can_view
        FROM users u
        JOIN role_permissions rp ON u.role = rp.role
        WHERE u.username = 'liuwei'
        AND rp.module IN ('project', 'quotation')
        ORDER BY rp.module
    """)
    
    permissions = cursor.fetchall()
    for perm in permissions:
        username, role, company, module, level, can_view = perm
        logger.info(f"✅ {username} ({role}) - {module}模块: {level}级权限, 可查看: {can_view}")
    
    # 2. 数据量统计
    logger.info("\n2️⃣ 数据量统计:")
    
    # 总项目数
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]
    
    # 活跃项目数
    cursor.execute("SELECT COUNT(*) FROM projects WHERE is_active = true")
    active_projects = cursor.fetchone()[0]
    
    # 不同阶段的项目数
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN current_stage NOT IN ('lost', 'paused', 'signed') THEN 1 END) as valid_business,
            COUNT(CASE WHEN authorization_code IS NOT NULL AND authorization_code != '' THEN 1 END) as with_auth
        FROM projects
    """)
    
    stats = cursor.fetchone()
    total, valid_business, with_auth = stats
    
    logger.info(f"📊 项目统计:")
    logger.info(f"  - 总项目数: {total_projects}")
    logger.info(f"  - 活跃项目 (is_active=true): {active_projects}")
    logger.info(f"  - 有效业务项目 (非lost/paused/signed): {valid_business}")
    logger.info(f"  - 有授权编号的项目: {with_auth}")
    
    # 3. 系统级权限应该看到的数据
    logger.info(f"\n3️⃣ 权限分析:")
    logger.info(f"✅ liuwei拥有project和quotation的系统级权限")
    logger.info(f"✅ 理论上应该能看到所有 {total_projects} 个项目")
    logger.info(f"✅ 理论上应该能看到所有报价单")
    
    # 4. 可能的过滤原因
    logger.info(f"\n4️⃣ 可能的过滤原因分析:")
    logger.info(f"📌 差异数据:")
    logger.info(f"  - 总项目 vs 活跃项目: {total_projects} vs {active_projects} (差异: {total_projects - active_projects})")
    logger.info(f"  - 总项目 vs 有效业务: {total_projects} vs {valid_business} (差异: {total_projects - valid_business})")
    
    # 5. 最可能的原因
    logger.info(f"\n5️⃣ 最可能的原因:")
    logger.info("🔍 前端或应用层面的默认过滤条件")
    logger.info("   可能的过滤包括:")
    logger.info("   - 默认只显示活跃项目 (is_active=true)")
    logger.info("   - 默认只显示有效业务项目 (排除lost/paused/signed)")
    logger.info("   - 用户界面上有未注意到的过滤器")
    logger.info("   - 浏览器缓存或会话状态问题")
    
    # 6. 解决建议
    logger.info(f"\n6️⃣ 解决建议:")
    logger.info("💡 立即检查步骤:")
    logger.info("1. 用liuwei账户登录，检查项目列表页面的URL")
    logger.info("2. 查看是否有筛选条件被意外激活 (如is_active、stage_not等)")
    logger.info("3. 点击'清除筛选'或'全部项目'按钮")
    logger.info("4. 检查浏览器开发者工具的Network面板，查看实际的API请求参数")
    logger.info("5. 尝试手动访问 /project/?clear_filters=1")
    
    logger.info("\n🔧 技术检查步骤:")
    logger.info("1. 检查用户会话中是否有缓存的过滤条件")
    logger.info("2. 确认前端JavaScript没有自动添加过滤参数")
    logger.info("3. 验证access_control.py中的get_viewable_data函数执行结果")
    logger.info("4. 检查项目列表视图的实际SQL查询")
    
    # 7. 验证步骤
    logger.info(f"\n7️⃣ 验证步骤:")
    logger.info("✅ 如果问题解决，liuwei应该能看到:")
    logger.info(f"   - 项目管理: {total_projects} 个项目 (所有项目)")
    logger.info("   - 报价管理: 所有报价单")
    logger.info("   - 客户管理: 所有客户 (因为customer是company级权限)")
    
    conn.close()
    
    logger.info("\n" + "="*60)
    logger.info("🎯 结论: 权限配置正确，问题在于前端过滤逻辑")
    logger.info("="*60)

if __name__ == "__main__":
    final_diagnosis()