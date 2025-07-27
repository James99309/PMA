#!/usr/bin/env python3
"""
详尽的云端和本地数据库差异分析
包括表、字段、约束、索引、序列、视图、函数、触发器等所有可能影响代码运行的差异
"""

import psycopg2
from collections import defaultdict
import json
from datetime import datetime

class DatabaseAnalyzer:
    def __init__(self, db_url, env_name):
        self.db_url = db_url
        self.env_name = env_name
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"❌ 连接{self.env_name}数据库失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def get_complete_schema(self):
        """获取完整的数据库模式信息"""
        schema = {
            'basic_info': self._get_basic_info(),
            'tables': self._get_tables_info(),
            'foreign_keys': self._get_foreign_keys(),
            'check_constraints': self._get_check_constraints(),
            'unique_constraints': self._get_unique_constraints(),
            'primary_keys': self._get_primary_keys(),
            'indexes': self._get_indexes(),
            'sequences': self._get_sequences(),
            'views': self._get_views(),
            'functions': self._get_functions(),
            'triggers': self._get_triggers(),
            'enums': self._get_enums(),
            'collations': self._get_collations()
        }
        return schema
    
    def _get_basic_info(self):
        """获取数据库基本信息"""
        try:
            self.cursor.execute("SELECT version()")
            version = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT current_database()")
            database = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT current_user")
            user = self.cursor.fetchone()[0]
            
            return {
                'version': version,
                'database': database,
                'user': user
            }
        except Exception as e:
            print(f"⚠️ 获取{self.env_name}基本信息失败: {e}")
            return {}
    
    def _get_tables_info(self):
        """获取详细的表信息"""
        tables = {}
        
        # 获取所有表
        self.cursor.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        all_tables = self.cursor.fetchall()
        
        for table_name, table_type in all_tables:
            # 获取表的详细字段信息
            self.cursor.execute("""
                SELECT 
                    column_name,
                    ordinal_position,
                    column_default,
                    is_nullable,
                    data_type,
                    character_maximum_length,
                    character_octet_length,
                    numeric_precision,
                    numeric_scale,
                    datetime_precision,
                    character_set_name,
                    collation_name,
                    domain_name,
                    udt_name,
                    is_identity,
                    identity_generation,
                    is_generated,
                    generation_expression
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = []
            for col in self.cursor.fetchall():
                columns.append({
                    'name': col[0],
                    'position': col[1],
                    'default': col[2],
                    'nullable': col[3] == 'YES',
                    'data_type': col[4],
                    'max_length': col[5],
                    'octet_length': col[6],
                    'numeric_precision': col[7],
                    'numeric_scale': col[8],
                    'datetime_precision': col[9],
                    'charset': col[10],
                    'collation': col[11],
                    'domain': col[12],
                    'udt_name': col[13],
                    'is_identity': col[14] == 'YES',
                    'identity_generation': col[15],
                    'is_generated': col[16] == 'YES',
                    'generation_expression': col[17]
                })
            
            # 获取表的统计信息
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = self.cursor.fetchone()[0]
            except:
                row_count = None
            
            tables[table_name] = {
                'type': table_type,
                'columns': columns,
                'row_count': row_count
            }
        
        return tables
    
    def _get_foreign_keys(self):
        """获取外键约束"""
        self.cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule,
                rc.match_option
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name
        """)
        
        fks = []
        for row in self.cursor.fetchall():
            fks.append({
                'name': row[0],
                'table': row[1],
                'column': row[2],
                'ref_table': row[3],
                'ref_column': row[4],
                'delete_rule': row[5],
                'update_rule': row[6],
                'match_option': row[7]
            })
        return fks
    
    def _get_check_constraints(self):
        """获取检查约束"""
        self.cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                cc.check_clause
            FROM information_schema.table_constraints tc
            JOIN information_schema.check_constraints cc
                ON tc.constraint_name = cc.constraint_name
            WHERE tc.constraint_type = 'CHECK'
                AND tc.table_schema = 'public'
            ORDER BY tc.table_name, tc.constraint_name
        """)
        
        checks = []
        for row in self.cursor.fetchall():
            checks.append({
                'name': row[0],
                'table': row[1],
                'clause': row[2]
            })
        return checks
    
    def _get_unique_constraints(self):
        """获取唯一约束"""
        self.cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'UNIQUE'
                AND tc.table_schema = 'public'
            GROUP BY tc.constraint_name, tc.table_name
            ORDER BY tc.table_name, tc.constraint_name
        """)
        
        uniques = []
        for row in self.cursor.fetchall():
            uniques.append({
                'name': row[0],
                'table': row[1],
                'columns': row[2]
            })
        return uniques
    
    def _get_primary_keys(self):
        """获取主键约束"""
        self.cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
            GROUP BY tc.constraint_name, tc.table_name
            ORDER BY tc.table_name
        """)
        
        pks = []
        for row in self.cursor.fetchall():
            pks.append({
                'name': row[0],
                'table': row[1],
                'columns': row[2]
            })
        return pks
    
    def _get_indexes(self):
        """获取索引信息"""
        self.cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        indexes = []
        for row in self.cursor.fetchall():
            indexes.append({
                'schema': row[0],
                'table': row[1],
                'name': row[2],
                'definition': row[3]
            })
        return indexes
    
    def _get_sequences(self):
        """获取序列信息"""
        self.cursor.execute("""
            SELECT 
                sequence_name,
                data_type,
                start_value,
                minimum_value,
                maximum_value,
                increment,
                cycle_option
            FROM information_schema.sequences
            WHERE sequence_schema = 'public'
            ORDER BY sequence_name
        """)
        
        sequences = []
        for row in self.cursor.fetchall():
            sequences.append({
                'name': row[0],
                'data_type': row[1],
                'start_value': row[2],
                'min_value': row[3],
                'max_value': row[4],
                'increment': row[5],
                'cycle': row[6] == 'YES'
            })
        return sequences
    
    def _get_views(self):
        """获取视图信息"""
        self.cursor.execute("""
            SELECT 
                table_name,
                view_definition
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        views = []
        for row in self.cursor.fetchall():
            views.append({
                'name': row[0],
                'definition': row[1]
            })
        return views
    
    def _get_functions(self):
        """获取函数信息"""
        try:
            self.cursor.execute("""
                SELECT 
                    routine_name,
                    routine_type,
                    data_type,
                    routine_definition
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                ORDER BY routine_name
            """)
            
            functions = []
            for row in self.cursor.fetchall():
                functions.append({
                    'name': row[0],
                    'type': row[1],
                    'return_type': row[2],
                    'definition': row[3]
                })
            return functions
        except Exception as e:
            print(f"⚠️ 获取{self.env_name}函数信息失败: {e}")
            return []
    
    def _get_triggers(self):
        """获取触发器信息"""
        try:
            self.cursor.execute("""
                SELECT 
                    trigger_name,
                    event_manipulation,
                    event_object_table,
                    action_timing,
                    action_statement
                FROM information_schema.triggers
                WHERE trigger_schema = 'public'
                ORDER BY event_object_table, trigger_name
            """)
            
            triggers = []
            for row in self.cursor.fetchall():
                triggers.append({
                    'name': row[0],
                    'event': row[1],
                    'table': row[2],
                    'timing': row[3],
                    'action': row[4]
                })
            return triggers
        except Exception as e:
            print(f"⚠️ 获取{self.env_name}触发器信息失败: {e}")
            return []
    
    def _get_enums(self):
        """获取枚举类型"""
        try:
            self.cursor.execute("""
                SELECT 
                    t.typname,
                    string_agg(e.enumlabel, ',' ORDER BY e.enumsortorder) as enum_values
                FROM pg_type t 
                JOIN pg_enum e ON t.oid = e.enumtypid  
                JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
                WHERE n.nspname = 'public'
                GROUP BY t.typname
                ORDER BY t.typname
            """)
            
            enums = []
            for row in self.cursor.fetchall():
                enums.append({
                    'name': row[0],
                    'values': row[1].split(',') if row[1] else []
                })
            return enums
        except Exception as e:
            print(f"⚠️ 获取{self.env_name}枚举类型失败: {e}")
            return []
    
    def _get_collations(self):
        """获取排序规则"""
        try:
            self.cursor.execute("""
                SELECT 
                    collation_name,
                    character_set_name
                FROM information_schema.collations
                WHERE collation_schema = 'public'
                ORDER BY collation_name
            """)
            
            collations = []
            for row in self.cursor.fetchall():
                collations.append({
                    'name': row[0],
                    'charset': row[1]
                })
            return collations
        except Exception as e:
            print(f"⚠️ 获取{self.env_name}排序规则失败: {e}")
            return []

