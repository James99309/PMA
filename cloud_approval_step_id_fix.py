#!/usr/bin/env python3
"""
云端数据库 ApprovalRecord 表 step_id 字段修复脚本
修复step_id字段的NOT NULL约束，支持模板快照情况下的NULL值

Created: 2025-06-27
Author: Assistant
Purpose: 修复云端数据库审批记录中的step_id类型错误
"""

import os
import sys
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# 云端数据库连接配置
CLOUD_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def parse_db_url(db_url):
    """解析数据库URL"""
    parsed = urlparse(db_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def get_cloud_connection():
    """获取云端数据库连接"""
    db_config = parse_db_url(CLOUD_DB_URL)
    return psycopg2.connect(**db_config)

def backup_cloud_approval_data():
    """备份云端审批相关数据"""
    print("=== 备份云端审批数据 ===")
    
    backup_dir = "cloud_db_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/approval_backup_{timestamp}.sql"
    
    db_config = parse_db_url(CLOUD_DB_URL)
    
    # 使用pg_dump备份审批相关表
    dump_cmd = [
        'pg_dump',
        f"--host={db_config['host']}",
        f"--port={db_config['port']}",
        f"--username={db_config['user']}",
        f"--dbname={db_config['database']}",
        '--verbose',
        '--clean',
        '--no-owner',
        '--no-privileges',
        '--format=plain',
        '--table=approval_record',
        '--table=approval_step',
        '--table=approval_instance',
        '--table=approval_process_template',
        f"--file={backup_file}"
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    try:
        import subprocess
        print(f"正在备份审批数据到: {backup_file}")
        result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 审批数据备份成功: {backup_file}")
            return backup_file
        else:
            print(f"❌ 备份失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ 备份过程出错: {str(e)}")
        return None

def check_cloud_approval_schema():
    """检查云端approval_record表的当前结构"""
    print("=== 检查云端approval_record表结构 ===")
    
    try:
        conn = get_cloud_connection()
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'approval_record'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        print(f"approval_record 表存在: {table_exists}")
        
        if table_exists:
            # 检查step_id字段的详细信息
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'approval_record'
                AND column_name = 'step_id';
            """)
            
            step_id_info = cursor.fetchone()
            if step_id_info:
                col_name, data_type, is_nullable, default_val = step_id_info
                print(f"step_id字段信息:")
                print(f"  数据类型: {data_type}")
                print(f"  可为空: {is_nullable}")
                print(f"  默认值: {default_val}")
                
                return is_nullable == 'NO'  # 返回True表示需要修复
            else:
                print("❌ 未找到step_id字段")
                return False
        else:
            print("❌ approval_record表不存在")
            return False
            
    except Exception as e:
        print(f"❌ 检查数据库结构时出错: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def check_problematic_records():
    """检查云端是否存在step_id为NULL的问题记录"""
    print("=== 检查问题记录 ===")
    
    try:
        conn = get_cloud_connection()
        cursor = conn.cursor()
        
        # 检查是否有step_id为NULL的记录
        cursor.execute("""
            SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL;
        """)
        
        null_count = cursor.fetchone()[0]
        print(f"step_id为NULL的记录数: {null_count}")
        
        # 检查总记录数
        cursor.execute("SELECT COUNT(*) FROM approval_record;")
        total_count = cursor.fetchone()[0]
        print(f"总审批记录数: {total_count}")
        
        if null_count > 0:
            # 显示一些示例记录
            cursor.execute("""
                SELECT id, approval_instance_id, approver_id, created_at
                FROM approval_record 
                WHERE step_id IS NULL 
                LIMIT 5;
            """)
            
            print(f"示例NULL记录:")
            for record in cursor.fetchall():
                print(f"  ID: {record[0]}, Instance: {record[1]}, Approver: {record[2]}, Created: {record[3]}")
        
        return null_count > 0
        
    except Exception as e:
        print(f"❌ 检查问题记录时出错: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def fix_cloud_step_id_constraint():
    """修复云端step_id字段的NOT NULL约束"""
    print("=== 修复云端step_id字段约束 ===")
    
    try:
        conn = get_cloud_connection()
        cursor = conn.cursor()
        
        # 开始事务
        cursor.execute("BEGIN;")
        
        # 修改step_id字段，允许NULL值
        alter_sql = "ALTER TABLE approval_record ALTER COLUMN step_id DROP NOT NULL;"
        
        print(f"执行SQL: {alter_sql}")
        cursor.execute(alter_sql)
        
        # 验证修改结果
        cursor.execute("""
            SELECT column_name, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'approval_record' 
            AND column_name = 'step_id';
        """)
        
        result = cursor.fetchone()
        if result:
            col_name, is_nullable = result
            print(f"验证结果 - 字段: {col_name}, 可为空: {is_nullable}")
            
            if is_nullable == 'YES':
                print("✅ step_id字段约束修改成功")
                cursor.execute("COMMIT;")
                return True
            else:
                print("❌ step_id字段约束修改失败")
                cursor.execute("ROLLBACK;")
                return False
        else:
            print("❌ 无法验证修改结果")
            cursor.execute("ROLLBACK;")
            return False
            
    except Exception as e:
        print(f"❌ 修复过程出错: {str(e)}")
        try:
            cursor.execute("ROLLBACK;")
        except:
            pass
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_fix_report():
    """创建修复报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"cloud_approval_fix_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 云端数据库审批字段修复报告\n\n")
        f.write(f"**修复时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**目标数据库**: {CLOUD_DB_URL.replace(CLOUD_DB_URL.split('@')[0].split(':')[-1], '***')}\n\n")
        f.write(f"## 修复内容\n")
        f.write(f"- 修改 `approval_record` 表的 `step_id` 字段约束\n")
        f.write(f"- 从 `NOT NULL` 改为允许 `NULL` 值\n")
        f.write(f"- 支持模板快照情况下的审批记录\n\n")
        f.write(f"## 相关文件\n")
        f.write(f"- 本地修复脚本: `fix_approval_record_step_id.py`\n")
        f.write(f"- 云端修复脚本: `cloud_approval_step_id_fix.py`\n")
        f.write(f"- 修复报告: `{report_file}`\n\n")
        f.write(f"## 技术细节\n")
        f.write(f"```sql\n")
        f.write(f"ALTER TABLE approval_record ALTER COLUMN step_id DROP NOT NULL;\n")
        f.write(f"```\n")
    
    return report_file

def main():
    """主函数"""
    print("=== 云端数据库审批字段修复工具 ===")
    print(f"目标数据库: {CLOUD_DB_URL.replace(CLOUD_DB_URL.split('@')[0].split(':')[-1], '***')}")
    print()
    
    try:
        # 1. 备份审批数据
        backup_file = backup_cloud_approval_data()
        if not backup_file:
            print("❌ 备份失败，建议修复备份问题后再继续")
            confirm = input("是否跳过备份继续修复？(y/N): ")
            if confirm.lower() != 'y':
                return
        print()
        
        # 2. 检查当前表结构
        needs_fix = check_cloud_approval_schema()
        print()
        
        if not needs_fix:
            print("✅ step_id字段已经允许NULL值，无需修复")
            return
        
        # 3. 检查问题记录
        has_null_records = check_problematic_records()
        print()
        
        # 4. 确认执行修复
        print("⚠️ 发现step_id字段不允许NULL值，需要修复")
        if has_null_records:
            print("⚠️ 发现存在step_id为NULL的记录，这可能导致数据插入错误")
        
        confirm = input("是否执行修复？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 用户取消修复")
            return
        
        # 5. 执行修复
        success = fix_cloud_step_id_constraint()
        print()
        
        # 6. 生成报告
        report_file = create_fix_report()
        
        if success:
            print("🎉 云端数据库审批字段修复完成！")
            print(f"📁 备份文件: {backup_file if backup_file else '无'}")
            print(f"📄 修复报告: {report_file}")
            print()
            print("现在云端数据库可以正确处理模板快照的审批记录了。")
        else:
            print("❌ 云端数据库审批字段修复失败！")
            print(f"📁 备份文件: {backup_file if backup_file else '无'}")
            print(f"📄 修复报告: {report_file}")
            print("请检查错误信息并手动修复。")
    
    except Exception as e:
        print(f"❌ 执行过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
"""
云端数据库 ApprovalRecord 表 step_id 字段修复脚本
修复step_id字段的NOT NULL约束，支持模板快照情况下的NULL值

Created: 2025-06-27
Author: Assistant
Purpose: 修复云端数据库审批记录中的step_id类型错误
"""

import os
import sys
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# 云端数据库连接配置
CLOUD_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def parse_db_url(db_url):
    """解析数据库URL"""
    parsed = urlparse(db_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def get_cloud_connection():
    """获取云端数据库连接"""
    db_config = parse_db_url(CLOUD_DB_URL)
    return psycopg2.connect(**db_config)

def backup_cloud_approval_data():
    """备份云端审批相关数据"""
    print("=== 备份云端审批数据 ===")
    
    backup_dir = "cloud_db_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/approval_backup_{timestamp}.sql"
    
    db_config = parse_db_url(CLOUD_DB_URL)
    
    # 使用pg_dump备份审批相关表
    dump_cmd = [
        'pg_dump',
        f"--host={db_config['host']}",
        f"--port={db_config['port']}",
        f"--username={db_config['user']}",
        f"--dbname={db_config['database']}",
        '--verbose',
        '--clean',
        '--no-owner',
        '--no-privileges',
        '--format=plain',
        '--table=approval_record',
        '--table=approval_step',
        '--table=approval_instance',
        '--table=approval_process_template',
        f"--file={backup_file}"
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = db_config['password']
    
    try:
        import subprocess
        print(f"正在备份审批数据到: {backup_file}")
        result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 审批数据备份成功: {backup_file}")
            return backup_file
        else:
            print(f"❌ 备份失败: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ 备份过程出错: {str(e)}")
        return None

def check_cloud_approval_schema():
    """检查云端approval_record表的当前结构"""
    print("=== 检查云端approval_record表结构 ===")
    
    try:
        conn = get_cloud_connection()
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'approval_record'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        print(f"approval_record 表存在: {table_exists}")
        
        if table_exists:
            # 检查step_id字段的详细信息
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = 'approval_record'
                AND column_name = 'step_id';
            """)
            
            step_id_info = cursor.fetchone()
            if step_id_info:
                col_name, data_type, is_nullable, default_val = step_id_info
                print(f"step_id字段信息:")
                print(f"  数据类型: {data_type}")
                print(f"  可为空: {is_nullable}")
                print(f"  默认值: {default_val}")
                
                return is_nullable == 'NO'  # 返回True表示需要修复
            else:
                print("❌ 未找到step_id字段")
                return False
        else:
            print("❌ approval_record表不存在")
            return False
            
    except Exception as e:
        print(f"❌ 检查数据库结构时出错: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def check_problematic_records():
    """检查云端是否存在step_id为NULL的问题记录"""
    print("=== 检查问题记录 ===")
    
    try:
        conn = get_cloud_connection()
        cursor = conn.cursor()
        
        # 检查是否有step_id为NULL的记录
        cursor.execute("""
            SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL;
        """)
        
        null_count = cursor.fetchone()[0]
        print(f"step_id为NULL的记录数: {null_count}")
        
        # 检查总记录数
        cursor.execute("SELECT COUNT(*) FROM approval_record;")
        total_count = cursor.fetchone()[0]
        print(f"总审批记录数: {total_count}")
        
        if null_count > 0:
            # 显示一些示例记录
            cursor.execute("""
                SELECT id, approval_instance_id, approver_id, created_at
                FROM approval_record 
                WHERE step_id IS NULL 
                LIMIT 5;
            """)
            
            print(f"示例NULL记录:")
            for record in cursor.fetchall():
                print(f"  ID: {record[0]}, Instance: {record[1]}, Approver: {record[2]}, Created: {record[3]}")
        
        return null_count > 0
        
    except Exception as e:
        print(f"❌ 检查问题记录时出错: {str(e)}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def fix_cloud_step_id_constraint():
    """修复云端step_id字段的NOT NULL约束"""
    print("=== 修复云端step_id字段约束 ===")
    
    try:
        conn = get_cloud_connection()
        cursor = conn.cursor()
        
        # 开始事务
        cursor.execute("BEGIN;")
        
        # 修改step_id字段，允许NULL值
        alter_sql = "ALTER TABLE approval_record ALTER COLUMN step_id DROP NOT NULL;"
        
        print(f"执行SQL: {alter_sql}")
        cursor.execute(alter_sql)
        
        # 验证修改结果
        cursor.execute("""
            SELECT column_name, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'approval_record' 
            AND column_name = 'step_id';
        """)
        
        result = cursor.fetchone()
        if result:
            col_name, is_nullable = result
            print(f"验证结果 - 字段: {col_name}, 可为空: {is_nullable}")
            
            if is_nullable == 'YES':
                print("✅ step_id字段约束修改成功")
                cursor.execute("COMMIT;")
                return True
            else:
                print("❌ step_id字段约束修改失败")
                cursor.execute("ROLLBACK;")
                return False
        else:
            print("❌ 无法验证修改结果")
            cursor.execute("ROLLBACK;")
            return False
            
    except Exception as e:
        print(f"❌ 修复过程出错: {str(e)}")
        try:
            cursor.execute("ROLLBACK;")
        except:
            pass
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_fix_report():
    """创建修复报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"cloud_approval_fix_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 云端数据库审批字段修复报告\n\n")
        f.write(f"**修复时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**目标数据库**: {CLOUD_DB_URL.replace(CLOUD_DB_URL.split('@')[0].split(':')[-1], '***')}\n\n")
        f.write(f"## 修复内容\n")
        f.write(f"- 修改 `approval_record` 表的 `step_id` 字段约束\n")
        f.write(f"- 从 `NOT NULL` 改为允许 `NULL` 值\n")
        f.write(f"- 支持模板快照情况下的审批记录\n\n")
        f.write(f"## 相关文件\n")
        f.write(f"- 本地修复脚本: `fix_approval_record_step_id.py`\n")
        f.write(f"- 云端修复脚本: `cloud_approval_step_id_fix.py`\n")
        f.write(f"- 修复报告: `{report_file}`\n\n")
        f.write(f"## 技术细节\n")
        f.write(f"```sql\n")
        f.write(f"ALTER TABLE approval_record ALTER COLUMN step_id DROP NOT NULL;\n")
        f.write(f"```\n")
    
    return report_file

def main():
    """主函数"""
    print("=== 云端数据库审批字段修复工具 ===")
    print(f"目标数据库: {CLOUD_DB_URL.replace(CLOUD_DB_URL.split('@')[0].split(':')[-1], '***')}")
    print()
    
    try:
        # 1. 备份审批数据
        backup_file = backup_cloud_approval_data()
        if not backup_file:
            print("❌ 备份失败，建议修复备份问题后再继续")
            confirm = input("是否跳过备份继续修复？(y/N): ")
            if confirm.lower() != 'y':
                return
        print()
        
        # 2. 检查当前表结构
        needs_fix = check_cloud_approval_schema()
        print()
        
        if not needs_fix:
            print("✅ step_id字段已经允许NULL值，无需修复")
            return
        
        # 3. 检查问题记录
        has_null_records = check_problematic_records()
        print()
        
        # 4. 确认执行修复
        print("⚠️ 发现step_id字段不允许NULL值，需要修复")
        if has_null_records:
            print("⚠️ 发现存在step_id为NULL的记录，这可能导致数据插入错误")
        
        confirm = input("是否执行修复？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 用户取消修复")
            return
        
        # 5. 执行修复
        success = fix_cloud_step_id_constraint()
        print()
        
        # 6. 生成报告
        report_file = create_fix_report()
        
        if success:
            print("🎉 云端数据库审批字段修复完成！")
            print(f"📁 备份文件: {backup_file if backup_file else '无'}")
            print(f"📄 修复报告: {report_file}")
            print()
            print("现在云端数据库可以正确处理模板快照的审批记录了。")
        else:
            print("❌ 云端数据库审批字段修复失败！")
            print(f"📁 备份文件: {backup_file if backup_file else '无'}")
            print(f"📄 修复报告: {report_file}")
            print("请检查错误信息并手动修复。")
    
    except Exception as e:
        print(f"❌ 执行过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 