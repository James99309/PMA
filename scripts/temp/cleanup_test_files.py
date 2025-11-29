#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理本地数据库中的云端测试文件
1. 删除 Supabase 存储中的文件
2. 清空数据库中的文件路径
"""
import sys
import os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.product import Product
from app.models.product_code import ProductCategory
from app.utils.supabase_client import get_supabase_client


def extract_storage_path(url):
    """从完整URL提取存储路径"""
    # URL格式: https://xxx.supabase.co/storage/v1/object/public/bucket-name/path/to/file
    if not url or 'supabase' not in url:
        return None, None

    try:
        # 找到 /public/ 后面的部分
        parts = url.split('/storage/v1/object/public/')
        if len(parts) != 2:
            return None, None

        path_part = parts[1]
        # 第一个 / 之前是 bucket，之后是文件路径
        slash_idx = path_part.find('/')
        if slash_idx == -1:
            return None, None

        bucket = path_part[:slash_idx]
        file_path = path_part[slash_idx + 1:]
        return bucket, file_path
    except Exception as e:
        print(f"解析URL失败: {url}, 错误: {e}")
        return None, None


def cleanup_files(dry_run=True):
    app = create_app()
    with app.app_context():
        supabase_client = get_supabase_client()

        # 收集所有需要删除的云端文件
        cloud_files = []

        # 从 products 表收集
        products = Product.query.filter(
            (Product.image_path.like('%supabase%')) |
            (Product.pdf_path.like('%supabase%'))
        ).all()

        print(f"\n找到 {len(products)} 个产品有云端文件")
        for p in products:
            if p.image_path and 'supabase' in p.image_path:
                cloud_files.append(('product', p.id, 'image', p.image_path))
            if p.pdf_path and 'supabase' in p.pdf_path:
                cloud_files.append(('product', p.id, 'pdf', p.pdf_path))

        # 从 product_categories 表收集
        categories = ProductCategory.query.filter(
            (ProductCategory.image_path.like('%supabase%')) |
            (ProductCategory.pdf_path.like('%supabase%'))
        ).all()

        print(f"找到 {len(categories)} 个分类有云端文件")
        for c in categories:
            if c.image_path and 'supabase' in c.image_path:
                cloud_files.append(('category', c.id, 'image', c.image_path))
            if c.pdf_path and 'supabase' in c.pdf_path:
                cloud_files.append(('category', c.id, 'pdf', c.pdf_path))

        print(f"\n共 {len(cloud_files)} 个云端文件需要清理:")

        # 删除云端文件
        deleted_files = set()  # 避免重复删除
        for table, obj_id, file_type, url in cloud_files:
            bucket, file_path = extract_storage_path(url)
            if not bucket or not file_path:
                print(f"  ❌ 无法解析: {url[:60]}...")
                continue

            file_key = f"{bucket}/{file_path}"
            if file_key in deleted_files:
                continue
            deleted_files.add(file_key)

            if dry_run:
                print(f"  [DRY RUN] 将删除: {bucket}/{file_path[:50]}...")
            else:
                try:
                    result = supabase_client.supabase.storage.from_(bucket).remove([file_path])
                    print(f"  ✅ 已删除: {bucket}/{file_path[:50]}...")
                except Exception as e:
                    print(f"  ❌ 删除失败: {bucket}/{file_path[:50]}... 错误: {e}")

        # 清空数据库字段
        if dry_run:
            print(f"\n[DRY RUN] 将清空 {len(products)} 个产品的文件路径")
            print(f"[DRY RUN] 将清空 {len(categories)} 个分类的文件路径")
        else:
            # 清空产品文件路径
            for p in products:
                if p.image_path and 'supabase' in p.image_path:
                    p.image_path = None
                if p.pdf_path and 'supabase' in p.pdf_path:
                    p.pdf_path = None

            # 清空分类文件路径
            for c in categories:
                if c.image_path and 'supabase' in c.image_path:
                    c.image_path = None
                if c.pdf_path and 'supabase' in c.pdf_path:
                    c.pdf_path = None

            db.session.commit()
            print(f"\n✅ 已清空 {len(products)} 个产品的文件路径")
            print(f"✅ 已清空 {len(categories)} 个分类的文件路径")

        print("\n清理完成！")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='清理本地数据库中的云端测试文件')
    parser.add_argument('--execute', action='store_true', help='实际执行清理（默认为dry run）')
    args = parser.parse_args()

    cleanup_files(dry_run=not args.execute)