class DatabaseComparator:
    def __init__(self, local_schema, cloud_schema):
        self.local = local_schema
        self.cloud = cloud_schema
        self.differences = {
            'critical': [],  # 可能导致代码运行错误的差异
            'important': [], # 重要但不致命的差异
            'minor': []      # 次要差异
        }
    
    def compare_all(self):
        """执行全面对比"""
        print("\n" + "="*100)
        print("🔍 详尽数据库差异分析")
        print("="*100)
        
        self._compare_basic_info()
        self._compare_tables()
        self._compare_foreign_keys()
        self._compare_constraints()
        self._compare_indexes()
        self._compare_sequences()
        self._compare_views()
        self._compare_functions()
        self._compare_triggers()
        self._compare_enums()
        
        self._categorize_and_report()
    
    def _compare_basic_info(self):
        """对比基本信息"""
        print("\n1️⃣ 数据库基本信息对比:")
        
        local_info = self.local.get('basic_info', {})
        cloud_info = self.cloud.get('basic_info', {})
        
        print(f"   本地数据库: {local_info.get('database', 'N/A')}")
        print(f"   云端数据库: {cloud_info.get('database', 'N/A')}")
        print(f"   本地用户: {local_info.get('user', 'N/A')}")
        print(f"   云端用户: {cloud_info.get('user', 'N/A')}")
        
        # 版本对比
        local_version = local_info.get('version', '')
        cloud_version = cloud_info.get('version', '')
        
        if local_version != cloud_version:
            self.differences['important'].append({
                'type': 'version_difference',
                'description': f"PostgreSQL版本不同: 本地({local_version[:20]}...) vs 云端({cloud_version[:20]}...)",
                'impact': 'medium'
            })
    
    def _compare_tables(self):
        """对比表结构"""
        print("\n2️⃣ 表结构对比:")
        
        local_tables = set(self.local.get('tables', {}).keys())
        cloud_tables = set(self.cloud.get('tables', {}).keys())
        
        # 表级别差异
        missing_in_cloud = local_tables - cloud_tables
        missing_in_local = cloud_tables - local_tables
        common_tables = local_tables & cloud_tables
        
        print(f"   本地表数: {len(local_tables)}")
        print(f"   云端表数: {len(cloud_tables)}")
        print(f"   共同表数: {len(common_tables)}")
        
        if missing_in_cloud:
            print(f"   ❌ 云端缺失表: {sorted(missing_in_cloud)}")
            for table in missing_in_cloud:
                self.differences['critical'].append({
                    'type': 'missing_table',
                    'table': table,
                    'description': f"云端缺失表: {table}",
                    'impact': 'high'
                })
        
        if missing_in_local:
            print(f"   ⚠️ 本地缺失表: {sorted(missing_in_local)}")
            for table in missing_in_local:
                self.differences['minor'].append({
                    'type': 'extra_table',
                    'table': table,
                    'description': f"本地缺失表: {table}",
                    'impact': 'low'
                })
        
        # 字段级别对比
        self._compare_table_columns(common_tables)
    
    def _compare_table_columns(self, common_tables):
        """对比表字段"""
        print("\n   📋 字段级别差异:")
        
        local_tables = self.local.get('tables', {})
        cloud_tables = self.cloud.get('tables', {})
        
        for table in sorted(common_tables):
            local_cols = {col['name']: col for col in local_tables[table]['columns']}
            cloud_cols = {col['name']: col for col in cloud_tables[table]['columns']}
            
            local_col_names = set(local_cols.keys())
            cloud_col_names = set(cloud_cols.keys())
            
            missing_in_cloud = local_col_names - cloud_col_names
            missing_in_local = cloud_col_names - local_col_names
            
            if missing_in_cloud or missing_in_local:
                print(f"\n      📋 表 {table}:")
                
                if missing_in_cloud:
                    print(f"         ❌ 云端缺失字段: {sorted(missing_in_cloud)}")
                    for field in missing_in_cloud:
                        local_col = local_cols[field]
                        impact = 'high' if not local_col['nullable'] and not local_col['default'] else 'medium'
                        self.differences['critical'].append({
                            'type': 'missing_column',
                            'table': table,
                            'column': field,
                            'description': f"云端缺失字段 {table}.{field} ({local_col['data_type']})",
                            'local_definition': local_col,
                            'impact': impact
                        })
                
                if missing_in_local:
                    print(f"         ⚠️ 本地缺失字段: {sorted(missing_in_local)}")
                    for field in missing_in_local:
                        cloud_col = cloud_cols[field]
                        self.differences['minor'].append({
                            'type': 'extra_column',
                            'table': table,
                            'column': field,
                            'description': f"本地缺失字段 {table}.{field} ({cloud_col['data_type']})",
                            'cloud_definition': cloud_col,
                            'impact': 'low'
                        })
            
            # 比较共同字段的属性差异
            common_cols = local_col_names & cloud_col_names
            for col_name in common_cols:
                local_col = local_cols[col_name]
                cloud_col = cloud_cols[col_name]
                
                differences = []
                
                # 数据类型差异
                if local_col['data_type'] != cloud_col['data_type']:
                    differences.append(f"类型: {local_col['data_type']} vs {cloud_col['data_type']}")
                
                # 可空性差异
                if local_col['nullable'] != cloud_col['nullable']:
                    differences.append(f"可空: {local_col['nullable']} vs {cloud_col['nullable']}")
                
                # 默认值差异
                if local_col['default'] != cloud_col['default']:
                    differences.append(f"默认值: {local_col['default']} vs {cloud_col['default']}")
                
                # 长度差异
                if local_col['max_length'] != cloud_col['max_length']:
                    differences.append(f"最大长度: {local_col['max_length']} vs {cloud_col['max_length']}")
                
                # 精度差异
                if local_col['numeric_precision'] != cloud_col['numeric_precision']:
                    differences.append(f"数值精度: {local_col['numeric_precision']} vs {cloud_col['numeric_precision']}")
                
                if differences:
                    print(f"         🔄 字段差异 {col_name}: {'; '.join(differences)}")
                    
                    impact = 'high' if 'nullable' in differences[0] or 'type' in differences[0] else 'medium'
                    self.differences['important'].append({
                        'type': 'column_difference',
                        'table': table,
                        'column': col_name,
                        'description': f"字段差异 {table}.{col_name}: {'; '.join(differences)}",
                        'local_definition': local_col,
                        'cloud_definition': cloud_col,
                        'impact': impact
                    })
    
    def _compare_foreign_keys(self):
        """对比外键约束"""
        print("\n3️⃣ 外键约束对比:")
        
        local_fks = {f"{fk['table']}.{fk['column']}": fk for fk in self.local.get('foreign_keys', [])}
        cloud_fks = {f"{fk['table']}.{fk['column']}": fk for fk in self.cloud.get('foreign_keys', [])}
        
        local_fk_keys = set(local_fks.keys())
        cloud_fk_keys = set(cloud_fks.keys())
        
        print(f"   本地外键数: {len(local_fks)}")
        print(f"   云端外键数: {len(cloud_fks)}")
        
        missing_in_cloud = local_fk_keys - cloud_fk_keys
        missing_in_local = cloud_fk_keys - local_fk_keys
        
        if missing_in_cloud:
            print(f"   ❌ 云端缺失外键约束:")
            for fk_key in sorted(missing_in_cloud):
                fk = local_fks[fk_key]
                print(f"      {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}")
                self.differences['critical'].append({
                    'type': 'missing_foreign_key',
                    'description': f"云端缺失外键: {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}",
                    'constraint': fk,
                    'impact': 'high'
                })
        
        if missing_in_local:
            print(f"   ⚠️ 本地缺失外键约束:")
            for fk_key in sorted(missing_in_local):
                fk = cloud_fks[fk_key]
                print(f"      {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}")
        
        # 检查外键规则差异
        common_fks = local_fk_keys & cloud_fk_keys
        for fk_key in common_fks:
            local_fk = local_fks[fk_key]
            cloud_fk = cloud_fks[fk_key]
            
            if (local_fk['delete_rule'] != cloud_fk['delete_rule'] or 
                local_fk['update_rule'] != cloud_fk['update_rule']):
                
                print(f"   🔄 外键规则差异 {fk_key}:")
                print(f"      DELETE: {local_fk['delete_rule']} vs {cloud_fk['delete_rule']}")
                print(f"      UPDATE: {local_fk['update_rule']} vs {cloud_fk['update_rule']}")
                
                self.differences['important'].append({
                    'type': 'foreign_key_rule_difference',
                    'description': f"外键规则差异: {fk_key}",
                    'local_fk': local_fk,
                    'cloud_fk': cloud_fk,
                    'impact': 'medium'
                })
    
    def _compare_constraints(self):
        """对比其他约束"""
        print("\n4️⃣ 约束对比:")
        
        # 比较检查约束
        local_checks = {f"{c['table']}.{c['name']}": c for c in self.local.get('check_constraints', [])}
        cloud_checks = {f"{c['table']}.{c['name']}": c for c in self.cloud.get('check_constraints', [])}
        
        missing_checks = set(local_checks.keys()) - set(cloud_checks.keys())
        if missing_checks:
            print(f"   ❌ 云端缺失检查约束: {len(missing_checks)}个")
            for check in missing_checks:
                constraint = local_checks[check]
                self.differences['important'].append({
                    'type': 'missing_check_constraint',
                    'description': f"云端缺失检查约束: {check}",
                    'constraint': constraint,
                    'impact': 'medium'
                })
        
        # 比较唯一约束
        local_uniques = {f"{c['table']}.{c['name']}": c for c in self.local.get('unique_constraints', [])}
        cloud_uniques = {f"{c['table']}.{c['name']}": c for c in self.cloud.get('unique_constraints', [])}
        
        missing_uniques = set(local_uniques.keys()) - set(cloud_uniques.keys())
        if missing_uniques:
            print(f"   ❌ 云端缺失唯一约束: {len(missing_uniques)}个")
            for unique in missing_uniques:
                constraint = local_uniques[unique]
                self.differences['important'].append({
                    'type': 'missing_unique_constraint',
                    'description': f"云端缺失唯一约束: {unique}",
                    'constraint': constraint,
                    'impact': 'medium'
                })
        
        # 比较主键约束
        local_pks = {f"{c['table']}": c for c in self.local.get('primary_keys', [])}
        cloud_pks = {f"{c['table']}": c for c in self.cloud.get('primary_keys', [])}
        
        for table in local_pks:
            if table not in cloud_pks:
                self.differences['critical'].append({
                    'type': 'missing_primary_key',
                    'description': f"云端缺失主键: {table}",
                    'constraint': local_pks[table],
                    'impact': 'high'
                })
            elif local_pks[table]['columns'] != cloud_pks[table]['columns']:
                self.differences['critical'].append({
                    'type': 'primary_key_difference',
                    'description': f"主键定义不同: {table}",
                    'local_pk': local_pks[table],
                    'cloud_pk': cloud_pks[table],
                    'impact': 'high'
                })
    
    def _compare_indexes(self):
        """对比索引"""
        print("\n5️⃣ 索引对比:")
        
        local_indexes = {idx['name']: idx for idx in self.local.get('indexes', [])}
        cloud_indexes = {idx['name']: idx for idx in self.cloud.get('indexes', [])}
        
        local_idx_names = set(local_indexes.keys())
        cloud_idx_names = set(cloud_indexes.keys())
        
        missing_in_cloud = local_idx_names - cloud_idx_names
        missing_in_local = cloud_idx_names - local_idx_names
        
        print(f"   本地索引数: {len(local_indexes)}")
        print(f"   云端索引数: {len(cloud_indexes)}")
        
        if missing_in_cloud:
            print(f"   ❌ 云端缺失索引 ({len(missing_in_cloud)}个):")
            performance_indexes = []
            system_indexes = []
            
            for idx_name in sorted(missing_in_cloud):
                idx = local_indexes[idx_name]
                print(f"      {idx_name} on {idx['table']}")
                
                if any(keyword in idx_name for keyword in ['idx_', 'index_']):
                    performance_indexes.append(idx_name)
                    self.differences['important'].append({
                        'type': 'missing_performance_index',
                        'description': f"云端缺失性能索引: {idx_name}",
                        'index': idx,
                        'impact': 'medium'
                    })
                else:
                    system_indexes.append(idx_name)
                    self.differences['minor'].append({
                        'type': 'missing_system_index',
                        'description': f"云端缺失系统索引: {idx_name}",
                        'index': idx,
                        'impact': 'low'
                    })
        
        if missing_in_local:
            print(f"   ⚠️ 本地缺失索引 ({len(missing_in_local)}个): {sorted(missing_in_local)}")
    
    def _compare_sequences(self):
        """对比序列"""
        print("\n6️⃣ 序列对比:")
        
        local_seqs = {seq['name']: seq for seq in self.local.get('sequences', [])}
        cloud_seqs = {seq['name']: seq for seq in self.cloud.get('sequences', [])}
        
        missing_seqs = set(local_seqs.keys()) - set(cloud_seqs.keys())
        if missing_seqs:
            print(f"   ❌ 云端缺失序列: {sorted(missing_seqs)}")
            for seq_name in missing_seqs:
                self.differences['critical'].append({
                    'type': 'missing_sequence',
                    'description': f"云端缺失序列: {seq_name}",
                    'sequence': local_seqs[seq_name],
                    'impact': 'high'
                })
    
    def _compare_views(self):
        """对比视图"""
        print("\n7️⃣ 视图对比:")
        
        local_views = {view['name']: view for view in self.local.get('views', [])}
        cloud_views = {view['name']: view for view in self.cloud.get('views', [])}
        
        missing_views = set(local_views.keys()) - set(cloud_views.keys())
        if missing_views:
            print(f"   ❌ 云端缺失视图: {sorted(missing_views)}")
            for view_name in missing_views:
                self.differences['important'].append({
                    'type': 'missing_view',
                    'description': f"云端缺失视图: {view_name}",
                    'view': local_views[view_name],
                    'impact': 'medium'
                })
    
    def _compare_functions(self):
        """对比函数"""
        print("\n8️⃣ 函数对比:")
        
        local_funcs = {func['name']: func for func in self.local.get('functions', [])}
        cloud_funcs = {func['name']: func for func in self.cloud.get('functions', [])}
        
        missing_funcs = set(local_funcs.keys()) - set(cloud_funcs.keys())
        if missing_funcs:
            print(f"   ❌ 云端缺失函数: {sorted(missing_funcs)}")
            for func_name in missing_funcs:
                self.differences['important'].append({
                    'type': 'missing_function',
                    'description': f"云端缺失函数: {func_name}",
                    'function': local_funcs[func_name],
                    'impact': 'medium'
                })
    
    def _compare_triggers(self):
        """对比触发器"""
        print("\n9️⃣ 触发器对比:")
        
        local_triggers = {f"{t['table']}.{t['name']}": t for t in self.local.get('triggers', [])}
        cloud_triggers = {f"{t['table']}.{t['name']}": t for t in self.cloud.get('triggers', [])}
        
        missing_triggers = set(local_triggers.keys()) - set(cloud_triggers.keys())
        if missing_triggers:
            print(f"   ❌ 云端缺失触发器: {sorted(missing_triggers)}")
            for trigger_key in missing_triggers:
                self.differences['important'].append({
                    'type': 'missing_trigger',
                    'description': f"云端缺失触发器: {trigger_key}",
                    'trigger': local_triggers[trigger_key],
                    'impact': 'medium'
                })
    
    def _compare_enums(self):
        """对比枚举类型"""
        print("\n🔟 枚举类型对比:")
        
        local_enums = {enum['name']: enum for enum in self.local.get('enums', [])}
        cloud_enums = {enum['name']: enum for enum in self.cloud.get('enums', [])}
        
        missing_enums = set(local_enums.keys()) - set(cloud_enums.keys())
        if missing_enums:
            print(f"   ❌ 云端缺失枚举类型: {sorted(missing_enums)}")
            for enum_name in missing_enums:
                self.differences['important'].append({
                    'type': 'missing_enum',
                    'description': f"云端缺失枚举类型: {enum_name}",
                    'enum': local_enums[enum_name],
                    'impact': 'medium'
                })
    
    def _categorize_and_report(self):
        """分类并报告差异"""
        print("\n" + "="*100)
        print("📊 差异分类和影响分析")
        print("="*100)
        
        critical_count = len(self.differences['critical'])
        important_count = len(self.differences['important'])
        minor_count = len(self.differences['minor'])
        
        print(f"\n🚨 关键差异 (可能导致代码运行错误): {critical_count}个")
        for diff in self.differences['critical']:
            print(f"   ❌ {diff['description']}")
        
        print(f"\n⚠️ 重要差异 (影响功能或性能): {important_count}个")
        for diff in self.differences['important']:
            print(f"   🔸 {diff['description']}")
        
        print(f"\n ℹ️ 次要差异 (影响较小): {minor_count}个")
        
        # 生成修复建议
        self._generate_fix_recommendations()
    
    def _generate_fix_recommendations(self):
        """生成修复建议"""
        print(f"\n" + "="*100)
        print("🔧 修复建议")
        print("="*100)
        
        critical_fixes = []
        important_fixes = []
        
        for diff in self.differences['critical']:
            if diff['type'] == 'missing_column':
                critical_fixes.append(f"ADD COLUMN {diff['table']}.{diff['column']}")
            elif diff['type'] == 'missing_table':
                critical_fixes.append(f"CREATE TABLE {diff['table']}")
            elif diff['type'] == 'missing_foreign_key':
                critical_fixes.append(f"ADD FOREIGN KEY {diff['constraint']['table']}.{diff['constraint']['column']}")
        
        for diff in self.differences['important']:
            if diff['type'] == 'missing_performance_index':
                important_fixes.append(f"CREATE INDEX {diff['index']['name']}")
        
        print(f"\n🔥 立即修复 (关键):")
        for fix in critical_fixes[:10]:  # 只显示前10个
            print(f"   • {fix}")
        
        print(f"\n📈 计划修复 (重要):")
        for fix in important_fixes[:10]:  # 只显示前10个
            print(f"   • {fix}")
        
        if critical_fixes:
            print(f"\n⚠️ 警告: 发现 {len(critical_fixes)} 个关键差异可能导致代码运行错误!")

