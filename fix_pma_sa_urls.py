#!/usr/bin/env python3
"""
修复PMA-SA数据库中错误的发票URL
将指向product-images的URL更正为invoice-images
"""

import psycopg2
import json
import sys

def fix_pma_sa_invoice_urls():
    """修复PMA-SA数据库中的发票URL"""
    
    # PMA-SA数据库配置
    pma_sa_db_url = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = psycopg2.connect(pma_sa_db_url)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("PMA-SA发票URL修复工具")
        print("=" * 60)
        
        # 1. 查找需要修复的记录
        cursor.execute("""
            SELECT id, description, invoice_images
            FROM public.expense_details 
            WHERE invoice_images LIKE '%product-images%'
            ORDER BY id
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("没有找到需要修复的记录")
            return
        
        print(f"找到 {len(records)} 条需要修复的记录:")
        
        fixed_count = 0
        failed_count = 0
        
        for record_id, description, invoice_images_json in records:
            print(f"\n处理记录 ID {record_id}: {description[:50]}...")
            
            try:
                # 解析JSON
                invoice_images = json.loads(invoice_images_json) if invoice_images_json else []
                
                if not invoice_images:
                    print(f"  跳过: 没有发票图片")
                    continue
                
                # 修复URL
                updated_images = []
                fixed_files = 0
                
                for image_info in invoice_images:
                    original_url = image_info.get('url', '')
                    
                    if 'product-images' in original_url:
                        # 替换product-images为invoice-images
                        new_url = original_url.replace('product-images', 'invoice-images')
                        
                        # 更新图片信息
                        updated_image_info = image_info.copy()
                        updated_image_info['url'] = new_url
                        updated_images.append(updated_image_info)
                        
                        print(f"    修复文件: {image_info.get('filename', 'unknown')}")
                        print(f"      原URL: {original_url[:80]}...")
                        print(f"      新URL: {new_url[:80]}...")
                        fixed_files += 1
                    else:
                        # URL已经正确，保持不变
                        updated_images.append(image_info)
                
                if fixed_files > 0:
                    # 更新数据库
                    new_json = json.dumps(updated_images)
                    
                    cursor.execute("""
                        UPDATE public.expense_details 
                        SET invoice_images = %s 
                        WHERE id = %s
                    """, (new_json, record_id))
                    
                    print(f"  ✅ 成功修复 {fixed_files} 个文件的URL")
                    fixed_count += 1
                else:
                    print(f"  ℹ️  无需修复")
                
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                failed_count += 1
        
        # 提交更改
        if fixed_count > 0:
            conn.commit()
            print(f"\n✅ 成功提交数据库更改")
        
        # 总结
        print(f"\n" + "=" * 60)
        print(f"修复完成:")
        print(f"  成功修复: {fixed_count} 条记录")
        print(f"  修复失败: {failed_count} 条记录")
        print("=" * 60)
        
        # 验证修复结果
        print(f"\n验证修复结果...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM public.expense_details 
            WHERE invoice_images LIKE '%product-images%'
        """)
        
        remaining_wrong_urls = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM public.expense_details 
            WHERE invoice_images LIKE '%invoice-images%'
        """)
        
        correct_urls = cursor.fetchone()[0]
        
        print(f"验证结果:")
        print(f"  剩余错误URL: {remaining_wrong_urls} 个")
        print(f"  正确URL: {correct_urls} 个")
        
        if remaining_wrong_urls == 0:
            print(f"  🎉 所有URL已修复完成！")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"修复过程发生错误: {e}")

def main():
    print("PMA-SA发票URL修复工具")
    print("将错误指向product-images的URL修复为invoice-images")
    print()
    
    try:
        fix_pma_sa_invoice_urls()
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"程序运行错误: {e}")

if __name__ == "__main__":
    main()