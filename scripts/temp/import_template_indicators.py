#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段2: 从产品模版导入指标到规格字典

逻辑：
1. 获取所有活跃模版中的 SpecTemplateItem（有 definition_id 且 options 非空）
2. 收集 {definition_name: {value: code, ...}}（去重，同名规格合并所有模版的值）
3. 对每个 definition_name，查找/创建 SpecificationDictionary
4. 创建 SpecificationOption 记录

导入范围：
- options JSON: {"value": "code"} 对 — 直接使用已有编码
- general_value: 如果不在 options 中，用 allocate_code_for_value() 生成编码

使用方法:
    python scripts/temp/import_template_indicators.py [--dry-run | --execute]
"""
import sys
import os
import argparse

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
from app.models.spec_template import SpecDefinition, SpecTemplate, SpecTemplateItem
from app.models.product_code import SpecificationDictionary, SpecificationOption

# 编码安全字符集（与 spec_template.py 保持一致）
SAFE_CHARS = "346789ABCDEFGHJKLMNPRTUVWXY"


def allocate_code_for_value(value, existing_codes):
    """根据值内容计算编码字符（基于哈希的分配策略）

    与 app/views/spec_template.py:allocate_code_for_value 保持一致
    """
    used_codes = set(existing_codes.values()) if existing_codes else set()

    if value:
        hash_val = sum(ord(c) for c in str(value)) % len(SAFE_CHARS)
    else:
        hash_val = 0

    for i in range(len(SAFE_CHARS)):
        idx = (hash_val + i) % len(SAFE_CHARS)
        if SAFE_CHARS[idx] not in used_codes:
            return SAFE_CHARS[idx]

    return 'X'


def collect_template_values():
    """从所有活跃模版收集规格值

    Returns:
        dict: {definition_name: {'unit': str, 'values': {value: code, ...}}}
    """
    items = SpecTemplateItem.query.join(SpecTemplate).filter(
        SpecTemplate.is_active == True,
        SpecTemplateItem.definition_id.isnot(None)
    ).all()

    result = {}  # {def_name: {'unit': ..., 'values': {value: code}}}

    for item in items:
        if not item.definition:
            continue

        def_name = item.definition.name
        def_unit = item.definition.unit

        if def_name not in result:
            result[def_name] = {'unit': def_unit, 'values': {}}

        values_dict = result[def_name]['values']

        # 导入 options JSON: {"value": "code"}
        if item.options and isinstance(item.options, dict):
            for value, code in item.options.items():
                if value and value not in values_dict:
                    values_dict[value] = code

        # 导入 general_value（如果不在 options 中）
        if item.general_value and item.general_value not in values_dict:
            # general_value 没有编码，稍后用 allocate_code_for_value 生成
            values_dict[item.general_value] = None  # 标记需要生成编码

    return result


def import_indicators(dry_run=True):
    """从产品模版导入指标到规格字典"""
    print("=" * 60)
    print("阶段2: 从产品模版导入指标到规格字典")
    print("=" * 60)

    if dry_run:
        print("【试运行模式】不会实际修改数据\n")
    else:
        print("【执行模式】将修改数据库\n")

    # 检查前置条件：specification_options 应为空（阶段1已执行）
    existing_count = SpecificationOption.query.count()
    if existing_count > 0:
        print(f"警告: specification_options 表中有 {existing_count} 条记录")
        print("请先执行阶段1清理脚本 (cleanup_product_code_spec_options.py)")
        if not dry_run:
            print("中止执行")
            return
        print("试运行模式继续...\n")

    # Step 1: 收集模版数据
    print("Step 1: 收集模版规格值...")
    values_by_def = collect_template_values()
    print(f"  发现 {len(values_by_def)} 个不同的规格定义")

    total_values = sum(len(v['values']) for v in values_by_def.values())
    print(f"  总共 {total_values} 个唯一指标值")
    print()

    # Step 2: 对每个 definition，查找/创建字典条目，创建指标
    created_dicts = 0
    created_options = 0
    skipped_options = 0

    for def_name, data in sorted(values_by_def.items()):
        unit = data['unit']
        values = data['values']

        if not values:
            continue

        # 查找 SpecificationDictionary
        spec_dict = SpecificationDictionary.query.filter_by(name=def_name).first()

        if spec_dict:
            print(f"  {def_name}: 字典已存在 (ID: {spec_dict.id})")
        else:
            print(f"  {def_name}: 需创建字典 (unit={unit})")
            if not dry_run:
                spec_dict = SpecificationDictionary(
                    name=def_name,
                    unit=unit,
                    is_active=True
                )
                db.session.add(spec_dict)
                db.session.flush()  # 获取 ID
            created_dicts += 1

        # 获取已有的指标（跳过已存在的）
        existing_options = {}
        if spec_dict and spec_dict.id:
            for opt in SpecificationOption.query.filter_by(spec_id=spec_dict.id).all():
                existing_options[opt.value] = opt.code

        # 为需要编码的 general_value 生成编码
        # 先收集所有已有编码（包括即将创建的）
        all_codes = dict(existing_options)
        for v, c in values.items():
            if c is not None:
                all_codes[v] = c

        # 检测并修复编码冲突（多个模版合并时同一编码可能被不同值使用）
        code_to_value = {}
        for v, c in list(values.items()):
            if c is None:
                continue
            if c in code_to_value:
                new_code = allocate_code_for_value(v, all_codes)
                print(f"    ⚠ 编码冲突: '{v}' 编码 '{c}' 已被 '{code_to_value[c]}' 占用 → '{new_code}'")
                values[v] = new_code
                all_codes[v] = new_code
                code_to_value[new_code] = v
            else:
                code_to_value[c] = v

        # 为 None 编码生成编码
        for v in list(values.keys()):
            if values[v] is None:
                code = allocate_code_for_value(v, all_codes)
                values[v] = code
                all_codes[v] = code

        # 创建 SpecificationOption
        position = len(existing_options)
        for value, code in sorted(values.items()):
            if value in existing_options:
                skipped_options += 1
                continue

            print(f"    + {value} → {code}")
            if not dry_run and spec_dict:
                opt = SpecificationOption(
                    spec_id=spec_dict.id,
                    value=value,
                    code=code,
                    is_active=True,
                    position=position
                )
                db.session.add(opt)
                position += 1
            created_options += 1

    print()
    print(f"汇总:")
    print(f"  新建字典: {created_dicts}")
    print(f"  新建指标: {created_options}")
    print(f"  跳过已存在: {skipped_options}")

    if not dry_run:
        db.session.commit()
        print("\n提交成功!")

        # 验证
        print("\n=== 验证 ===")
        result = db.session.execute(db.text("""
            SELECT sd.name, COUNT(so.id) as opt_count
            FROM specification_dictionary sd
            LEFT JOIN specification_options so ON so.spec_id = sd.id
            GROUP BY sd.id, sd.name
            ORDER BY opt_count DESC, sd.name
        """))
        rows = result.fetchall()
        print(f"\n规格字典指标统计 (共 {len(rows)} 个字典):")
        for row in rows:
            print(f"  {row.name}: {row.opt_count} 个指标")
    else:
        print("\n--- 试运行结束 ---")

    print("\n阶段2完成!")


def main():
    parser = argparse.ArgumentParser(description='从产品模版导入指标到规格字典')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='试运行（不修改数据）')
    group.add_argument('--execute', action='store_true', help='执行导入')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        import_indicators(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
