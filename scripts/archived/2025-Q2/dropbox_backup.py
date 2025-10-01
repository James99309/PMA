#!/usr/bin/env python3
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
