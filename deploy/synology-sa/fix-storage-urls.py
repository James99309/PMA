#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库中 Supabase 绝对 URL → NAS 代理 URL 转换脚本

迁移 OVS 数据库到 NAS 后运行此脚本，将 Supabase Storage 绝对 URL
转换为应用代理 URL（/storage/nas/...），使文件通过 NAS 优先 + Supabase 回退访问。

Supabase URL 格式:
  https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/{bucket}/{path}

转换为 NAS 代理 URL:
  /storage/nas/{bucket_type}?path={nas_subdir}%2F{path}

桶映射:
  invoice-images   → bucket_type=invoice,   nas_subdir=invoices
  product-images   → bucket_type=product,   nas_subdir=products
  rd-product-images → bucket_type=rd_product, nas_subdir=rd_products

用法:
  # 在 NAS 的 pma-app 容器内执行
  docker exec pma-app python deploy/synology-sa/fix-storage-urls.py --dry-run
  docker exec pma-app python deploy/synology-sa/fix-storage-urls.py
"""

import sys
import os
import json
import re
from urllib.parse import quote

# 路径修正
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

# Supabase OVS 项目 URL 前缀
SUPABASE_PREFIX = 'https://pqzviljbpfoqvyfulakl.supabase.co/storage/v1/object/public/'

# 桶名 → (bucket_type, nas_subdir)
BUCKET_MAP = {
    'invoice-images': ('invoice', 'invoices'),
    'product-images': ('product', 'products'),
    'rd-product-images': ('rd_product', 'rd_products'),
    'meeting-recordings': ('meeting', 'meetings'),
}


def convert_supabase_url(url):
    """
    将 Supabase 绝对 URL 转换为 NAS 代理 URL

    Returns:
        (new_url, changed) - 转换后的 URL 和是否发生了变化
    """
    if not url or not isinstance(url, str):
        return url, False

    if not url.startswith(SUPABASE_PREFIX):
        return url, False

    # 提取桶名和路径
    remainder = url[len(SUPABASE_PREFIX):]
    # remainder = "invoice-images/invoice_files/LOCAL-PMA/BX.../xxx.jpg"

    for bucket_name, (bucket_type, nas_subdir) in BUCKET_MAP.items():
        if remainder.startswith(bucket_name + '/'):
            file_path = remainder[len(bucket_name) + 1:]
            # NAS 代理路径: nas_subdir/file_path
            full_nas_path = f"{nas_subdir}/{file_path}"
            encoded_path = quote(full_nas_path, safe='')
            new_url = f"/storage/nas/{bucket_type}?path={encoded_path}"
            return new_url, True

    return url, False


def fix_product_urls(dry_run=True):
    """修复 Product 模型的 image_path 和 pdf_path"""
    from app.models.product import Product

    products = Product.query.filter(
        db.or_(
            Product.image_path.like(SUPABASE_PREFIX + '%'),
            Product.pdf_path.like(SUPABASE_PREFIX + '%')
        )
    ).all()

    count = 0
    for p in products:
        changed = False

        if p.image_path:
            new_url, did_change = convert_supabase_url(p.image_path)
            if did_change:
                if not dry_run:
                    p.image_path = new_url
                print(f"  Product #{p.id} image_path:")
                print(f"    OLD: {p.image_path}")
                print(f"    NEW: {new_url}")
                changed = True

        if p.pdf_path:
            new_url, did_change = convert_supabase_url(p.pdf_path)
            if did_change:
                if not dry_run:
                    p.pdf_path = new_url
                print(f"  Product #{p.id} pdf_path:")
                print(f"    OLD: {p.pdf_path}")
                print(f"    NEW: {new_url}")
                changed = True

        if changed:
            count += 1

    return count


def fix_expense_invoice_urls(dry_run=True):
    """修复 ExpenseDetail 模型的 invoice_images (JSON)"""
    from app.models.expense import ExpenseDetail

    details = ExpenseDetail.query.filter(
        ExpenseDetail.invoice_images.like('%' + SUPABASE_PREFIX.replace('/', '%') + '%')
    ).all()

    count = 0
    for d in details:
        if not d.invoice_images:
            continue

        try:
            images = json.loads(d.invoice_images)
        except (json.JSONDecodeError, TypeError):
            continue

        changed = False
        for img in images:
            if isinstance(img, dict) and img.get('url'):
                new_url, did_change = convert_supabase_url(img['url'])
                if did_change:
                    print(f"  ExpenseDetail #{d.id} invoice image:")
                    print(f"    OLD: {img['url']}")
                    print(f"    NEW: {new_url}")
                    if not dry_run:
                        img['url'] = new_url
                    changed = True

        if changed:
            if not dry_run:
                d.invoice_images = json.dumps(images, ensure_ascii=False)
            count += 1

    return count


def fix_attachment_urls(dry_run=True):
    """修复各种 Attachment 模型的 file_path / file_url"""
    count = 0

    # StageAttachment
    try:
        from app.models.gantt_models import StageAttachment
        attachments = StageAttachment.query.filter(
            StageAttachment.file_path.like(SUPABASE_PREFIX + '%')
        ).all()
        for a in attachments:
            new_url, did_change = convert_supabase_url(a.file_path)
            if did_change:
                print(f"  StageAttachment #{a.id}: {a.file_path} → {new_url}")
                if not dry_run:
                    a.file_path = new_url
                count += 1
    except Exception as e:
        print(f"  [SKIP] StageAttachment: {e}")

    # AnnouncementAttachment
    try:
        from app.models.announcement import AnnouncementAttachment
        attachments = AnnouncementAttachment.query.filter(
            AnnouncementAttachment.file_url.like(SUPABASE_PREFIX + '%')
        ).all()
        for a in attachments:
            new_url, did_change = convert_supabase_url(a.file_url)
            if did_change:
                print(f"  AnnouncementAttachment #{a.id}: {a.file_url} → {new_url}")
                if not dry_run:
                    a.file_url = new_url
                count += 1
    except Exception as e:
        print(f"  [SKIP] AnnouncementAttachment: {e}")

    # SpecAttachment
    try:
        from app.models.spec_template import SpecAttachment
        attachments = SpecAttachment.query.filter(
            SpecAttachment.file_path.like(SUPABASE_PREFIX + '%')
        ).all()
        for a in attachments:
            new_url, did_change = convert_supabase_url(a.file_path)
            if did_change:
                print(f"  SpecAttachment #{a.id}: {a.file_path} → {new_url}")
                if not dry_run:
                    a.file_path = new_url
                count += 1
    except Exception as e:
        print(f"  [SKIP] SpecAttachment: {e}")

    return count


def fix_worklog_urls(dry_run=True):
    """修复 Worklog 模型的 attachments (JSON)"""
    count = 0
    try:
        from app.models.worklog import Worklog
        worklogs = Worklog.query.filter(
            Worklog.attachments.like('%' + SUPABASE_PREFIX.replace('/', '%') + '%')
        ).all()
        for w in worklogs:
            if not w.attachments:
                continue
            try:
                attachments = json.loads(w.attachments)
            except (json.JSONDecodeError, TypeError):
                continue

            changed = False
            for att in attachments:
                if isinstance(att, dict):
                    for key in ['url', 'file_url', 'path']:
                        if att.get(key):
                            new_url, did_change = convert_supabase_url(att[key])
                            if did_change:
                                print(f"  Worklog #{w.id} attachment {key}: {att[key]} → {new_url}")
                                if not dry_run:
                                    att[key] = new_url
                                changed = True

            if changed:
                if not dry_run:
                    w.attachments = json.dumps(attachments, ensure_ascii=False)
                count += 1
    except Exception as e:
        print(f"  [SKIP] Worklog: {e}")

    return count


def main():
    dry_run = '--dry-run' in sys.argv

    app = create_app()
    with app.app_context():
        mode = "DRY RUN (preview only)" if dry_run else "LIVE (modifying database)"
        print(f"\n{'='*60}")
        print(f"  Supabase URL → NAS Proxy URL Migration")
        print(f"  Mode: {mode}")
        print(f"{'='*60}\n")

        total = 0

        print("[1/4] Fixing Product image_path / pdf_path...")
        total += fix_product_urls(dry_run)

        print(f"\n[2/4] Fixing ExpenseDetail invoice_images...")
        total += fix_expense_invoice_urls(dry_run)

        print(f"\n[3/4] Fixing Attachment file_path / file_url...")
        total += fix_attachment_urls(dry_run)

        print(f"\n[4/4] Fixing Worklog attachments...")
        total += fix_worklog_urls(dry_run)

        print(f"\n{'='*60}")
        print(f"  Total records to update: {total}")
        print(f"{'='*60}")

        if not dry_run and total > 0:
            print("\nCommitting changes...")
            db.session.commit()
            print("Done! All Supabase URLs converted to NAS proxy URLs.")
        elif dry_run and total > 0:
            print(f"\nRe-run without --dry-run to apply changes:")
            print(f"  docker exec pma-app python deploy/synology-sa/fix-storage-urls.py")
        else:
            print("\nNo Supabase URLs found. Nothing to update.")


if __name__ == '__main__':
    main()
