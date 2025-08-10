#!/usr/bin/env python3
"""
迁移数据预览脚本
在执行实际迁移前查看需要处理的数据
"""

import psycopg2
import json
from urllib.parse import urlparse

def preview_migration_data():
    """预览需要迁移的数据"""
    db_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("PMA项目发票迁移数据预览")
        print("=" * 80)
        
        # 查询需要迁移的记录
        query = """
        SELECT id, expense_id, description, invoice_images, created_at
        FROM public.expense_details 
        WHERE invoice_images LIKE %s
        ORDER BY id;
        """
        cursor.execute(query, ('%pqzviljbpfoqvyfulakl%',))
        
        records = cursor.fetchall()
        
        if not records:
            print("没有找到需要迁移的记录")
            return
        
        print(f"找到 {len(records)} 条记录需要迁移:")
        print()
        
        total_files = 0
        
        for i, (record_id, expense_id, description, invoice_images_json, created_at) in enumerate(records, 1):
            print(f"{i:2d}. 记录ID: {record_id}")
            print(f"    报销ID: {expense_id}")
            print(f"    描述: {description[:50]}{'...' if len(description) > 50 else ''}")
            print(f"    创建时间: {created_at}")
            
            try:
                invoice_images = json.loads(invoice_images_json) if invoice_images_json else []
                print(f"    发票文件数量: {len(invoice_images)}")
                
                for j, image_info in enumerate(invoice_images):
                    filename = image_info.get('filename', '未知文件名')
                    url = image_info.get('url', '')
                    size = image_info.get('size', 0)
                    
                    # 提取文件路径
                    file_path = extract_file_path_from_url(url)
                    
                    print(f"      文件{j+1}: {filename}")
                    print(f"        大小: {size} bytes ({size/1024:.1f} KB)")
                    print(f"        当前URL: {url}")
                    print(f"        文件路径: {file_path}")
                    
                    # 预测新URL
                    if file_path:
                        new_url = f"https://iqcyimnjtnmomvfuwjzw.supabase.co/storage/v1/object/public/invoice-images/{file_path}"
                        print(f"        新URL: {new_url}")
                    
                    total_files += 1
                    print()
                
            except json.JSONDecodeError:
                print(f"    ⚠ JSON解析失败")
            
            print("-" * 60)
        
        print(f"\\n总计: {len(records)} 条记录, {total_files} 个文件需要迁移")
        
        # 统计分析
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN invoice_images IS NOT NULL THEN 1 END) as has_images,
                COUNT(CASE WHEN invoice_images LIKE %s THEN 1 END) as pma_sa_urls,
                COUNT(CASE WHEN invoice_images LIKE %s THEN 1 END) as pma_urls
            FROM public.expense_details;
        """, ('%pqzviljbpfoqvyfulakl%', '%iqcyimnjtnmomvfuwjzw%'))
        
        stats = cursor.fetchone()
        total, has_images, pma_sa_urls, pma_urls = stats
        
        print("\\n数据库统计:")
        print(f"  总记录数: {total}")
        print(f"  有发票图片: {has_images}")
        print(f"  指向PMA-SA: {pma_sa_urls} (需要迁移)")
        print(f"  指向PMA: {pma_urls} (已正确)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"预览失败: {e}")

def extract_file_path_from_url(url: str) -> str:
    """从URL中提取文件路径"""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        if len(path_parts) > 6:
            return '/'.join(path_parts[6:])
        return None
    except:
        return None

if __name__ == "__main__":
    preview_migration_data()