#!/usr/bin/env python3
"""
完整对比本地和云端数据库结构
分析迁移后的差异原因
"""

import psycopg2
from collections import defaultdict
import json

def get_database_structure(db_url, env_name):
    """获取数据库完整结构"""
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        structure = {
            'tables': {},
            'constraints': {},
            'indexes': {}
        }
        
        print(f"\n=== 分析 {env_name} 数据库结构 ===")
        
        # 1. 获取所有表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"总表数: {len(tables)}")
        
        # 2. 获取每个表的字段结构
        for table in tables:
            cursor.execute("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable, 
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table,))
            
            columns = []
            for col in cursor.fetchall():
                columns.append({
                    'name': col[0],
                    'type': col[1],
                    'nullable': col[2] == 'YES',
                    'default': col[3],
                    'max_length': col[4],
                    'precision': col[5],
                    'scale': col[6]
                })
            
            structure['tables'][table] = columns
        
        # 3. 获取外键约束
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        constraints = []
        for row in cursor.fetchall():
            constraints.append({
                'table': row[0],
                'name': row[1],
                'column': row[2],
                'ref_table': row[3],
                'ref_column': row[4],
                'delete_rule': row[5],
                'update_rule': row[6]
            })
        structure['constraints'] = constraints
        
        # 4. 获取索引
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        
        indexes = []
        for row in cursor.fetchall():
            indexes.append({
                'schema': row[0],
                'table': row[1],
                'name': row[2],
                'definition': row[3]
            })
        structure['indexes'] = indexes
        
        cursor.close()
        conn.close()
        
        return structure
        
    except Exception as e:
        print(f"❌ 获取 {env_name} 数据库结构失败: {e}")
        return None

def compare_structures(local_struct, cloud_struct):
    """对比数据库结构差异"""
    print("\n" + "="*80)
    print("📊 数据库结构对比分析")
    print("="*80)
    
    # 1. 表级别对比
    print("\n1️⃣ 表结构对比:")
    local_tables = set(local_struct['tables'].keys())
    cloud_tables = set(cloud_struct['tables'].keys())
    
    missing_in_cloud = local_tables - cloud_tables
    missing_in_local = cloud_tables - local_tables
    common_tables = local_tables & cloud_tables
    
    print(f"   本地表数: {len(local_tables)}")
    print(f"   云端表数: {len(cloud_tables)}")
    print(f"   共同表数: {len(common_tables)}")
    
    if missing_in_cloud:
        print(f"   ❌ 云端缺失表 ({len(missing_in_cloud)}个): {sorted(missing_in_cloud)}")
    
    if missing_in_local:
        print(f"   ⚠️ 本地缺失表 ({len(missing_in_local)}个): {sorted(missing_in_local)}")
    
    # 2. 字段级别对比
    print("\n2️⃣ 字段结构差异:")
    field_differences = []
    
    for table in sorted(common_tables):
        local_cols = {col['name']: col for col in local_struct['tables'][table]}
        cloud_cols = {col['name']: col for col in cloud_struct['tables'][table]}
        
        local_field_names = set(local_cols.keys())
        cloud_field_names = set(cloud_cols.keys())
        
        missing_in_cloud_fields = local_field_names - cloud_field_names
        missing_in_local_fields = cloud_field_names - local_field_names
        
        if missing_in_cloud_fields or missing_in_local_fields:
            print(f"\n   📋 表 {table}:")
            if missing_in_cloud_fields:
                print(f"      ❌ 云端缺失字段: {sorted(missing_in_cloud_fields)}")
                for field in missing_in_cloud_fields:
                    local_field = local_cols[field]
                    field_differences.append({
                        'table': table,
                        'field': field,
                        'issue': 'missing_in_cloud',
                        'local_type': local_field['type'],
                        'local_default': local_field['default']
                    })
            
            if missing_in_local_fields:
                print(f"      ⚠️ 本地缺失字段: {sorted(missing_in_local_fields)}")
        
        # 检查字段类型差异
        common_fields = local_field_names & cloud_field_names
        for field in common_fields:
            local_field = local_cols[field]
            cloud_field = cloud_cols[field]
            
            type_diff = local_field['type'] != cloud_field['type']
            nullable_diff = local_field['nullable'] != cloud_field['nullable']
            default_diff = local_field['default'] != cloud_field['default']
            
            if type_diff or nullable_diff or default_diff:
                print(f"      🔄 字段差异 {field}:")
                if type_diff:
                    print(f"         类型: 本地({local_field['type']}) vs 云端({cloud_field['type']})")
                if nullable_diff:
                    print(f"         空值: 本地({local_field['nullable']}) vs 云端({cloud_field['nullable']})")
                if default_diff:
                    print(f"         默认值: 本地({local_field['default']}) vs 云端({cloud_field['default']})")
    
    # 3. 外键约束对比
    print("\n3️⃣ 外键约束对比:")
    local_fks = {f"{fk['table']}.{fk['column']}": fk for fk in local_struct['constraints']}
    cloud_fks = {f"{fk['table']}.{fk['column']}": fk for fk in cloud_struct['constraints']}
    
    local_fk_keys = set(local_fks.keys())
    cloud_fk_keys = set(cloud_fks.keys())
    
    missing_fks_cloud = local_fk_keys - cloud_fk_keys
    missing_fks_local = cloud_fk_keys - local_fk_keys
    
    print(f"   本地外键数: {len(local_fks)}")
    print(f"   云端外键数: {len(cloud_fks)}")
    
    if missing_fks_cloud:
        print(f"   ❌ 云端缺失外键约束 ({len(missing_fks_cloud)}个):")
        for fk_key in sorted(missing_fks_cloud):
            fk = local_fks[fk_key]
            print(f"      {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}")
    
    if missing_fks_local:
        print(f"   ⚠️ 本地缺失外键约束 ({len(missing_fks_local)}个):")
        for fk_key in sorted(missing_fks_local):
            fk = cloud_fks[fk_key]
            print(f"      {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}")
    
    # 4. 索引对比
    print("\n4️⃣ 索引对比:")
    local_indexes = {idx['name']: idx for idx in local_struct['indexes']}
    cloud_indexes = {idx['name']: idx for idx in cloud_struct['indexes']}
    
    local_idx_names = set(local_indexes.keys())
    cloud_idx_names = set(cloud_indexes.keys())
    
    missing_idx_cloud = local_idx_names - cloud_idx_names
    missing_idx_local = cloud_idx_names - local_idx_names
    
    print(f"   本地索引数: {len(local_indexes)}")
    print(f"   云端索引数: {len(cloud_indexes)}")
    
    if missing_idx_cloud:
        print(f"   ❌ 云端缺失索引 ({len(missing_idx_cloud)}个): {sorted(missing_idx_cloud)}")
    
    if missing_idx_local:
        print(f"   ⚠️ 本地缺失索引 ({len(missing_idx_local)}个): {sorted(missing_idx_local)}")
    
    return field_differences

