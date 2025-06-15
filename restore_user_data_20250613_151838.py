#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复6月13日15点18分云端备份中的用户数据和角色权限数据到云端数据库
只恢复users表和role_permissions表的结构和数据
"""

import psycopg2
import sys
import os
from datetime import datetime

# 云端数据库连接信息
CLOUD_DB_URL = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"

# 备份文件路径
BACKUP_FILE = "cloud_backup_20250613_151838.sql"

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

def extract_table_structure_and_data(backup_file, table_name):
    """从备份文件中提取指定表的结构和数据"""
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找CREATE TABLE语句
        create_start = content.find(f"CREATE TABLE public.{table_name} (")
        if create_start == -1:
            print(f"❌ 在备份文件中未找到表 {table_name} 的结构定义")
            return None, None
        
        # 找到CREATE TABLE语句的结束
        create_end = content.find(";", create_start)
        create_sql = content[create_start:create_end + 1]
        
        # 查找COPY语句（数据）
        copy_pattern = f"COPY public.{table_name} ("
        copy_start = content.find(copy_pattern)
        if copy_start == -1:
            print(f"❌ 在备份文件中未找到表 {table_name} 的数据")
            return create_sql, None
        
        # 找到数据的结束标记
        data_start = content.find("FROM stdin;", copy_start) + len("FROM stdin;\n")
        data_end = content.find("\\.", data_start)
        
        copy_header = content[copy_start:content.find("FROM stdin;", copy_start) + len("FROM stdin;")]
        data_content = content[data_start:data_end].strip()
        
        return create_sql, (copy_header, data_content)
    
    except Exception as e:
        print(f"❌ 读取备份文件失败: {e}")
        return None, None

def restore_table_to_cloud(conn, table_name, create_sql, data_info):
    """恢复表结构和数据到云端数据库"""
    try:
        cursor = conn.cursor()
        
        # 1. 删除现有表（如果存在）
        print(f"🔄 删除现有表 {table_name}...")
        cursor.execute(f"DROP TABLE IF EXISTS public.{table_name} CASCADE;")
        
        # 2. 创建表结构
        print(f"🔄 创建表结构 {table_name}...")
        cursor.execute(create_sql)
        
        # 3. 如果有数据，插入数据
        if data_info:
            copy_header, data_content = data_info
            print(f"🔄 插入数据到表 {table_name}...")
            
            # 解析COPY语句获取列名
            columns_start = copy_header.find("(") + 1
            columns_end = copy_header.find(")")
            columns = copy_header[columns_start:columns_end]
            
            # 使用COPY命令插入数据
            copy_sql = f"COPY public.{table_name} ({columns}) FROM STDIN;"
            cursor.copy_expert(copy_sql, data_content.split('\n'))
        
        # 4. 重新创建序列（如果需要）
        if table_name == "users":
            print("🔄 重新设置users表的序列...")
            cursor.execute("CREATE SEQUENCE IF NOT EXISTS public.users_id_seq AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;")
            cursor.execute("ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;")
            cursor.execute("ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);")
            cursor.execute("SELECT setval('public.users_id_seq', COALESCE((SELECT MAX(id) FROM public.users), 1), true);")
        
        elif table_name == "role_permissions":
            print("🔄 重新设置role_permissions表的序列...")
            cursor.execute("CREATE SEQUENCE IF NOT EXISTS public.role_permissions_id_seq AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;")
            cursor.execute("ALTER SEQUENCE public.role_permissions_id_seq OWNED BY public.role_permissions.id;")
            cursor.execute("ALTER TABLE ONLY public.role_permissions ALTER COLUMN id SET DEFAULT nextval('public.role_permissions_id_seq'::regclass);")
            cursor.execute("SELECT setval('public.role_permissions_id_seq', COALESCE((SELECT MAX(id) FROM public.role_permissions), 1), true);")
        
        print(f"✅ 表 {table_name} 恢复完成")
        return True
        
    except Exception as e:
        print(f"❌ 恢复表 {table_name} 失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始恢复6月13日15点18分云端备份数据到云端数据库")
    print("📅 备份时间: 2025-06-13 15:18:38")
    print("🎯 恢复范围: users表和role_permissions表")
    print("=" * 60)
    
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
        
        # 恢复users表
        print("\n📋 处理users表...")
        create_sql, data_info = extract_table_structure_and_data(BACKUP_FILE, "users")
        if create_sql:
            if not restore_table_to_cloud(conn, "users", create_sql, data_info):
                conn.rollback()
                return False
        
        # 恢复role_permissions表
        print("\n📋 处理role_permissions表...")
        create_sql, data_info = extract_table_structure_and_data(BACKUP_FILE, "role_permissions")
        if create_sql:
            if not restore_table_to_cloud(conn, "role_permissions", create_sql, data_info):
                conn.rollback()
                return False
        
        # 提交事务
        conn.commit()
        print("\n✅ 所有数据恢复完成！")
        
        # 验证恢复结果
        print("\n📊 验证恢复结果:")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM public.users;")
        user_count = cursor.fetchone()[0]
        print(f"   - users表记录数: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM public.role_permissions;")
        role_count = cursor.fetchone()[0]
        print(f"   - role_permissions表记录数: {role_count}")
        
        # 显示部分用户信息
        print("\n👥 用户信息预览:")
        cursor.execute("SELECT id, username, real_name, company_name, department, role FROM public.users ORDER BY id LIMIT 5;")
        users = cursor.fetchall()
        for user in users:
            print(f"   - ID:{user[0]} | {user[1]} | {user[2]} | {user[3]} | {user[4]} | {user[5]}")
        
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