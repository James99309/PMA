#!/usr/bin/env python3
"""
OVS数据库标准迁移升级脚本
基于standard_migration_upgrade.py，专门用于OVS数据库升级

使用步骤：
1. 检查当前迁移状态
2. 备份OVS数据库
3. 执行标准 flask db upgrade
4. 验证升级结果
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('StandardMigrationOVS')

class StandardMigrationUpgradeOVS:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # OVS 数据库配置
        self.ovs_url = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
        
    def step1_check_current_status(self):
        """步骤1: 检查当前迁移状态"""
        logger.info("=" * 60)
        logger.info("步骤1: 检查当前迁移状态")
        logger.info("=" * 60)
        
        try:
            # 检查本地迁移状态
            logger.info("检查本地迁移状态...")
            local_result = subprocess.run(['flask', 'db', 'current'], 
                                        capture_output=True, text=True, check=True)
            local_version = local_result.stdout.strip()
            logger.info(f"本地当前版本: {local_version}")
            
            # 检查OVS迁移状态
            logger.info("检查OVS迁移状态...")
            env = os.environ.copy()
            env['DATABASE_URL'] = self.ovs_url
            
            ovs_result = subprocess.run(['flask', 'db', 'current'], 
                                       capture_output=True, text=True, 
                                       check=True, env=env)
            ovs_version = ovs_result.stdout.strip()
            logger.info(f"OVS当前版本: {ovs_version}")
            
            return local_version, ovs_version
            
        except subprocess.CalledProcessError as e:
            logger.error(f"检查迁移状态失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return None, None
    
    def step2_backup_ovs(self):
        """步骤2: 备份OVS数据库"""
        logger.info("=" * 60)
        logger.info("步骤2: 备份OVS数据库")
        logger.info("=" * 60)
        
        backup_file = f"ovs_pre_upgrade_backup_{self.timestamp}.sql"
        backup_path = os.path.join(os.getcwd(), 'cloud_db_backups', backup_file)
        
        # 确保备份目录存在
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        try:
            # 解析数据库URL
            parsed = urlparse(self.ovs_url)
            
            # 构建pg_dump命令
            cmd = [
                'pg_dump',
                '--verbose', '--clean', '--if-exists',
                '--no-owner', '--no-privileges',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', backup_path
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            logger.info(f"开始备份OVS数据库到: {backup_path}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            # 检查备份文件大小
            backup_size = os.path.getsize(backup_path)
            logger.info(f"✅ 备份完成，文件大小: {backup_size:,} 字节")
            
            return backup_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 备份失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ 备份过程出错: {e}")
            return None
    
    def step3_upgrade_ovs(self):
        """步骤3: 升级OVS数据库到最新版本"""
        logger.info("=" * 60)
        logger.info("步骤3: 升级OVS数据库到最新版本")
        logger.info("=" * 60)
        
        try:
            # 设置环境变量指向OVS数据库
            env = os.environ.copy()
            env['DATABASE_URL'] = self.ovs_url
            
            logger.info("开始执行 flask db upgrade...")
            result = subprocess.run(['flask', 'db', 'upgrade'], 
                                  env=env, capture_output=True, text=True, check=True)
            
            logger.info("✅ 升级完成")
            logger.info("升级输出:")
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.info(result.stderr)
                
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 升级失败: {e}")
            logger.error(f"标准输出: {e.stdout}")
            logger.error(f"错误输出: {e.stderr}")
            return False
    
    def step4_verify_upgrade(self):
        """步骤4: 验证升级结果"""
        logger.info("=" * 60)
        logger.info("步骤4: 验证升级结果")
        logger.info("=" * 60)
        
        try:
            # 检查最终版本
            env = os.environ.copy()
            env['DATABASE_URL'] = self.ovs_url
            
            result = subprocess.run(['flask', 'db', 'current'], 
                                  capture_output=True, text=True, 
                                  check=True, env=env)
            final_version = result.stdout.strip()
            logger.info(f"升级后OVS版本: {final_version}")
            
            # 检查本地版本进行对比
            local_result = subprocess.run(['flask', 'db', 'current'], 
                                        capture_output=True, text=True, check=True)
            local_version = local_result.stdout.strip()
            logger.info(f"本地版本: {local_version}")
            
            if final_version == local_version:
                logger.info("✅ 验证成功: OVS版本与本地版本一致")
                return True
            else:
                logger.error(f"❌ 验证失败: 版本不匹配")
                logger.error(f"OVS: {final_version}")
                logger.error(f"本地: {local_version}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"验证过程失败: {e}")
            return False
    
    def run_standard_upgrade(self):
        """执行标准升级流程"""
        logger.info("🚀 开始OVS标准迁移升级流程")
        logger.info(f"时间戳: {self.timestamp}")
        
        try:
            # 步骤1: 检查状态
            local_version, ovs_version = self.step1_check_current_status()
            if not local_version or not ovs_version:
                logger.error("❌ 无法获取当前迁移状态，终止升级")
                return False
            
            if local_version == ovs_version:
                logger.info("✅ OVS已经是最新版本，无需升级")
                return True
            
            # 步骤2: 备份
            backup_path = self.step2_backup_ovs()
            if not backup_path:
                logger.error("❌ 备份失败，终止升级")
                return False
            
            # 步骤3: 升级
            if not self.step3_upgrade_ovs():
                logger.error("❌ 升级失败")
                logger.info(f"可以使用备份文件恢复: {backup_path}")
                return False
            
            # 步骤4: 验证
            if not self.step4_verify_upgrade():
                logger.error("❌ 验证失败")
                logger.info(f"可以使用备份文件恢复: {backup_path}")
                return False
            
            logger.info("=" * 60)
            logger.info("🎉 OVS标准迁移升级流程完成！")
            logger.info(f"备份文件已保存: {backup_path}")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ 升级流程异常: {e}")
            return False

def main():
    """主函数"""
    upgrader = StandardMigrationUpgradeOVS()
    success = upgrader.run_standard_upgrade()
    
    if success:
        print("\n✅ OVS标准迁移升级成功完成")
        sys.exit(0)
    else:
        print("\n❌ OVS标准迁移升级失败")
        sys.exit(1)

if __name__ == "__main__":
    main()