#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规格指标重新编码迁移脚本

功能：
1. 使用智能编码规则重新生成所有指标编码
2. 更新 SpecificationOption.code（字典层）
3. 更新 ProductSpec.field_code（产品规格层）
4. 更新 DevProductSpec.field_code（研发产品规格层）
5. 更新 Product.code_definition_snapshot（快照层）

使用方法：
    python3 scripts/temp/recode_spec_options.py

注意：执行前请先备份数据库！
"""
import sys
import os
import json
from datetime import datetime

# 路径修正
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
os.chdir(PROJECT_ROOT)

from app import create_app, db
from app.models.product_code import SpecificationDictionary, SpecificationOption
from app.models.product_spec import ProductSpec
from app.models.dev_product import DevProductSpec
from app.models.product import Product


def _extract_candidates(value, preferred_type=None):
    """从指标值提取候选编码字符"""
    digits = []
    letters = []

    for char in str(value):
        if char.isdigit() and char != '0':
            if char not in digits:
                digits.append(char)
        elif char.isalpha() and char.isascii():
            upper_char = char.upper()
            if upper_char not in letters:
                letters.append(upper_char)

    if preferred_type == 'digit':
        return digits + letters
    elif preferred_type == 'letter':
        return letters + digits
    else:
        first_char = next((c for c in str(value) if c.isalnum() and c.isascii()), None)
        if first_char and first_char.isdigit():
            return digits + letters
        else:
            return letters + digits


def _get_fallback_chars(code_type):
    """获取备用字符集"""
    if code_type == 'digit':
        return list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    else:
        return list('123456789')


def generate_new_codes_for_spec(options):
    """
    为一个规格的所有指标生成新的智能编码

    Args:
        options: 按 position 排序的指标列表

    Returns:
        dict: {option_id: new_code}
    """
    if not options:
        return {}

    # 确定首选类型（基于第一个指标值）
    first_value = options[0].value
    first_char = next((c for c in str(first_value) if c.isalnum() and c.isascii()), None)
    if first_char and first_char.isdigit():
        preferred_type = 'digit'
    else:
        preferred_type = 'letter'

    used_codes = set()
    result = {}

    for opt in options:
        # 提取候选字符
        candidates = _extract_candidates(opt.value, preferred_type)

        # 找到第一个未使用的字符
        new_code = None
        for char in candidates:
            if char not in used_codes and char != '0':
                new_code = char
                break

        # 候选用完，使用备用字符集
        if not new_code:
            fallback = _get_fallback_chars(preferred_type)
            for char in fallback:
                if char not in used_codes and char != '0':
                    new_code = char
                    break

        if new_code:
            used_codes.add(new_code)
            result[opt.id] = new_code
        else:
            result[opt.id] = opt.code  # 保留原编码

    return result


def update_product_snapshots(spec_name, old_code, new_code):
    """更新产品快照中的编码"""
    updated_count = 0

    # 查找使用此规格的产品
    product_specs = ProductSpec.query.filter_by(
        field_name=spec_name,
        field_code=old_code
    ).all()

    product_ids = set(ps.product_id for ps in product_specs)

    for pid in product_ids:
        product = db.session.get(Product, pid)
        if not product or not product.code_definition_snapshot:
            continue

        snapshot = product.code_definition_snapshot
        updated = False

        # 更新快照中的编码信息
        if isinstance(snapshot, dict):
            # 检查 fields 部分
            if 'fields' in snapshot:
                for field in snapshot['fields']:
                    if field.get('name') == spec_name:
                        if 'options' in field:
                            for opt in field['options']:
                                if opt.get('code') == old_code:
                                    opt['code'] = new_code
                                    updated = True

            # 检查 code_parts 部分
            if 'code_parts' in snapshot:
                for part in snapshot['code_parts']:
                    if part.get('field_name') == spec_name and part.get('code') == old_code:
                        part['code'] = new_code
                        updated = True

        if updated:
            product.code_definition_snapshot = snapshot
            updated_count += 1

    return updated_count


def run_migration(dry_run=True):
    """
    执行迁移

    Args:
        dry_run: True=只显示变更，不实际执行；False=执行变更
    """
    print("=" * 70)
    print(f"规格指标重新编码迁移 {'(预览模式)' if dry_run else '(执行模式)'}")
    print("=" * 70)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 统计
    stats = {
        'specs_processed': 0,
        'options_changed': 0,
        'options_unchanged': 0,
        'product_specs_updated': 0,
        'dev_product_specs_updated': 0,
        'snapshots_updated': 0
    }

    # 记录所有变更
    changes = []  # [(spec_name, value, old_code, new_code)]

    # 获取所有规格
    specs = SpecificationDictionary.query.order_by(SpecificationDictionary.display_order).all()

    for spec in specs:
        # 获取该规格的所有指标，按 position 排序
        options = SpecificationOption.query.filter_by(spec_id=spec.id)\
            .order_by(SpecificationOption.position, SpecificationOption.id).all()

        if not options:
            continue

        stats['specs_processed'] += 1

        # 生成新编码
        new_codes = generate_new_codes_for_spec(options)

        print(f"\n【{spec.name}】{len(options)}个指标")

        for opt in options:
            old_code = opt.code
            new_code = new_codes.get(opt.id, old_code)

            if old_code != new_code:
                status = "变更"
                stats['options_changed'] += 1
                changes.append((spec.name, opt.value, old_code, new_code))

                if not dry_run:
                    # 1. 更新字典层
                    opt.code = new_code

                    # 2. 更新产品规格层
                    updated_ps = ProductSpec.query.filter_by(
                        field_name=spec.name,
                        field_value=opt.value
                    ).update({'field_code': new_code})
                    stats['product_specs_updated'] += updated_ps

                    # 3. 更新研发产品规格层
                    updated_dps = DevProductSpec.query.filter_by(
                        field_name=spec.name,
                        field_value=opt.value
                    ).update({'field_code': new_code})
                    stats['dev_product_specs_updated'] += updated_dps

                    # 4. 更新快照层
                    updated_snapshots = update_product_snapshots(spec.name, old_code, new_code)
                    stats['snapshots_updated'] += updated_snapshots
            else:
                status = "不变"
                stats['options_unchanged'] += 1

            print(f"  {opt.value}: {old_code} → {new_code} ({status})")

    # 提交事务
    if not dry_run:
        db.session.commit()
        print("\n✅ 事务已提交")

    # 汇总
    print("\n" + "=" * 70)
    print("迁移统计")
    print("=" * 70)
    print(f"处理规格数: {stats['specs_processed']}")
    print(f"编码变更: {stats['options_changed']}")
    print(f"编码不变: {stats['options_unchanged']}")

    if not dry_run:
        print(f"ProductSpec 更新: {stats['product_specs_updated']}")
        print(f"DevProductSpec 更新: {stats['dev_product_specs_updated']}")
        print(f"快照更新: {stats['snapshots_updated']}")

    print()

    if dry_run:
        print("=" * 70)
        print("这是预览模式，未执行任何变更")
        print("确认无误后，请使用 --execute 参数执行迁移")
        print("=" * 70)
    else:
        print("=" * 70)
        print("✅ 迁移完成！")
        print("=" * 70)

    return stats, changes


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='规格指标重新编码迁移')
    parser.add_argument('--execute', action='store_true', help='执行迁移（默认为预览模式）')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        dry_run = not args.execute
        run_migration(dry_run=dry_run)
