#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接连接云端SP8D数据库诊断"承载功率"指标数据
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载云端数据库配置
env_file = os.path.join(os.path.dirname(__file__), '../../.env.supabase.prod')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ 已加载配置文件: {env_file}")
else:
    print(f"❌ 配置文件不存在: {env_file}")
    exit(1)

# 获取云端数据库URL
# 云端SP8D数据库连接信息
DATABASE_URL = os.getenv('DATABASE_URL')

# 如果没有设置DATABASE_URL，使用云端SP8D数据库的默认配置
if not DATABASE_URL:
    print("⚠️ 未找到DATABASE_URL环境变量，使用云端SP8D数据库默认配置")
    DB_HOST = 'aws-0-ap-southeast-1.pooler.supabase.com'
    DB_PORT = '6543'
    DB_NAME = 'postgres'
    DB_USER = 'postgres.iqcyimnjtnmomvfuwjzw'
    DB_PASSWORD = 'towsys-coGdoq-6gofdi'
    DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'

print(f"数据库HOST: {DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else 'unknown'}")
print(f"数据库URL: {DATABASE_URL[:50]}...")

# 创建数据库连接
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("诊断：云端SP8D数据库 - 承载功率指标数据")
print("=" * 80)
print()

with engine.connect() as conn:
    # 1. 查找"承载功率"字段配置
    print("【步骤1】查找'承载功率'规格字段配置")
    print("-" * 80)

    result = conn.execute(text("""
        SELECT
            pcf.id,
            pcf.name,
            pcf.subcategory_id,
            ps.name as product_name
        FROM product_code_fields pcf
        LEFT JOIN product_subcategories ps ON pcf.subcategory_id = ps.id
        WHERE pcf.name = '承载功率'
          AND pcf.field_type = 'spec'
        LIMIT 1
    """))

    field_row = result.fetchone()

    if not field_row:
        print("❌ 未找到'承载功率'字段配置")
        print("\n尝试查找包含'功率'的字段：")

        result = conn.execute(text("""
            SELECT
                pcf.id,
                pcf.name,
                pcf.subcategory_id,
                ps.name as product_name
            FROM product_code_fields pcf
            LEFT JOIN product_subcategories ps ON pcf.subcategory_id = ps.id
            WHERE pcf.name LIKE '%功率%'
              AND pcf.field_type = 'spec'
            ORDER BY pcf.name
        """))

        similar_fields = result.fetchall()
        if similar_fields:
            for row in similar_fields:
                print(f"  - ID: {row[0]}, 名称: '{row[1]}', 产品: {row[3] or 'N/A'}")
        else:
            print("  未找到任何包含'功率'的规格字段")

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
        print("  (无预定义选项)")

    print(f"\n预定义值集合: {predefined_values}")

    # 3. 查找DevProductSpec中的数据
    print(f"\n【步骤3】查找DevProductSpec表中的'承载功率'数据")
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
    print(f"\n【步骤4】查找ProductSpec表中的'承载功率'数据")
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

    # 5. 模拟API逻辑
    print(f"\n【步骤5】模拟API排除逻辑")
    print("=" * 80)

    # 合并所有产品值
    all_product_values = dev_values | product_values
    print(f"合并后的所有产品值: {all_product_values}")
    print(f"数量: {len(all_product_values)}")

    # 排除预定义值
    product_only_values = all_product_values - predefined_values
    print(f"\n排除预定义值后: {product_only_values}")
    print(f"数量: {len(product_only_values)}")

    # 6. 诊断结论
    print(f"\n【诊断结论】")
    print("=" * 80)

    if len(product_only_values) == 0:
        print("❌ 问题确认：API会返回空列表")
        print("\n原因分析:")

        if len(all_product_values) == 0:
            print("  🔴 根本原因：数据库中没有任何产品使用'承载功率'规格")
            print("     → DevProductSpec表: 0条记录")
            print("     → ProductSpec表: 0条记录")
            print("\n  解决方案：")
            print("     1. 确认产品数据是否正确保存")
            print("     2. 检查保存产品时的规格数据写入逻辑")
            print("     3. 手动添加测试数据验证")
        elif len(all_product_values) > 0 and len(predefined_values) == 0:
            print("  🟡 原因：有产品数据，但没有预定义选项")
            print(f"     → 产品使用值: {all_product_values}")
            print("     → 预定义选项: 0个")
            print("\n  ⚠️ 这种情况不应该返回空列表！可能是代码逻辑问题")
        else:
            print("  🟠 原因：所有产品使用值都已在预定义选项池中")
            print(f"     → 产品使用值: {all_product_values}")
            print(f"     → 预定义选项: {predefined_values}")
            print(f"     → 差集: {product_only_values} (空)")
            print("\n  这是设计逻辑问题：")
            print("     当前逻辑：只显示'产品独有'的值（不在预定义中的）")
            print("     用户期望：显示'所有产品使用过'的值")
            print("\n  解决方案：")
            print("     方案A：修改API，不排除预定义值")
            print("     方案B：添加参数控制是否排除预定义值")
            print("     方案C：前端显示时区分[预定义]和[产品值]")
    else:
        print("✅ API应该返回非空列表")
        print(f"\n预期返回值: {product_only_values}")
        print(f"数量: {len(product_only_values)}")

    print("\n" + "=" * 80)
    print("诊断完成！")
    print("=" * 80)
