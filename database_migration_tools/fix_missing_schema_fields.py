#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复云端数据库缺失的关键字段
主要解决非admin用户500错误问题
"""

import psycopg2
import logging
import datetime
import subprocess
import os
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('修复缺失字段')

class MissingFieldsFixer:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = '/Users/nijie/Documents/PMA/cloud_db_backups'
        
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"
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
    
    def backup_cloud_database(self):
        """备份云端数据库"""
        logger.info("🔍 [1/4] 备份云端数据库...")
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        backup_file = f"{self.backup_dir}/pma_db_ovs_backup_before_field_fix_{self.timestamp}.sql"
        
        try:
            cmd = [
                'pg_dump',
                '-h', cloud_params['host'],
                '-p', str(cloud_params['port']),
                '-U', cloud_params['user'],
                '-d', cloud_params['dbname'],
                '--verbose',
                '--clean',
                '--if-exists',
                '--no-owner',
                '--no-privileges',
                '-f', backup_file
            ]
            
            env = {**dict(os.environ), 'PGPASSWORD': cloud_params['password']}
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 备份成功: {backup_file}")
                return backup_file
            else:
                logger.error(f"❌ 备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程出错: {str(e)}")
            return None
    
    def check_missing_fields(self):
        """检查云端数据库缺失的字段"""
        logger.info("🔍 [2/4] 检查缺失字段...")
        
        # 连接本地数据库获取正确的结构
        local_params = self.parse_db_url(self.local_db_url)
        local_conn = psycopg2.connect(**local_params)
        local_cursor = local_conn.cursor()
        
        # 连接云端数据库
        cloud_params = self.parse_db_url(self.cloud_db_url)
        cloud_conn = psycopg2.connect(**cloud_params)
        cloud_cursor = cloud_conn.cursor()
        
        missing_fields = {}
        
        # 检查users表
        logger.info("📋 检查users表...")
        local_cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
        """)
        local_users_columns = {row[0]: row for row in local_cursor.fetchall()}
        
        cloud_cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
        """)
        cloud_users_columns = {row[0]: row for row in cloud_cursor.fetchall()}
        
        users_missing = []
        for col_name, col_info in local_users_columns.items():
            if col_name not in cloud_users_columns:
                users_missing.append((col_name, col_info))
                logger.warning(f"⚠️ users表缺失字段: {col_name} ({col_info[1]})")
        
        if users_missing:
            missing_fields['users'] = users_missing
        
        # 检查role_permissions表
        logger.info("📋 检查role_permissions表...")
        local_cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'role_permissions'
            ORDER BY ordinal_position
        """)
        local_rp_columns = {row[0]: row for row in local_cursor.fetchall()}
        
        cloud_cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'role_permissions'
            ORDER BY ordinal_position
        """)
        cloud_rp_columns = {row[0]: row for row in cloud_cursor.fetchall()}
        
        rp_missing = []
        for col_name, col_info in local_rp_columns.items():
            if col_name not in cloud_rp_columns:
                rp_missing.append((col_name, col_info))
                logger.warning(f"⚠️ role_permissions表缺失字段: {col_name} ({col_info[1]})")
        
        if rp_missing:
            missing_fields['role_permissions'] = rp_missing
        
        local_conn.close()
        cloud_conn.close()
        
        return missing_fields
    
    def add_missing_fields(self, missing_fields):
        """添加缺失的字段到云端数据库"""
        logger.info("🔍 [3/4] 添加缺失字段...")
        
        if not missing_fields:
            logger.info("✅ 没有缺失字段，无需修复")
            return True
        
        cloud_params = self.parse_db_url(self.cloud_db_url)
        conn = psycopg2.connect(**cloud_params)
        conn.autocommit = False
        cursor = conn.cursor()
        
        operations = []
        
        try:
            for table_name, fields in missing_fields.items():
                logger.info(f"🔧 修复表: {table_name}")
                
                for col_name, col_info in fields:
                    col_name, data_type, is_nullable, col_default = col_info
                    
                    # 构建ALTER TABLE语句
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {data_type}"
                    
                    if col_default is not None:
                        sql += f" DEFAULT {col_default}"
                    
                    if is_nullable == 'NO':
                        # 如果字段不允许NULL，先添加为允许NULL，然后可以后续设置默认值
                        pass  # 暂时允许NULL，避免约束冲突
                    
                    logger.info(f"🔄 执行: {sql}")
                    cursor.execute(sql)
                    operations.append(f"添加字段 {table_name}.{col_name}")
            
            # 提交更改
            conn.commit()
            logger.info(f"✅ 字段添加成功，执行了 {len(operations)} 个操作")
            
            for op in operations:
                logger.info(f"   - {op}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 字段添加失败: {str(e)}")
            conn.rollback()
            cursor.close()
            conn.close()
            return False
    
    def generate_fix_report(self, missing_fields, backup_file, fix_success):
        """生成修复报告"""
        logger.info("🔍 [4/4] 生成修复报告...")
        
        report_file = f"{self.backup_dir}/missing_fields_fix_report_{self.timestamp}.md"
        
        report_content = f"""# 缺失字段修复报告

