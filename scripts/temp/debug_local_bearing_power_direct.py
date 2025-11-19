#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接连接本地数据库诊断"频率范围"指标数据
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
print("诊断：本地数据库 - 频率范围指标数据")
print("=" * 80)
print()

with engine.connect() as conn:
    # 1. 查找"频率范围"字段配置
    print("【步骤1】查找'频率范围'规格字段配置")
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
        LIMIT 1
    """))

    field_row = result.fetchone()

    if not field_row:
        print("❌ 未找到'频率范围'字段配置")
        print("\n尝试查找包含'频率'的字段：")

        result = conn.execute(text("""
            SELECT
                pcf.id,
                pcf.name,
                pcf.subcategory_id,
                ps.name as product_name
            FROM product_code_fields pcf
            LEFT JOIN product_subcategories ps ON pcf.subcategory_id = ps.id
            WHERE pcf.name LIKE '%频率%'
              AND pcf.field_type = 'spec'
            ORDER BY pcf.name
        """))

        similar_fields = result.fetchall()
        if similar_fields:
            for row in similar_fields:
                print(f"  - ID: {row[0]}, 名称: '{row[1]}', 产品: {row[3] or 'N/A'}")
        else:
            print("  未找到任何包含'频率'的规格字段")

        exit(1)

    field_id = field_row[0]
    field_name = field_row[1]
    product_name = field_row[3]

    print(f"✅ 找到字段配置:")
    print(f"  字段ID: {field_id}")
    print(f"  字段名称: '{field_name}'")
    print(f"  所属产品: {product_name or 'N/A'}")
    print(f"  产品ID: {field_row[2]}")

    # 2. 查找预定义选项
    print(f"\n【步骤2】查找预定义选项值")
    print("-" * 80)

    result = conn.execute(text("""
        SELECT id, value, code, is_active
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
                print(f"  [{active_mark}] {opt_value} (编码: {opt[2]}, ID: {opt[0]})")
    else:
        print("  ⚠️ (无预定义选项) - 这可能是问题所在！")

    print(f"\n预定义值集合: {predefined_values}")

    # 3. 查找DevProductSpec中的数据
    print(f"\n【步骤3】查找DevProductSpec表中的'频率范围'数据")
    print("-" * 80)

    result = conn.execute(text("""
        SELECT
            dps.id,
            dps.dev_product_id,
            dps.field_value,
            dp.name as product_name,
            dp.subcategory_id
        FROM dev_product_specs dps
        LEFT JOIN dev_products dp ON dps.dev_product_id = dp.id
        WHERE dps.field_name = :field_name
        ORDER BY dp.name, dps.field_value
    """), {"field_name": field_name})

    dev_specs = result.fetchall()
    dev_values = set()
    dev_products_map = {}

    print(f"DevProductSpec记录数: {len(dev_specs)}")

    if dev_specs:
        print("\nDevProductSpec数据详情:")
        for spec in dev_specs:
            spec_id, dev_product_id, field_value, product_name, subcategory_id = spec

            if field_value and field_value.strip():
                dev_values.add(field_value.strip())

                if product_name not in dev_products_map:
                    dev_products_map[product_name] = set()
                dev_products_map[product_name].add(field_value.strip())

                print(f"  产品: {product_name or '未知'}")
                print(f"    值: {field_value}")
                print(f"    产品ID: {dev_product_id}")
                print(f"    子分类ID: {subcategory_id}")
                print()
    else:
        print("  (无数据)")

    print(f"DevProductSpec值集合: {dev_values}")
    print(f"涉及产品数量: {len(dev_products_map)}")
    if dev_products_map:
        print("按产品分组:")
        for pname, values in dev_products_map.items():
            print(f"  - {pname}: {values}")

    # 4. 查找ProductSpec中的数据
    print(f"\n【步骤4】查找ProductSpec表中的'频率范围'数据")
    print("-" * 80)

    product_values = set()
    products_map = {}

    try:
        # 先尝试简化查询，只查product_specs表
        result = conn.execute(text("""
            SELECT
                id,
                product_id,
                field_value
            FROM product_specs
            WHERE field_name = :field_name
        """), {"field_name": field_name})

        product_specs = result.fetchall()

        print(f"ProductSpec记录数: {len(product_specs)}")

        if product_specs:
            print("\nProductSpec数据详情:")
            for spec in product_specs:
                spec_id, product_id, field_value = spec

                if field_value and field_value.strip():
                    product_values.add(field_value.strip())

                    product_key = f"产品ID:{product_id}"
                    if product_key not in products_map:
                        products_map[product_key] = set()
                    products_map[product_key].add(field_value.strip())

                    print(f"  产品ID: {product_id}")
                    print(f"    值: {field_value}")
                    print()
        else:
            print("  (无数据)")

        print(f"ProductSpec值集合: {product_values}")
        print(f"涉及产品数量: {len(products_map)}")
        if products_map:
            print("按产品分组:")
            for pname, values in products_map.items():
                print(f"  - {pname}: {values}")
    except Exception as e:
        print(f"⚠️ 查询ProductSpec失败（可能表结构不同）: {str(e)[:100]}")
        print("  跳过ProductSpec表查询")

    # 5. 诊断结论
    print(f"\n【诊断结论】")
    print("=" * 80)

    if len(predefined_options) == 0:
        print("❌ 问题确认：本地数据库没有预定义指标选项！")
        print("\n原因分析:")
        print("  🔴 根本原因：ProductCodeFieldOption表中没有'频率范围'的预定义选项")
        print(f"     → 字段ID: {field_id}")
        print(f"     → 预定义选项数量: 0")
        print("\n这就是为什么前端不显示指标选项的原因！")
        print("\n解决方案：")
        print("  方案1：在规格管理页面为'频率范围'字段手动添加预定义指标选项")
        print("         （例如：800-960MHz、1710-2170MHz等）")
        print("  方案2：从云端数据库同步预定义选项数据（如果云端有配置）")
        print("  方案3：执行SQL直接插入预定义选项（快速修复）")
    else:
        print("✅ 预定义选项存在")
        print(f"\n预定义选项: {predefined_values}")
        print(f"数量: {len(predefined_options)}")

        # 检查是否有不活跃的选项
        inactive_options = [opt for opt in predefined_options if not opt[3]]
        if inactive_options:
            print(f"\n⚠️ 注意：有 {len(inactive_options)} 个不活跃的选项")
            for opt in inactive_options:
                print(f"   - {opt[1]} (ID: {opt[0]})")
            print("   如果API设置了 include_inactive=false，这些选项不会显示")

        print("\n如果前端仍然不显示，请检查：")
        print("  1. API参数是否正确传递（field_id、include_inactive等）")
        print("  2. 浏览器Network标签中的实际API响应")
        print("  3. JavaScript控制台是否有错误")
        print("  4. fields.html 第408-409行是否注释了 include_product_values 参数")

    # 6. 对比云端和本地差异
    print(f"\n【云端vs本地对比】")
    print("-" * 80)
    print("云端SP8D数据库：")
    print("  - '频率范围' 预定义选项: （待查询）")
    print(f"\n本地数据库：")
    print(f"  - '频率范围' 预定义选项: {len(predefined_options)}个")
    if predefined_options:
        print(f"  - 选项值: {', '.join(sorted(predefined_values))}")
    else:
        print("  - ⚠️ 本地没有预定义选项，需要添加！")
        print("\n建议：在规格管理页面手动添加预定义选项")

    print("\n" + "=" * 80)
    print("诊断完成！")
    print("=" * 80)
