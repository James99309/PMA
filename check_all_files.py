#!/usr/bin/env python3
"""
检查存储桶中的所有文件
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, '/Users/nijie/Documents/PMA')

# 设置环境变量
os.environ['SUPABASE_URL'] = 'https://iqcyimnjtnmomvfuwjzw.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY3lpbW5qdG5tb212ZnV3anp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDc1Mjg5NiwiZXhwIjoyMDcwMzI4ODk2fQ.ivIwtz0Icp0eBibB4RAVh9iAULTHhCkKfPF9QOFnvfY'
os.environ['SUPABASE_BUCKET_INVOICE'] = 'invoice-images'

def list_directory_recursive(client, bucket_name, path="", level=0, max_level=3):
    """递归列出目录内容"""
    if level > max_level:
        return
    
    indent = "  " * level
    try:
        print(f"{indent}📁 正在检查: {path or '根目录'}")
        result = client.supabase.storage.from_(bucket_name).list(path)
        
        if hasattr(result, 'data') and result.data:
            print(f"{indent}✅ 找到 {len(result.data)} 项:")
            for item in result.data:
                if item.get('metadata') is None:  # 文件夹
                    print(f"{indent}  📂 {item['name']}/")
                    new_path = f"{path}/{item['name']}" if path else item['name']
                    list_directory_recursive(client, bucket_name, new_path, level + 1, max_level)
                else:  # 文件
                    size = item.get('metadata', {}).get('size', 0)
                    print(f"{indent}  📄 {item['name']} ({size} bytes)")
        else:
            print(f"{indent}📝 目录为空")
            
    except Exception as e:
        print(f"{indent}❌ 访问失败: {e}")

def main():
    print("🔍 检查Supabase存储桶中的所有内容")
    
    try:
        from app.utils.supabase_client import SupabaseStorageClient
        
        client = SupabaseStorageClient()
        bucket_name = client.get_bucket_name('invoice')
        
        print(f"📦 存储桶: {bucket_name}")
        print(f"🌐 URL: {client.supabase_url}")
        
        # 递归列出所有内容
        list_directory_recursive(client, bucket_name)
        
        # 额外：尝试直接搜索特定的文件名模式
        print(f"\n🔍 搜索最近的文件名模式...")
        test_patterns = [
            "PMA_BX2025081016_01_01.heic",
            "PMA_BX2025081016_02_01.heic", 
            "PMA_BX2025081015_01_01.heic",
            "PMA_BX2025081014_01_01.heic"
        ]
        
        for filename in test_patterns:
            print(f"\n🎯 搜索文件: {filename}")
            # 尝试不同的可能路径
            possible_paths = [
                filename,  # 根目录
                f"invoice_files/PMA/BX{filename.split('_')[1][2:]}/{filename}",  # 标准路径
                f"expense_invoices/{filename}",  # 旧路径
                f"uploads/{filename}",  # 上传路径
            ]
            
            for test_path in possible_paths:
                try:
                    # 尝试获取文件的公开URL来测试是否存在
                    public_url = client.supabase.storage.from_(bucket_name).get_public_url(test_path)
                    print(f"  路径: {test_path}")
                    print(f"  URL: {public_url}")
                    
                    # 尝试访问URL的HEAD请求（但我们无法在这里进行HTTP请求）
                    print(f"  尝试删除测试:")
                    delete_result = client.supabase.storage.from_(bucket_name).remove([test_path])
                    print(f"  删除结果: {delete_result}")
                    break  # 如果找到了就停止
                    
                except Exception as e:
                    print(f"  ❌ 路径 {test_path} 失败: {e}")
                    
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()