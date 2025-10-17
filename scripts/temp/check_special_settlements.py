#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析41组重复，对比真实类型，决定删除哪条"""
import sys
import os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

# 类型映射
TYPE_MAPPING = {
    'integrator': 'system_integrator',
    'dealer': 'dealer',
    'designer': 'design_issues',
    'contractor': 'contractor',
    'user': 'end_user',
    'end_user': 'end_user',
    # 其他未知类型
    'partner': None,
    'design_institute': 'design_issues',
    'direct_customer': 'end_user',
    'general_contractor': 'contractor',
    'other': None,
    'system_integrator': 'system_integrator'
}

def analyze_duplicates():
    """分析所有重复，对比真实类型"""
    
    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("=" * 120)
    print("重复关联分析 - 基于公司真实类型")
    print("=" * 120)
    
    try:
        # 查找所有同项目+同公司ID的重复
        query = text("""
            SELECT
                project_id,
                company_id,
                p.project_name,
                c.company_name,
                c.company_type as real_company_type,
                COUNT(*) as count,
                array_agg(pca.id ORDER BY pca.created_at) as assoc_ids,
                array_agg(pca.customer_type ORDER BY pca.created_at) as assoc_types,
                array_agg(pca.created_at ORDER BY pca.created_at) as created_times
            FROM project_customer_associations pca
            JOIN projects p ON p.id = pca.project_id
            JOIN companies c ON c.id = pca.company_id
            GROUP BY project_id, company_id, p.project_name, c.company_name, c.company_type
            HAVING COUNT(*) > 1
            ORDER BY project_id
        """)
        
        duplicates = session.execute(query).fetchall()
        
        print(f"\n发现 {len(duplicates)} 组重复\n")
        
        delete_strategy = {
            'delete_both_wrong': [],  # 两条都不对，删除迁移的
            'delete_manual_wrong': [],  # 手动的不对，删除手动的
            'delete_migration_wrong': [],  # 迁移的不对，删除迁移的
            'keep_both': [],  # 两条都对或无法判断
            'no_real_type': []  # 公司没有类型
        }
        
        for i, dup in enumerate(duplicates, 1):
            real_type = dup.real_company_type
            expected_assoc_type = TYPE_MAPPING.get(real_type) if real_type else None
            
            print(f"【{i}/{len(duplicates)}】{dup.project_name[:50]}")
            print(f"  公司: {dup.company_name[:50]} (ID: {dup.company_id})")
            print(f"  真实类型: {real_type} → 期望关联类型: {expected_assoc_type}")
            print()
            
            for j, (aid, atype, ctime) in enumerate(zip(dup.assoc_ids, dup.assoc_types, dup.created_times), 1):
                is_migration = ctime >= '2025-10-15'
                match = "✅" if atype == expected_assoc_type else "❌"
                source = "迁移" if is_migration else "手动"
                
                print(f"    [{j}] 关联ID:{aid} | 类型:{atype:20} {match} | {source} | {ctime}")
            
            # 决策逻辑
            if not expected_assoc_type:
                print(f"  ⚠️  公司没有有效类型，无法判断")
                delete_strategy['no_real_type'].append(dup)
            else:
                matches = [atype == expected_assoc_type for atype in dup.assoc_types]
                is_migrations = [ctime >= '2025-10-15' for ctime in dup.created_times]
                
                if all(not m for m in matches):
                    # 都不匹配，删除迁移的（保留最早的手动添加）
                    print(f"  💡 决策: 都不匹配，删除迁移创建的")
                    delete_ids = [aid for aid, is_mig in zip(dup.assoc_ids, is_migrations) if is_mig]
                    print(f"  ❌ 删除: {delete_ids}")
                    delete_strategy['delete_both_wrong'].append({
                        'dup': dup,
                        'delete_ids': delete_ids
                    })
                elif matches[0] and not matches[1]:
                    # 第一条对，第二条不对
                    print(f"  💡 决策: 保留第一条（匹配），删除第二条")
                    delete_strategy['delete_migration_wrong'].append({
                        'dup': dup,
                        'delete_ids': [dup.assoc_ids[1]]
                    })
                elif not matches[0] and matches[1]:
                    # 第一条不对，第二条对
                    print(f"  💡 决策: 删除第一条（不匹配），保留第二条")
                    delete_strategy['delete_manual_wrong'].append({
                        'dup': dup,
                        'delete_ids': [dup.assoc_ids[0]]
                    })
                elif all(matches):
                    # 都匹配
                    print(f"  💡 决策: 都匹配，保留最早的")
                    delete_strategy['keep_both'].append({
                        'dup': dup,
                        'delete_ids': [dup.assoc_ids[1]]
                    })
                else:
                    print(f"  ⚠️  复杂情况，需人工判断")
            
            print()
        
        # 统计
        print("\n" + "=" * 120)
        print("📊 删除策略统计")
        print("=" * 120)
        
        total_delete = 0
        for key, items in delete_strategy.items():
            if items:
                count = len(items)
                delete_count = sum(len(item['delete_ids']) for item in items if 'delete_ids' in item)
                total_delete += delete_count
                print(f"\n{key}: {count} 组，将删除 {delete_count} 条")
        
        print(f"\n总计将删除: {total_delete} 条关联记录")
        
        return delete_strategy
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()
        engine.dispose()

if __name__ == '__main__':
    analyze_duplicates()
