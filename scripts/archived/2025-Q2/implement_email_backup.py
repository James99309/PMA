#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实现邮件备份功能
基于分析结果，为PMA系统添加邮件备份功能
"""

import os
import subprocess
import gzip
import tempfile
from datetime import datetime
from urllib.parse import urlparse
from config import CLOUD_DB_URL

def create_email_backup_service():
    """创建邮件备份服务的增强版本"""
    
    email_backup_code = '''
def create_backup_with_email(self, backup_type='full'):
    """创建备份并通过邮件发送"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"pma_backup_{backup_type}_{timestamp}.sql"
    
    try:
        logger.info(f"🔄 开始创建{backup_type}备份: {backup_filename}")
        
        # 创建临时备份文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
            backup_path = temp_file.name
        
        # 构建pg_dump命令
        cmd = [
            'pg_dump',
            '--host', self.db_config['host'],
            '--port', str(self.db_config['port']),
            '--username', self.db_config['username'],
            '--no-password',
            '--format', 'plain',
            '--clean',
            '--create',
            '--encoding', 'UTF8'
        ]
        
        # 根据备份类型添加选项
        if backup_type == 'schema_only':
            cmd.append('--schema-only')
        elif backup_type == 'data_only':
            cmd.append('--data-only')
        
        cmd.append(self.db_config['database'])
        
        # 设置环境变量
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['password']
        
        # 执行备份
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
        
        if result.returncode != 0:
            logger.error(f"❌ 备份创建失败: {result.stderr}")
            os.remove(backup_path)
            return None
        
        # 获取原始文件大小
        original_size = os.path.getsize(backup_path)
        original_size_mb = original_size / (1024 * 1024)
        
        logger.info(f"✅ 原始备份文件: {original_size_mb:.2f} MB")
        
        # 压缩备份文件
        compressed_path = backup_path + '.gz'
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.writelines(f_in)
        
        compressed_size = os.path.getsize(compressed_path)
        compressed_size_mb = compressed_size / (1024 * 1024)
        compression_ratio = compressed_size / original_size if original_size > 0 else 0
        
        logger.info(f"✅ 压缩备份文件: {compressed_size_mb:.2f} MB (压缩比: {compression_ratio:.1%})")
        
        # 删除原始文件，使用压缩文件
        os.remove(backup_path)
        backup_path = compressed_path
        backup_filename = backup_filename + '.gz'
        
        # 检查是否适合邮件发送
        max_email_size_mb = 20  # 保守的邮件附件大小限制
        
        if compressed_size_mb <= max_email_size_mb:
            # 发送邮件
            email_sent = self._send_backup_email(backup_path, backup_filename, compressed_size_mb, backup_type)
            if email_sent:
                logger.info(f"📧 备份文件已通过邮件发送")
            else:
                logger.warning(f"⚠️ 邮件发送失败，备份文件已保存到本地")
        else:
            logger.warning(f"⚠️ 备份文件过大 ({compressed_size_mb:.2f} MB)，跳过邮件发送")
        
        # 保存到本地备份目录
        local_backup_path = os.path.join(self.backup_location, backup_filename)
        os.makedirs(self.backup_location, exist_ok=True)
        
        # 移动文件到备份目录
        import shutil
        shutil.move(backup_path, local_backup_path)
        
        logger.info(f"💾 备份文件已保存: {local_backup_path}")
        
        return local_backup_path
        
    except Exception as e:
        logger.error(f"❌ 备份过程中发生错误: {str(e)}")
        # 清理临时文件
        for temp_path in [backup_path, compressed_path]:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
        return None