def analyze_migration_issues(field_differences):
    """分析迁移问题原因"""
    print("\n" + "="*80)
    print("🔍 迁移问题分析")
    print("="*80)
    
    print("\n📋 字段缺失汇总:")
    tables_with_issues = defaultdict(list)
    for diff in field_differences:
        if diff['issue'] == 'missing_in_cloud':
            tables_with_issues[diff['table']].append(diff['field'])
    
    for table, fields in tables_with_issues.items():
        print(f"   {table}: {fields}")
    
    print(f"\n📊 统计:")
    print(f"   受影响表数: {len(tables_with_issues)}")
    print(f"   缺失字段总数: {len(field_differences)}")
    
    print(f"\n🎯 可能原因:")
    print(f"   1. 迁移脚本执行不完整")
    print(f"   2. 某些迁移文件未被执行")
    print(f"   3. 迁移过程中出现错误但未中断")
    print(f"   4. 手动修改导致的差异")
    print(f"   5. 版本分支差异")

if __name__ == "__main__":
    # 数据库连接配置
    local_url = 'postgresql://nijie@localhost:5432/pma_local'
    cloud_url = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'
    
    # 获取结构
    print("开始数据库结构对比...")
    local_struct = get_database_structure(local_url, "本地")
    cloud_struct = get_database_structure(cloud_url, "云端")
    
    if local_struct and cloud_struct:
        field_differences = compare_structures(local_struct, cloud_struct)
        analyze_migration_issues(field_differences)
        
        # 保存详细对比结果
        comparison_result = {
            'local': local_struct,
            'cloud': cloud_struct,
            'differences': field_differences,
            'timestamp': '2025-07-27 10:20:00'
        }
        
        with open('数据库结构对比详情.json', 'w', encoding='utf-8') as f:
            json.dump(comparison_result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细对比结果已保存到: 数据库结构对比详情.json")
    
    print(f"\n" + "="*80)
    print("分析完成")
    print("="*80)