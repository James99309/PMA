#!/usr/bin/env python3
"""
检查实际存储路径
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, '/Users/nijie/Documents/PMA')

# 设置环境变量
os.environ['SUPABASE_URL'] = 'https://iqcyimnjtnmomvfuwjzw.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY3lpbW5qdG5tb212ZnV3anp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDc1Mjg5NiwiZXhwIjoyMDcwMzI4ODk2fQ.ivIwtz0Icp0eBibB4RAVh9iAULTHhCkKfPF9QOFnvfY'
os.environ['SUPABASE_BUCKET_INVOICE'] = 'invoice-images'

def main():
    print("🔍 检查Supabase存储中的实际文件路径")
    
    try:
        from app.utils.supabase_client import SupabaseStorageClient
        
        client = SupabaseStorageClient()
        bucket_name = client.get_bucket_name('invoice')
        
        print(f"📦 检查存储桶: {bucket_name}")
        
        # 列出根目录
        print("\n📁 根目录内容:")
        root_files = client.supabase.storage.from_(bucket_name).list("")
        if hasattr(root_files, 'data') and root_files.data:
            for item in root_files.data:
                print(f"  - {item['name']} (类型: {'文件夹' if item.get('metadata') is None else '文件'})")
        
        # 列出invoice_files目录
        print("\n📁 invoice_files 目录内容:")
        try:
            invoice_files = client.supabase.storage.from_(bucket_name).list("invoice_files")
            if hasattr(invoice_files, 'data') and invoice_files.data:
                for item in invoice_files.data:
                    print(f"  - invoice_files/{item['name']}")
                    
                    # 如果是PMA文件夹，继续查看内容
                    if item['name'] == 'PMA':
                        print("\n📁 invoice_files/PMA 目录内容:")
                        pma_files = client.supabase.storage.from_(bucket_name).list("invoice_files/PMA")
                        if hasattr(pma_files, 'data') and pma_files.data:
                            for pma_item in pma_files.data:
                                print(f"    - invoice_files/PMA/{pma_item['name']}")
                                
                                # 查看具体报销单文件夹内容
                                if pma_item['name'].startswith('BX2025'):
                                    expense_path = f"invoice_files/PMA/{pma_item['name']}"
                                    print(f"\n📁 {expense_path} 目录内容:")
                                    expense_files = client.supabase.storage.from_(bucket_name).list(expense_path)
                                    if hasattr(expense_files, 'data') and expense_files.data:
                                        for file_item in expense_files.data:
                                            print(f"      - {expense_path}/{file_item['name']}")
                                    break  # 只检查一个报销单文件夹
            else:
                print("  (空或无法访问)")
        except Exception as e:
            print(f"  ❌ 访问invoice_files失败: {e}")
        
        # 列出temp_expense_invoices目录
        print("\n📁 temp_expense_invoices 目录内容:")
        try:
            temp_files = client.supabase.storage.from_(bucket_name).list("temp_expense_invoices")
            if hasattr(temp_files, 'data') and temp_files.data:
                for item in temp_files.data[:5]:  # 只显示前5个
                    print(f"  - temp_expense_invoices/{item['name']}")
            else:
                print("  (空或无法访问)")
        except Exception as e:
            print(f"  ❌ 访问temp_expense_invoices失败: {e}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()