#!/usr/bin/env python3
"""
数据库结构同步验证脚本
用于验证本地和云端数据库结构是否一致
"""

import os
import psycopg2

# 数据库连接信息
LOCAL_URL = os.getenv('DATABASE_URL', 'postgresql://nijie@localhost:5432/pma_local')
CLOUD_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

def get_table_structure(conn_url, db_name):
    """获取数据库的表结构"""
    try:
        conn = psycopg2.connect(conn_url)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute('''
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        ''')
        tables = [row[0] for row in cursor.fetchall()]
        
        structure = {}
        
        for table in tables:
            # 获取表的字段信息
            cursor.execute('''
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable, 
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position;
            ''', (table,))
            
            columns = cursor.fetchall()
            structure[table] = {}
            
            for col in columns:
                col_name = col[0]
                structure[table][col_name] = {
                    'data_type': col[1],
                    'is_nullable': col[2],
                    'column_default': col[3],
                    'character_maximum_length': col[4]
                }
        
        cursor.close()
        conn.close()
        return structure, tables
        
    except Exception as e:
        print(f'获取{db_name}数据库结构失败: {e}')
        return {}, []

def verify_api_endpoints():
    """验证API端点是否存在"""
    print('\n=== API端点验证 ===')
    
    # 检查文件是否存在相关API
    try:
        with open('app/views/customer.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if '/api/available_accounts' in content:
                print('✅ 客户账户API端点已添加')
            else:
                print('❌ 客户账户API端点缺失')
    except Exception as e:
        print(f'❌ 无法检查customer.py文件: {e}')
    
    # 检查权限API
    try:
        with open('app/views/user.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'manage-permissions' in content and 'permission_level' in content:
                print('✅ 权限保存API端点正常')
            else:
                print('❌ 权限保存API端点异常')
    except Exception as e:
        print(f'❌ 无法检查user.py文件: {e}')

def main():
    print('=== 数据库结构同步验证 ===\n')
    
    # 获取本地和云端数据库结构
    print('1. 获取本地数据库结构...')
    local_structure, local_tables = get_table_structure(LOCAL_URL, '本地')
    
    print('2. 获取云端数据库结构...')
    cloud_structure, cloud_tables = get_table_structure(CLOUD_URL, '云端')
    
    if not local_structure or not cloud_structure:
        print('❌ 无法获取数据库结构，停止验证')
        return
    
    print(f'本地数据库表数量: {len(local_tables)}')
    print(f'云端数据库表数量: {len(cloud_tables)}')
    
    # 对比表列表
    local_set = set(local_tables)
    cloud_set = set(cloud_tables)
    missing_in_cloud = local_set - cloud_set
    missing_in_local = cloud_set - local_set
    common_tables = local_set & cloud_set
    
    print(f'\n=== 表对比结果 ===')
    if missing_in_cloud:
        print(f'❌ 云端缺少的表: {sorted(missing_in_cloud)}')
    if missing_in_local:
        print(f'❌ 本地缺少的表: {sorted(missing_in_local)}')
    if not missing_in_cloud and not missing_in_local:
        print('✅ 表列表完全一致')
    
    # 检查关键表的结构
    print(f'\n=== 关键表结构验证 ===')
    key_tables = ['role_permissions', 'approval_step', 'products', 'quotations', 'projects']
    
    differences_found = False
    for table in key_tables:
        if table in common_tables:
            local_cols = local_structure[table]
            cloud_cols = cloud_structure[table]
            
            # 检查字段差异
            local_col_names = set(local_cols.keys())
            cloud_col_names = set(cloud_cols.keys())
            
            missing_in_cloud_cols = local_col_names - cloud_col_names
            missing_in_local_cols = cloud_col_names - local_col_names
            
            if missing_in_cloud_cols or missing_in_local_cols:
                differences_found = True
                print(f'❌ {table} 表存在字段差异')
                if missing_in_cloud_cols:
                    print(f'   云端缺少字段: {sorted(missing_in_cloud_cols)}')
                if missing_in_local_cols:
                    print(f'   本地缺少字段: {sorted(missing_in_local_cols)}')
            else:
                print(f'✅ {table} 表结构一致')
    
    if not differences_found:
        print('\n🎉 所有关键表结构完全一致！')
    
    # 验证API端点
    verify_api_endpoints()
    
    print('\n=== 验证完成 ===')
    if not differences_found:
        print('✅ 数据库结构同步成功')
        print('✅ 系统应该能够正常工作')
    else:
        print('⚠️  仍存在一些结构差异，请检查')

if __name__ == '__main__':
    main()
