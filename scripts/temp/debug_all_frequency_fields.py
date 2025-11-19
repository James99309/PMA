#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断本地数据库 - 所有"频率范围"字段的预定义选项汇总
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载本地数据库配置
env_file = os.path.join(os.path.dirname(__file__), '../../.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ 已加载配置文件: {env_file}")
else:
    print(f"❌ 配置文件不存在: {env_file}")
    exit(1)

# 获取本地数据库URL
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("⚠️ 未找到DATABASE_URL环境变量")
    exit(1)

print(f"数据库HOST: {DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else 'unknown'}")
print(f"数据库URL: {DATABASE_URL[:50]}...")

# 创建数据库连接
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("诊断：所有产品的'频率范围'字段配置汇总")
print("=" * 80)
print()

with engine.connect() as conn:
    # 1. 查找所有名为"频率范围"的字段配置
    print("【步骤1】查找所有'频率范围'字段配置")
    print("-" * 80)

    result = conn.execute(text("""
        SELECT
            pcf.id,
            pcf.name,
            pcf.subcategory_id,
            ps.name as product_name
        FROM product_code_fields pcf
        LEFT JOIN product_subcategories ps ON pcf.subcategory_id = ps.id
        WHERE pcf.name = '频率范围'
          AND pcf.field_type = 'spec'
        ORDER BY pcf.id
    """))

    frequency_fields = result.fetchall()

    if not frequency_fields:
        print("❌ 未找到任何'频率范围'字段配置")
        exit(1)

    print(f"找到 {len(frequency_fields)} 个'频率范围'字段配置:")
    for field in frequency_fields:
        print(f"  - 字段ID: {field[0]}, 产品: {field[3] or '未分配'} (产品ID: {field[2]})")

    # 2. 汇总所有字段的预定义选项
    print(f"\n【步骤2】汇总所有字段的预定义选项")
    print("-" * 80)

    all_predefined_values = set()
    field_options_map = {}

    for field in frequency_fields:
        field_id = field[0]
        product_name = field[3] or '未分配'

        result = conn.execute(text("""
            SELECT id, value, code, is_active, position
            FROM product_code_field_options
            WHERE field_id = :field_id
            ORDER BY position
        """), {"field_id": field_id})

        options = result.fetchall()

        if options:
            field_options_map[field_id] = {
                'product_name': product_name,
                'options': []
            }

            for opt in options:
                opt_value = opt[1]
                if opt_value and opt_value.strip():
                    all_predefined_values.add(opt_value.strip())
                    field_options_map[field_id]['options'].append({
                        'value': opt_value,
                        'code': opt[2],
                        'is_active': opt[3],
                        'position': opt[4]
                    })

    print(f"总计去重后的预定义选项值: {len(all_predefined_values)}个")
    print("\n所有预定义选项值（去重）:")
    for val in sorted(all_predefined_values):
        print(f"  - {val}")

    print(f"\n按字段分组的预定义选项:")
    for field_id, data in field_options_map.items():
        print(f"\n  字段ID {field_id} ({data['product_name']}):")
        for opt in data['options']:
            active_mark = "✓" if opt['is_active'] else "✗"
            print(f"    [{active_mark}] {opt['value']} (编码: {opt['code']}, 位置: {opt['position']})")

    # 3. 检查是否有"通用"频率范围字段（subcategory_id为NULL）
    print(f"\n【步骤3】检查是否有通用字段")
    print("-" * 80)

    universal_fields = [f for f in frequency_fields if f[2] is None]

    if universal_fields:
        print(f"✅ 找到 {len(universal_fields)} 个通用'频率范围'字段（不限产品）:")
        for field in universal_fields:
            print(f"  - 字段ID: {field[0]}")
            if field[0] in field_options_map:
                print(f"    预定义选项数: {len(field_options_map[field[0]]['options'])}")
    else:
        print("❌ 没有通用字段，每个产品都有独立的'频率范围'字段")

    # 4. 查询产品实际使用的频率范围值
    print(f"\n【步骤4】查询所有产品实际使用的频率范围值")
    print("-" * 80)

    # DevProductSpec
    result = conn.execute(text("""
        SELECT DISTINCT field_value
        FROM dev_product_specs
        WHERE field_name = '频率范围'
          AND field_value IS NOT NULL
          AND field_value != ''
        ORDER BY field_value
    """))

    dev_values = set(row[0].strip() for row in result.fetchall() if row[0])

    # ProductSpec
    result = conn.execute(text("""
        SELECT DISTINCT field_value
        FROM product_specs
        WHERE field_name = '频率范围'
          AND field_value IS NOT NULL
          AND field_value != ''
        ORDER BY field_value
    """))

    product_values = set(row[0].strip() for row in result.fetchall() if row[0])

    all_usage_values = dev_values | product_values

    print(f"产品实际使用的频率范围值: {len(all_usage_values)}个")
    print("\n实际使用值列表:")
    for val in sorted(all_usage_values):
        in_predefined = "✓ 已预定义" if val in all_predefined_values else "✗ 未预定义"
        print(f"  - {val} ({in_predefined})")

    # 5. 对比分析
    print(f"\n【步骤5】对比分析")
    print("=" * 80)

    # 找出预定义但未使用的值
    predefined_not_used = all_predefined_values - all_usage_values
    # 找出使用了但未预定义的值
    used_not_predefined = all_usage_values - all_predefined_values

    print(f"预定义选项总数: {len(all_predefined_values)}")
    print(f"实际使用值总数: {len(all_usage_values)}")
    print(f"\n预定义但未使用的值: {len(predefined_not_used)}个")
    if predefined_not_used:
        for val in sorted(predefined_not_used):
            print(f"  - {val}")

    print(f"\n使用了但未预定义的值: {len(used_not_predefined)}个")
    if used_not_predefined:
        for val in sorted(used_not_predefined):
            print(f"  - {val}")

    # 6. 诊断结论
    print(f"\n【诊断结论】")
    print("=" * 80)

    print(f"✅ 本地数据库共有 {len(frequency_fields)} 个'频率范围'字段配置")
    print(f"✅ 预定义选项总计: {len(all_predefined_values)}个去重值")
    print(f"✅ 产品实际使用: {len(all_usage_values)}个去重值")

    print("\n关于添加指标时的显示逻辑：")
    print("  当前API设置（include_product_values已注释）：")
    print("    → 应该显示：对应字段的预定义选项")
    print("    → 不显示：产品实际使用值")

    print("\n可能的问题：")
    print("  1. 如果API传递的field_id不正确，可能返回错误字段的预定义选项")
    print("  2. 如果不同产品的'频率范围'字段ID不同，需确保传递正确的field_id")
    print("  3. 截图中显示的很多频率值可能是产品实际使用值，不是预定义选项")

    print("\n建议：")
    print("  - 确认API请求中的field_id参数")
    print("  - 检查该字段ID对应的预定义选项列表")
    print("  - 如需显示所有产品使用值，需启用include_product_values参数")

    print("\n" + "=" * 80)
    print("诊断完成！")
    print("=" * 80)
