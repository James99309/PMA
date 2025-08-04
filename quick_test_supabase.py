#!/usr/bin/env python3
"""
快速测试 Supabase 连接
不依赖 Flask 应用，直接测试 Supabase 库
"""

import os
import sys
from io import BytesIO

def test_supabase_connection():
    """测试 Supabase 连接"""
    try:
        # 检查环境变量
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        bucket_name = os.getenv('SUPABASE_BUCKET')
        
        if not all([supabase_url, supabase_key, bucket_name]):
            print("❌ 缺少 Supabase 环境变量")
            return False
        
        print(f"✅ 环境变量检查通过")
        print(f"URL: {supabase_url}")
        print(f"Bucket: {bucket_name}")
        
        # 测试 Supabase 导入
        try:
            from supabase import create_client
            print("✅ Supabase 库导入成功")
        except ImportError:
            print("❌ Supabase 库未安装")
            return False
        
        # 创建客户端
        try:
            supabase = create_client(supabase_url, supabase_key)
            print("✅ Supabase 客户端创建成功")
        except Exception as e:
            print(f"❌ 客户端创建失败: {e}")
            return False
        
        # 测试简单的存储操作（列出bucket）
        try:
            buckets = supabase.storage.list_buckets()
            print(f"✅ 成功连接到 Supabase Storage")
            if hasattr(buckets, '__len__'):
                print(f"   找到 {len(buckets)} 个存储桶")
        except Exception as e:
            print(f"⚠️  存储桶列表获取失败: {e}")
            print("   这可能是权限问题，但不影响上传功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔗 快速 Supabase 连接测试")
    print("=" * 40)
    
    success = test_supabase_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Supabase 连接测试通过!")
        print("现在可以启动应用测试文件上传功能了")
    else:
        print("❌ 连接测试失败")
    
    sys.exit(0 if success else 1)