def main():
    # 数据库连接配置
    local_url = 'postgresql://nijie@localhost:5432/pma_local'
    cloud_url = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'
    
    print("开始详尽数据库差异分析...")
    
    # 分析本地数据库
    print("\n正在分析本地数据库...")
    local_analyzer = DatabaseAnalyzer(local_url, "本地")
    if not local_analyzer.connect():
        return
    
    local_schema = local_analyzer.get_complete_schema()
    local_analyzer.disconnect()
    
    # 分析云端数据库
    print("正在分析云端数据库...")
    cloud_analyzer = DatabaseAnalyzer(cloud_url, "云端")
    if not cloud_analyzer.connect():
        return
    
    cloud_schema = cloud_analyzer.get_complete_schema()
    cloud_analyzer.disconnect()
    
    # 执行对比
    comparator = DatabaseComparator(local_schema, cloud_schema)
    comparator.compare_all()
    
    # 保存详细结果
    result = {
        'local_schema': local_schema,
        'cloud_schema': cloud_schema,
        'differences': comparator.differences,
        'analysis_time': datetime.now().isoformat(),
        'summary': {
            'critical_issues': len(comparator.differences['critical']),
            'important_issues': len(comparator.differences['important']),
            'minor_issues': len(comparator.differences['minor'])
        }
    }
    
    with open('详尽数据库差异分析结果.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n💾 详细分析结果已保存到: 详尽数据库差异分析结果.json")
    print("="*100)

if __name__ == "__main__":
    main()