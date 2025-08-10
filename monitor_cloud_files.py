#!/usr/bin/env python3
"""
监控云端文件状态
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, '/Users/nijie/Documents/PMA')

# 设置环境变量
os.environ['SUPABASE_URL'] = 'https://iqcyimnjtnmomvfuwjzw.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY3lpbW5qdG5tb212ZnV3anp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDc1Mjg5NiwiZXhwIjoyMDcwMzI4ODk2fQ.ivIwtz0Icp0eBibB4RAVh9iAULTHhCkKfPF9QOFnvfY'
os.environ['SUPABASE_BUCKET_INVOICE'] = 'invoice-images'

def check_directory(client, bucket_name, path, name):
    """检查指定目录"""
    print(f"\n📁 检查{name}: {path}")
    try:
        files = client.supabase.storage.from_(bucket_name).list(path)
        if hasattr(files, 'data') and files.data:
            print(f"✅ 找到 {len(files.data)} 个文件:")
            for file_item in files.data:
                size = file_item.get('metadata', {}).get('size', 0)
                filename = file_item['name']
                print(f"  📄 {filename} ({size} bytes)")
        else:
            print("📝 目录为空或不存在")
    except Exception as e:
        print(f"❌ 检查失败: {e}")

def main():
    print("🔍 监控云端文件状态")
    
    try:
        from app.utils.supabase_client import SupabaseStorageClient
        
        client = SupabaseStorageClient()
        bucket_name = client.get_bucket_name('invoice')
        
        # 检查多个可能相关的目录
        check_directories = [
            ("invoice_files/PMA/BX2025081017", "BX2025081017目录"),
            ("invoice_files/PMA", "PMA根目录"),
            ("temp_expense_invoices", "临时文件目录")
        ]
        
        for path, name in check_directories:
            check_directory(client, bucket_name, path, name)
            
    except Exception as e:
        print(f"❌ 监控失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()