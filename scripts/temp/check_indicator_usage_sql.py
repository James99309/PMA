#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查规格指标的使用情况（使用SQL直连）
判断是否可以安全删除编码为A的指标
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
env_file = os.path.join(os.path.dirname(__file__), '../../.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ 未找到DATABASE_URL环境变量")
    exit(1)

engine = create_engine(DATABASE_URL)

print("=" * 80)
print("检查规格指标的使用情况")
print("=" * 80)

with engine.connect() as conn:
    # 查找所有编码为"A"的规格指标
    result = conn.execute(text("""
        SELECT
            pcfo.id,
            pcfo.field_id,
            pcfo.value,
            pcfo.code,
            pcf.name as field_name,
            ps.name as product_name
        FROM product_code_field_options pcfo
        JOIN product_code_fields pcf ON pcfo.field_id = pcf.id
        LEFT JOIN product_subcategories ps ON pcf.subcategory_id = ps.id
        WHERE pcfo.code = 'A'
        ORDER BY pcfo.id
    """))

    a_coded_options = result.fetchall()

    print(f"\n找到 {len(a_coded_options)} 个编码为'A'的规格指标\n")

    if not a_coded_options:
        print("✅ 没有编码为'A'的指标，无需处理")
        exit(0)

    total_used = 0
    total_unused = 0
    usage_details = []

    for option in a_coded_options:
        option_id = option[0]
        field_id = option[1]
        value = option[2]
        code = option[3]
        field_name = option[4]
        product_name = option[5] or '未分配'

        # 检查是否被标准产品使用
        result_product = conn.execute(text("""
            SELECT COUNT(*)
            FROM product_specs
            WHERE field_name = :field_name
              AND field_value = :value
        """), {"field_name": field_name, "value": value})
        used_in_products = result_product.scalar()

        # 检查是否被研发产品使用
        result_dev = conn.execute(text("""
            SELECT COUNT(*)
            FROM dev_product_specs
            WHERE field_name = :field_name
              AND field_value = :value
        """), {"field_name": field_name, "value": value})
        used_in_dev_products = result_dev.scalar()

        total_usage = used_in_products + used_in_dev_products

        if total_usage > 0:
            total_used += 1
            status = f"❌ 已被使用 ({total_usage}次)"
            usage_details.append({
                'id': option_id,
                'product': product_name,
                'field': field_name,
                'value': value,
                'usage': total_usage
            })
        else:
            total_unused += 1
            status = f"✅ 未被使用"

        print(f"指标ID {option_id}: {product_name} - {field_name}")
        print(f"  值: {value}")
        print(f"  编码: {code}")
        print(f"  状态: {status}")
        print()

    print("=" * 80)
    print("统计汇总")
    print("=" * 80)
    print(f"编码为'A'的指标总数: {len(a_coded_options)}")
    print(f"  已被使用: {total_used} 个 ❌")
    print(f"  未被使用: {total_unused} 个 ✅")

    if total_used > 0:
        print("\n已被使用的指标详情:")
        for detail in usage_details:
            print(f"  ID {detail['id']}: {detail['product']} - {detail['field']} = {detail['value']} (使用{detail['usage']}次)")

    print("\n" + "=" * 80)
    print("建议")
    print("=" * 80)

    if total_used > 0:
        print("⚠️  发现已被使用的指标！")
        print("\n推荐方案：")
        print("  ✅ 【保留现有指标】 - 不删除已有指标，避免影响现有产品")
        print("  ✅ 【新增指标自动优化】 - 修复后的代码会为新指标分配随机编码")
        print("  ✅ 【逐步优化】 - 未来新增产品会有更好的编码区分度")
        print("\n如果坚持要重新编码：")
        print("  1. 导出所有相关产品数据")
        print("  2. 删除指标并重新创建")
        print("  3. 手动更新所有产品的MN编码和规格记录")
        print("  4. 验证产品编码快照的一致性")
        print("  ⚠️  风险很高，不建议！")
    else:
        print("✅ 所有编码为'A'的指标都未被使用")
        print("\n可以安全执行以下操作：")
        print("  1. 删除这些未使用的指标")
        print("  2. 重新添加时会自动分配随机编码")
        print("  3. 获得更好的编码区分度")
        print("\n生成删除SQL（需确认后执行）：")
        option_ids = [str(opt[0]) for opt in a_coded_options]
        print(f"  DELETE FROM product_code_field_options WHERE code='A' AND id IN ({','.join(option_ids)});")

    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)
