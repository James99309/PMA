#!/usr/bin/env python3
"""
比较本地和云端OVS数据库差异
根据CLAUDE.md规范执行数据库结构对比
"""

import psycopg2
import os
import logging
from datetime import datetime
import json

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_info(connection_string, db_name):
    """获取数据库结构信息"""
    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        
        # 获取所有表信息
        cur.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = {row[0]: row[1] for row in cur.fetchall()}
        
        # 获取所有列信息
        columns = {}
        for table_name in tables.keys():
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default,
                       character_maximum_length, numeric_precision, numeric_scale
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns[table_name] = cur.fetchall()
        
        # 获取主键信息
        primary_keys = {}
        for table_name in tables.keys():
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'public' 
                  AND tc.table_name = %s 
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position;
            """, (table_name,))
            pk_columns = [row[0] for row in cur.fetchall()]
            if pk_columns:
                primary_keys[table_name] = pk_columns
        
        # 获取外键信息
        foreign_keys = {}
        cur.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='public'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        for row in cur.fetchall():
            table_name, column_name, foreign_table, foreign_column, constraint_name = row
            if table_name not in foreign_keys:
                foreign_keys[table_name] = []
            foreign_keys[table_name].append({
                'column': column_name,
                'references_table': foreign_table,
                'references_column': foreign_column,
                'constraint_name': constraint_name
            })
        
        # 获取索引信息
        indexes = {}
        cur.execute("""
            SELECT 
                schemaname, tablename, indexname, indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        for row in cur.fetchall():
            schema, table_name, index_name, index_def = row
            if table_name not in indexes:
                indexes[table_name] = []
            indexes[table_name].append({
                'name': index_name,
                'definition': index_def
            })
        
        # 获取约束信息
        constraints = {}
        cur.execute("""
            SELECT 
                tc.table_name, 
                tc.constraint_name, 
                tc.constraint_type,
                cc.check_clause
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.check_constraints cc 
                ON tc.constraint_name = cc.constraint_name
            WHERE tc.table_schema = 'public' 
                AND tc.constraint_type IN ('CHECK', 'UNIQUE')
            ORDER BY tc.table_name, tc.constraint_name;
        """)
        for row in cur.fetchall():
            table_name, constraint_name, constraint_type, check_clause = row
            if table_name not in constraints:
                constraints[table_name] = []
            constraints[table_name].append({
                'name': constraint_name,
                'type': constraint_type,
                'definition': check_clause
            })
        
        cur.close()
        conn.close()
        
        return {
            'database_name': db_name,
            'tables': tables,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'indexes': indexes,
            'constraints': constraints
        }
        
    except Exception as e:
        logger.error(f"获取数据库 {db_name} 信息失败: {e}")
        return None

