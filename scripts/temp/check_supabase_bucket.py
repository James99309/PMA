#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查Supabase存储桶中的产品文件"""

from supabase import create_client

SUPABASE_URL = "https://iqcyimnjtnmomvfuwjzw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY3lpbW5qdG5tb212ZnV3anp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDc1Mjg5NiwiZXhwIjoyMDcwMzI4ODk2fQ.ivIwtz0Icp0eBibB4RAVh9iAULTHhCkKfPF9QOFnvfY"
BUCKET_NAME = "product-images"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print(f"检查存储桶: {BUCKET_NAME}")
print("=" * 60)

# 列出存储桶中的所有文件
try:
    # 列出 product_files/PMA 目录下的文件
    result = supabase.storage.from_(BUCKET_NAME).list("product_files/PMA")

    if result:
        print(f"\n📁 product_files/PMA/ 目录内容:")
        if len(result) == 0:
            print("  (空目录)")
        else:
            for item in result[:20]:
                print(f"  - {item.get('name', item)}")
            if len(result) > 20:
                print(f"  ... 还有 {len(result) - 20} 个项目")
        print(f"\n总计: {len(result)} 个项目")
    else:
        print("\n✅ product_files/PMA/ 目录为空或不存在")

except Exception as e:
    print(f"列出文件出错: {e}")

# 也检查根目录
print("\n" + "-" * 60)
try:
    result = supabase.storage.from_(BUCKET_NAME).list("")
    print(f"\n📁 存储桶根目录内容:")
    if result:
        for item in result[:20]:
            print(f"  - {item.get('name', item)}")
        if len(result) > 20:
            print(f"  ... 还有 {len(result) - 20} 个项目")
        print(f"\n总计: {len(result)} 个项目")
    else:
        print("  (空)")
except Exception as e:
    print(f"列出根目录出错: {e}")
