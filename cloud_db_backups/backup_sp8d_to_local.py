#!/usr/bin/env python3
"""
备份云端sp8d数据库到本地脚本
将云端 pma_db_sp8d 数据库完整备份到本地目录
"""

import os
import subprocess
import datetime
import sys

def backup_sp8d_database():
    """备份云端sp8d数据库到本地"""
    
    # 云端数据库连接信息
    CLOUD_DB_URL = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
    
    # 本地备份目录
    backup_dir = "/Users/nijie/Documents/PMA/cloud_db_backups"
    
    # 确保备份目录存在
    os.makedirs(backup_dir, exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 备份文件名
    backup_filename = f"cloud_sp8d_backup_{timestamp}.sql"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # 备份信息文件
    info_filename = f"cloud_sp8d_backup_info_{timestamp}.md"
    info_path = os.path.join(backup_dir, info_filename)
    
    print(f"开始备份云端sp8d数据库...")
    print(f"备份文件: {backup_path}")
    
    try:
        # 使用pg_dump备份数据库
        cmd = [
            "pg_dump",
            "--verbose",
            "--clean",
            "--no-acl",
            "--no-owner",
            "--format=plain",
            "--file", backup_path,
            CLOUD_DB_URL
        ]
        
        # 执行备份命令
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print(f"✅ 备份成功完成!")
            print(f"📁 备份文件保存至: {backup_path}")
            
            # 获取备份文件大小
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / 1024 / 1024
            
            # 创建备份信息文件
            info_content = f"""# 云端sp8d数据库备份信息

## 备份详情
- **备份时间**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **数据库**: pma_db_sp8d (云端)
- **连接地址**: dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com
- **备份文件**: {backup_filename}
- **文件大小**: {file_size_mb:.2f} MB ({file_size:,} bytes)
- **备份方式**: pg_dump (完整备份，包含结构和数据)

## 备份状态
✅ 备份成功完成

## 备份选项
- 格式: Plain SQL
- 包含清理语句: 是
- 包含权限: 否
- 包含所有者: 否

## 使用说明
1. 恢复到本地PostgreSQL:
   ```bash
   psql -d your_local_database < {backup_filename}
   ```

2. 查看备份内容:
   ```bash
   head -n 50 {backup_filename}
   ```

## 注意事项
- 此备份仅用于本地开发和测试
- 不会修改云端数据库的任何数据或结构
- 备份文件包含完整的数据库结构和数据
"""
            
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(info_content)
            
            print(f"📋 备份信息文件: {info_path}")
            print(f"💾 备份大小: {file_size_mb:.2f} MB")
            
            # 显示最近的备份文件
            print("\n📂 最近的sp8d备份文件:")
            sp8d_files = [f for f in os.listdir(backup_dir) if 'sp8d' in f and f.endswith('.sql')]
            sp8d_files.sort(reverse=True)
            for i, file in enumerate(sp8d_files[:5]):
                file_path = os.path.join(backup_dir, file)
                file_size = os.path.getsize(file_path) / 1024 / 1024
                print(f"  {i+1}. {file} ({file_size:.1f} MB)")
            
            return True
            
        else:
            print(f"❌ 备份失败!")
            print(f"错误代码: {result.returncode}")
            print(f"错误信息: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 备份超时 (10分钟)")
        return False
    except Exception as e:
        print(f"❌ 备份过程中出错: {str(e)}")
        return False

def list_existing_backups():
    """列出现有的sp8d备份文件"""
    backup_dir = "/Users/nijie/Documents/PMA/cloud_db_backups"
    
    if not os.path.exists(backup_dir):
        print("❌ 备份目录不存在")
        return
    
    sp8d_files = [f for f in os.listdir(backup_dir) if 'sp8d' in f and f.endswith('.sql')]
    
    if not sp8d_files:
        print("📂 未找到现有的sp8d备份文件")
        return
    
    sp8d_files.sort(reverse=True)
    print(f"\n📂 现有的sp8d备份文件 (共 {len(sp8d_files)} 个):")
    
    for i, file in enumerate(sp8d_files):
        file_path = os.path.join(backup_dir, file)
        file_size = os.path.getsize(file_path) / 1024 / 1024
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"  {i+1:2d}. {file}")
        print(f"      大小: {file_size:.1f} MB, 修改时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🔄 云端sp8d数据库备份工具")
    print("=" * 50)
    
    # 检查pg_dump是否可用
    try:
        subprocess.run(["pg_dump", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 错误: 未找到 pg_dump 命令")
        print("请确保已安装 PostgreSQL 客户端工具")
        sys.exit(1)
    
    # 显示现有备份
    list_existing_backups()
    
    # 询问是否进行备份
    print("\n🤔 是否要创建新的sp8d数据库备份?")
    print("注意: 这只会备份数据到本地，不会修改云端数据库")
    
    choice = input("请输入 'y' 继续备份，或 'n' 取消: ").strip().lower()
    
    if choice in ['y', 'yes', '是']:
        success = backup_sp8d_database()
        if success:
            print("\n🎉 备份完成! 您可以安全地使用备份文件进行本地开发和测试。")
        else:
            print("\n😔 备份失败，请检查网络连接和数据库访问权限。")
            sys.exit(1)
    else:
        print("🚫 备份已取消")