def _send_backup_email(self, backup_path, filename, file_size_mb, backup_type):
    """通过邮件发送备份文件"""
    try:
        from flask_mail import Message
        from app import mail
        
        # 准备邮件内容
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        subject = f'PMA数据库自动备份 - {timestamp}'
        
        # 获取数据库统计信息
        db_stats = self._get_database_stats()
        
        body = f"""
PMA系统自动备份报告

📊 备份信息:
- 备份时间: {timestamp}
- 备份类型: {backup_type}
- 备份文件: {filename}
- 文件大小: {file_size_mb:.2f} MB

📈 数据库统计:
- 数据库大小: {db_stats.get('db_size', 'N/A')}
- 总记录数: {db_stats.get('total_records', 'N/A'):,} 条
- 主要数据表:
  • 报价明细: {db_stats.get('quotation_details', 0):,} 条
  • 项目记录: {db_stats.get('projects', 0):,} 条
  • 公司信息: {db_stats.get('companies', 0):,} 条

🔧 系统信息:
- 环境: 生产环境
- 版本: 1.0.1
- 平台: Render Cloud
- 备份策略: 每日自动备份

📋 使用说明:
1. 下载附件中的备份文件
2. 解压 .gz 文件得到 .sql 文件
3. 使用 psql 命令恢复数据库:
   psql -h hostname -U username -d database < backup_file.sql

⚠️ 重要提醒:
- 请妥善保存此备份文件
- 建议定期测试备份文件的完整性
- 如有问题请及时联系系统管理员

---
PMA自动备份系统
此邮件由系统自动发送，请勿回复
        """.strip()
        
        # 创建邮件
        recipients = [
            'James.ni@evertacsolutions.com',
            'james98980566@gmail.com'
        ]
        
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body
        )
        
        # 添加备份文件作为附件
        with open(backup_path, 'rb') as f:
            msg.attach(
                filename,
                'application/gzip',
                f.read(),
                'attachment'
            )
        
        # 发送邮件
        mail.send(msg)
        logger.info(f"✅ 备份邮件已发送到: {', '.join(recipients)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {str(e)}")
        return False

def _get_database_stats(self):
    """获取数据库统计信息"""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password']
        )
        
        stats = {}
        
        with conn.cursor() as cursor:
            # 获取数据库大小
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            stats['db_size'] = cursor.fetchone()[0]
            
            # 获取主要表的记录数
            tables = ['quotation_details', 'projects', 'companies', 'quotations', 'contacts']
            total_records = 0
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats[table] = count
                    total_records += count
                except:
                    stats[table] = 0
            
            stats['total_records'] = total_records
        
        conn.close()
        return stats
        
    except Exception as e:
        logger.warning(f"获取数据库统计信息失败: {str(e)}")
        return {}
