#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将模板中的规格值（general_value 和 子产品配置值）迁移为 SpecificationOption 记录

数据来源：
1. SpecTemplateItem.general_value → 模板通用值
2. ProductConfigValue.value → 子产品配置值

编码来源：
- 优先使用 SpecTemplateItem.options 中已有的 MN 编码映射
- 无已有编码时使用 allocate_code_for_value() 生成（与 MN 系统一致）

用法：
  # dry-run 预览（默认）
  python scripts/temp/migrate_spec_values_to_indicators.py

  # 实际执行
  python scripts/temp/migrate_spec_values_to_indicators.py --execute
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
from app.models.spec_template import SpecTemplateItem, ProductConfigValue, SpecDefinition
from app.models.product_code import SpecificationDictionary, SpecificationOption
from app.views.spec_template import allocate_code_for_value


def collect_values():
    """
    收集所有需要迁移的 (definition_name, value, mn_code) 三元组

    Returns:
        dict: {definition_name: {value: mn_code_or_None, ...}, ...}
    """
    values_by_def = {}  # {def_name: {value: code_or_None}}

    items = SpecTemplateItem.query.filter(
        SpecTemplateItem.definition_id.isnot(None)
    ).all()

    for item in items:
        if not item.definition:
            continue
        def_name = item.definition.name
        if def_name not in values_by_def:
            values_by_def[def_name] = {}

        options = item.options or {}  # {value: code} MN 编码映射

        # 1. general_value
        gv = (item.general_value or '').strip()
        if gv and gv != 'None' and gv not in values_by_def[def_name]:
            values_by_def[def_name][gv] = options.get(gv)

        # 2. 子产品配置值
        for cv in item.config_values:
            val = (cv.value or '').strip()
            if val and val != 'None' and val not in values_by_def[def_name]:
                values_by_def[def_name][val] = options.get(val)

    return values_by_def


def migrate(execute=False):
    """执行迁移"""
    values_by_def = collect_values()

    total_values = sum(len(vals) for vals in values_by_def.values())
    print(f"\n收集到 {len(values_by_def)} 个规格定义，共 {total_values} 个唯一值\n")

    if total_values == 0:
        print("没有需要迁移的数据。")
        return

    created_count = 0
    skipped_count = 0
    dict_created_count = 0

    for def_name, value_map in sorted(values_by_def.items()):
        # 查找或创建 SpecificationDictionary
        spec_dict = SpecificationDictionary.query.filter_by(name=def_name).first()
        dict_exists = spec_dict is not None

        if not spec_dict:
            # 获取 unit 信息
            definition = SpecDefinition.query.filter_by(name=def_name).first()
            unit = definition.unit if definition else None

            if execute:
                spec_dict = SpecificationDictionary(
                    name=def_name,
                    unit=unit,
                    is_active=True
                )
                db.session.add(spec_dict)
                db.session.flush()
            dict_created_count += 1
            print(f"\n[NEW DICT] {def_name}" + (f" (unit={unit})" if unit else ""))
        else:
            print(f"\n[DICT] {def_name} (id={spec_dict.id})")

        # 获取已有的 SpecificationOption
        existing_options = {}
        if spec_dict and dict_exists:
            for opt in SpecificationOption.query.filter_by(
                spec_id=spec_dict.id, is_active=True
            ).all():
                existing_options[opt.value] = opt.code

        # 构建已分配编码映射（用于 allocate_code_for_value）
        assigned = dict(existing_options)

        for value, mn_code in sorted(value_map.items()):
            if value in existing_options:
                print(f"  [SKIP] '{value}' → 已存在 (code={existing_options[value]})")
                skipped_count += 1
                continue

            # 确定编码
            if mn_code:
                # 使用已有的 MN 编码
                code = mn_code
                code_source = "MN"
            else:
                # 用 allocate_code_for_value 生成
                code = allocate_code_for_value(value, assigned)
                code_source = "GEN"

            print(f"  [CREATE] '{value}' → code='{code}' ({code_source})")

            if execute and spec_dict:
                option = SpecificationOption(
                    spec_id=spec_dict.id,
                    value=value,
                    code=code,
                    is_active=True
                )
                db.session.add(option)

            # 记录到已分配映射，避免编码冲突
            assigned[value] = code
            created_count += 1

    if execute:
        db.session.commit()
        print(f"\n✅ 迁移完成!")
    else:
        print(f"\n📋 DRY-RUN 预览（未实际执行）")

    print(f"   新建字典: {dict_created_count}")
    print(f"   新建指标: {created_count}")
    print(f"   已存在跳过: {skipped_count}")
    print(f"   总计: {created_count + skipped_count}")

    if not execute and created_count > 0:
        print(f"\n💡 加 --execute 参数实际执行迁移")


def main():
    parser = argparse.ArgumentParser(description='迁移规格值到 SpecificationOption')
    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认 dry-run）')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        migrate(execute=args.execute)


if __name__ == '__main__':
    main()
