#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断特定用户roy的500错误问题
对比admin、quah、roy三个用户的数据差异
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('用户错误诊断')

class UserErrorDiagnostic:
    def __init__(self):
        self.cloud_db_url = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
    
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
        params = self.parse_db_url(self.cloud_db_url)
        return psycopg2.connect(**params)
    
    def compare_users_data(self):
        """比较admin、quah、roy三个用户的详细数据"""
        logger.info("🔍 对比三个用户的详细数据...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 获取三个用户的基本信息
        cursor.execute("""
            SELECT id, username, role, email, phone, department, 
                   is_department_manager, is_active, company_name,
                   is_profile_complete, created_at, last_login
            FROM users 
            WHERE username IN ('admin', 'quah', 'roy')
            ORDER BY username
        """)
        
        users = cursor.fetchall()
        logger.info("👥 用户基本信息对比:")
        
        user_data = {}
        for user in users:
            user_id, username, role, email, phone, dept, is_dept_mgr, is_active, company, is_complete, created_at, last_login = user
            user_data[username] = {
                'id': user_id,
                'role': role,
                'email': email,
                'phone': phone,
                'department': dept,
                'is_department_manager': is_dept_mgr,
                'is_active': is_active,
                'company_name': company,
                'is_profile_complete': is_complete,
                'created_at': created_at,
                'last_login': last_login
            }
            
            logger.info(f"\n📋 {username} (ID: {user_id}):")
            logger.info(f"  - 角色: {role}")
            logger.info(f"  - 邮箱: {email}")
            logger.info(f"  - 电话: {phone}")
            logger.info(f"  - 部门: {dept}")
            logger.info(f"  - 部门负责人: {is_dept_mgr}")
            logger.info(f"  - 账户激活: {is_active}")
            logger.info(f"  - 公司名称: {company}")
            logger.info(f"  - 资料完整: {is_complete}")
            logger.info(f"  - 创建时间: {created_at}")
            logger.info(f"  - 最后登录: {last_login}")
        
        return user_data
    
    def check_permissions_data(self, user_data):
        """检查用户权限数据"""
        logger.info("\n🔍 检查用户权限配置...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查role_permissions表中的角色权限
        for username, data in user_data.items():
            role = data['role']
            logger.info(f"\n📋 {username} ({role}) 的权限配置:")
            
            cursor.execute("""
                SELECT module, can_view, can_create, can_edit, can_delete,
                       pricing_discount_limit, settlement_discount_limit,
                       permission_level, permission_level_description
                FROM role_permissions 
                WHERE role = %s
                ORDER BY module
            """, (role,))
            
            permissions = cursor.fetchall()
            if permissions:
                for perm in permissions:
                    module, can_view, can_create, can_edit, can_delete, pricing_limit, settlement_limit, perm_level, perm_desc = perm
                    logger.info(f"  - {module}: 查看={can_view}, 创建={can_create}, 编辑={can_edit}, 删除={can_delete}")
                    if perm_level:
                        logger.info(f"    权限级别: {perm_level} ({perm_desc})")
            else:
                logger.warning(f"  ⚠️ 角色 {role} 没有权限配置!")
        
        conn.close()
    
    def check_user_specific_permissions(self, user_data):
        """检查用户特定权限表(如果存在)"""
        logger.info("\n🔍 检查用户特定权限...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查是否有permissions表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'permissions'
        """)
        
        permissions_table_exists = cursor.fetchone()
        
        if permissions_table_exists:
            logger.info("📋 找到permissions表，检查用户特定权限:")
            
            # 获取permissions表结构
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'permissions'
                ORDER BY ordinal_position
            """)
            
            perm_columns = cursor.fetchall()
            logger.info("permissions表结构:")
            for col in perm_columns:
                nullable = "可空" if col[2] == 'YES' else "不可空"
                logger.info(f"  - {col[0]}: {col[1]} ({nullable})")
            
            # 检查三个用户的特定权限
            for username, data in user_data.items():
                user_id = data['id']
                cursor.execute("SELECT * FROM permissions WHERE user_id = %s", (user_id,))
                user_perms = cursor.fetchall()
                
                logger.info(f"\n{username} (ID: {user_id}) 的特定权限:")
                if user_perms:
                    for perm in user_perms:
                        logger.info(f"  - {perm}")
                else:
                    logger.info("  - 无特定权限记录")
        else:
            logger.info("✅ 没有找到permissions表")
        
        conn.close()
    
    def check_data_integrity_issues(self, user_data):
        """检查数据完整性问题"""
        logger.info("\n🔍 检查数据完整性问题...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查NULL值问题
        for username, data in user_data.items():
            logger.info(f"\n📋 {username} 数据完整性检查:")
            
            # 检查关键字段的NULL值
            null_fields = []
            for field, value in data.items():
                if value is None and field in ['role', 'email', 'is_active']:
                    null_fields.append(field)
            
            if null_fields:
                logger.warning(f"  ⚠️ 关键字段为NULL: {null_fields}")
            else:
                logger.info("  ✅ 关键字段完整")
            
            # 检查布尔字段的特殊值
            if data['is_active'] is None:
                logger.warning(f"  ⚠️ is_active字段为NULL，可能导致权限问题")
            elif not data['is_active']:
                logger.warning(f"  ⚠️ 账户未激活")
            
            if data['is_profile_complete'] is None:
                logger.warning(f"  ⚠️ is_profile_complete字段为NULL")
            elif not data['is_profile_complete']:
                logger.info(f"  ℹ️ 用户资料未完善")
        
        conn.close()
    
    def check_related_tables(self, user_data):
        """检查相关表中的数据"""
        logger.info("\n🔍 检查相关表数据...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查用户在项目中的关联
        for username, data in user_data.items():
            user_id = data['id']
            logger.info(f"\n📋 {username} 相关数据:")
            
            # 检查project_members表
            try:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM project_members 
                    WHERE user_id = %s
                """, (user_id,))
                project_count = cursor.fetchone()[0]
                logger.info(f"  - 参与项目数量: {project_count}")
            except Exception as e:
                logger.warning(f"  ⚠️ 无法查询project_members: {e}")
            
            # 检查projects表中作为owner的项目
            try:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM projects 
                    WHERE owner_id = %s
                """, (user_id,))
                owned_projects = cursor.fetchone()[0]
                logger.info(f"  - 拥有项目数量: {owned_projects}")
            except Exception as e:
                logger.warning(f"  ⚠️ 无法查询projects: {e}")
            
            # 检查companies表的关联
            try:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM companies 
                    WHERE shared_with_users LIKE %s
                """, (f'%{user_id}%',))
                company_access = cursor.fetchone()[0]
                logger.info(f"  - 有权访问的公司数量: {company_access}")
            except Exception as e:
                logger.warning(f"  ⚠️ 无法查询companies: {e}")
        
        conn.close()
    
    def run_diagnosis(self):
        """运行完整的用户错误诊断"""
        logger.info("🚀 开始特定用户错误诊断...")
        
        try:
            # 1. 对比用户基本数据
            user_data = self.compare_users_data()
            
            # 2. 检查权限配置
            self.check_permissions_data(user_data)
            
            # 3. 检查用户特定权限
            self.check_user_specific_permissions(user_data)
            
            # 4. 检查数据完整性
            self.check_data_integrity_issues(user_data)
            
            # 5. 检查相关表数据
            self.check_related_tables(user_data)
            
            logger.info("\n" + "="*60)
            logger.info("🎯 诊断总结")
            logger.info("="*60)
            
            # 分析roy用户的特殊问题
            roy_data = user_data.get('roy', {})
            if roy_data:
                logger.info("🔍 roy用户特殊问题分析:")
                
                potential_issues = []
                
                if not roy_data.get('is_active'):
                    potential_issues.append("账户未激活")
                
                if roy_data.get('role') != user_data.get('quah', {}).get('role'):
                    potential_issues.append(f"角色不同: roy={roy_data.get('role')}, quah={user_data.get('quah', {}).get('role')}")
                
                if not roy_data.get('is_profile_complete'):
                    potential_issues.append("用户资料未完善")
                
                if potential_issues:
                    logger.warning("⚠️ 发现的问题:")
                    for issue in potential_issues:
                        logger.warning(f"  - {issue}")
                else:
                    logger.info("✅ roy用户基本数据看起来正常")
            
            logger.info("\n💡 建议:")
            logger.info("1. 如果roy账户未激活，需要激活账户")
            logger.info("2. 如果角色权限不同，检查role_permissions表配置")
            logger.info("3. 检查应用代码中的权限检查逻辑")
            logger.info("4. 查看详细的500错误堆栈信息")
            
        except Exception as e:
            logger.error(f"❌ 诊断过程中出错: {str(e)}")

if __name__ == "__main__":
    diagnostic = UserErrorDiagnostic()
    diagnostic.run_diagnosis()