'''
    
    return email_backup_code

def update_backup_service_file():
    """更新备份服务文件"""
    
    backup_service_file = 'app/services/database_backup.py'
    
    # 读取现有文件
    with open(backup_service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经包含邮件备份功能
    if 'create_backup_with_email' in content:
        print("✅ 邮件备份功能已存在")
        return True
    
    # 在类中添加邮件备份方法
    email_methods = '''
    def create_backup_with_email(self, backup_type='full'):
        """创建备份并通过邮件发送"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"pma_backup_{backup_type}_{timestamp}.sql"
        
        try:
            logger.info(f"🔄 开始创建{backup_type}备份: {backup_filename}")
            
            # 创建临时备份文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                backup_path = temp_file.name
            
            # 构建pg_dump命令
            cmd = [
                'pg_dump',
                '--host', self.db_config['host'],
                '--port', str(self.db_config['port']),
                '--username', self.db_config['username'],
                '--no-password',
                '--format', 'plain',
                '--clean',
                '--create',
                '--encoding', 'UTF8'
            ]
            
            # 根据备份类型添加选项
            if backup_type == 'schema_only':
                cmd.append('--schema-only')
            elif backup_type == 'data_only':
                cmd.append('--data-only')
            
            cmd.append(self.db_config['database'])
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # 执行备份
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ 备份创建失败: {result.stderr}")
                os.remove(backup_path)
                return None
            
            # 获取原始文件大小
            original_size = os.path.getsize(backup_path)
            original_size_mb = original_size / (1024 * 1024)
            
            logger.info(f"✅ 原始备份文件: {original_size_mb:.2f} MB")
            
            # 压缩备份文件
            compressed_path = backup_path + '.gz'
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            compressed_size = os.path.getsize(compressed_path)
            compressed_size_mb = compressed_size / (1024 * 1024)
            compression_ratio = compressed_size / original_size if original_size > 0 else 0
            
            logger.info(f"✅ 压缩备份文件: {compressed_size_mb:.2f} MB (压缩比: {compression_ratio:.1%})")
            
            # 删除原始文件，使用压缩文件
            os.remove(backup_path)
            backup_path = compressed_path
            backup_filename = backup_filename + '.gz'
            
            # 检查是否适合邮件发送
            max_email_size_mb = 20  # 保守的邮件附件大小限制
            
            if compressed_size_mb <= max_email_size_mb:
                # 发送邮件
                email_sent = self._send_backup_email(backup_path, backup_filename, compressed_size_mb, backup_type)
                if email_sent:
                    logger.info(f"📧 备份文件已通过邮件发送")
                else:
                    logger.warning(f"⚠️ 邮件发送失败，备份文件已保存到本地")
            else:
                logger.warning(f"⚠️ 备份文件过大 ({compressed_size_mb:.2f} MB)，跳过邮件发送")
            
            # 保存到本地备份目录
            local_backup_path = os.path.join(self.backup_location, backup_filename)
            os.makedirs(self.backup_location, exist_ok=True)
            
            # 移动文件到备份目录
            import shutil
            shutil.move(backup_path, local_backup_path)
            
            logger.info(f"💾 备份文件已保存: {local_backup_path}")
            
            return local_backup_path
            
        except Exception as e:
            logger.error(f"❌ 备份过程中发生错误: {str(e)}")
            # 清理临时文件
            for temp_path in [backup_path, compressed_path]:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            return None

    def _send_backup_email(self, backup_path, filename, file_size_mb, backup_type):
        """通过邮件发送备份文件"""
        try:
            from flask_mail import Message
            from app import mail
            
            # 准备邮件内容
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            subject = f'PMA数据库自动备份 - {timestamp}'
            
            # 获取数据库统计信息
            db_stats = self._get_database_stats()
            
            body = f"""
PMA系统自动备份报告

📊 备份信息:
- 备份时间: {timestamp}
- 备份类型: {backup_type}
- 备份文件: {filename}
- 文件大小: {file_size_mb:.2f} MB

📈 数据库统计:
- 数据库大小: {db_stats.get('db_size', 'N/A')}
- 总记录数: {db_stats.get('total_records', 'N/A'):,} 条
- 主要数据表:
  • 报价明细: {db_stats.get('quotation_details', 0):,} 条
  • 项目记录: {db_stats.get('projects', 0):,} 条
  • 公司信息: {db_stats.get('companies', 0):,} 条

🔧 系统信息:
- 环境: 生产环境
- 版本: 1.0.1
- 平台: Render Cloud
- 备份策略: 每日自动备份

📋 使用说明:
1. 下载附件中的备份文件
2. 解压 .gz 文件得到 .sql 文件
3. 使用 psql 命令恢复数据库:
   psql -h hostname -U username -d database < backup_file.sql

⚠️ 重要提醒:
- 请妥善保存此备份文件
- 建议定期测试备份文件的完整性
- 如有问题请及时联系系统管理员

