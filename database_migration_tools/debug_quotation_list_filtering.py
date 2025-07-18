#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试报价单列表过滤问题
检查为什么系统级权限用户看不到所有报价单
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('报价单列表调试')

class QuotationListDebugger:
    def __init__(self):
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"
    
    def parse_db_url(self, db_url):
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    def connect_db(self):
        params = self.parse_db_url(self.local_db_url)
        return psycopg2.connect(**params)
    
    def simulate_get_viewable_data(self):
        """模拟get_viewable_data函数对报价单的处理"""
        logger.info("🔍 模拟get_viewable_data函数对liuwei用户的处理...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 获取liuwei用户信息
        cursor.execute("""
            SELECT id, username, company_name, role
            FROM users WHERE username = 'liuwei'
        """)
        user_info = cursor.fetchone()
        user_id, username, company_name, role = user_info
        
        logger.info(f"👤 用户: {username} (ID: {user_id}, 公司: {company_name}, 角色: {role})")
        
        # 获取权限级别
        cursor.execute("""
            SELECT permission_level, can_view
            FROM role_permissions 
            WHERE role = %s AND module = 'quotation'
        """, (role,))
        
        perm_info = cursor.fetchone()
        if perm_info:
            perm_level, can_view = perm_info
            logger.info(f"📋 权限配置: {perm_level}级权限, 可查看: {can_view}")
            
            # 模拟系统级权限的查询
            if perm_level == 'system':
                logger.info("✅ 系统级权限 - 应该返回所有报价单")
                
                # 基础查询：所有报价单
                cursor.execute("SELECT COUNT(*) FROM quotations")
                total_quotations = cursor.fetchone()[0]
                logger.info(f"📊 基础查询结果: {total_quotations} 个报价单")
                
                # 分公司统计
                cursor.execute("""
                    SELECT 
                        u.company_name,
                        COUNT(q.id) as quotation_count
                    FROM quotations q
                    JOIN projects p ON q.project_id = p.id
                    JOIN users u ON p.owner_id = u.id
                    GROUP BY u.company_name
                    ORDER BY quotation_count DESC
                """)
                
                company_stats = cursor.fetchall()
                logger.info("📊 按公司分布:")
                for company, count in company_stats:
                    is_user_company = "✅" if company == company_name else "❌"
                    logger.info(f"  {is_user_company} {company}: {count} 个报价单")
        
        conn.close()
    
    def check_quotation_list_query_logic(self):
        """检查报价单列表的实际查询逻辑"""
        logger.info("\n🔍 检查报价单列表查询逻辑...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 模拟quotation.py中的查询构建过程
        logger.info("🔧 模拟list_quotations函数的查询构建:")
        
        # 1. 基础查询 (get_viewable_data的结果)
        cursor.execute("""
            SELECT COUNT(*) FROM quotations q
            -- 这里应该是get_viewable_data的结果，对于系统级权限应该是所有记录
        """)
        base_count = cursor.fetchone()[0]
        logger.info(f"1. 基础查询 (get_viewable_data): {base_count} 个报价单")
        
        # 2. 检查是否有默认的项目类型过滤
        logger.info("2. 检查默认的角色过滤逻辑:")
        logger.info("   - channel_manager 默认过滤: project_type = 'channel_follow'")
        logger.info("   - sales_director 默认过滤: project_type = 'marketing_focus'")
        logger.info("   - solution_manager: 无默认过滤 ✅")
        
        # 3. 检查可能的隐式过滤
        logger.info("\n3. 检查可能的隐式过滤条件:")
        
        # 检查活跃项目过滤
        cursor.execute("""
            SELECT COUNT(q.id)
            FROM quotations q
            JOIN projects p ON q.project_id = p.id
            WHERE p.is_active = true
        """)
        active_project_quotations = cursor.fetchone()[0]
        
        # 检查有效业务项目过滤
        cursor.execute("""
            SELECT COUNT(q.id)
            FROM quotations q
            JOIN projects p ON q.project_id = p.id
            WHERE p.current_stage NOT IN ('lost', 'paused', 'signed')
        """)
        valid_business_quotations = cursor.fetchone()[0]
        
        logger.info(f"   - 活跃项目的报价单: {active_project_quotations}")
        logger.info(f"   - 有效业务项目的报价单: {valid_business_quotations}")
        logger.info(f"   - 总报价单: {base_count}")
        
        # 4. 检查分页逻辑
        logger.info("\n4. 检查分页和加载逻辑:")
        default_limit = 20
        first_page_count = min(default_limit, base_count)
        logger.info(f"   - 默认第一页加载: {first_page_count} 个报价单")
        logger.info(f"   - 是否有更多数据: {base_count > default_limit}")
        
        conn.close()
    
    def check_frontend_filtering_possibilities(self):
        """检查前端可能的过滤逻辑"""
        logger.info("\n🔍 分析前端可能的过滤逻辑...")
        
        logger.info("💡 可能导致数据不完整的原因:")
        logger.info("1. **前端JavaScript过滤**:")
        logger.info("   - 可能有客户端筛选逻辑")
        logger.info("   - 可能基于用户角色自动应用过滤")
        
        logger.info("\n2. **URL参数过滤**:")
        logger.info("   - 可能有隐藏的URL参数")
        logger.info("   - 浏览器可能缓存了过滤参数")
        
        logger.info("\n3. **分页加载问题**:")
        logger.info("   - 可能在滚动加载时有问题")
        logger.info("   - Ajax请求可能没有正确处理系统级权限")
        
        logger.info("\n4. **会话状态问题**:")
        logger.info("   - 可能有会话级别的过滤缓存")
        logger.info("   - 权限检查可能使用了缓存的结果")
    
    def provide_debugging_steps(self):
        """提供具体的调试步骤"""
        logger.info("\n💡 建议的调试步骤:")
        
        logger.info("🔧 立即检查步骤:")
        logger.info("1. 用liuwei账户登录，访问报价单列表页面")
        logger.info("2. 打开浏览器开发者工具 -> Network 面板")
        logger.info("3. 刷新页面，查看 /quotations 请求")
        logger.info("4. 检查请求参数中是否有意外的过滤条件")
        
        logger.info("\n📊 数据验证步骤:")
        logger.info("1. 检查页面显示的总数是否正确")
        logger.info("2. 尝试不同的排序和筛选选项")
        logger.info("3. 测试滚动加载是否正常工作")
        logger.info("4. 对比其他系统级用户看到的数据")
        
        logger.info("\n🐛 技术调试步骤:")
        logger.info("1. 在quotation.py的list_quotations函数中添加调试日志")
        logger.info("2. 打印get_viewable_data的返回结果")
        logger.info("3. 打印最终查询的SQL和参数")
        logger.info("4. 检查total_count和实际返回的quotations数量")
    
    def create_test_query(self):
        """创建测试查询来验证权限"""
        logger.info("\n🧪 创建验证查询...")
        
        test_sql = """
-- 验证liuwei系统级权限应该看到的报价单数量
WITH user_info AS (
    SELECT id, username, company_name, role
    FROM users WHERE username = 'liuwei'
),
user_permissions AS (
    SELECT permission_level
    FROM role_permissions 
    WHERE role = (SELECT role FROM user_info) 
    AND module = 'quotation'
)
SELECT 
    (SELECT username FROM user_info) as username,
    (SELECT permission_level FROM user_permissions) as permission_level,
    COUNT(*) as should_see_quotations,
    COUNT(CASE WHEN u.company_name = (SELECT company_name FROM user_info) THEN 1 END) as company_quotations,
    COUNT(CASE WHEN u.company_name != (SELECT company_name FROM user_info) THEN 1 END) as other_company_quotations
FROM quotations q
JOIN projects p ON q.project_id = p.id
JOIN users u ON p.owner_id = u.id
CROSS JOIN user_info, user_permissions;
        """
        
        logger.info("📝 验证SQL查询:")
        logger.info(test_sql)
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute(test_sql)
        result = cursor.fetchone()
        
        if result:
            username, perm_level, total, company, other = result
            logger.info(f"\n📊 验证结果:")
            logger.info(f"  - 用户: {username}")
            logger.info(f"  - 权限级别: {perm_level}")
            logger.info(f"  - 应该看到的报价单总数: {total}")
            logger.info(f"  - 本公司报价单: {company}")
            logger.info(f"  - 其他公司报价单: {other}")
            
            if perm_level == 'system':
                logger.info(f"✅ 系统级权限应该看到所有 {total} 个报价单")
                if other > 0:
                    logger.warning(f"⚠️ 特别注意: 有 {other} 个其他公司的报价单应该被显示")
        
        conn.close()
    
    def run_debug(self):
        """运行完整的调试过程"""
        logger.info("🚀 开始调试报价单列表过滤问题...")
        logger.info("="*60)
        
        try:
            # 1. 模拟访问控制
            self.simulate_get_viewable_data()
            
            # 2. 检查查询逻辑
            self.check_quotation_list_query_logic()
            
            # 3. 分析前端过滤
            self.check_frontend_filtering_possibilities()
            
            # 4. 创建验证查询
            self.create_test_query()
            
            # 5. 提供调试步骤
            self.provide_debugging_steps()
            
            logger.info("\n" + "="*60)
            logger.info("🎯 调试总结")
            logger.info("="*60)
            logger.info("重点检查: 前端过滤逻辑和分页加载机制")
            logger.info("如果数据库查询正确，问题可能在前端实现")
            
        except Exception as e:
            logger.error(f"❌ 调试过程中出错: {str(e)}")

if __name__ == "__main__":
    debugger = QuotationListDebugger()
    debugger.run_debug()