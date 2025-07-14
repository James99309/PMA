#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断本地系统权限级别问题
检查liuwei用户为何看不到其他公司的项目和报价单
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('本地权限诊断')

class LocalPermissionDiagnostic:
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
    
    def check_liuwei_user_info(self):
        """检查liuwei用户基本信息"""
        logger.info("🔍 检查liuwei用户基本信息...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 查找liuwei用户
        cursor.execute("""
            SELECT id, username, role, email, company_name, department, 
                   is_department_manager, is_active, is_profile_complete
            FROM users 
            WHERE username = 'liuwei'
        """)
        
        user_info = cursor.fetchone()
        if user_info:
            user_id, username, role, email, company, dept, is_dept_mgr, is_active, is_complete = user_info
            logger.info(f"👤 找到用户: {username} (ID: {user_id})")
            logger.info(f"  - 角色: {role}")
            logger.info(f"  - 邮箱: {email}")
            logger.info(f"  - 公司: {company}")
            logger.info(f"  - 部门: {dept}")
            logger.info(f"  - 部门负责人: {is_dept_mgr}")
            logger.info(f"  - 账户激活: {is_active}")
            logger.info(f"  - 资料完整: {is_complete}")
            
            conn.close()
            return {
                'id': user_id,
                'username': username,
                'role': role,
                'company_name': company,
                'department': dept
            }
        else:
            logger.error("❌ 未找到用户liuwei")
            conn.close()
            return None
    
    def check_permission_levels(self, user_info):
        """检查权限级别配置"""
        logger.info("\n🔍 检查权限级别配置...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查角色权限配置
        role = user_info['role']
        logger.info(f"📋 {user_info['username']} 的角色权限 ({role}):")
        
        cursor.execute("""
            SELECT module, can_view, can_create, can_edit, can_delete,
                   permission_level, permission_level_description
            FROM role_permissions 
            WHERE role = %s
            AND module IN ('project', 'quotation')
            ORDER BY module
        """, (role,))
        
        role_permissions = cursor.fetchall()
        system_level_modules = []
        
        for perm in role_permissions:
            module, can_view, can_create, can_edit, can_delete, perm_level, perm_desc = perm
            logger.info(f"  - {module}:")
            logger.info(f"    权限: 查看={can_view}, 创建={can_create}, 编辑={can_edit}, 删除={can_delete}")
            logger.info(f"    权限级别: {perm_level} ({perm_desc or '无描述'})")
            
            if perm_level == 'system':
                system_level_modules.append(module)
        
        # 检查用户特定权限
        cursor.execute("""
            SELECT module, can_view, can_create, can_edit, can_delete
            FROM permissions 
            WHERE user_id = %s
            AND module IN ('project', 'quotation')
            ORDER BY module
        """, (user_info['id'],))
        
        user_permissions = cursor.fetchall()
        if user_permissions:
            logger.info(f"\n📋 {user_info['username']} 的特定权限:")
            for perm in user_permissions:
                module, can_view, can_create, can_edit, can_delete = perm
                logger.info(f"  - {module}: 查看={can_view}, 创建={can_create}, 编辑={can_edit}, 删除={can_delete}")
        else:
            logger.info(f"\n📋 {user_info['username']} 无特定权限记录")
        
        conn.close()
        return system_level_modules
    
    def check_companies_data(self, user_info):
        """检查公司数据和用户关联"""
        logger.info("\n🔍 检查公司数据和用户关联...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查所有公司
        cursor.execute("""
            SELECT id, company_name, shared_with_users, share_contacts
            FROM companies 
            ORDER BY id
        """)
        
        companies = cursor.fetchall()
        logger.info(f"📋 系统中的公司 ({len(companies)} 个):")
        
        user_company = user_info['company_name']
        accessible_companies = []
        
        for company in companies:
            company_id, company_name, shared_users, share_contacts = company
            is_user_company = (company_name == user_company)
            
            # 检查用户是否在shared_with_users中
            has_access = False
            if shared_users:
                try:
                    # shared_users可能是JSON格式或字符串格式
                    if isinstance(shared_users, str):
                        has_access = str(user_info['id']) in shared_users
                    else:
                        has_access = user_info['id'] in shared_users
                except:
                    has_access = False
            
            logger.info(f"  - ID: {company_id}, 名称: {company_name}")
            logger.info(f"    用户公司: {is_user_company}")
            logger.info(f"    共享用户: {shared_users}")
            logger.info(f"    用户有访问权: {has_access}")
            
            if is_user_company or has_access:
                accessible_companies.append(company_id)
        
        logger.info(f"\n✅ {user_info['username']} 应该能访问的公司ID: {accessible_companies}")
        
        conn.close()
        return accessible_companies
    
    def check_projects_data(self, user_info, accessible_companies):
        """检查项目数据"""
        logger.info("\n🔍 检查项目数据...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查所有项目的公司归属
        cursor.execute("""
            SELECT p.id, p.name, p.owner_id, p.company_id, c.name as company_name,
                   u.username as owner_name
            FROM projects p
            LEFT JOIN companies c ON p.company_id = c.id
            LEFT JOIN users u ON p.owner_id = u.id
            ORDER BY p.id
            LIMIT 20
        """)
        
        projects = cursor.fetchall()
        logger.info(f"📋 项目数据分析 (前20个):")
        
        visible_projects = 0
        total_projects = len(projects)
        
        for project in projects:
            proj_id, proj_name, owner_id, company_id, company_name, owner_name = project
            
            # 判断用户是否应该能看到这个项目
            should_see = False
            reasons = []
            
            # 1. 如果是项目所有者
            if owner_id == user_info['id']:
                should_see = True
                reasons.append("项目所有者")
            
            # 2. 如果公司可访问
            if company_id in accessible_companies:
                should_see = True
                reasons.append("公司可访问")
            
            # 3. 系统级权限应该能看到所有项目
            # 但这里可能有额外的过滤逻辑
            
            if should_see:
                visible_projects += 1
            
            logger.info(f"  - 项目ID: {proj_id}, 名称: {proj_name[:30]}...")
            logger.info(f"    所有者: {owner_name} (ID: {owner_id})")
            logger.info(f"    公司: {company_name} (ID: {company_id})")
            logger.info(f"    应该可见: {should_see} ({', '.join(reasons) if reasons else '无权限'})")
        
        logger.info(f"\n📊 项目可见性统计:")
        logger.info(f"  - 总项目数: {total_projects}")
        logger.info(f"  - 应该可见: {visible_projects}")
        logger.info(f"  - 不可见: {total_projects - visible_projects}")
        
        conn.close()
        return visible_projects, total_projects
    
    def check_quotations_data(self, user_info, accessible_companies):
        """检查报价单数据"""
        logger.info("\n🔍 检查报价单数据...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查报价单的项目关联
        cursor.execute("""
            SELECT q.id, q.quotation_number, q.owner_id, q.project_id,
                   p.name as project_name, p.company_id, c.name as company_name,
                   u.username as owner_name
            FROM quotations q
            LEFT JOIN projects p ON q.project_id = p.id
            LEFT JOIN companies c ON p.company_id = c.id
            LEFT JOIN users u ON q.owner_id = u.id
            ORDER BY q.id
            LIMIT 20
        """)
        
        quotations = cursor.fetchall()
        logger.info(f"📋 报价单数据分析 (前20个):")
        
        visible_quotations = 0
        total_quotations = len(quotations)
        
        for quotation in quotations:
            quot_id, quot_number, owner_id, project_id, project_name, company_id, company_name, owner_name = quotation
            
            # 判断用户是否应该能看到这个报价单
            should_see = False
            reasons = []
            
            # 1. 如果是报价单所有者
            if owner_id == user_info['id']:
                should_see = True
                reasons.append("报价单所有者")
            
            # 2. 如果项目公司可访问
            if company_id in accessible_companies:
                should_see = True
                reasons.append("项目公司可访问")
            
            if should_see:
                visible_quotations += 1
            
            logger.info(f"  - 报价单ID: {quot_id}, 编号: {quot_number}")
            logger.info(f"    所有者: {owner_name} (ID: {owner_id})")
            logger.info(f"    项目: {project_name} (ID: {project_id})")
            logger.info(f"    公司: {company_name} (ID: {company_id})")
            logger.info(f"    应该可见: {should_see} ({', '.join(reasons) if reasons else '无权限'})")
        
        logger.info(f"\n📊 报价单可见性统计:")
        logger.info(f"  - 总报价单数: {total_quotations}")
        logger.info(f"  - 应该可见: {visible_quotations}")
        logger.info(f"  - 不可见: {total_quotations - visible_quotations}")
        
        conn.close()
        return visible_quotations, total_quotations
    
    def check_application_filters(self, user_info):
        """检查应用程序中可能的过滤逻辑"""
        logger.info("\n🔍 分析可能的应用程序过滤逻辑...")
        
        logger.info("🎯 可能的原因分析:")
        logger.info("1. 权限级别虽然是'system'，但应用代码中可能有额外的过滤条件")
        logger.info("2. 公司shared_with_users字段可能没有正确配置")
        logger.info("3. 前端或后端可能有基于company_name的过滤逻辑")
        logger.info("4. 数据库查询中可能包含了用户公司的WHERE条件")
        
        logger.info("\n💡 建议检查:")
        logger.info("1. 检查项目列表视图的数据库查询逻辑")
        logger.info("2. 检查报价单列表视图的数据库查询逻辑")
        logger.info("3. 确认companies表的shared_with_users字段配置")
        logger.info("4. 查看应用日志中的SQL查询语句")
    
    def run_diagnosis(self):
        """运行完整的权限诊断"""
        logger.info("🚀 开始本地权限级别诊断...")
        
        try:
            # 1. 检查用户信息
            user_info = self.check_liuwei_user_info()
            if not user_info:
                return
            
            # 2. 检查权限级别
            system_level_modules = self.check_permission_levels(user_info)
            
            # 3. 检查公司数据
            accessible_companies = self.check_companies_data(user_info)
            
            # 4. 检查项目数据
            visible_projects, total_projects = self.check_projects_data(user_info, accessible_companies)
            
            # 5. 检查报价单数据
            visible_quotations, total_quotations = self.check_quotations_data(user_info, accessible_companies)
            
            # 6. 分析应用程序逻辑
            self.check_application_filters(user_info)
            
            logger.info("\n" + "="*60)
            logger.info("🎯 诊断总结")
            logger.info("="*60)
            
            logger.info(f"用户: {user_info['username']} (公司: {user_info['company_name']})")
            logger.info(f"系统级权限模块: {system_level_modules}")
            logger.info(f"可访问公司数: {len(accessible_companies)}")
            logger.info(f"项目可见性: {visible_projects}/{total_projects}")
            logger.info(f"报价单可见性: {visible_quotations}/{total_quotations}")
            
            if len(system_level_modules) > 0 and (visible_projects < total_projects or visible_quotations < total_quotations):
                logger.warning("\n⚠️ 发现问题:")
                logger.warning("用户拥有系统级权限，但无法看到所有数据")
                logger.warning("可能的原因:")
                logger.warning("1. 应用代码中有额外的公司过滤逻辑")
                logger.warning("2. companies表的shared_with_users配置不完整")
                logger.warning("3. 权限级别配置与实际查询逻辑不匹配")
            
        except Exception as e:
            logger.error(f"❌ 诊断过程中出错: {str(e)}")

if __name__ == "__main__":
    diagnostic = LocalPermissionDiagnostic()
    diagnostic.run_diagnosis()