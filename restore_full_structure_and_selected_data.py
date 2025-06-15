#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复6月13日15点18分云端备份数据到云端数据库
- 恢复所有表结构
- 恢复users表数据
- 恢复role_permissions表数据
- 恢复所有字典表数据
"""

import psycopg2
import sys
import os
import re
from datetime import datetime
from io import StringIO

# 云端数据库连接信息
CLOUD_DB_URL = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"

# 备份文件路径
BACKUP_FILE = "cloud_backup_20250613_151838.sql"

# 需要恢复数据的表（除了结构）
DATA_TABLES = [
    'users',
    'role_permissions',
    # 字典表和基础数据表
    'affiliations',
    'dictionaries',
    'product_categories',
    'product_subcategories',
    'product_regions',
    'companies',
    'permissions',
    'system_settings',
    'alembic_version',
    'version_records'
]

def connect_to_cloud_db():
    """连接到云端数据库"""
    try:
        conn = psycopg2.connect(CLOUD_DB_URL)
        conn.autocommit = False
        print("✅ 成功连接到云端数据库")
        return conn
    except Exception as e:
        print(f"❌ 连接云端数据库失败: {e}")
        return None

def extract_all_table_structures(backup_file):
    """从备份文件中提取所有表结构"""
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有CREATE TABLE语句
        create_tables = []
        pattern = r'CREATE TABLE public\.\w+\s*\([^;]+\);'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            create_sql = match.group(0)
            # 提取表名
            table_match = re.search(r'CREATE TABLE public\.(\w+)', create_sql)
            if table_match:
                table_name = table_match.group(1)
                create_tables.append((table_name, create_sql))
        
        print(f"✅ 找到 {len(create_tables)} 个表结构")
        return create_tables
    
    except Exception as e:
        print(f"❌ 读取备份文件失败: {e}")
        return []

def extract_table_data(backup_file, table_name):
    """从备份文件中提取指定表的数据"""
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找COPY语句（数据）
        copy_pattern = f"COPY public.{table_name} ("
        copy_start = content.find(copy_pattern)
        if copy_start == -1:
            print(f"⚠️  在备份文件中未找到表 {table_name} 的数据")
            return None
        
        # 找到数据的结束标记
        data_start = content.find("FROM stdin;", copy_start) + len("FROM stdin;\n")
        data_end = content.find("\\.", data_start)
        
        copy_header = content[copy_start:content.find("FROM stdin;", copy_start) + len("FROM stdin;")]
        data_content = content[data_start:data_end].strip()
        
        return copy_header, data_content
    
    except Exception as e:
        print(f"❌ 读取表 {table_name} 数据失败: {e}")
        return None

def extract_sequences(backup_file):
    """从备份文件中提取所有序列定义"""
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sequences = []
        
        # 查找CREATE SEQUENCE语句
        pattern = r'CREATE SEQUENCE public\.\w+[^;]+;'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            sequences.append(match.group(0))
        
        # 查找ALTER SEQUENCE OWNED BY语句
        pattern = r'ALTER SEQUENCE public\.\w+ OWNED BY[^;]+;'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            sequences.append(match.group(0))
        
        # 查找ALTER TABLE DEFAULT语句
        pattern = r'ALTER TABLE ONLY public\.\w+ ALTER COLUMN \w+ SET DEFAULT[^;]+;'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            sequences.append(match.group(0))
        
        print(f"✅ 找到 {len(sequences)} 个序列相关语句")
        return sequences
    
    except Exception as e:
        print(f"❌ 读取序列定义失败: {e}")
        return []

def restore_structures_to_cloud(conn, table_structures):
    """恢复所有表结构到云端数据库"""
    try:
        cursor = conn.cursor()
        
        print("🔄 删除所有现有表...")
        # 获取所有表名并删除
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%' 
            AND tablename NOT LIKE 'sql_%'
        """)
        existing_tables = cursor.fetchall()
        
        for (table_name,) in existing_tables:
            cursor.execute(f"DROP TABLE IF EXISTS public.{table_name} CASCADE;")
        
        print("🔄 删除所有现有序列...")
        cursor.execute("""
            SELECT sequence_name FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        existing_sequences = cursor.fetchall()
        
        for (seq_name,) in existing_sequences:
            cursor.execute(f"DROP SEQUENCE IF EXISTS public.{seq_name} CASCADE;")
        
        print("🔄 创建所有表结构...")
        for table_name, create_sql in table_structures:
            try:
                cursor.execute(create_sql)
                print(f"   ✅ 创建表: {table_name}")
            except Exception as e:
                print(f"   ❌ 创建表 {table_name} 失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复表结构失败: {e}")
        return False

def restore_sequences_to_cloud(conn, sequences):
    """恢复所有序列到云端数据库"""
    try:
        cursor = conn.cursor()
        
        print("🔄 创建所有序列...")
        for seq_sql in sequences:
            try:
                cursor.execute(seq_sql)
            except Exception as e:
                print(f"   ⚠️  序列语句执行警告: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复序列失败: {e}")
        return False

def restore_table_data_to_cloud(conn, table_name, data_info):
    """恢复表数据到云端数据库"""
    try:
        cursor = conn.cursor()
        
        if not data_info:
            print(f"   ⚠️  表 {table_name} 无数据")
            return True
        
        copy_header, data_content = data_info
        print(f"🔄 插入数据到表 {table_name}...")
        
        # 解析COPY语句获取列名
        columns_start = copy_header.find("(") + 1
        columns_end = copy_header.find(")")
        columns = copy_header[columns_start:columns_end]
        
        # 使用StringIO来处理数据
        data_io = StringIO(data_content)
        
        # 使用COPY命令插入数据
        copy_sql = f"COPY public.{table_name} ({columns}) FROM STDIN;"
        cursor.copy_expert(copy_sql, data_io)
        
        # 获取插入的记录数
        cursor.execute(f"SELECT COUNT(*) FROM public.{table_name};")
        count = cursor.fetchone()[0]
        print(f"   ✅ 插入 {count} 条记录到表 {table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复表 {table_name} 数据失败: {e}")
        return False

def reset_sequences(conn):
    """重置所有序列的当前值"""
    try:
        cursor = conn.cursor()
        
        print("🔄 重置序列当前值...")
        
        # 获取所有序列
        cursor.execute("""
            SELECT sequence_name FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        sequences = cursor.fetchall()
        
        for (seq_name,) in sequences:
            # 找到对应的表和列
            table_name = seq_name.replace('_id_seq', '')
            if table_name in [t for t in DATA_TABLES]:
                try:
                    cursor.execute(f"SELECT setval('public.{seq_name}', COALESCE((SELECT MAX(id) FROM public.{table_name}), 1), true);")
                    print(f"   ✅ 重置序列: {seq_name}")
                except Exception as e:
                    print(f"   ⚠️  重置序列 {seq_name} 警告: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 重置序列失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 开始恢复6月13日15点18分云端备份数据到云端数据库")
    print("📅 备份时间: 2025-06-13 15:18:38")
    print("🎯 恢复范围:")
    print("   - 所有表结构")
    print("   - users表数据")
    print("   - role_permissions表数据")
    print("   - 所有字典表数据")
    print("=" * 80)
    
    # 检查备份文件是否存在
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ 备份文件不存在: {BACKUP_FILE}")
        return False
    
    # 连接到云端数据库
    conn = connect_to_cloud_db()
    if not conn:
        return False
    
    try:
        # 开始事务
        conn.autocommit = False
        
        # 1. 提取所有表结构
        print("\n📋 提取所有表结构...")
        table_structures = extract_all_table_structures(BACKUP_FILE)
        if not table_structures:
            print("❌ 未找到任何表结构")
            return False
        
        # 2. 恢复所有表结构
        print("\n📋 恢复所有表结构...")
        if not restore_structures_to_cloud(conn, table_structures):
            conn.rollback()
            return False
        
        # 3. 提取并恢复序列
        print("\n📋 恢复序列...")
        sequences = extract_sequences(BACKUP_FILE)
        if sequences:
            restore_sequences_to_cloud(conn, sequences)
        
        # 4. 恢复指定表的数据
        print("\n📋 恢复表数据...")
        for table_name in DATA_TABLES:
            print(f"\n处理表: {table_name}")
            data_info = extract_table_data(BACKUP_FILE, table_name)
            if data_info:
                if not restore_table_data_to_cloud(conn, table_name, data_info):
                    print(f"⚠️  表 {table_name} 数据恢复失败，继续处理其他表...")
        
        # 5. 重置序列
        print("\n📋 重置序列...")
        reset_sequences(conn)
        
        # 提交事务
        conn.commit()
        print("\n✅ 所有数据恢复完成！")
        
        # 验证恢复结果
        print("\n📊 验证恢复结果:")
        cursor = conn.cursor()
        
        # 统计表数量
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        print(f"   - 总表数量: {table_count}")
        
        # 统计各个重要表的记录数
        for table_name in DATA_TABLES:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM public.{table_name};")
                count = cursor.fetchone()[0]
                print(f"   - {table_name}表记录数: {count}")
            except:
                print(f"   - {table_name}表: 不存在或无数据")
        
        # 显示部分用户信息
        try:
            print("\n👥 用户信息预览:")
            cursor.execute("SELECT id, username, real_name, company_name, department, role FROM public.users ORDER BY id LIMIT 5;")
            users = cursor.fetchall()
            for user in users:
                print(f"   - ID:{user[0]} | {user[1]} | {user[2]} | {user[3]} | {user[4]} | {user[5]}")
        except:
            print("   - 无法获取用户信息预览")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢复过程中发生错误: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
        print("\n🔐 数据库连接已关闭")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 数据恢复任务完成！")
        sys.exit(0)
    else:
        print("\n💥 数据恢复任务失败！")
        sys.exit(1) 