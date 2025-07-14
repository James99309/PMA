#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复用户权限问题
为quah和roy用户添加必要的permissions表记录
"""

import psycopg2
import logging
import datetime
import subprocess
import os
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('权限修复')

class UserPermissionsFixer:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = '/Users/nijie/Documents/PMA/cloud_db_backups'
        
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
    
    def backup_permissions_tables(self):
        """备份权限相关表"""
        logger.info("🔍 [1/4] 备份权限相关表...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = f"{self.backup_dir}/permissions_backup_before_fix_{self.timestamp}.sql"
        
        try:
            cmd = [
                'pg_dump',
                '-h', cloud_params['host'],
                '-p', str(cloud_params['port']),
                '-U', cloud_params['user'],
                '-d', cloud_params['dbname'],
                '--verbose',
                '--data-only',
                '--table', 'permissions',
                '--table', 'role_permissions',
                '-f', backup_file
            ]
            
            env = {**dict(os.environ), 'PGPASSWORD': cloud_params['password']}
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 权限表备份成功: {backup_file}")
                return backup_file
            else:
                logger.error(f"❌ 备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程出错: {str(e)}")
            return None
    
    def get_admin_permissions_template(self):
        """获取admin用户的权限作为模板"""
        logger.info("🔍 [2/4] 获取admin权限模板...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        conn = psycopg2.connect(**cloud_params)
        cursor = conn.cursor()
        
        # 获取admin用户的权限设置
        cursor.execute("""
            SELECT module, can_view, can_create, can_edit, can_delete
            FROM permissions 
            WHERE user_id = 1
            ORDER BY module
        """)
        
        admin_permissions = cursor.fetchall()
        logger.info(f"📋 获取到 {len(admin_permissions)} 个admin权限模板:")
        
        for perm in admin_permissions:
            module, can_view, can_create, can_edit, can_delete = perm
            logger.info(f"  - {module}: 查看={can_view}, 创建={can_create}, 编辑={can_edit}, 删除={can_delete}")
        
        conn.close()
        return admin_permissions
    
    def create_user_permissions_based_on_role(self, user_id, username, role, admin_permissions):
        """基于角色和admin模板为用户创建权限"""
        logger.info(f"🔍 [3/4] 为 {username} (ID: {user_id}) 创建权限...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        conn = psycopg2.connect(**cloud_params)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # 为sales_manager角色定义基础权限
        sales_manager_modules = {
            'customer': {'view': True, 'create': True, 'edit': True, 'delete': True},
            'project': {'view': True, 'create': True, 'edit': True, 'delete': True},
            'quotation': {'view': True, 'create': True, 'edit': True, 'delete': True},
            'product': {'view': True, 'create': False, 'edit': False, 'delete': False},
        }
        
        operations = []
        
        try:
            # 检查用户是否已有权限记录
            cursor.execute("SELECT COUNT(*) FROM permissions WHERE user_id = %s", (user_id,))
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                logger.warning(f"⚠️ 用户 {username} 已有 {existing_count} 条权限记录，跳过")
                conn.close()
                return []
            
            if role == 'sales_manager':
                # 为sales_manager创建基础权限
                for module, perms in sales_manager_modules.items():
                    cursor.execute("""
                        INSERT INTO permissions (user_id, module, can_view, can_create, can_edit, can_delete)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (user_id, module, perms['view'], perms['create'], perms['edit'], perms['delete']))
                    
                    operations.append(f"添加 {module} 权限: {perms}")
                    logger.info(f"  ✅ 添加 {module} 权限")
            
            else:
                # 其他角色暂时不处理
                logger.info(f"  ℹ️ 角色 {role} 暂不自动创建权限")
            
            # 提交更改
            conn.commit()
            logger.info(f"✅ 为 {username} 创建了 {len(operations)} 条权限记录")
            
            cursor.close()
            conn.close()
            return operations
            
        except Exception as e:
            logger.error(f"❌ 为 {username} 创建权限失败: {str(e)}")
            conn.rollback()
            cursor.close()
            conn.close()
            return []
    
    def verify_fix(self):
        """验证修复结果"""
        logger.info("🔍 [4/4] 验证修复结果...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        conn = psycopg2.connect(**cloud_params)
        cursor = conn.cursor()
        
        # 检查三个用户的权限记录
        for user_id, username in [(1, 'admin'), (2, 'quah'), (3, 'roy')]:
            cursor.execute("""
                SELECT COUNT(*), 
                       COUNT(CASE WHEN can_view = true THEN 1 END) as view_count,
                       COUNT(CASE WHEN can_create = true THEN 1 END) as create_count
                FROM permissions 
                WHERE user_id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            total, view_count, create_count = result
            
            logger.info(f"📋 {username} (ID: {user_id}): {total} 条权限，{view_count} 个查看权限，{create_count} 个创建权限")
        
        conn.close()
    
    def generate_fix_report(self, backup_file, operations):
        """生成修复报告"""
        report_file = f"{self.backup_dir}/user_permissions_fix_report_{self.timestamp}.md"
        
        report_content = f"""# 用户权限修复报告

## 修复概述
- 修复时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 目标数据库: 云端PostgreSQL (pma_db_ovs)
- 修复内容: 为非admin用户添加permissions表记录

## 问题描述
roy用户访问项目管理时出现500错误，经诊断发现：
1. admin用户在permissions表中有完整的权限记录
2. quah和roy用户在permissions表中没有权限记录
3. 应用程序权限检查同时依赖role_permissions和permissions表

## 修复操作
"""
        
        if operations:
            total_ops = sum(len(ops) for ops in operations.values())
            report_content += f"总共执行了 {total_ops} 个权限添加操作:\n\n"
            
            for username, ops in operations.items():
                report_content += f"### {username}\n"
                for op in ops:
                    report_content += f"- {op}\n"
                report_content += "\n"
        else:
            report_content += "未执行任何修复操作\n\n"
        
        report_content += f"""
## 修复结果
- 备份文件: {backup_file or '无'}
- 权限记录已同步

## 建议
1. 测试roy用户登录和访问项目管理功能
2. 如果仍有问题，检查应用权限检查逻辑中的异常处理
3. 考虑优化权限系统架构，统一使用一种权限表

## 后续监控
建议监控以下用户的访问情况：
- roy用户访问项目管理
- quah用户访问客户管理
- 确保没有新的500错误出现
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📋 修复报告已生成: {report_file}")
        return report_file
    
    def run(self):
        """执行完整的权限修复流程"""
        logger.info("🚀 开始用户权限修复...")
        
        try:
            # 1. 备份权限表
            backup_file = self.backup_permissions_tables()
            
            # 2. 获取admin权限模板
            admin_permissions = self.get_admin_permissions_template()
            
            # 3. 为quah和roy用户创建权限
            all_operations = {}
            
            # 为quah用户创建权限
            operations_quah = self.create_user_permissions_based_on_role(2, 'quah', 'sales_manager', admin_permissions)
            if operations_quah:
                all_operations['quah'] = operations_quah
            
            # 为roy用户创建权限
            operations_roy = self.create_user_permissions_based_on_role(3, 'roy', 'sales_manager', admin_permissions)
            if operations_roy:
                all_operations['roy'] = operations_roy
            
            # 4. 验证修复结果
            self.verify_fix()
            
            # 5. 生成报告
            report_file = self.generate_fix_report(backup_file, all_operations)
            
            logger.info("🎉 用户权限修复完成!")
            logger.info(f"📋 详细报告: {report_file}")
            
            if all_operations:
                logger.info("\n💡 建议:")
                logger.info("1. 立即测试roy用户登录和访问项目管理")
                logger.info("2. 确认quah用户功能正常")
                logger.info("3. 监控应用日志确保没有新的权限错误")
            else:
                logger.info("ℹ️ 没有执行权限修改，用户可能已有权限记录")
            
            return len(all_operations) > 0
            
        except Exception as e:
            logger.error(f"❌ 权限修复过程中出错: {str(e)}")
            return False

if __name__ == "__main__":
    fixer = UserPermissionsFixer()
    success = fixer.run()
    if not success:
        exit(1)