## 修复概述
- 修复时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 目标数据库: 云端PostgreSQL (pma_db_ovs)
- 修复状态: {'成功' if fix_success else '失败'}

## 问题描述
非admin用户访问项目管理和客户管理时出现500错误，经诊断发现云端数据库缺失关键字段：

### 缺失字段分析
"""
        
        if missing_fields:
            for table_name, fields in missing_fields.items():
                report_content += f"\n#### {table_name}表\n"
                for col_name, col_info in fields:
                    col_name, data_type, is_nullable, col_default = col_info
                    nullable_str = "不可空" if is_nullable == 'NO' else "可空"
                    default_str = f" 默认值: {col_default}" if col_default else ""
                    report_content += f"- **{col_name}**: {data_type} ({nullable_str}){default_str}\n"
        else:
            report_content += "\n✅ 没有发现缺失字段\n"
        
        report_content += f"""

## 修复结果
- 备份文件: {backup_file or '无'}
- 修复状态: {'✅ 成功' if fix_success else '❌ 失败'}

## 执行步骤
1. ✅ 备份云端数据库
2. ✅ 检查缺失字段
3. {'✅' if fix_success else '❌'} 添加缺失字段
4. ✅ 生成修复报告

## 安全确认
- ✅ 修复前已备份云端数据库
- ✅ 仅添加缺失字段，不修改现有数据
- ✅ 所有操作可回滚

## 后续建议
1. 测试非admin用户登录和权限访问
2. 如果仍有问题，检查应用代码中的权限逻辑
3. 考虑完整的schema同步以确保结构一致性
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📋 修复报告已生成: {report_file}")
        return report_file
    
    def run(self):
        """执行完整的修复流程"""
        logger.info("🚀 开始修复缺失字段...")
        
        try:
            # 1. 备份云端数据库
            backup_file = self.backup_cloud_database()
            if not backup_file:
                logger.error("❌ 备份失败，中止修复")
                return False
            
            # 2. 检查缺失字段
            missing_fields = self.check_missing_fields()
            
            # 3. 添加缺失字段
            fix_success = self.add_missing_fields(missing_fields)
            
            # 4. 生成报告
            report_file = self.generate_fix_report(missing_fields, backup_file, fix_success)
            
            if fix_success:
                logger.info("🎉 缺失字段修复完成!")
                logger.info(f"📋 详细报告: {report_file}")
                logger.info("\n💡 建议:")
                logger.info("1. 测试非admin用户登录")
                logger.info("2. 检查项目管理和客户管理功能")
                logger.info("3. 如果仍有错误，检查应用权限逻辑")
            else:
                logger.error("❌ 字段修复失败，请查看报告")
            
            return fix_success
            
        except Exception as e:
            logger.error(f"❌ 修复过程中出错: {str(e)}")
            return False

if __name__ == "__main__":
    fixer = MissingFieldsFixer()
    success = fixer.run()
    if not success:
        exit(1)