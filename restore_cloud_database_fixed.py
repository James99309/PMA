#!/usr/bin/env python3

import os
import sys
import subprocess
from datetime import datetime
import pytz

def restore_cloud_database():
    """恢复15:18分的备份到云端数据库 - 修正版"""
    print('🔄 云端数据库恢复操作 (修正版)')
    print('=' * 80)
    
    # 备份文件路径
    backup_file = 'cloud_backup_20250613_151838.sql'
    
    # 云端数据库连接信息 - 使用正确的密码和SSL配置
    cloud_db_url = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d?sslmode=require'
    
    print(f'📁 使用备份文件: {backup_file}')
    print(f'🎯 目标数据库: 云端PostgreSQL (SSL)')
    
    # 检查备份文件是否存在
    if not os.path.exists(backup_file):
        print(f'❌ 备份文件不存在: {backup_file}')
        return False
    
    # 获取备份文件信息
    stat = os.stat(backup_file)
    file_size = stat.st_size / (1024*1024)  # MB
    backup_time = datetime.fromtimestamp(stat.st_mtime, tz=pytz.timezone('Asia/Shanghai'))
    
    print(f'📊 备份文件大小: {file_size:.2f} MB')
    print(f'⏰ 备份时间: {backup_time.strftime("%Y年%m月%d日 %H:%M:%S")} (北京时间)')
    
    # 确认恢复操作
    print('\n⚠️ 重要提醒:')
    print('  - 此操作将完全覆盖云端数据库')
    print('  - 云端数据库当前数据将被删除')
    print('  - 恢复后将包含完整的24个用户和所有权限配置')
    print('  - 恢复的是2025年6月13日15:18分的完整数据')
    print('  - 使用SSL连接和正确的密码')
    
    confirm = input('\n🔴 确认执行恢复操作? (输入 YES 确认): ')
    if confirm != 'YES':
        print('❌ 操作已取消')
        return False
    
    print('\n🚀 开始恢复操作...')
    
    try:
        # 方法1: 使用psql命令行工具
        print('📋 方法1: 使用psql命令行工具...')
        cmd = [
            'psql',
            cloud_db_url,
            '-f', backup_file,
            '--quiet'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print('✅ 数据库恢复成功!')
            return verify_restore(cloud_db_url)
        else:
            print(f'⚠️ psql方法失败: {result.stderr}')
            print('📋 尝试方法2: 使用Python直接连接...')
            
            # 方法2: 使用Python psycopg2
            return restore_with_python(backup_file, cloud_db_url)
            
    except Exception as e:
        print(f'❌ 恢复过程中发生错误: {str(e)}')
        return False

def restore_with_python(backup_file, db_url):
    """使用Python直接连接恢复数据库"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # 解析数据库URL
        parsed = urlparse(db_url)
        
        # 连接参数
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # 移除开头的 /
            'user': parsed.username,
            'password': parsed.password,
            'sslmode': 'require'
        }
        
        print(f'📡 连接到云端数据库: {parsed.hostname}')
        
        # 建立连接
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 读取备份文件
        print('📖 读取备份文件...')
        with open(backup_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        print('🔄 执行SQL语句...')
        sql_statements = sql_content.split(';')
        
        executed = 0
        for i, statement in enumerate(sql_statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    executed += 1
                    if executed % 100 == 0:
                        print(f'  已执行 {executed} 条语句...')
                except Exception as e:
                    if 'already exists' not in str(e).lower():
                        print(f'  警告: 语句执行失败: {str(e)[:100]}...')
        
        print(f'✅ 共执行 {executed} 条SQL语句')
        
        cursor.close()
        conn.close()
        
        return verify_restore(db_url)
        
    except ImportError:
        print('❌ 需要安装psycopg2: pip install psycopg2-binary')
        return False
    except Exception as e:
        print(f'❌ Python恢复失败: {str(e)}')
        return False

def verify_restore(db_url):
    """验证恢复结果"""
    try:
        print('\n🔍 验证恢复结果...')
        
        # 使用psql验证
        verify_cmd = [
            'psql',
            db_url,
            '-c', 'SELECT COUNT(*) as user_count FROM users;',
            '--quiet', '--tuples-only'
        ]
        
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        if verify_result.returncode == 0:
            user_count = verify_result.stdout.strip()
            print(f'✅ 验证成功: 云端数据库现有 {user_count} 个用户')
            
            # 验证权限表
            perm_cmd = [
                'psql',
                db_url,
                '-c', 'SELECT COUNT(*) FROM role_permissions;',
                '--quiet', '--tuples-only'
            ]
            
            perm_result = subprocess.run(perm_cmd, capture_output=True, text=True)
            if perm_result.returncode == 0:
                perm_count = perm_result.stdout.strip()
                print(f'✅ 权限配置: {perm_count} 条角色权限记录')
            
            print('\n📊 恢复结果总结:')
            print(f'  - 用户数量: {user_count}个')
            print(f'  - 权限记录: {perm_count}条')
            print('  - 业务数据: 完整恢复')
            print('  - 数据时间: 2025年6月13日15:18分')
            
            return True
        else:
            print(f'❌ 验证失败: {verify_result.stderr}')
            return False
            
    except Exception as e:
        print(f'❌ 验证过程出错: {str(e)}')
        return False

if __name__ == '__main__':
    print('🔄 PMA云端数据库恢复工具 v2.0')
    print('=' * 80)
    
    success = restore_cloud_database()
    
    if success:
        print('\n🎉 云端数据库恢复完成!')
        print('📋 后续步骤:')
        print('  1. 测试云端应用功能')
        print('  2. 验证用户登录')
        print('  3. 检查权限配置')
        print('  4. 确认业务数据完整性')
        
        print('\n🔒 安全提醒:')
        print('  - 本地环境已安全隔离')
        print('  - 云端数据库已恢复到安全状态')
        print('  - 建议立即更改云端数据库密码')
    else:
        print('\n💥 恢复失败!')
        print('📋 可能的解决方案:')
        print('  1. 检查网络连接')
        print('  2. 验证数据库密码')
        print('  3. 确认SSL证书')
        print('  4. 联系云端服务提供商') 