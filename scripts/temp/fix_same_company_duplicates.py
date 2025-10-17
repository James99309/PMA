#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复项目客户关联中同一公司ID的重复"""
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
from datetime import datetime
import json

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def fix_same_company_duplicates(dry_run=True):
    """修复同一项目+同一公司ID的重复关联"""
    
    print("=" * 100)
    print("修复项目客户关联 - 同一公司ID重复")
    print("=" * 100)
    print(f"\n模式: {'🔍 预演模式' if dry_run else '🚀 执行模式'}")
    print("-" * 100)
    
    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    stats = {
        'total_groups': 0,
        'total_deleted': 0,
        'deleted_ids': [],
        'details': []
    }
    
    try:
        # 查找同一项目+同一公司ID的重复
        query = text("""
            SELECT
                project_id,
                company_id,
                p.project_name,
                c.company_name,
                COUNT(*) as count,
                array_agg(pca.id ORDER BY pca.created_at) as assoc_ids,
                array_agg(pca.customer_type ORDER BY pca.created_at) as types
            FROM project_customer_associations pca
            JOIN projects p ON p.id = pca.project_id
            JOIN companies c ON c.id = pca.company_id
            GROUP BY project_id, company_id, p.project_name, c.company_name
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, project_id
        """)
        
        duplicates = session.execute(query).fetchall()
        stats['total_groups'] = len(duplicates)
        
        if not duplicates:
            print("\n✅ 未发现需要修复的重复")
            return stats
        
        print(f"\n发现 {len(duplicates)} 组重复\n")
        
        for i, dup in enumerate(duplicates, 1):
            print(f"【{i}/{len(duplicates)}】{dup.project_name}")
            print(f"  公司: {dup.company_name} (ID: {dup.company_id})")
            print(f"  重复次数: {dup.count}")
            
            # 保留第一个（最早），删除其他
            keep_id = dup.assoc_ids[0]
            delete_ids = dup.assoc_ids[1:]
            
            print(f"  ✅ 保留: 关联ID {keep_id} ({dup.types[0]})")
            for j, (del_id, del_type) in enumerate(zip(delete_ids, dup.types[1:]), 1):
                print(f"  ❌ 删除: 关联ID {del_id} ({del_type})")
            
            stats['deleted_ids'].extend(delete_ids)
            stats['total_deleted'] += len(delete_ids)
            
            stats['details'].append({
                'project_id': dup.project_id,
                'project_name': dup.project_name,
                'company_id': dup.company_id,
                'company_name': dup.company_name,
                'keep_id': keep_id,
                'delete_ids': delete_ids
            })
            
            if not dry_run:
                # 执行删除
                delete_query = text("""
                    DELETE FROM project_customer_associations
                    WHERE id = ANY(:ids)
                """)
                session.execute(delete_query, {'ids': delete_ids})
                print(f"  ✅ 已删除 {len(delete_ids)} 条")
            
            print()
        
        # 提交事务
        if not dry_run:
            print("\n" + "-" * 100)
            print("提交事务...")
            session.commit()
            print("✅ 事务已提交")
        
        # 统计
        print("\n" + "=" * 100)
        print("📊 修复统计")
        print("=" * 100)
        print(f"\n  重复组数: {stats['total_groups']}")
        print(f"  {'计划删除' if dry_run else '已删除'}: {stats['total_deleted']} 条")
        
        # 保存报告
        report_path = os.path.join(get_project_root(), 
                                  'scripts/temp/fix_duplicates_result.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'dry_run': dry_run,
                'stats': stats
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n  详细报告: {report_path}")
        
        if dry_run:
            print("\n" + "=" * 100)
            print("⚠️  预演模式，未实际修改数据")
            print("要执行修复，请运行:")
            print("  python3 scripts/temp/fix_same_company_duplicates.py --execute")
            print("=" * 100)
        else:
            print("\n" + "=" * 100)
            print("✅ 修复完成！")
            print("\n验证:")
            print("  python3 scripts/temp/analyze_duplicate_strategy.py")
            print("=" * 100)
        
        return stats
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            print("\n回滚事务...")
            session.rollback()
            print("✅ 已回滚")
        return None
    finally:
        session.close()
        engine.dispose()

if __name__ == '__main__':
    dry_run = '--execute' not in sys.argv
    force = '--force' in sys.argv
    
    if not dry_run and not force:
        print("\n" + "!" * 100)
        print("⚠️  警告：即将删除重复的关联记录！")
        print("!" * 100)
        print("\n策略：保留最早创建的记录，删除后创建的")
        print("影响：约41组重复，将删除41条记录")
        print("\n确认数据库已备份")
        print()
        response = input("确认执行？(输入 'YES'): ")
        if response != 'YES':
            print("\n已取消")
            sys.exit(0)
    
    result = fix_same_company_duplicates(dry_run=dry_run)
    sys.exit(0 if result else 1)
