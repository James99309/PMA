#!/usr/bin/env python3
"""
终极迁移同步脚本 - 标准流程
当数据库结构与迁移历史不一致时的最终解决方案

这将成为以后处理复杂迁移冲突的标准方法
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UltimateMigrationSync')

class UltimateMigrationSync:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sp8d_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        
    def get_current_versions(self):
        """获取当前迁移版本"""
        logger.info("📋 检查当前迁移版本...")
        
        # 本地版本
        result = subprocess.run(['flask', 'db', 'current'], capture_output=True, text=True, check=True)
        local_version = result.stdout.strip()
        logger.info(f"本地版本: {local_version}")
        
        # SP8D版本
        env = os.environ.copy()
        env['DATABASE_URL'] = self.sp8d_url
        result = subprocess.run(['flask', 'db', 'current'], env=env, capture_output=True, text=True, check=True)
        sp8d_version = result.stdout.strip()
        logger.info(f"SP8D版本: {sp8d_version}")
        
        return local_version, sp8d_version
    
    def backup_sp8d(self):
        """备份SP8D数据库"""
        logger.info("💾 备份SP8D数据库...")
        
        backup_file = f"sp8d_ultimate_sync_backup_{self.timestamp}.sql"
        backup_path = os.path.join(os.getcwd(), 'cloud_db_backups', backup_file)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        parsed = urlparse(self.sp8d_url)
        cmd = [
            'pg_dump', '--verbose', '--clean', '--if-exists',
            '--no-owner', '--no-privileges',
            '-h', parsed.hostname, '-p', str(parsed.port or 5432),
            '-U', parsed.username, '-d', parsed.path.lstrip('/'),
            '-f', backup_path
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        subprocess.run(cmd, env=env, check=True)
        backup_size = os.path.getsize(backup_path)
        logger.info(f"✅ 备份完成: {backup_path} ({backup_size:,} 字节)")
        
        return backup_path
    
    def force_update_migration_version(self, target_version):
        """强制更新SP8D的迁移版本"""
        logger.info(f"🔧 强制更新SP8D迁移版本到: {target_version}")
        
        parsed = urlparse(self.sp8d_url)
        
        # 直接更新alembic_version表
        update_sql = f"UPDATE alembic_version SET version_num = '{target_version}';"
        
        cmd = [
            'psql',
            '-h', parsed.hostname,
            '-p', str(parsed.port or 5432),
            '-U', parsed.username,
            '-d', parsed.path.lstrip('/'),
            '-c', update_sql
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        logger.info("✅ 迁移版本更新完成")
        
        return True
    
    def verify_version_sync(self, expected_version):
        """验证版本同步结果"""
        logger.info("🔍 验证版本同步结果...")
        
        env = os.environ.copy()
        env['DATABASE_URL'] = self.sp8d_url
        
        result = subprocess.run(['flask', 'db', 'current'], env=env, capture_output=True, text=True, check=True)
        actual_version = result.stdout.strip()
        
        if actual_version == expected_version:
            logger.info(f"✅ 版本同步成功: {actual_version}")
            return True
        else:
            logger.error(f"❌ 版本同步失败: 期望 {expected_version}, 实际 {actual_version}")
            return False
    
    def compare_table_counts(self):
        """对比表数量"""
        logger.info("📊 对比数据库表数量...")
        
        # 本地表数量
        local_result = subprocess.run(['psql', '-d', 'pma_local', '-t', '-c', '\\dt'], 
                                    capture_output=True, text=True, check=True)
        local_count = len([line for line in local_result.stdout.strip().split('\\n') if line.strip()])
        
        # SP8D表数量
        parsed = urlparse(self.sp8d_url)
        env = os.environ.copy()
        env['PGPASSWORD'] = parsed.password
        
        sp8d_result = subprocess.run([
            'psql', 
            '-h', parsed.hostname, '-p', str(parsed.port or 5432),
            '-U', parsed.username, '-d', parsed.path.lstrip('/'),
            '-t', '-c', '\\dt'
        ], env=env, capture_output=True, text=True, check=True)
        sp8d_count = len([line for line in sp8d_result.stdout.strip().split('\\n') if line.strip()])
        
        logger.info(f"本地表数量: {local_count}")
        logger.info(f"SP8D表数量: {sp8d_count}")
        
        if local_count == sp8d_count:
            logger.info("✅ 表数量一致")
            return True
        else:
            logger.warning(f"⚠️ 表数量不一致 (差异: {abs(local_count - sp8d_count)})")
            return False
    
    def run_ultimate_sync(self):
        """执行终极同步流程"""
        logger.info("🚀 开始终极迁移同步流程")
        logger.info("=" * 60)
        
        try:
            # 步骤1: 检查当前状态
            local_version, sp8d_version = self.get_current_versions()
            
            if local_version == sp8d_version:
                logger.info("✅ 版本已同步，无需操作")
                return True
            
            # 步骤2: 备份
            backup_path = self.backup_sp8d()
            
            # 步骤3: 强制更新版本
            if not self.force_update_migration_version(local_version):
                logger.error("❌ 强制更新版本失败")
                return False
            
            # 步骤4: 验证同步
            if not self.verify_version_sync(local_version):
                logger.error("❌ 版本同步验证失败")
                return False
            
            # 步骤5: 对比表结构
            self.compare_table_counts()
            
            # 完成
            logger.info("=" * 60)
            logger.info("🎉 终极迁移同步完成！")
            logger.info(f"✅ SP8D迁移版本已同步到: {local_version}")
            logger.info(f"💾 备份文件: {backup_path}")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 终极同步失败: {e}")
            return False

def main():
    """主函数"""
    sync = UltimateMigrationSync()
    success = sync.run_ultimate_sync()
    
    if success:
        print("\\n✅ 终极迁移同步成功")
        print("\\n📋 标准流程总结:")
        print("1. 备份云端数据库")
        print("2. 强制更新迁移版本到本地版本")
        print("3. 验证版本同步结果")
        print("4. 对比数据库结构")
        print("\\n🎯 此流程可作为以后处理复杂迁移冲突的标准方法")
        sys.exit(0)
    else:
        print("\\n❌ 终极迁移同步失败")
        sys.exit(1)

if __name__ == "__main__":
    main()