#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除SP8D产品图片脚本

功能：
1. 从SP8D数据库提取所有产品图片路径
2. 删除Supabase存储桶中的文件
3. 清空数据库中的image_path和pdf_path字段

使用方式：
    python scripts/temp/delete_sp8d_product_images.py
"""

import os
import sys
import re

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

PROJECT_ROOT = get_project_root()
sys.path.insert(0, PROJECT_ROOT)

import psycopg2
from supabase import create_client

# SP8D数据库配置
SP8D_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

# Supabase配置
SUPABASE_URL = "https://iqcyimnjtnmomvfuwjzw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY3lpbW5qdG5tb212ZnV3anp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDc1Mjg5NiwiZXhwIjoyMDcwMzI4ODk2fQ.ivIwtz0Icp0eBibB4RAVh9iAULTHhCkKfPF9QOFnvfY"
BUCKET_NAME = "product-images"


def extract_storage_path(url):
    """
    从Supabase URL提取存储路径

    URL格式: https://xxx.supabase.co/storage/v1/object/public/product-images/product_files/PMA/123/image_123_xxx.png
    返回: product_files/PMA/123/image_123_xxx.png
    """
    if not url:
        return None

    # 匹配存储路径
    pattern = r'/storage/v1/object/public/[^/]+/(.+)$'
    match = re.search(pattern, url)

    if match:
        return match.group(1)
    return None


def get_product_image_paths():
    """从SP8D数据库获取所有产品图片路径"""
    conn = psycopg2.connect(SP8D_DB_URL)
    cur = conn.cursor()

    # 查询所有有image_path的产品
    cur.execute("""
        SELECT id, image_path, pdf_path
        FROM products
        WHERE image_path IS NOT NULL OR pdf_path IS NOT NULL
    """)

    products = cur.fetchall()
    cur.close()
    conn.close()

    return products


def delete_storage_files(supabase, storage_paths):
    """批量删除Supabase存储文件"""
    deleted = 0
    failed = 0

    for path in storage_paths:
        if not path:
            continue

        try:
            result = supabase.storage.from_(BUCKET_NAME).remove([path])
            print(f"  ✅ 删除: {path}")
            deleted += 1
        except Exception as e:
            print(f"  ❌ 失败: {path} - {e}")
            failed += 1

    return deleted, failed


def clear_database_fields():
    """清空数据库中的image_path和pdf_path字段"""
    conn = psycopg2.connect(SP8D_DB_URL)
    cur = conn.cursor()

    cur.execute("""
        UPDATE products
        SET image_path = NULL, pdf_path = NULL
        WHERE image_path IS NOT NULL OR pdf_path IS NOT NULL
    """)

    updated_count = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    return updated_count


def main():
    print("=" * 60)
    print("SP8D 产品图片删除工具")
    print("=" * 60)

    # 步骤1: 获取产品图片路径
    print("\n📋 步骤1: 获取产品图片路径...")
    products = get_product_image_paths()

    image_paths = []
    pdf_paths = []
    supabase_image_count = 0
    local_pdf_count = 0

    for product_id, image_path, pdf_path in products:
        if image_path:
            if image_path.startswith('http'):
                storage_path = extract_storage_path(image_path)
                if storage_path:
                    image_paths.append(storage_path)
                    supabase_image_count += 1
            else:
                local_pdf_count += 1

        if pdf_path:
            if pdf_path.startswith('http'):
                storage_path = extract_storage_path(pdf_path)
                if storage_path:
                    pdf_paths.append(storage_path)
            else:
                local_pdf_count += 1

    print(f"  - 总产品数: {len(products)}")
    print(f"  - Supabase图片路径: {supabase_image_count}")
    print(f"  - 本地文件路径（跳过）: {local_pdf_count}")
    print(f"  - 待删除存储文件: {len(image_paths) + len(pdf_paths)}")

    if not image_paths and not pdf_paths:
        print("\n⚠️ 没有需要删除的云端文件")
    else:
        # 显示将要删除的文件路径
        print("\n📁 将要删除的文件路径:")
        all_paths = image_paths + pdf_paths
        for i, path in enumerate(all_paths[:10]):  # 只显示前10个
            print(f"  {i+1}. {path}")
        if len(all_paths) > 10:
            print(f"  ... 还有 {len(all_paths) - 10} 个文件")

    # 步骤2: 删除Supabase存储文件
    print("\n🗑️ 步骤2: 删除Supabase存储文件...")

    # 创建Supabase客户端
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    all_paths = image_paths + pdf_paths
    if all_paths:
        deleted, failed = delete_storage_files(supabase, all_paths)
        print(f"\n  删除统计: 成功 {deleted}, 失败 {failed}")
    else:
        print("  无文件需要删除")

    # 步骤3: 清空数据库字段
    print("\n💾 步骤3: 清空数据库路径字段...")
    updated = clear_database_fields()
    print(f"  已更新 {updated} 条产品记录")

    # 完成
    print("\n" + "=" * 60)
    print("✅ 删除完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
