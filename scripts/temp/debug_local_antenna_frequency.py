#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断本地数据库 - 室内全向吸顶天线的频率范围字段配置
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
print("诊断：室内全向吸顶天线 - 频率范围字段配置")
print("=" * 80)
print()

with engine.connect() as conn:
    # 1. 查找"室内全向吸顶天线"产品分类
    print("【步骤1】查找'室内全向吸顶天线'产品分类")
    print("-" * 80)

    result = conn.execute(text("""
        SELECT id, name, category_id
        FROM product_subcategories
        WHERE name LIKE '%室内全向吸顶天线%'
        LIMIT 5
    """))

    subcategories = result.fetchall()

    if not subcategories:
        print("❌ 未找到'室内全向吸顶天线'产品分类")

        # 尝试查找所有天线类产品
        print("\n尝试查找包含'天线'的产品分类：")
        result = conn.execute(text("""
            SELECT id, name, category_id
            FROM product_subcategories
            WHERE name LIKE '%天线%'
            ORDER BY name
            LIMIT 10
        """))

        antenna_products = result.fetchall()
        if antenna_products:
            for row in antenna_products:
                print(f"  - ID: {row[0]}, 名称: '{row[1]}'")
        exit(1)

    print(f"找到 {len(subcategories)} 个相关产品分类:")
    for sub in subcategories:
        print(f"  - ID: {sub[0]}, 名称: '{sub[1]}'")

    # 使用第一个作为目标
    target_subcategory_id = subcategories[0][0]
    target_subcategory_name = subcategories[0][1]

    print(f"\n使用产品分类: {target_subcategory_name} (ID: {target_subcategory_id})")

    # 2. 查找该产品的"频率范围"字段配置
    print(f"\n【步骤2】查找该产品的'频率范围'字段配置")
    print("-" * 80)

    result = conn.execute(text("""
        SELECT
            id,
            name,
            field_type,
            subcategory_id
        FROM product_code_fields
        WHERE subcategory_id = :subcategory_id
          AND name = '频率范围'
          AND field_type = 'spec'
        LIMIT 1
    """), {"subcategory_id": target_subcategory_id})

    field_row = result.fetchone()

    if not field_row:
        print(f"❌ 该产品分类下没有'频率范围'字段配置")

        # 查找该产品的所有规格字段
        print(f"\n查找该产品的所有规格字段：")
        result = conn.execute(text("""
            SELECT id, name, field_type
            FROM product_code_fields
            WHERE subcategory_id = :subcategory_id
              AND field_type = 'spec'
            ORDER BY position
        """), {"subcategory_id": target_subcategory_id})

        all_fields = result.fetchall()
        if all_fields:
            for f in all_fields:
                print(f"  - ID: {f[0]}, 名称: '{f[1]}', 类型: {f[2]}")
        else:
            print("  该产品没有任何规格字段配置")
        exit(1)

    field_id = field_row[0]
    field_name = field_row[1]

    print(f"✅ 找到字段配置:")
    print(f"  字段ID: {field_id}")
    print(f"  字段名称: '{field_name}'")
    print(f"  产品分类: {target_subcategory_name}")
    print(f"  产品分类ID: {target_subcategory_id}")

    # 3. 查找预定义选项
    print(f"\n【步骤3】查找预定义选项值")
    print("-" * 80)

    result = conn.execute(text("""
        SELECT id, value, code, is_active, position
        FROM product_code_field_options
        WHERE field_id = :field_id
        ORDER BY position
    """), {"field_id": field_id})

    predefined_options = result.fetchall()
    predefined_values = set()

    print(f"预定义选项数量: {len(predefined_options)}")
    if predefined_options:
        print("预定义选项列表:")
        for opt in predefined_options:
            opt_value = opt[1]
            if opt_value and opt_value.strip():
                predefined_values.add(opt_value.strip())
                active_mark = "✓" if opt[3] else "✗"
                print(f"  [{active_mark}] {opt_value} (编码: {opt[2]}, ID: {opt[0]}, 位置: {opt[4]})")
    else:
        print("  ⚠️ (无预定义选项) - 这就是问题所在！")

    print(f"\n预定义值集合: {predefined_values}")

    # 4. 查找该产品已使用的频率范围值
    print(f"\n【步骤4】查找'{target_subcategory_name}'已使用的'频率范围'值")
    print("-" * 80)

    # 从DevProduct查找该分类的产品
    result = conn.execute(text("""
        SELECT
            dp.id,
            dp.name,
            dps.field_value
        FROM dev_products dp
        LEFT JOIN dev_product_specs dps ON dp.id = dps.dev_product_id
        WHERE dp.subcategory_id = :subcategory_id
          AND dps.field_name = '频率范围'
        ORDER BY dp.name
    """), {"subcategory_id": target_subcategory_id})

    dev_products_with_freq = result.fetchall()

    if dev_products_with_freq:
        print(f"找到 {len(dev_products_with_freq)} 条研发产品记录:")
        for row in dev_products_with_freq:
            print(f"  - 产品: {row[1]}, 频率范围: {row[2]}")
    else:
        print("  该产品分类下没有研发产品使用'频率范围'规格")

    # 5. 诊断结论
    print(f"\n【诊断结论】")
    print("=" * 80)

    if len(predefined_options) == 0:
        print("❌ 问题确认：该产品的'频率范围'字段没有预定义选项！")
        print("\n原因分析:")
        print(f"  🔴 ProductCodeFieldOption表中字段ID {field_id} 没有预定义选项")
        print(f"  🔴 这就是为什么添加指标时看不到可选项的原因")
        print("\n解决方案：")
        print(f"  1. 在规格管理页面为字段ID {field_id} 添加预定义选项")
        print("  2. 添加常用的频率范围选项（如：120 MHz, 350-470 MHz等）")
        print("  3. 添加完成后，刷新页面即可在添加指标时看到选项")
    else:
        print("✅ 预定义选项存在")
        print(f"\n预定义选项列表:")
        for val in sorted(predefined_values):
            print(f"  - {val}")

        print("\n这些选项应该在添加指标时显示")
        print("如果前端仍然不显示，请检查：")
        print("  1. 确认field_id参数传递正确")
        print(f"     → 应该传递: field_id={field_id}")
        print("  2. 确认已注释 include_product_values 参数")
        print("  3. 查看浏览器Network标签中的API响应")
        print("  4. 清除浏览器缓存并刷新页面")

    print("\n" + "=" * 80)
    print("诊断完成！")
    print("=" * 80)