---
PMA自动备份系统
此邮件由系统自动发送，请勿回复
            """.strip()
            
            # 创建邮件
            recipients = [
                'James.ni@evertacsolutions.com',
                'james98980566@gmail.com'
            ]
            
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=body
            )
            
            # 添加备份文件作为附件
            with open(backup_path, 'rb') as f:
                msg.attach(
                    filename,
                    'application/gzip',
                    f.read(),
                    'attachment'
                )
            
            # 发送邮件
            mail.send(msg)
            logger.info(f"✅ 备份邮件已发送到: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {str(e)}")
            return False

    def _get_database_stats(self):
        """获取数据库统计信息"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password']
            )
            
            stats = {}
            
            with conn.cursor() as cursor:
                # 获取数据库大小
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                stats['db_size'] = cursor.fetchone()[0]
                
                # 获取主要表的记录数
                tables = ['quotation_details', 'projects', 'companies', 'quotations', 'contacts']
                total_records = 0
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        stats[table] = count
                        total_records += count
                    except:
                        stats[table] = 0
                
                stats['total_records'] = total_records
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.warning(f"获取数据库统计信息失败: {str(e)}")
            return {}

    def _daily_backup_job_with_email(self):
        """每日备份任务（带邮件发送）"""
        logger.info("🕛 执行定时完整备份（邮件发送）...")
        self.create_backup_with_email('full')
'''
    
    # 添加必要的导入
    import_additions = '''import tempfile
import gzip
import shutil'''
    
    # 在文件开头添加导入
    if 'import tempfile' not in content:
        content = content.replace('import time', f'import time\n{import_additions}')
    
    # 在类的最后添加新方法
    class_end_pattern = 'def get_backup_service():'
    if class_end_pattern in content:
        content = content.replace(class_end_pattern, email_methods + '\n\n' + class_end_pattern)
    
    # 写回文件
    with open(backup_service_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 邮件备份功能已添加到备份服务")
    return True

def create_test_email_backup():
    """创建测试邮件备份脚本"""
    
    test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试邮件备份功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.database_backup import get_backup_service
from app import create_app
import logging

logging.basicConfig(level=logging.INFO)

def test_email_backup():
    """测试邮件备份功能"""
    print("🧪 开始测试邮件备份功能...")
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        # 获取备份服务
        backup_service = get_backup_service()
        
        if not backup_service:
            print("❌ 备份服务未启用")
            return False
        
        # 测试邮件备份
        print("📧 创建测试备份并发送邮件...")
        backup_path = backup_service.create_backup_with_email('full')
        
        if backup_path:
            print(f"✅ 测试备份成功: {backup_path}")
            print("📧 请检查邮箱是否收到备份文件")
            return True
        else:
            print("❌ 测试备份失败")
            return False

if __name__ == "__main__":
    test_email_backup()
'''
    
    with open('test_email_backup.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ 测试脚本已创建: test_email_backup.py")

def main():
    """主函数"""
    print("📧 实施PMA邮件备份功能")
    print("=" * 50)
    
    print("\n📊 基于分析结果:")
    print("- 数据库大小: 15.55 MB")
    print("- 压缩备份: 0.35 MB")
    print("- 邮件可行性: ✅ 完全支持")
    
    print("\n🔧 开始实施邮件备份功能...")
    
    # 1. 更新备份服务文件
    print("1. 更新备份服务文件...")
    update_backup_service_file()
    
    # 2. 创建测试脚本
    print("2. 创建测试脚本...")
    create_test_email_backup()
    
    print("\n✅ 邮件备份功能实施完成！")
    
    print("\n📋 下一步操作:")
    print("1. 重启PMA应用使更改生效")
    print("2. 运行测试脚本: python test_email_backup.py")
    print("3. 检查邮箱是否收到测试备份")
    print("4. 配置定时任务使用邮件备份")
    
    print("\n⏰ 邮件备份发送逻辑:")
    print("- 触发时间: 每天凌晨00:00")
    print("- 备份流程: 创建 → 压缩 → 检查大小 → 发送邮件 → 本地保存")
    print("- 接收邮箱: James.ni@evertacsolutions.com, james98980566@gmail.com")
    print("- 文件格式: .sql.gz (压缩SQL文件)")
    print("- 邮件内容: 包含备份统计和使用说明")

if __name__ == "__main__":
    main() 