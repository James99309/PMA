#!/usr/bin/env python3
"""
数据库结构一致性验证脚本
比较本地 pma_local 和云端 SP8D 数据库的表、字段、约束、索引等结构
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import reflection

def get_database_info(engine, db_name):
    """获取数据库的详细结构信息"""
    inspector = reflection.Inspector.from_engine(engine)
    
    info = {
        'database_name': db_name,
        'tables': {},
        'sequences': [],
        'constraints': {},
        'indexes': {}
    }
    
    # 获取所有表名
    table_names = inspector.get_table_names()
    info['table_count'] = len(table_names)
    
    print(f"📊 正在分析 {db_name} 数据库...")
    
    for table_name in table_names:
        print(f"  - 分析表: {table_name}")
        
        # 表基本信息
        columns = inspector.get_columns(table_name)
        info['tables'][table_name] = {
            'columns': columns,
            'column_count': len(columns)
        }
        
        # 获取主键
        try:
            pk_constraint = inspector.get_pk_constraint(table_name)
            info['tables'][table_name]['primary_key'] = pk_constraint
        except:
            info['tables'][table_name]['primary_key'] = None
        
        # 获取外键
        try:
            foreign_keys = inspector.get_foreign_keys(table_name)
            info['tables'][table_name]['foreign_keys'] = foreign_keys
        except:
            info['tables'][table_name]['foreign_keys'] = []
        
        # 获取唯一约束
        try:
            unique_constraints = inspector.get_unique_constraints(table_name)
            info['tables'][table_name]['unique_constraints'] = unique_constraints
        except:
            info['tables'][table_name]['unique_constraints'] = []
        
        # 获取检查约束
        try:
            check_constraints = inspector.get_check_constraints(table_name)
            info['tables'][table_name]['check_constraints'] = check_constraints
        except:
            info['tables'][table_name]['check_constraints'] = []
        
        # 获取索引
        try:
            indexes = inspector.get_indexes(table_name)
            info['tables'][table_name]['indexes'] = indexes
            # 也添加到全局索引集合中
            for idx in indexes:
                info['indexes'][f"{table_name}.{idx['name']}"] = idx
        except:
            info['tables'][table_name]['indexes'] = []
    
    # 获取序列信息
    try:
        with engine.connect() as conn:
            sequences = conn.execute(text("""
                SELECT sequence_name FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            """)).fetchall()
            info['sequences'] = [seq[0] for seq in sequences]
    except:
        info['sequences'] = []
    
    return info

def compare_column_structures(local_columns, cloud_columns, table_name):
    """比较表的字段结构"""
    differences = []
    
    # 创建字段名到字段信息的映射
    local_cols = {col['name']: col for col in local_columns}
    cloud_cols = {col['name']: col for col in cloud_columns}
    
    # 检查字段数量
    if len(local_cols) != len(cloud_cols):
        differences.append(f"字段数量不一致: 本地({len(local_cols)}) vs 云端({len(cloud_cols)})")
    
    # 检查缺失的字段
    local_only = set(local_cols.keys()) - set(cloud_cols.keys())
    cloud_only = set(cloud_cols.keys()) - set(local_cols.keys())
    
    if local_only:
        differences.append(f"本地独有字段: {', '.join(local_only)}")
    if cloud_only:
        differences.append(f"云端独有字段: {', '.join(cloud_only)}")
    
    # 检查共同字段的属性
    common_fields = set(local_cols.keys()) & set(cloud_cols.keys())
    for field_name in common_fields:
        local_col = local_cols[field_name]
        cloud_col = cloud_cols[field_name]
        
        # 比较数据类型
        if str(local_col['type']) != str(cloud_col['type']):
            differences.append(f"字段 {field_name} 类型不一致: 本地({local_col['type']}) vs 云端({cloud_col['type']})")
        
        # 比较可空性
        if local_col['nullable'] != cloud_col['nullable']:
            differences.append(f"字段 {field_name} 可空性不一致: 本地({local_col['nullable']}) vs 云端({cloud_col['nullable']})")
        
        # 比较默认值
        if local_col.get('default') != cloud_col.get('default'):
            differences.append(f"字段 {field_name} 默认值不一致: 本地({local_col.get('default')}) vs 云端({cloud_col.get('default')})")
    
    return differences

def compare_constraints(local_constraints, cloud_constraints, constraint_type, table_name):
    """比较约束"""
    differences = []
    
    local_set = set()
    cloud_set = set()
    
    # 转换为可比较的格式
    for constraint in local_constraints:
        if constraint_type == 'foreign_keys':
            key = f"{constraint.get('name', 'unnamed')}({','.join(constraint.get('constrained_columns', []))})"
        elif constraint_type == 'unique_constraints':
            key = f"{constraint.get('name', 'unnamed')}({','.join(constraint.get('column_names', []))})"
        elif constraint_type == 'check_constraints':
            key = f"{constraint.get('name', 'unnamed')}"
        else:
            key = str(constraint)
        local_set.add(key)
    
    for constraint in cloud_constraints:
        if constraint_type == 'foreign_keys':
            key = f"{constraint.get('name', 'unnamed')}({','.join(constraint.get('constrained_columns', []))})"
        elif constraint_type == 'unique_constraints':
            key = f"{constraint.get('name', 'unnamed')}({','.join(constraint.get('column_names', []))})"
        elif constraint_type == 'check_constraints':
            key = f"{constraint.get('name', 'unnamed')}"
        else:
            key = str(constraint)
        cloud_set.add(key)
    
    local_only = local_set - cloud_set
    cloud_only = cloud_set - local_set
    
    if local_only:
        differences.append(f"本地独有{constraint_type}: {', '.join(local_only)}")
    if cloud_only:
        differences.append(f"云端独有{constraint_type}: {', '.join(cloud_only)}")
    
    return differences

def compare_indexes(local_indexes, cloud_indexes, table_name):
    """比较索引"""
    differences = []
    
    # 创建索引名到索引信息的映射
    local_idx = {idx['name']: idx for idx in local_indexes}
    cloud_idx = {idx['name']: idx for idx in cloud_indexes}
    
    local_only = set(local_idx.keys()) - set(cloud_idx.keys())
    cloud_only = set(cloud_idx.keys()) - set(local_idx.keys())
    
    if local_only:
        differences.append(f"本地独有索引: {', '.join(local_only)}")
    if cloud_only:
        differences.append(f"云端独有索引: {', '.join(cloud_only)}")
    
    # 检查共同索引的属性
    common_indexes = set(local_idx.keys()) & set(cloud_idx.keys())
    for idx_name in common_indexes:
        local_index = local_idx[idx_name]
        cloud_index = cloud_idx[idx_name]
        
        if local_index.get('column_names') != cloud_index.get('column_names'):
            differences.append(f"索引 {idx_name} 字段不一致: 本地({local_index.get('column_names')}) vs 云端({cloud_index.get('column_names')})")
        
        if local_index.get('unique') != cloud_index.get('unique'):
            differences.append(f"索引 {idx_name} 唯一性不一致: 本地({local_index.get('unique')}) vs 云端({cloud_index.get('unique')})")
    
    return differences

def main():
    print("🔍 数据库结构一致性验证工具")
    print("=" * 60)
    
    # 连接本地数据库
    local_engine = create_engine('postgresql://nijie:@localhost:5432/pma_local')
    
    # 连接云端数据库
    cloud_password = os.environ.get('PGPASSWORD', 'Abc12345')
    cloud_engine = create_engine(f'postgresql://pma_db_sp8d_user:{cloud_password}@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com:5432/pma_db_sp8d?sslmode=require')
    
    try:
        # 获取数据库信息
        print("1️⃣ 获取本地数据库结构...")
        local_info = get_database_info(local_engine, "pma_local")
        
        print("2️⃣ 获取云端数据库结构...")
        cloud_info = get_database_info(cloud_engine, "pma_db_sp8d")
        
        print("3️⃣ 开始结构对比...")
        
        # 基本统计对比
        print(f"\n📊 基本信息对比:")
        print(f"  本地表数量: {local_info['table_count']}")
        print(f"  云端表数量: {cloud_info['table_count']}")
        print(f"  本地序列数量: {len(local_info['sequences'])}")
        print(f"  云端序列数量: {len(cloud_info['sequences'])}")
        
        # 检查表差异
        local_tables = set(local_info['tables'].keys())
        cloud_tables = set(cloud_info['tables'].keys())
        
        missing_in_cloud = local_tables - cloud_tables
        missing_in_local = cloud_tables - local_tables
        
        if missing_in_cloud:
            print(f"❌ 云端缺失的表: {', '.join(missing_in_cloud)}")
        if missing_in_local:
            print(f"❌ 本地缺失的表: {', '.join(missing_in_local)}")
        
        if not missing_in_cloud and not missing_in_local:
            print("✅ 表结构一致：两个数据库包含相同的表")
        
        # 详细对比每个表
        print(f"\n🔍 详细表结构对比:")
        overall_differences = []
        
        common_tables = local_tables & cloud_tables
        for table_name in sorted(common_tables):
            print(f"\n📋 检查表: {table_name}")
            table_differences = []
            
            local_table = local_info['tables'][table_name]
            cloud_table = cloud_info['tables'][table_name]
            
            # 比较字段
            col_diffs = compare_column_structures(
                local_table['columns'], 
                cloud_table['columns'], 
                table_name
            )
            table_differences.extend(col_diffs)
            
            # 比较主键
            if local_table['primary_key'] != cloud_table['primary_key']:
                table_differences.append(f"主键不一致")
            
            # 比较外键
            fk_diffs = compare_constraints(
                local_table['foreign_keys'], 
                cloud_table['foreign_keys'], 
                'foreign_keys', 
                table_name
            )
            table_differences.extend(fk_diffs)
            
            # 比较唯一约束
            unique_diffs = compare_constraints(
                local_table['unique_constraints'], 
                cloud_table['unique_constraints'], 
                'unique_constraints', 
                table_name
            )
            table_differences.extend(unique_diffs)
            
            # 比较检查约束
            check_diffs = compare_constraints(
                local_table['check_constraints'], 
                cloud_table['check_constraints'], 
                'check_constraints', 
                table_name
            )
            table_differences.extend(check_diffs)
            
            # 比较索引
            idx_diffs = compare_indexes(
                local_table['indexes'], 
                cloud_table['indexes'], 
                table_name
            )
            table_differences.extend(idx_diffs)
            
            if table_differences:
                print(f"  ❌ 发现 {len(table_differences)} 个差异:")
                for diff in table_differences:
                    print(f"    - {diff}")
                overall_differences.extend([f"{table_name}: {diff}" for diff in table_differences])
            else:
                print(f"  ✅ 表结构完全一致")
        
        # 检查alembic版本
        print(f"\n🏷️ 检查迁移版本:")
        try:
            with local_engine.connect() as conn:
                local_version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            print(f"  本地版本: {local_version}")
        except Exception as e:
            print(f"  本地版本获取失败: {e}")
        
        try:
            with cloud_engine.connect() as conn:
                cloud_version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
            print(f"  云端版本: {cloud_version}")
        except Exception as e:
            print(f"  云端版本获取失败: {e}")
        
        # 总结报告
        print(f"\n📝 验证总结:")
        print("=" * 60)
        
        if overall_differences:
            print(f"❌ 发现 {len(overall_differences)} 个结构差异:")
            for i, diff in enumerate(overall_differences, 1):
                print(f"  {i}. {diff}")
        else:
            print("✅ 数据库结构完全一致！")
            print("✅ 所有表、字段、约束、索引都匹配")
        
        print(f"\n✅ 验证完成！")
        
    except Exception as e:
        print(f"❌ 验证过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        local_engine.dispose()
        cloud_engine.dispose()

if __name__ == "__main__":
    main()