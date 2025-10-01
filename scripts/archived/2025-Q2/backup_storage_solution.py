#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份存储解决方案
解决Render平台临时文件系统的备份丢失问题
"""

import os
import subprocess
import logging
from datetime import datetime
from urllib.parse import urlparse
from config import CLOUD_DB_URL

logger = logging.getLogger(__name__)

class SecureBackupSolution:
    """安全备份解决方案"""
    
    def __init__(self):
        self.db_config = self._parse_database_url(CLOUD_DB_URL)
        
    def _parse_database_url(self, database_url):
        """解析数据库URL"""
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'username': parsed.username,
            'password': parsed.password,
            'database': parsed.path.strip('/')
        }
    
    def create_backup_with_email(self):
        """创建备份并通过邮件发送"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"cloud_backup_{timestamp}.sql"
        
        try:
            logger.info(f"开始创建备份: {backup_filename}")
            
            # 创建备份到临时文件
            cmd = [
                'pg_dump',
                '--host', self.db_config['host'],
                '--port', str(self.db_config['port']),
                '--username', self.db_config['username'],
                '--no-password',
                '--format', 'plain',
                '--clean',
                '--create',
                '--encoding', 'UTF8',
                self.db_config['database']
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # 执行备份
            with open(backup_filename, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
            
            if result.returncode == 0:
                file_size = os.path.getsize(backup_filename) / (1024 * 1024)
                logger.info(f"✅ 备份创建成功: {backup_filename} ({file_size:.2f} MB)")
                
                # 发送邮件
                self._send_backup_email(backup_filename, file_size)
                
                # 清理临时文件
                os.remove(backup_filename)
                return True
            else:
                logger.error(f"❌ 备份创建失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 备份过程中发生错误: {str(e)}")
            return False
    
    def _send_backup_email(self, filename, file_size_mb):
        """通过邮件发送备份文件"""
        try:
            from flask_mail import Message
            from app import mail
            
            # 检查文件大小（邮件附件限制通常为25MB）
            if file_size_mb > 20:  # 20MB以下才通过邮件发送
                logger.warning(f"备份文件过大 ({file_size_mb:.2f} MB)，跳过邮件发送")
                return False
            
            msg = Message(
                subject=f'PMA数据库备份 - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                recipients=['James.ni@evertacsolutions.com'],  # 您的邮箱
                body=f"""
PMA系统自动备份报告

备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
备份文件: {filename}
文件大小: {file_size_mb:.2f} MB
备份状态: 成功

请妥善保存此备份文件。

---
PMA自动备份系统
                """.strip()
            )
            
            # 添加备份文件作为附件
            with open(filename, 'rb') as f:
                msg.attach(filename, 'application/sql', f.read())
            
            mail.send(msg)
            logger.info(f"✅ 备份文件已通过邮件发送: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {str(e)}")
            return False
    
    def setup_github_backup(self):
        """设置GitHub备份方案"""
        github_script = """#!/bin/bash
# GitHub备份脚本
# 将备份文件推送到私有GitHub仓库

BACKUP_REPO="your-username/pma-backups"  # 替换为您的GitHub仓库
BACKUP_DIR="./github_backups"

# 创建备份目录
mkdir -p $BACKUP_DIR
cd $BACKUP_DIR

# 如果是第一次，克隆仓库
if [ ! -d ".git" ]; then
    git clone https://github.com/$BACKUP_REPO.git .
fi

# 创建数据库备份
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="cloud_backup_$TIMESTAMP.sql"

pg_dump \\
    --host=dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com \\
    --port=5432 \\
    --username=pma_db_sp8d_user \\
    --no-password \\
    --format=plain \\
    --clean \\
    --create \\
    --encoding=UTF8 \\
    pma_db_sp8d > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 提交到GitHub
git add .
git commit -m "Auto backup: $TIMESTAMP"
git push origin main

echo "✅ 备份已推送到GitHub: $BACKUP_FILE.gz"
"""
        
        with open('github_backup.sh', 'w') as f:
            f.write(github_script)
        
        os.chmod('github_backup.sh', 0o755)
        logger.info("✅ GitHub备份脚本已创建: github_backup.sh")
    
    def setup_dropbox_backup(self):
        """设置Dropbox备份方案"""
        dropbox_script = """#!/usr/bin/env python3
# Dropbox备份脚本
import dropbox
import subprocess
import os
from datetime import datetime

# Dropbox配置
DROPBOX_ACCESS_TOKEN = "your_dropbox_access_token"  # 需要获取Dropbox API令牌

def create_and_upload_backup():
    # 创建备份
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"cloud_backup_{timestamp}.sql"
    
    # 数据库备份命令
    cmd = [
        'pg_dump',
        '--host', 'dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com',
        '--port', '5432',
        '--username', 'pma_db_sp8d_user',
        '--no-password',
        '--format', 'plain',
        '--clean', '--create',
        'pma_db_sp8d'
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = 'LXNGJmR6bFrNecoaWbdbdzPpltIAd40w'
    
    with open(backup_filename, 'w') as f:
        subprocess.run(cmd, stdout=f, env=env)
    
    # 上传到Dropbox
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    with open(backup_filename, 'rb') as f:
        dbx.files_upload(f.read(), f'/PMA_Backups/{backup_filename}')
    
    # 清理本地文件
    os.remove(backup_filename)
    print(f"✅ 备份已上传到Dropbox: {backup_filename}")

if __name__ == "__main__":
    create_and_upload_backup()
"""
        
        with open('dropbox_backup.py', 'w') as f:
            f.write(dropbox_script)
        
        logger.info("✅ Dropbox备份脚本已创建: dropbox_backup.py")

def main():
    """主函数 - 演示各种备份方案"""
    solution = SecureBackupSolution()
    
    print("🔧 PMA备份存储解决方案")
    print("=" * 50)
    
    print("\n1. 📧 邮件备份方案")
    print("   - 自动将备份文件发送到指定邮箱")
    print("   - 适合小于20MB的备份文件")
    print("   - 已集成到现有系统中")
    
    print("\n2. 📁 GitHub私有仓库备份")
    print("   - 将备份文件推送到GitHub私有仓库")
    print("   - 版本控制，可追踪历史备份")
    print("   - 免费且可靠")
    solution.setup_github_backup()
    
    print("\n3. ☁️ Dropbox云存储备份")
    print("   - 上传到Dropbox云存储")
    print("   - 自动同步到本地设备")
    print("   - 需要Dropbox API令牌")
    solution.setup_dropbox_backup()
    
    print("\n4. 🔄 手动下载备份")
    print("   - 通过Web界面手动下载备份")
    print("   - 访问: http://localhost:10000/backup")
    print("   - 需要系统管理员权限")
    
    print("\n📋 推荐方案:")
    print("   1. 启用邮件备份（小文件）")
    print("   2. 设置GitHub私有仓库（大文件）")
    print("   3. 定期手动下载重要备份")

if __name__ == "__main__":
    main() 