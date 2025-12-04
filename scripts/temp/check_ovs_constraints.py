#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查OVS关键约束状态
"""
import psycopg2

# 正确的OVS数据库配置（根据CLAUDE-DATABASE.md）
OVS_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.pqzviljbpfoqvyfulakl',
    'password': 'nyjrIc-gubcu4-rukhoc',
    'sslmode': 'require'
}

def main():
    print("="*60)
    print("OVS 关键约束状态检查")
    print("="*60)

    conn = psycopg2.connect(**OVS_DB_CONFIG)
    cursor = conn.cursor()

    # 检查nullable约束修复
    print("\n1. 检查 nullable 约束")
    print("-"*40)

    nullable_checks = [
        # 应该允许NULL的
        ("companies", "share_enabled", "YES"),
        ("dev_products", "currency", "YES"),
        ("permissions", "permission_level", "YES"),
        ("quotations", "currency", "YES"),
        # 应该不允许NULL的
        ("expense_details", "currency", "NO"),
        ("expense_details", "exchange_rate", "NO"),
        ("expenses", "currency", "NO"),
        ("product_categories", "display_order", "NO"),
        ("product_relations", "default_quantity", "NO"),
        ("product_relations", "is_active", "NO"),
        ("quotation_details", "quantity_synced", "NO"),
        ("quotations", "customer_id", "NO"),
        ("settlement_orders", "currency", "NO"),
        ("specification_dictionary", "display_order", "NO"),
    ]

    all_ok = True
    for table, column, expected in nullable_checks:
        cursor.execute("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, (table, column))
        result = cursor.fetchone()
        if result:
            actual = result[0]
            status = "✅" if actual == expected else "❌"
            if actual != expected:
                all_ok = False
            print(f"  {status} {table}.{column}: {actual} (期望: {expected})")

    # 检查default约束修复
    print("\n2. 检查 default 值约束")
    print("-"*40)

    default_checks = [
        ("companies", "share_enabled", "false"),
        ("approval_record", "status", "'approved'"),
        ("expenses", "total_amount", "0.0"),
        ("expenses", "is_locked", "false"),
        ("product_specs", "include_in_description", "true"),
        ("projects", "share_enabled", "false"),
        ("settlement_orders", "settlement_status", "'pending'"),
        ("stage_dependencies", "lag_days", "0"),
    ]

    for table, column, expected_part in default_checks:
        cursor.execute("""
            SELECT column_default
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, (table, column))
        result = cursor.fetchone()
        if result:
            actual = result[0] or "None"
            has_expected = expected_part in str(actual) if actual != "None" else False
            status = "✅" if has_expected else "❌"
            if not has_expected:
                all_ok = False
            print(f"  {status} {table}.{column}: {actual[:50] if actual else 'None'}")

    # 检查数据完整性
    print("\n3. 检查数据完整性（关键字段无NULL）")
    print("-"*40)

    data_checks = [
        ("quotations", "customer_id"),
        ("expense_details", "currency"),
        ("expenses", "currency"),
        ("settlement_orders", "currency"),
    ]

    for table, column in data_checks:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
        null_count = cursor.fetchone()[0]
        status = "✅" if null_count == 0 else "❌"
        print(f"  {status} {table}.{column}: {null_count} 个NULL值")
        if null_count > 0:
            all_ok = False

    print("\n" + "="*60)
    if all_ok:
        print("🎉 所有关键约束检查通过！")
    else:
        print("⚠️ 部分约束检查未通过，请检查上面的详细信息")
    print("="*60)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
