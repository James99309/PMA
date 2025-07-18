#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断剩余的报价单权限问题
检查为什么修复后仍然看不到所有报价单
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('剩余问题诊断')

class RemainingQuotationIssuesDiagnostic:
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
    
    def check_quotation_list_logic(self):
        """检查报价单列表的查询逻辑"""
        logger.info("🔍 检查报价单列表的查询逻辑...")
        
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
        
        # 检查报价单的公司分布
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
        logger.info("📊 报价单按公司分布:")
        total_quotations = 0
        other_company_quotations = 0
        
        for company, count in company_stats:
            total_quotations += count
            if company != company_name:
                other_company_quotations += count
            
            is_user_company = "✅" if company == company_name else "❌"
            logger.info(f"  {is_user_company} {company}: {count} 个报价单")
        
        logger.info(f"\n📈 统计总结:")
        logger.info(f"  - 总报价单数: {total_quotations}")
        logger.info(f"  - 本公司报价单: {total_quotations - other_company_quotations}")
        logger.info(f"  - 其他公司报价单: {other_company_quotations}")
        logger.info(f"  - 系统级权限应该看到: {total_quotations} (全部)")
        
        conn.close()
        return {
            'total': total_quotations,
            'other_company': other_company_quotations,
            'user_company': company_name
        }
    
    def check_access_control_implementation(self):
        """检查访问控制的具体实现"""
        logger.info("\n🔍 检查访问控制的具体实现...")
        
        # 模拟get_viewable_data的逻辑
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 获取用户权限级别
        cursor.execute("""
            SELECT permission_level, can_view
            FROM role_permissions 
            WHERE role = 'solution_manager' AND module = 'quotation'
        """)
        
        perm_info = cursor.fetchone()
        if perm_info:
            perm_level, can_view = perm_info
            logger.info(f"📋 liuwei的quotation权限:")
            logger.info(f"  - 权限级别: {perm_level}")
            logger.info(f"  - 可查看: {can_view}")
            
            if perm_level == 'system':
                logger.info("✅ 确认为系统级权限，应该能看到所有报价单")
                
                # 模拟access_control.py中的系统级查询
                cursor.execute("SELECT COUNT(*) FROM quotations")
                system_count = cursor.fetchone()[0]
                logger.info(f"📊 系统级查询应该返回: {system_count} 个报价单")
        
        conn.close()
    
    def check_potential_filters(self):
        """检查可能的额外过滤条件"""
        logger.info("\n🔍 检查可能的额外过滤条件...")
        
        logger.info("💡 可能的过滤原因:")
        logger.info("1. 报价单列表视图中可能有额外的过滤逻辑")
        logger.info("2. 前端JavaScript可能有自动过滤")
        logger.info("3. URL参数中可能有隐藏的过滤条件")
        logger.info("4. 角色特殊处理逻辑可能覆盖了权限系统")
        
        # 检查quotation.py中是否有角色特殊处理
        logger.info("\n🔧 需要检查的代码位置:")
        logger.info("1. app/views/quotation.py 的 list_quotations 函数")
        logger.info("2. 查找是否有 solution_manager 角色的特殊处理")
        logger.info("3. 检查是否有默认的项目类型过滤")
        logger.info("4. 验证 get_viewable_data 的调用参数")
    
    def run_diagnosis(self):
        """运行完整诊断"""
        logger.info("🚀 开始诊断剩余的报价单权限问题...")
        logger.info("="*60)
        
        try:
            # 1. 检查报价单列表逻辑
            stats = self.check_quotation_list_logic()
            
            # 2. 检查访问控制实现
            self.check_access_control_implementation()
            
            # 3. 检查潜在过滤
            self.check_potential_filters()
            
            logger.info("\n" + "="*60)
            logger.info("🎯 诊断结果")
            logger.info("="*60)
            
            if stats['other_company'] > 0:
                logger.warning(f"⚠️ 存在 {stats['other_company']} 个其他公司的报价单")
                logger.warning("如果看不到这些报价单，说明权限检查仍有问题")
                logger.info("\n💡 下一步行动:")
                logger.info("1. 检查 quotation.py 中是否有角色特殊处理覆盖了权限系统")
                logger.info("2. 检查前端是否有自动应用的过滤条件")
                logger.info("3. 验证 can_view_quotation 函数是否正确调用")
            else:
                logger.info("ℹ️ 所有报价单都属于同一公司，权限问题可能不明显")
            
        except Exception as e:
            logger.error(f"❌ 诊断过程中出错: {str(e)}")

if __name__ == "__main__":
    diagnostic = RemainingQuotationIssuesDiagnostic()
    diagnostic.run_diagnosis()