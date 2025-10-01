#!/usr/bin/env python3
"""
检查临时文件目录
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
    print("🔍 检查临时文件目录")
    
    try:
        from app.utils.supabase_client import SupabaseStorageClient
        
        client = SupabaseStorageClient()
        bucket_name = client.get_bucket_name('invoice')
        
        print(f"📦 存储桶: {bucket_name}")
        
        # 检查临时文件目录
        print("\n📁 temp_expense_invoices 目录内容:")
        try:
            temp_files = client.supabase.storage.from_(bucket_name).list("temp_expense_invoices")
            if hasattr(temp_files, 'data') and temp_files.data:
                print(f"✅ 找到 {len(temp_files.data)} 个临时目录:")
                for item in temp_files.data:
                    print(f"  📂 temp_expense_invoices/{item['name']}")
                    
                    # 查看每个临时目录的内容
                    temp_path = f"temp_expense_invoices/{item['name']}"
                    try:
                        files_in_temp = client.supabase.storage.from_(bucket_name).list(temp_path)
                        if hasattr(files_in_temp, 'data') and files_in_temp.data:
                            for file_item in files_in_temp.data:
                                size = file_item.get('metadata', {}).get('size', 0)
                                print(f"    📄 {file_item['name']} ({size} bytes)")
                    except Exception as e:
                        print(f"    ❌ 无法访问: {e}")
            else:
                print("📝 临时目录为空")
        except Exception as e:
            print(f"❌ 访问temp_expense_invoices失败: {e}")
        
        # 测试删除指定的文件
        test_file_path = "temp_expense_invoices/5dfa849b-90f0-42df-b44e-67ea9840532d/tempImagejrUReU_20250810_201354_5dfa849b.jpg"
        print(f"\n🗑️ 尝试删除指定文件:")
        print(f"路径: {test_file_path}")
        
        try:
            delete_result = client.supabase.storage.from_(bucket_name).remove([test_file_path])
            print(f"删除结果: {delete_result}")
        except Exception as e:
            print(f"删除失败: {e}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()