def compare_databases():
    """比较本地和云端OVS数据库"""
    logger.info("🔍 开始比较本地和云端OVS数据库...")
    
    # 数据库连接信息
    local_db_url = os.getenv('DATABASE_URL') or "postgresql://nijie@localhost:5432/pma_local"
    ovs_db_url = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
    
    logger.info(f"本地数据库: {local_db_url.split('@')[1] if '@' in local_db_url else local_db_url}")
    logger.info(f"OVS云端数据库: {ovs_db_url.split('@')[1].split('?')[0] if '@' in ovs_db_url else ovs_db_url}")
    
    logger.info("📊 获取本地数据库结构...")
    local_info = get_database_info(local_db_url, "本地数据库")
    
    logger.info("☁️  获取OVS云端数据库结构...")  
    ovs_info = get_database_info(ovs_db_url, "OVS云端数据库")
    
    if not local_info or not ovs_info:
        logger.error("❌ 无法获取数据库信息")
        return
    
    # 比较结果
    comparison_result = {
        'timestamp': datetime.now().isoformat(),
        'local_tables': len(local_info['tables']),
        'ovs_tables': len(ovs_info['tables']),
        'differences': {
            'tables_only_in_local': [],
            'tables_only_in_ovs': [],
            'column_differences': {},
            'primary_key_differences': {},
            'foreign_key_differences': {},
            'constraint_differences': {},
            'index_differences': {}
        }
    }
    
    # 比较表
    local_tables = set(local_info['tables'].keys())
    ovs_tables = set(ovs_info['tables'].keys())
    
    comparison_result['differences']['tables_only_in_local'] = list(local_tables - ovs_tables)
    comparison_result['differences']['tables_only_in_ovs'] = list(ovs_tables - local_tables)
    
    # 比较共同表的结构
    common_tables = local_tables & ovs_tables
    
    for table_name in common_tables:
        # 比较列结构
        local_cols = {col[0]: col[1:] for col in local_info['columns'][table_name]}
        ovs_cols = {col[0]: col[1:] for col in ovs_info['columns'][table_name]}
        
        local_col_names = set(local_cols.keys())
        ovs_col_names = set(ovs_cols.keys())
        
        if local_col_names != ovs_col_names or local_cols != ovs_cols:
            comparison_result['differences']['column_differences'][table_name] = {
                'columns_only_in_local': list(local_col_names - ovs_col_names),
                'columns_only_in_ovs': list(ovs_col_names - local_col_names),
                'different_definitions': {}
            }
            
            # 检查共同列的定义差异
            common_cols = local_col_names & ovs_col_names
            for col_name in common_cols:
                if local_cols[col_name] != ovs_cols[col_name]:
                    comparison_result['differences']['column_differences'][table_name]['different_definitions'][col_name] = {
                        'local': local_cols[col_name],
                        'ovs': ovs_cols[col_name]
                    }
        
        # 比较主键
        local_pk = local_info['primary_keys'].get(table_name, [])
        ovs_pk = ovs_info['primary_keys'].get(table_name, [])
        if local_pk != ovs_pk:
            comparison_result['differences']['primary_key_differences'][table_name] = {
                'local': local_pk,
                'ovs': ovs_pk
            }
        
        # 比较外键
        local_fk = local_info['foreign_keys'].get(table_name, [])
        ovs_fk = ovs_info['foreign_keys'].get(table_name, [])
        if local_fk != ovs_fk:
            comparison_result['differences']['foreign_key_differences'][table_name] = {
                'local': local_fk,
                'ovs': ovs_fk
            }
    
    # 输出比较结果
    logger.info("📋 数据库比较结果:")
    logger.info(f"本地数据库表数量: {len(local_tables)}")
    logger.info(f"OVS云端数据库表数量: {len(ovs_tables)}")
    
    if comparison_result['differences']['tables_only_in_local']:
        logger.warning(f"⚠️  仅存在于本地的表 ({len(comparison_result['differences']['tables_only_in_local'])}): {comparison_result['differences']['tables_only_in_local']}")
    
    if comparison_result['differences']['tables_only_in_ovs']:
        logger.warning(f"⚠️  仅存在于OVS云端的表 ({len(comparison_result['differences']['tables_only_in_ovs'])}): {comparison_result['differences']['tables_only_in_ovs']}")
    
    diff_count = len(comparison_result['differences']['column_differences'])
    if diff_count > 0:
        logger.warning(f"⚠️  有 {diff_count} 个表存在列结构差异")
        for table_name, diffs in comparison_result['differences']['column_differences'].items():
            logger.warning(f"  📋 表 {table_name}:")
            if diffs['columns_only_in_local']:
                logger.warning(f"    - 仅本地有: {diffs['columns_only_in_local']}")
            if diffs['columns_only_in_ovs']:
                logger.warning(f"    - 仅OVS云端有: {diffs['columns_only_in_ovs']}")
            if diffs['different_definitions']:
                logger.warning(f"    - 定义不同的列: {list(diffs['different_definitions'].keys())}")
    
    pk_diff_count = len(comparison_result['differences']['primary_key_differences'])
    if pk_diff_count > 0:
        logger.warning(f"⚠️  有 {pk_diff_count} 个表存在主键差异")
    
    fk_diff_count = len(comparison_result['differences']['foreign_key_differences'])
    if fk_diff_count > 0:
        logger.warning(f"⚠️  有 {fk_diff_count} 个表存在外键差异")
    
    # 保存比较结果
    result_file = f"ovs_database_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 详细比较结果已保存到: {result_file}")
    
    # 判断是否需要迁移
    has_differences = (
        comparison_result['differences']['tables_only_in_local'] or
        comparison_result['differences']['column_differences'] or
        comparison_result['differences']['primary_key_differences'] or
        comparison_result['differences']['foreign_key_differences']
    )
    
    if has_differences:
        logger.warning("⚠️  检测到数据库结构差异，建议执行OVS迁移同步")
        return True
    else:
        logger.info("✅ 本地和OVS云端数据库结构一致，无需迁移")
        return False

if __name__ == "__main__":
    needs_migration = compare_databases()
    if needs_migration:
        print("\n🔄 执行建议: 运行OVS标准迁移工具进行同步")
        print("命令: python3 standard_migration_upgrade_ovs.py")