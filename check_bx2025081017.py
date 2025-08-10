#!/usr/bin/env python3
"""
检查BX2025081017的云端文件
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
    print("🔍 检查BX2025081017的云端文件")
    
    try:
        from app.utils.supabase_client import SupabaseStorageClient
        
        client = SupabaseStorageClient()
        bucket_name = client.get_bucket_name('invoice')
        
        # 检查BX2025081017目录
        target_path = "invoice_files/PMA/BX2025081017"
        print(f"📁 检查目录: {target_path}")
        
        try:
            files = client.supabase.storage.from_(bucket_name).list(target_path)
            if hasattr(files, 'data') and files.data:
                print(f"✅ 找到 {len(files.data)} 个文件:")
                for file_item in files.data:
                    size = file_item.get('metadata', {}).get('size', 0)
                    filename = file_item['name']
                    print(f"  📄 {filename} ({size} bytes)")
                    
                    # 生成公开URL
                    full_path = f"{target_path}/{filename}"
                    public_url = client.supabase.storage.from_(bucket_name).get_public_url(full_path)
                    print(f"      URL: {public_url}")
            else:
                print("📝 目录为空或不存在")
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()