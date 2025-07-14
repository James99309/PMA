#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排查云端非admin账户权限错误
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('权限错误排查')

class CloudPermissionDebugger:
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
    
    def check_users_and_roles(self):
        """检查用户和角色数据"""
        logger.info("🔍 检查用户和角色数据...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查用户表结构
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
        """)
        user_columns = cursor.fetchall()
        
        logger.info("📋 users表结构:")
        for col in user_columns:
            nullable = "可空" if col[2] == 'YES' else "不可空"
            logger.info(f"  - {col[0]}: {col[1]} ({nullable})")
        
        # 检查用户数据（先检查account_id字段是否存在）
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'users' 
            AND column_name = 'account_id'
        """)
        
        account_id_exists = cursor.fetchone()
        
        if account_id_exists:
            cursor.execute("""
                SELECT id, username, email, account_id, role, is_active, 
                       language_preference, updated_at
                FROM users 
                ORDER BY id
                LIMIT 10
            """)
            users = cursor.fetchall()
            
            logger.info("\n👥 用户数据 (前10个):")
            for user in users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 角色: {user[4]}, 账户ID: {user[3]}, 活跃: {user[5]}")
        else:
            logger.error("❌ users.account_id 字段缺失!")
            cursor.execute("""
                SELECT id, username, email, role, is_active, 
                       language_preference, updated_at
                FROM users 
                ORDER BY id
                LIMIT 10
            """)
            users = cursor.fetchall()
            
            logger.info("\n👥 用户数据 (前10个) - 无account_id字段:")
            for user in users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 角色: {user[3]}, 活跃: {user[4]}")
        
        # 检查role_permissions表
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'role_permissions'
            ORDER BY ordinal_position
        """)
        role_perm_columns = cursor.fetchall()
        
        logger.info("\n📋 role_permissions表结构:")
        for col in role_perm_columns:
            nullable = "可空" if col[2] == 'YES' else "不可空"
            logger.info(f"  - {col[0]}: {col[1]} ({nullable})")
        
        # 检查权限数据
        cursor.execute("""
            SELECT id, user_id, role, permission_level, permission_level_description
            FROM role_permissions 
            ORDER BY user_id
            LIMIT 10
        """)
        permissions = cursor.fetchall()
        
        logger.info("\n🔐 权限数据 (前10个):")
        for perm in permissions:
            logger.info(f"  - ID: {perm[0]}, 用户ID: {perm[1]}, 角色: {perm[2]}, 权限级别: {perm[3]}, 描述: {perm[4]}")
        
        conn.close()
    
    def check_accounts_and_companies(self):
        """检查账户和公司数据"""
        logger.info("\n🔍 检查账户和公司数据...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查accounts表
        try:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'accounts'
                ORDER BY ordinal_position
            """)
            account_columns = cursor.fetchall()
            
            if account_columns:
                logger.info("📋 accounts表结构:")
                for col in account_columns:
                    nullable = "可空" if col[2] == 'YES' else "不可空"
                    logger.info(f"  - {col[0]}: {col[1]} ({nullable})")
                
                cursor.execute("SELECT * FROM accounts LIMIT 5")
                accounts = cursor.fetchall()
                logger.info(f"🏢 账户数据: {len(accounts)} 条记录")
            else:
                logger.warning("⚠️ accounts表不存在或无字段")
        except Exception as e:
            logger.warning(f"⚠️ 无法访问accounts表: {e}")
        
        # 检查companies表
        try:
            cursor.execute("""
                SELECT id, name, account_id, shared_with_users, share_contacts
                FROM companies 
                ORDER BY id
                LIMIT 10
            """)
            companies = cursor.fetchall()
            
            logger.info(f"\n🏢 公司数据 (前10个):")
            for company in companies:
                logger.info(f"  - ID: {company[0]}, 名称: {company[1]}, 账户ID: {company[2]}, 共享用户: {company[3]}")
        except Exception as e:
            logger.error(f"❌ 访问companies表出错: {e}")
        
        conn.close()
    
    def check_missing_fields(self):
        """检查可能缺失的字段"""
        logger.info("\n🔍 检查可能缺失的关键字段...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查users表是否有account_id字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'users' 
            AND column_name = 'account_id'
        """)
        
        account_id_exists = cursor.fetchone()
        if account_id_exists:
            logger.info("✅ users.account_id 字段存在")
        else:
            logger.error("❌ users.account_id 字段缺失!")
        
        # 检查role_permissions表的新字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'role_permissions' 
            AND column_name IN ('permission_level', 'permission_level_description')
        """)
        
        new_fields = cursor.fetchall()
        logger.info(f"✅ role_permissions表新字段: {[field[0] for field in new_fields]}")
        
        # 检查是否有NULL值问题
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(account_id) as users_with_account_id,
                COUNT(*) - COUNT(account_id) as users_without_account_id
            FROM users
        """)
        
        user_stats = cursor.fetchone()
        logger.info(f"\n📊 用户数据统计:")
        logger.info(f"  - 总用户数: {user_stats[0]}")
        logger.info(f"  - 有account_id的用户: {user_stats[1]}")
        logger.info(f"  - 缺少account_id的用户: {user_stats[2]}")
        
        if user_stats[2] > 0:
            logger.warning("⚠️ 发现用户缺少account_id，这可能导致权限错误")
        
        conn.close()
    
    def check_specific_user_permissions(self, user_id=None):
        """检查特定用户的权限配置"""
        logger.info(f"\n🔍 检查用户权限配置...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查account_id字段是否存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'users' 
            AND column_name = 'account_id'
        """)
        
        account_id_exists = cursor.fetchone()
        
        if account_id_exists:
            # 获取非admin用户（包含account_id）
            cursor.execute("""
                SELECT id, username, role, account_id, is_active
                FROM users 
                WHERE role != 'admin' OR role IS NULL
                ORDER BY id
                LIMIT 5
            """)
            
            non_admin_users = cursor.fetchall()
            logger.info("👤 非admin用户:")
            for user in non_admin_users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 角色: {user[2]}, 账户ID: {user[3]}, 活跃: {user[4]}")
        else:
            # 获取非admin用户（不包含account_id）
            cursor.execute("""
                SELECT id, username, role, is_active
                FROM users 
                WHERE role != 'admin' OR role IS NULL
                ORDER BY id
                LIMIT 5
            """)
            
            non_admin_users = cursor.fetchall()
            logger.info("👤 非admin用户 (无account_id字段):")
            for user in non_admin_users:
                logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 角色: {user[2]}, 活跃: {user[3]}")
            
            # 检查该用户的权限配置
            cursor.execute("""
                SELECT role, permission_level, permission_level_description
                FROM role_permissions 
                WHERE user_id = %s
            """, (user[0],))
            
            user_permissions = cursor.fetchall()
            if user_permissions:
                logger.info(f"    权限: {user_permissions}")
            else:
                logger.warning(f"    ⚠️ 用户 {user[1]} 没有权限配置")
        
        conn.close()
    
    def check_database_triggers_and_functions(self):
        """检查数据库触发器和函数"""
        logger.info("\n🔍 检查数据库触发器和函数...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查触发器
        cursor.execute("""
            SELECT trigger_name, event_object_table, action_statement
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
        """)
        
        triggers = cursor.fetchall()
        if triggers:
            logger.info("🔧 数据库触发器:")
            for trigger in triggers:
                logger.info(f"  - {trigger[0]} on {trigger[1]}")
        else:
            logger.info("✅ 没有发现触发器")
        
        # 检查自定义函数
        cursor.execute("""
            SELECT routine_name, routine_type
            FROM information_schema.routines
            WHERE routine_schema = 'public'
        """)
        
        functions = cursor.fetchall()
        if functions:
            logger.info("🔧 自定义函数:")
            for func in functions:
                logger.info(f"  - {func[0]} ({func[1]})")
        else:
            logger.info("✅ 没有发现自定义函数")
        
        conn.close()
    
    def run_diagnosis(self):
        """运行完整的权限错误诊断"""
        logger.info("🚀 开始云端权限错误诊断...")
        
        try:
            self.check_users_and_roles()
            self.check_accounts_and_companies()
            self.check_missing_fields()
            self.check_specific_user_permissions()
            self.check_database_triggers_and_functions()
            
            logger.info("\n" + "="*60)
            logger.info("🎯 诊断总结")
            logger.info("="*60)
            logger.info("1. 检查users表是否有account_id字段且非NULL")
            logger.info("2. 检查role_permissions表是否有新添加的字段")
            logger.info("3. 检查非admin用户是否有正确的权限配置")
            logger.info("4. 检查是否有数据库约束或触发器导致错误")
            logger.info("\n建议:")
            logger.info("- 如果发现缺少字段或NULL值，需要补充数据")
            logger.info("- 如果权限配置有问题，需要修复权限逻辑")
            logger.info("- 可能需要检查应用代码中的权限判断逻辑")
            
        except Exception as e:
            logger.error(f"❌ 诊断过程中出错: {str(e)}")

if __name__ == "__main__":
    debugger = CloudPermissionDebugger()
    debugger.run_diagnosis()