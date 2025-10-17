#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成重名公司决策表"""
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

def generate_decision_table():
    """生成重名公司决策表"""
    
    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("=" * 120)
    print("重名公司决策表 - 需要您确认是否合并")
    print("=" * 120)
    
    try:
        # 查找所有重名公司
        query = text("""
            SELECT
                company_name,
                array_agg(id ORDER BY id) as company_ids,
                COUNT(*) as count
            FROM companies
            WHERE is_deleted = false
            GROUP BY company_name
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
        """)
        
        duplicates = session.execute(query).fetchall()
        
        for i, dup in enumerate(duplicates, 1):
            print(f"\n【{i}/{len(duplicates)}】{dup.company_name}")
            print(f"  重名次数: {dup.count}")
            print(f"  公司ID: {dup.company_ids}")
            print()
            
            # 每个ID的详细信息
            for cid in dup.company_ids:
                detail_query = text("""
                    SELECT
                        c.id,
                        c.created_at,
                        c.owner_id,
                        u.name as owner_name,
                        COUNT(DISTINCT pca.project_id) as project_count,
                        COUNT(DISTINCT contacts.id) as contact_count,
                        array_agg(DISTINCT p.project_name ORDER BY p.project_name) 
                            FILTER (WHERE p.project_name IS NOT NULL) as project_names
                    FROM companies c
                    LEFT JOIN users u ON u.id = c.owner_id
                    LEFT JOIN project_customer_associations pca ON pca.company_id = c.id
                    LEFT JOIN projects p ON p.id = pca.project_id
                    LEFT JOIN contacts ON contacts.company_id = c.id AND contacts.is_deleted = false
                    WHERE c.id = :cid
                    GROUP BY c.id, c.created_at, c.owner_id, u.name
                """)
                
                result = session.execute(detail_query, {'cid': cid}).fetchone()
                
                print(f"    公司ID {result.id}:")
                print(f"      创建时间: {result.created_at}")
                print(f"      创建人: {result.owner_name} (ID:{result.owner_id})")
                print(f"      关联项目数: {result.project_count}")
                print(f"      联系人数: {result.contact_count}")
                
                if result.project_names and len(result.project_names) > 0:
                    print(f"      关联项目:")
                    for pname in result.project_names[:5]:  # 只显示前5个
                        print(f"        - {pname}")
                    if len(result.project_names) > 5:
                        print(f"        ... 还有 {len(result.project_names) - 5} 个项目")
                print()
            
            print(f"  ❓ 决策问题:")
            print(f"     1. 这是两个不同的公司（恰好同名）？还是录入错误？")
            print(f"     2. 如果需要合并，保留哪个ID？（考虑创建时间、关联数据）")
            print("-" * 120)
        
        print(f"\n总计: {len(duplicates)} 组重名公司需要决策")
        print("=" * 120)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        engine.dispose()

if __name__ == '__main__':
    generate_decision_table()
