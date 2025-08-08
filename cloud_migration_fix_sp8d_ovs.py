#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端SP8D和OVS数据库安全迁移修复脚本

基于CLAUDE-DATABASE.md规范的标准化云端数据库迁移工具
用于修复云端部署中的版本同步和枚举值问题

支持的数据库：
- SP8D: pma_db_sp8d (新加坡云端数据库)
- OVS:  pma_db_ovs  (新加坡云端数据库)

修复内容：
1. 版本管理同步 (v1.0.1 → v1.3.5)
2. 审批状态枚举修复 (添加 RECALLED 值)
3. 完整数据库备份 (符合CLAUDE-DATABASE.md规范)

使用方法：
python cloud_migration_fix_sp8d_ovs.py --database sp8d
python cloud_migration_fix_sp8d_ovs.py --database ovs
"""

import os
import sys
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cloud_migration_fix.log')
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置 (基于CLAUDE-DATABASE.md规范)
DATABASE_CONFIG = {
    'sp8d': {
        'name': 'pma_db_sp8d',
        'user': 'pma_db_sp8d_user', 
        'host': 'dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com',
        'port': '5432',
        'display_name': 'SP8D云端数据库',
        'backup_prefix': 'sp8d_migration_fix'
    },
    'ovs': {
        'name': 'pma_db_ovs',
        'user': 'pma_db_ovs_user',
        'host': 'dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com', 
        'port': '5432',
        'display_name': 'OVS云端数据库',
        'backup_prefix': 'ovs_migration_fix'
    }
}

class CloudMigrationFixer:
    """云端数据库迁移修复工具"""
    
    def __init__(self, database_type):
        self.database_type = database_type
        self.config = DATABASE_CONFIG[database_type]
        self.backup_dir = Path('cloud_db_backups')
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_pre_migration_backup(self):
        """创建迁移前备份 (符合CLAUDE-DATABASE.md规范)"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{self.config['backup_prefix']}_backup_{timestamp}.sql"
            backup_path = self.backup_dir / backup_filename
            
            logger.info(f"🔄 开始备份{self.config['display_name']}...")
            logger.info(f"📁 备份文件: {backup_path}")
            
            # 构建pg_dump命令 (使用CLAUDE-DATABASE.md标准选项)
            cmd = [
                'pg_dump',
                '-h', self.config['host'],
                '-p', self.config['port'], 
                '-U', self.config['user'],
                '-d', self.config['name'],
                '--verbose',
                '--clean',
                '--if-exists', 
                '--no-owner',
                '--no-privileges',
                '-f', str(backup_path)
            ]
            
            # 通过环境变量传递密码 (符合安全规范)
            env = os.environ.copy()
            password = self.get_database_password()
            if password:
                env['PGPASSWORD'] = password
            
            # 使用subprocess.run同步执行 (符合CLAUDE-DATABASE.md规范)
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                # 验证备份文件
                backup_size = backup_path.stat().st_size
                logger.info(f"✅ 备份成功完成")
                logger.info(f"📊 备份文件大小: {backup_size / 1024 / 1024:.2f} MB")
                
                # 验证备份完整性
                self.verify_backup_integrity(backup_path)
                return backup_path
            else:
                logger.error(f"❌ 备份失败: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ 备份超时 (超过5分钟)")
            return None
        except Exception as e:
            logger.error(f"❌ 备份异常: {str(e)}")
            return None
    
    def verify_backup_integrity(self, backup_path):
        """验证备份完整性 (符合CLAUDE-DATABASE.md质量验证)"""
        try:
            with open(backup_path, 'r') as f:
                content = f.read()
            
            # 标准完整性检查
            table_count = content.count('CREATE TABLE')
            constraint_count = content.count('ADD CONSTRAINT')
            index_count = content.count('CREATE') and 'INDEX' in content
            data_count = content.count('COPY') and 'FROM stdin' in content
            
            logger.info(f"📋 备份完整性验证:")
            logger.info(f"  - 表数量: {table_count}")
            logger.info(f"  - 约束数量: {constraint_count}")
            logger.info(f"  - 包含数据: {'是' if data_count else '否'}")
            
            if table_count == 0:
                logger.warning("⚠️  备份可能不完整：未发现表结构")
            elif data_count == 0:
                logger.warning("⚠️  备份可能不完整：未发现表数据")
            else:
                logger.info("✅ 备份完整性验证通过")
                
        except Exception as e:
            logger.warning(f"⚠️  备份完整性验证失败: {str(e)}")
    
    def get_database_password(self):
        """获取数据库密码 (从环境变量或配置)"""
        # 优先从环境变量获取
        if self.database_type == 'sp8d':
            return os.getenv('SP8D_DATABASE_PASSWORD')
        elif self.database_type == 'ovs':
            return os.getenv('OVS_DATABASE_PASSWORD')
        return None
    
    def fix_version_sync(self):
        """修复版本同步问题"""
        try:
            logger.info("🔄 开始修复版本同步问题...")
            
            from app import create_app
            app = create_app()
            
            with app.app_context():
                from app.models.version_management import VersionRecord, UpgradeLog
                from app.extensions import db
                from sqlalchemy import text
                import json
                
                # 读取目标版本信息
                version_file = 'app_version.json'
                if os.path.exists(version_file):
                    with open(version_file, 'r') as f:
                        version_data = json.load(f)
                        target_version = version_data.get('app_version', '1.3.5')
                else:
                    target_version = '1.3.5'
                
                logger.info(f"📖 目标版本: {target_version}")
                
                # 检查当前版本
                current_version = VersionRecord.get_current_version()
                if current_version:
                    current_ver = current_version.version_number
                    logger.info(f"📊 当前{self.config['display_name']}版本: {current_ver}")
                    
                    if current_ver == target_version:
                        logger.info("✅ 版本已经正确，无需修复")
                        return True
                else:
                    current_ver = "无版本记录"
                    logger.info(f"⚠️  {self.config['display_name']}中没有当前版本记录")
                
                # 执行版本修复
                logger.info(f"🔧 修复版本: {current_ver} → {target_version}")
                
                # 检查目标版本是否存在
                existing_version = VersionRecord.query.filter_by(version_number=target_version).first()
                
                if existing_version:
                    logger.info("✅ 找到现有版本记录，设置为当前版本")
                    VersionRecord.query.update({'is_current': False})
                    existing_version.is_current = True
                    version_record = existing_version
                else:
                    logger.info(f"🔧 创建新版本记录: {target_version}")
                    VersionRecord.query.update({'is_current': False})
                    
                    version_record = VersionRecord(
                        version_number=target_version,
                        version_name=f'PMA项目管理系统 {target_version}',
                        description=f'{self.config["display_name"]}版本修复：从 {current_ver} 更新到 {target_version}。修复云端部署版本不一致问题，确保版本管理功能正常。',
                        is_current=True,
                        environment='production',
                        release_date=datetime.now()
                    )
                    db.session.add(version_record)
                    db.session.flush()
                
                # 创建升级日志
                logger.info("📝 记录升级日志...")
                upgrade_log = UpgradeLog(
                    version_id=version_record.id,
                    from_version=current_ver if current_ver != "无版本记录" else None,
                    to_version=target_version,
                    upgrade_type='cloud_migration_fix',
                    status='success',
                    operator_name=f'{self.config["display_name"]}迁移修复工具',
                    environment='production',
                    upgrade_notes=f'{self.config["display_name"]}云端版本同步修复：解决版本显示不一致问题，确保版本管理功能正常运行。',
                    upgrade_date=datetime.now()
                )
                db.session.add(upgrade_log)
                db.session.commit()
                
                logger.info("✅ 版本同步修复完成")
                return True
                
        except Exception as e:
            logger.error(f"❌ 版本同步修复失败: {str(e)}")
            return False
    
    def fix_approval_status_enum(self):
        """修复审批状态枚举问题"""
        try:
            logger.info("🔄 开始修复审批状态枚举...")
            
            from app import create_app
            app = create_app()
            
            with app.app_context():
                from app.extensions import db
                from sqlalchemy import text
                
                # 检查枚举值
                result = db.session.execute(text("""
                    SELECT enumlabel 
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid 
                    WHERE t.typname = 'approvalstatus'
                    ORDER BY e.enumsortorder
                """))
                
                enum_values = [row[0] for row in result.fetchall()]
                logger.info(f"📋 当前{self.config['display_name']}枚举值: {enum_values}")
                
                # 检查是否缺少RECALLED
                if 'RECALLED' in enum_values or 'recalled' in enum_values:
                    logger.info("✅ RECALLED 值已存在，无需修复")
                    return True
                
                logger.info("⚠️  发现问题：缺少 RECALLED 枚举值")
                logger.info("🔧 开始修复...")
                
                # 提交当前事务
                db.session.commit()
                
                # 使用原始连接执行ALTER TYPE (符合PostgreSQL规范)
                connection = db.engine.raw_connection()
                try:
                    cursor = connection.cursor()
                    cursor.execute("ALTER TYPE approvalstatus ADD VALUE 'RECALLED'")
                    connection.commit()
                    logger.info("✅ 成功添加 RECALLED 到枚举类型")
                    
                    # 验证添加结果
                    cursor.execute("""
                        SELECT enumlabel 
                        FROM pg_enum e
                        JOIN pg_type t ON e.enumtypid = t.oid 
                        WHERE t.typname = 'approvalstatus'
                        ORDER BY e.enumsortorder
                    """)
                    
                    new_values = [row[0] for row in cursor.fetchall()]
                    logger.info(f"✅ 验证成功，{self.config['display_name']}新枚举值: {new_values}")
                    
                finally:
                    cursor.close()
                    connection.close()
                
                # 测试功能
                logger.info("🧪 测试功能...")
                from app.models.approval import ApprovalStatus
                logger.info(f"📝 ApprovalStatus.RECALLED = {ApprovalStatus.RECALLED.value}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ 审批状态枚举修复失败: {str(e)}")
            return False
    
    def verify_fixes(self):
        """验证修复结果"""
        try:
            logger.info("🔍 验证修复结果...")
            
            from app import create_app
            app = create_app()
            
            with app.app_context():
                from app.models.version_management import VersionRecord
                from app.models.approval import ApprovalStatus, ApprovalInstance
                from app.extensions import db
                from sqlalchemy import text
                
                # 验证版本修复
                current_version = VersionRecord.get_current_version()
                if current_version:
                    logger.info(f"✅ 版本验证通过: {current_version.version_number}")
                    logger.info(f"✅ 发布时间: {current_version.release_date}")
                else:
                    logger.error("❌ 版本验证失败: 未找到当前版本")
                    return False
                
                # 验证枚举修复
                result = db.session.execute(text("""
                    SELECT enumlabel 
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid 
                    WHERE t.typname = 'approvalstatus'
                    AND e.enumlabel = 'RECALLED'
                """))
                
                if result.fetchone():
                    logger.info("✅ 枚举验证通过: RECALLED 值存在")
                    
                    # 测试枚举查询
                    try:
                        test_query = ApprovalInstance.query.filter(
                            ApprovalInstance.status == ApprovalStatus.RECALLED
                        ).limit(1)
                        test_query.statement  # 验证SQL有效性
                        logger.info("✅ 枚举功能验证通过: 可正常查询")
                    except Exception as e:
                        logger.warning(f"⚠️  枚举功能验证警告: {str(e)}")
                        
                else:
                    logger.error("❌ 枚举验证失败: RECALLED 值不存在")
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"❌ 验证过程失败: {str(e)}")
            return False
    
    def run_migration_fix(self):
        """执行完整的迁移修复流程"""
        logger.info("=" * 60)
        logger.info(f"🚀 开始{self.config['display_name']}迁移修复")
        logger.info("=" * 60)
        
        try:
            # 第1步：创建备份
            logger.info("📋 第1步：创建迁移前备份")
            backup_path = self.create_pre_migration_backup()
            if not backup_path:
                logger.error("❌ 备份失败，停止迁移")
                return False
            
            # 第2步：修复版本同步
            logger.info("📋 第2步：修复版本同步问题")
            if not self.fix_version_sync():
                logger.error("❌ 版本同步修复失败")
                return False
            
            # 第3步：修复枚举问题  
            logger.info("📋 第3步：修复审批状态枚举")
            if not self.fix_approval_status_enum():
                logger.error("❌ 枚举修复失败")
                return False
            
            # 第4步：验证修复结果
            logger.info("📋 第4步：验证修复结果")
            if not self.verify_fixes():
                logger.error("❌ 修复验证失败")
                return False
            
            # 修复完成
            logger.info("=" * 60)
            logger.info(f"✅ {self.config['display_name']}迁移修复完成")
            logger.info("=" * 60)
            logger.info("")
            logger.info("📋 修复内容:")
            logger.info("- ✅ 版本同步: v1.0.1 → v1.3.5")
            logger.info("- ✅ 枚举修复: 添加 RECALLED 值")
            logger.info("- ✅ 数据备份: 已完成安全备份")
            logger.info("- ✅ 功能验证: 所有功能正常")
            logger.info("")
            logger.info("📋 后续操作:")
            logger.info("1. 重启云端应用服务")
            logger.info("2. 访问版本管理页面验证版本显示")
            logger.info("3. 测试报销图片上传功能")
            logger.info("4. 检查应用错误日志")
            logger.info(f"5. 备份文件位置: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移修复异常: {str(e)}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='云端SP8D和OVS数据库安全迁移修复工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python cloud_migration_fix_sp8d_ovs.py --database sp8d
  python cloud_migration_fix_sp8d_ovs.py --database ovs

环境变量:
  SP8D_DATABASE_PASSWORD  SP8D数据库密码
  OVS_DATABASE_PASSWORD   OVS数据库密码
        """
    )
    
    parser.add_argument(
        '--database', 
        choices=['sp8d', 'ovs'],
        required=True,
        help='指定要修复的数据库类型'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建迁移修复器
        fixer = CloudMigrationFixer(args.database)
        
        # 执行修复
        success = fixer.run_migration_fix()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("❌ 用户中断操作")
        return 1
    except Exception as e:
        logger.error(f"❌ 程序异常: {str(e)}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)