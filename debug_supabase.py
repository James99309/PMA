#!/usr/bin/env python3
"""
临时调试脚本 - 测试Supabase连接和配置
"""

import os
import sys

def test_supabase_config():
    """测试Supabase配置"""
    print("=" * 60)
    print("🔧 Supabase配置测试")
    print("=" * 60)
    
    # 1. 检查环境变量
    print("\n1️⃣ 环境变量检查:")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')  
    supabase_bucket = os.getenv('SUPABASE_BUCKET')
    force_cloud = os.getenv('FORCE_CLOUD_UPLOAD')
    
    print(f"   SUPABASE_URL: {supabase_url[:30] + '...' if supabase_url else 'NOT SET'}")
    print(f"   SUPABASE_KEY: {supabase_key[:30] + '...' if supabase_key else 'NOT SET'}")
    print(f"   SUPABASE_BUCKET: {supabase_bucket}")
    print(f"   FORCE_CLOUD_UPLOAD: {force_cloud}")
    
    if not supabase_url or not supabase_key:
        print("❌ 关键环境变量缺失!")
        # 尝试从配置文件加载
        env_file_path = '.env.supabase'
        if os.path.exists(env_file_path):
            print(f"\n🔍 尝试从配置文件加载: {env_file_path}")
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
                        print(f"   ✅ 加载: {key}")
        
        # 重新检查
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        print(f"\n   重新检查 SUPABASE_URL: {supabase_url[:30] + '...' if supabase_url else 'NOT SET'}")
    
    # 2. 测试Supabase连接
    print("\n2️⃣ Supabase连接测试:")
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        print("   ✅ Supabase客户端创建成功")
        
        # 3. 测试存储桶访问
        print("\n3️⃣ 存储桶访问测试:")
        bucket_name = supabase_bucket or 'product-images'
        print(f"   测试桶: {bucket_name}")
        
        # 尝试列出存储桶内容（简单的连接测试）
        try:
            # 注意：这个操作可能需要特定权限
            result = supabase.storage.from_(bucket_name).list()
            print("   ✅ 存储桶访问成功")
            print(f"   存储桶中的文件数量: {len(result) if result else 0}")
        except Exception as bucket_error:
            print(f"   ⚠️ 存储桶访问测试失败: {bucket_error}")
            print("   这可能是权限问题，但不影响上传功能")
        
    except ImportError as e:
        print(f"   ❌ Supabase库导入失败: {e}")
        print("   请安装: pip install supabase")
        return False
    except Exception as e:
        print(f"   ❌ Supabase连接失败: {e}")
        return False
    
    # 4. 测试文件上传 (使用小的测试文件)
    print("\n4️⃣ 文件上传测试:")
    try:
        from app.utils.supabase_client import get_supabase_client
        from io import BytesIO
        
        # 创建一个小的测试图片文件
        test_content = b"test image content"
        test_file = BytesIO(test_content)
        test_file.filename = "test.jpg"
        
        client = get_supabase_client()
        print("   ✅ Supabase客户端获取成功")
        
        # 模拟上传测试
        print("   🔄 执行上传测试...")
        result_url = client.upload_expense_invoice(999, test_file, "test_upload.jpg")
        
        if result_url:
            print(f"   ✅ 测试上传成功: {result_url}")
        else:
            print("   ❌ 测试上传返回空URL")
            
    except Exception as upload_error:
        print(f"   ❌ 上传测试失败: {upload_error}")
        import traceback
        print(f"   详细错误: {traceback.format_exc()}")
        return False
    
    print("\n🎉 Supabase配置测试完成!")
    return True

if __name__ == "__main__":
    # 如果没有环境变量，先尝试加载配置文件
    if not os.getenv('SUPABASE_URL'):
        env_file_path = '.env.supabase'
        if os.path.exists(env_file_path):
            print(f"🔧 加载配置文件: {env_file_path}")
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    success = test_supabase_config()
    sys.exit(0 if success else 1)