#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将现有指标迁移到规格字典

此脚本执行以下操作：
1. 从 ProductCodeFieldOption 收集所有唯一的指标值和编码
2. 按规格名称分组，创建 SpecificationOption 记录
3. 更新 ProductCodeFieldOption 的 spec_option_id 引用

使用方法:
    python scripts/temp/migrate_spec_options.py [--dry-run]
"""
import sys
import os

# 路径修正 - 支持从任何位置运行
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
from app.models.product_code import (
    ProductCodeField, ProductCodeFieldOption,
    SpecificationDictionary, SpecificationOption
)
from datetime import datetime


def generate_smart_code(spec_id, value, used_codes):
    """智能生成指标编码

    Args:
        spec_id: 规格字典ID
        value: 指标值（如 "400-450"）
        used_codes: 已使用的编码集合

    Returns:
        str: 生成的编码字符
    """
    # 获取该规格的编码类型（基于第一个指标）
    first_option = SpecificationOption.query.filter_by(spec_id=spec_id)\
        .order_by(SpecificationOption.id).first()
    code_type = _determine_code_type(first_option.code) if first_option else None

    # 从指标值提取候选字符
    candidates = _extract_candidates(value, code_type)

    # 找到第一个未使用的字符（排除0）
    for char in candidates:
        if char not in used_codes and char != '0':
            return char

    # 候选用完，使用备用字符集
    fallback_chars = _get_fallback_chars(code_type)
    for char in fallback_chars:
        if char not in used_codes and char != '0':
            return char

    return None  # 全部用完（理论上不会发生）


def _determine_code_type(code):
    """判断编码类型"""
    if code and code.isdigit():
        return 'digit'
    elif code and code.isalpha():
        return 'letter'
    return None


def _extract_candidates(value, preferred_type=None):
    """从指标值提取候选编码字符"""
    digits = []
    letters = []

    for char in str(value):
        if char.isdigit() and char != '0':  # 排除0
            if char not in digits:
                digits.append(char)
        elif char.isalpha() and char.isascii():
            upper_char = char.upper()
            if upper_char not in letters:
                letters.append(upper_char)

    # 根据首字符或优先类型决定顺序
    if preferred_type == 'digit':
        return digits + letters
    elif preferred_type == 'letter':
        return letters + digits
    else:
        # 根据值的首个有效字符决定
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


def migrate_to_spec_options(dry_run=False):
    """将现有指标迁移到规格字典

    Args:
        dry_run: 如果为True，只显示将要执行的操作，不实际执行
    """
    print("=" * 60)
    print("开始迁移指标到规格字典")
    print("=" * 60)

    if dry_run:
        print("【试运行模式】不会实际修改数据")
        print()

    # 1. 收集所有规格名称
    spec_names = db.session.query(ProductCodeField.name).distinct().all()
    print(f"发现 {len(spec_names)} 个不同的规格名称")

    created_count = 0
    updated_count = 0
    skipped_count = 0

    for (spec_name,) in spec_names:
        # 获取规格字典记录
        spec_dict = SpecificationDictionary.query.filter_by(name=spec_name).first()
        if not spec_dict:
            print(f"⚠️ 规格 '{spec_name}' 未在规格字典中，跳过")
            skipped_count += 1
            continue

        print(f"\n处理规格: {spec_name} (ID: {spec_dict.id})")

        # 2. 收集该规格所有字段的指标（去重）
        fields = ProductCodeField.query.filter_by(name=spec_name).all()
        value_to_code = {}  # 相同值使用第一个遇到的编码
        value_to_options = {}  # 记录每个值对应的选项ID列表

        for field in fields:
            for option in field.options:
                if option.value not in value_to_code:
                    value_to_code[option.value] = option.code
                    value_to_options[option.value] = []
                value_to_options[option.value].append(option.id)

        print(f"  - 收集到 {len(value_to_code)} 个唯一指标值")

        # 3. 检查现有的 SpecificationOption 记录
        existing_options = {opt.value: opt for opt in
                          SpecificationOption.query.filter_by(spec_id=spec_dict.id).all()}

        # 已使用的编码
        used_codes = {opt.code for opt in existing_options.values()}

        # 4. 创建或获取 SpecificationOption 记录
        for value, code in value_to_code.items():
            if value in existing_options:
                spec_option = existing_options[value]
                print(f"    ✓ 指标 '{value}' 已存在 (ID: {spec_option.id}, Code: {spec_option.code})")
            else:
                # 检查编码是否已被使用，如果是则生成新编码
                if code in used_codes:
                    new_code = generate_smart_code(spec_dict.id, value, used_codes)
                    print(f"    ⚠️ 编码 '{code}' 已被使用，为 '{value}' 生成新编码: '{new_code}'")
                    code = new_code

                if not dry_run:
                    spec_option = SpecificationOption(
                        spec_id=spec_dict.id,
                        value=value,
                        code=code,
                        is_active=True,
                        position=len(existing_options) + created_count,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(spec_option)
                    db.session.flush()  # 获取ID
                    existing_options[value] = spec_option
                    used_codes.add(code)
                    print(f"    + 创建指标: '{value}' (Code: {code}, ID: {spec_option.id})")
                else:
                    print(f"    + [将创建] 指标: '{value}' (Code: {code})")
                created_count += 1

        # 5. 更新 ProductCodeFieldOption 引用
        if not dry_run:
            for value, option_ids in value_to_options.items():
                spec_option = existing_options.get(value)
                if spec_option:
                    for opt_id in option_ids:
                        field_option = ProductCodeFieldOption.query.get(opt_id)
                        if field_option and not field_option.spec_option_id:
                            field_option.spec_option_id = spec_option.id
                            updated_count += 1
                            print(f"    → 更新引用: FieldOption {opt_id} → SpecOption {spec_option.id}")

    if not dry_run:
        db.session.commit()
        print("\n" + "=" * 60)
        print("迁移完成！")
        print(f"  - 创建 {created_count} 个 SpecificationOption")
        print(f"  - 更新 {updated_count} 个 ProductCodeFieldOption 引用")
        print(f"  - 跳过 {skipped_count} 个未在字典中的规格")
    else:
        print("\n" + "=" * 60)
        print("试运行完成！")
        print(f"  - 将创建 {created_count} 个 SpecificationOption")
        print(f"  - 跳过 {skipped_count} 个未在字典中的规格")


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv

    app = create_app()
    with app.app_context():
        migrate_to_spec_options(dry_run=dry_run)
