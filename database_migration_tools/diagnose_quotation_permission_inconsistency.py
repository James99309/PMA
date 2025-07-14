#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断报价模块权限不一致问题
分析为什么liuwei用户在项目模块有系统级权限能看到所有项目，
但在报价模块的系统级权限却无法看到所有报价单
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('报价权限诊断')

class QuotationPermissionDiagnostic:
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
    
    def check_quotation_project_relationship(self):
        """检查报价单与项目的关联关系"""
        logger.info("🔍 检查报价单与项目的关联关系...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 获取liuwei用户信息
        cursor.execute("""
            SELECT id, username, company_name, role
            FROM users WHERE username = 'liuwei'
        """)
        user_info = cursor.fetchone()
        user_id, username, company_name, role = user_info
        
        logger.info(f"👤 用户: {username} (ID: {user_id}, 公司: {company_name})")
        
        # 1. 检查报价单总数和分布
        cursor.execute("SELECT COUNT(*) FROM quotations")
        total_quotations = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM quotations q
            JOIN projects p ON q.project_id = p.id
            JOIN users u ON p.owner_id = u.id
            WHERE u.company_name = %s
        """, (company_name,))
        company_quotations = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM quotations 
            WHERE owner_id = %s
        """, (user_id,))
        owned_quotations = cursor.fetchone()[0]
        
        logger.info(f"📊 报价单统计:")
        logger.info(f"  - 总报价单数: {total_quotations}")
        logger.info(f"  - 本公司项目的报价单: {company_quotations}")
        logger.info(f"  - liuwei拥有的报价单: {owned_quotations}")
        logger.info(f"  - 其他公司报价单: {total_quotations - company_quotations}")
        
        # 2. 检查具体的报价单归属
        cursor.execute("""
            SELECT q.id, q.quotation_number, q.owner_id, q.project_id,
                   p.project_name, p.owner_id as project_owner_id,
                   u1.username as quotation_owner, u1.company_name as quot_company,
                   u2.username as project_owner, u2.company_name as proj_company
            FROM quotations q
            JOIN projects p ON q.project_id = p.id
            LEFT JOIN users u1 ON q.owner_id = u1.id
            LEFT JOIN users u2 ON p.owner_id = u2.id
            ORDER BY q.id
            LIMIT 20
        """)
        
        quotation_details = cursor.fetchall()
        logger.info(f"\n📋 报价单详情分析 (前20个):")
        
        system_level_should_see = 0
        company_level_would_see = 0
        
        for quot in quotation_details:
            q_id, q_number, q_owner_id, proj_id, proj_name, proj_owner_id, q_owner, q_company, p_owner, p_company = quot
            
            # 系统级权限应该看到所有
            system_level_should_see += 1
            
            # 企业级权限判断
            if p_company == company_name or q_company == company_name:
                company_level_would_see += 1
            
            is_company_related = (p_company == company_name) or (q_company == company_name)
            
            logger.info(f"  - 报价单 {q_id} ({q_number}):")
            logger.info(f"    项目: {proj_name} (ID: {proj_id})")
            logger.info(f"    报价单所有者: {q_owner} ({q_company})")
            logger.info(f"    项目所有者: {p_owner} ({p_company})")
            logger.info(f"    与本公司相关: {is_company_related}")
        
        logger.info(f"\n📊 权限级别对比:")
        logger.info(f"  - 系统级权限应该看到: {system_level_should_see} (所有)")
        logger.info(f"  - 企业级权限会看到: {company_level_would_see}")
        logger.info(f"  - 差异: {system_level_should_see - company_level_would_see}")
        
        conn.close()
        return {
            'total': total_quotations,
            'company': company_quotations,
            'owned': owned_quotations,
            'user_info': user_info
        }
    
    def check_quotation_access_control_logic(self):
        """检查报价单访问控制逻辑的实现"""
        logger.info("\n🔍 检查报价单访问控制逻辑...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查liuwei的权限级别
        cursor.execute("""
            SELECT permission_level, can_view, can_create, can_edit, can_delete
            FROM role_permissions 
            WHERE role = 'solution_manager' AND module = 'quotation'
        """)
        
        quotation_permission = cursor.fetchone()
        if quotation_permission:
            perm_level, can_view, can_create, can_edit, can_delete = quotation_permission
            logger.info(f"📋 quotation模块权限配置:")
            logger.info(f"  - 权限级别: {perm_level}")
            logger.info(f"  - 可查看: {can_view}")
            logger.info(f"  - 可创建: {can_create}")
            logger.info(f"  - 可编辑: {can_edit}")
            logger.info(f"  - 可删除: {can_delete}")
        
        # 模拟access_control.py中的报价单访问逻辑
        logger.info(f"\n🧪 模拟访问控制逻辑:")
        if perm_level == 'system':
            logger.info("✅ 系统级权限 - 理论上应该能看到所有报价单")
            
            # 获取所有报价单
            cursor.execute("SELECT COUNT(*) FROM quotations")
            all_quotations = cursor.fetchone()[0]
            logger.info(f"📊 系统级查询应该返回: {all_quotations} 个报价单")
            
        elif perm_level == 'company':
            logger.info("🏢 企业级权限 - 应该看到企业项目的报价单")
            
            # 获取企业用户ID
            cursor.execute("""
                SELECT id FROM users WHERE company_name = '和源通信（上海）股份有限公司'
            """)
            company_user_ids = [row[0] for row in cursor.fetchall()]
            
            # 获取企业项目ID
            if company_user_ids:
                cursor.execute("""
                    SELECT id FROM projects WHERE owner_id = ANY(%s)
                """, (company_user_ids,))
                company_project_ids = [row[0] for row in cursor.fetchall()]
                
                # 获取企业项目的报价单
                if company_project_ids:
                    cursor.execute("""
                        SELECT COUNT(*) FROM quotations 
                        WHERE project_id = ANY(%s)
                    """, (company_project_ids,))
                    company_quotations = cursor.fetchone()[0]
                    logger.info(f"📊 企业级查询应该返回: {company_quotations} 个报价单")
        
        conn.close()
    
    def check_quotation_view_implementation(self):
        """检查报价单视图的具体实现"""
        logger.info("\n🔍 检查可能的权限实现差异...")
        
        # 读取相关文件内容
        try:
            quotation_view_path = "/Users/nijie/Documents/PMA/app/views/quotation.py"
            logger.info(f"📁 检查文件: {quotation_view_path}")
            
            # 这里我们需要检查报价单视图的实现
            logger.info("💡 需要检查的关键点:")
            logger.info("1. quotation.py视图文件中的权限检查逻辑")
            logger.info("2. 是否使用了get_viewable_data函数")
            logger.info("3. 是否有额外的过滤条件")
            logger.info("4. 项目详情页面的报价单访问权限检查")
            
        except Exception as e:
            logger.warning(f"⚠️ 无法直接检查文件: {e}")
    
    def analyze_permission_inconsistency(self):
        """分析权限不一致的可能原因"""
        logger.info("\n🔍 分析权限不一致的可能原因...")
        
        logger.info("🧩 可能的原因分析:")
        logger.info("1. **报价单访问控制实现不同**:")
        logger.info("   - 项目模块: 正确使用了get_viewable_data函数")
        logger.info("   - 报价单模块: 可能有不同的权限检查逻辑")
        
        logger.info("\n2. **报价单与项目的关联逻辑**:")
        logger.info("   - 报价单通过project_id关联项目")
        logger.info("   - 可能在企业级权限时只检查项目所有者的公司")
        logger.info("   - 而不是检查当前用户的权限级别")
        
        logger.info("\n3. **视图层面的权限检查**:")
        logger.info("   - 项目详情页面的报价单链接可能有独立的权限检查")
        logger.info("   - 可能使用了不同的权限判断逻辑")
        
        logger.info("\n4. **前端权限控制**:")
        logger.info("   - 前端可能对报价单有额外的权限验证")
        logger.info("   - JavaScript可能在点击时进行权限检查")
    
    def provide_solutions(self):
        """提供解决方案"""
        logger.info("\n💡 解决方案建议:")
        
        logger.info("🔧 立即检查步骤:")
        logger.info("1. 检查 app/views/quotation.py 文件:")
        logger.info("   - 确认是否使用了get_viewable_data函数")
        logger.info("   - 查看权限检查逻辑是否与project.py一致")
        
        logger.info("\n2. 检查报价单列表视图:")
        logger.info("   - 确认权限级别获取逻辑")
        logger.info("   - 验证系统级权限是否正确处理")
        
        logger.info("\n3. 检查项目详情页面的报价单权限:")
        logger.info("   - 查看报价单链接的权限检查")
        logger.info("   - 确认是否有独立的访问控制")
        
        logger.info("\n🎯 预期修复:")
        logger.info("修复后，liuwei用户应该能够:")
        logger.info("- 在报价单列表页面看到所有报价单")
        logger.info("- 从项目详情页面访问任何项目的报价单")
        logger.info("- 享受与项目模块一致的系统级权限")
    
    def run_diagnosis(self):
        """运行完整的报价权限诊断"""
        logger.info("🚀 开始报价模块权限不一致诊断...")
        logger.info("="*60)
        
        try:
            # 1. 检查报价单与项目关系
            stats = self.check_quotation_project_relationship()
            
            # 2. 检查访问控制逻辑
            self.check_quotation_access_control_logic()
            
            # 3. 检查视图实现
            self.check_quotation_view_implementation()
            
            # 4. 分析不一致原因
            self.analyze_permission_inconsistency()
            
            # 5. 提供解决方案
            self.provide_solutions()
            
            logger.info("\n" + "="*60)
            logger.info("🎯 诊断完成")
            logger.info("="*60)
            logger.info("核心问题: 报价模块的权限实现与项目模块不一致")
            logger.info("需要检查报价单视图的权限控制逻辑")
            
        except Exception as e:
            logger.error(f"❌ 诊断过程中出错: {str(e)}")

if __name__ == "__main__":
    diagnostic = QuotationPermissionDiagnostic()
    diagnostic.run_diagnosis()