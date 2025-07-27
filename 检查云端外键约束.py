#!/usr/bin/env python3
"""
检查云端数据库外键约束与本地的差异
用于诊断删除问题
"""

import os
import psycopg2
from urllib.parse import urlparse

def check_cloud_foreign_keys():
    """检查云端数据库的外键约束"""
    
    # 从环境变量获取云端数据库URL
    cloud_db_url = os.environ.get('DATABASE_URL')
    
    if not cloud_db_url:
        print("❌ 未找到云端数据库URL (DATABASE_URL环境变量)")
        return
    
    # 修复postgres://为postgresql://
    if cloud_db_url.startswith('postgres://'):
        cloud_db_url = cloud_db_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        print("=== 检查云端数据库外键约束 ===")
        conn = psycopg2.connect(cloud_db_url)
        cursor = conn.cursor()
        
        # 检查引用quotations表的外键约束
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY' 
                AND ccu.table_name='quotations'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        cloud_constraints = cursor.fetchall()
        print(f"云端引用quotations的外键约束 ({len(cloud_constraints)}个):")
        for constraint in cloud_constraints:
            print(f"  {constraint[0]}.{constraint[2]} -> {constraint[3]}.{constraint[4]} (DELETE: {constraint[5]})")
        
        # 检查quotations表的外键约束
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'quotations'
            ORDER BY kcu.column_name;
        """)
        
        quotation_constraints = cursor.fetchall()
        print(f"\nquotations表的外键约束 ({len(quotation_constraints)}个):")
        for constraint in quotation_constraints:
            print(f"  {constraint[1]}.{constraint[2]} -> {constraint[3]}.{constraint[4]} (DELETE: {constraint[5]})")
        
        # 检查特定表是否存在
        tables_to_check = ['quotation_details', 'settlement_orders', 'pricing_orders']
        print(f"\n检查关键表是否存在:")
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            exists = cursor.fetchone()[0]
            print(f"  {table}: {'✅ 存在' if exists else '❌ 不存在'}")
            
            if exists:
                # 检查是否有引用quotations的记录
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE quotation_id IS NOT NULL")
                    count = cursor.fetchone()[0]
                    print(f"    -> 有 {count} 条记录引用quotations")
                except Exception as e:
                    print(f"    -> 检查记录数时出错: {e}")
        
        cursor.close()
        conn.close()
        
        print("\n=== 可能的问题 ===")
        print("1. 如果云端缺少某些表，删除时不会遇到外键约束")
        print("2. 如果云端约束设置不同（如CASCADE），删除行为会不同")
        print("3. 如果云端数据分布不同，删除的报价单类型可能不同")
        
    except Exception as e:
        print(f"❌ 连接云端数据库失败: {e}")
        print("请确认DATABASE_URL环境变量设置正确")

def check_local_foreign_keys():
    """检查本地数据库的外键约束作为对比"""
    try:
        print("\n=== 检查本地数据库外键约束 (对比) ===")
        local_url = 'postgresql://nijie@localhost:5432/pma_local'
        conn = psycopg2.connect(local_url)
        cursor = conn.cursor()
        
        # 检查引用quotations表的外键约束
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY' 
                AND ccu.table_name='quotations'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        local_constraints = cursor.fetchall()
        print(f"本地引用quotations的外键约束 ({len(local_constraints)}个):")
        for constraint in local_constraints:
            print(f"  {constraint[0]}.{constraint[2]} -> {constraint[3]}.{constraint[4]} (DELETE: {constraint[5]})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 连接本地数据库失败: {e}")

if __name__ == "__main__":
    check_cloud_foreign_keys()
    check_local_foreign_keys()
    
    print("\n" + "="*60)
    print("🔧 修复建议:")
    print("1. 如果云端缺少表或约束，需要运行数据库迁移")
    print("2. 如果约束设置不同，需要同步约束规则")
    print("3. 部署包含完整外键处理的删除代码")
    print("="*60)