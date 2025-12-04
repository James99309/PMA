#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复SP8D中没有spec_option_id关联的product_code_field_options记录
将这些记录的value/code同步到specification_options中，并建立引用关系

注意：不会改变原有的value、code和position，只是建立引用关系
"""
import os
import sys

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
from app.models.product_code import (
    ProductCodeField, ProductCodeFieldOption,
    SpecificationDictionary, SpecificationOption
)

def fix_orphan_options():
    """修复没有spec_option_id的记录"""
    print("=" * 60)
    print("修复SP8D product_code_field_options 孤立记录")
    print("=" * 60)

    # 查找所有没有spec_option_id的记录（且field_type='spec'）
    orphan_options = db.session.query(ProductCodeFieldOption).join(
        ProductCodeField, ProductCodeFieldOption.field_id == ProductCodeField.id
    ).filter(
        ProductCodeFieldOption.spec_option_id.is_(None),
        ProductCodeFieldOption.value.isnot(None),
        ProductCodeField.field_type == 'spec'
    ).all()

    print(f"\n找到 {len(orphan_options)} 条孤立记录\n")

    if not orphan_options:
        print("✅ 没有需要修复的记录")
        return

    fixed_count = 0
    error_count = 0

    for option in orphan_options:
        field = ProductCodeField.query.get(option.field_id)
        if not field:
            print(f"  ❌ 找不到字段 ID={option.field_id}")
            error_count += 1
            continue

        print(f"\n处理: {field.name} = {option.value} (code={option.code})")

        # 查找对应的规格字典
        spec_dict = SpecificationDictionary.query.filter_by(name=field.name).first()
        if not spec_dict:
            print(f"  ❌ 规格 '{field.name}' 不在规格字典中")
            error_count += 1
            continue

        # 检查specification_options中是否已有该值
        existing_spec_option = SpecificationOption.query.filter_by(
            spec_id=spec_dict.id,
            value=option.value
        ).first()

        if existing_spec_option:
            # 已存在，直接引用
            print(f"  → 规格字典中已存在，直接引用 (ID={existing_spec_option.id})")
            option.spec_option_id = existing_spec_option.id
        else:
            # 不存在，需要创建
            # 获取当前最大position
            max_position = db.session.query(db.func.max(SpecificationOption.position))\
                .filter_by(spec_id=spec_dict.id).scalar() or 0

            new_spec_option = SpecificationOption(
                spec_id=spec_dict.id,
                value=option.value,
                code=option.code,
                is_active=True,
                position=max_position + 1
            )
            db.session.add(new_spec_option)
            db.session.flush()

            print(f"  → 在规格字典中创建新指标 (ID={new_spec_option.id}, code={option.code})")
            option.spec_option_id = new_spec_option.id

        fixed_count += 1

    # 提交事务
    db.session.commit()

    print("\n" + "=" * 60)
    print("修复结果:")
    print(f"  成功: {fixed_count}")
    print(f"  失败: {error_count}")
    print("=" * 60)

    # 验证
    remaining = db.session.query(ProductCodeFieldOption).join(
        ProductCodeField, ProductCodeFieldOption.field_id == ProductCodeField.id
    ).filter(
        ProductCodeFieldOption.spec_option_id.is_(None),
        ProductCodeFieldOption.value.isnot(None),
        ProductCodeField.field_type == 'spec'
    ).count()

    print(f"\n剩余孤立记录: {remaining}")
    if remaining == 0:
        print("🎉 所有记录已修复！")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        fix_orphan_options()
