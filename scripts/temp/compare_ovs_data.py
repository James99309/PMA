#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比OVS数据库迁移前后的数据完整性
检查各表的记录数量是否有缺失
"""
import psycopg2

# 注意：这是SP8D数据库配置（中文数据）
# OVS数据库应使用: postgres.pqzviljbpfoqvyfulakl / nyjrIc-gubcu4-rukhoc
SP8D_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.iqcyimnjtnmomvfuwjzw',
    'password': 'towsys-coGdoq-6gofdi',
    'sslmode': 'require'
}

# 迁移前的数据备份（从之前的备份或预期值）
EXPECTED_MIN_COUNTS = {
    'users': 10,
    'companies': 100,
    'products': 50,
    'projects': 10,
    'quotations': 100,
    'quotation_details': 200,
    'settlement_orders': 10,
    'expenses': 5,
    'expense_details': 5,
}


def run_query(cursor, sql):
    """安全执行查询，出错时回滚"""
    try:
        cursor.execute(sql)
        return cursor.fetchone()[0]
    except Exception as e:
        cursor.connection.rollback()
        return f"Error: {str(e)[:50]}"


def main():
    print("="*70)
    print("OVS 数据库数据完整性检查")
    print("="*70)

    conn = psycopg2.connect(**OVS_DB_CONFIG)
    conn.autocommit = True  # 使用自动提交避免事务问题
    cursor = conn.cursor()

    # 1. 获取所有表的记录数
    print("\n1. 各表记录数统计")
    print("-"*70)

    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
          AND table_name NOT LIKE 'pg_%'
          AND table_name NOT IN ('alembic_version', 'spatial_ref_sys')
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    table_counts = {}
    for table in tables:
        result = run_query(cursor, f"SELECT COUNT(*) FROM {table}")
        table_counts[table] = result if isinstance(result, int) else 0

    # 按记录数排序显示
    sorted_tables = sorted(table_counts.items(), key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True)

    print(f"\n{'表名':<40} {'记录数':>10}")
    print("-"*52)
    for table, count in sorted_tables:
        if isinstance(count, int) and count > 0:
            print(f"{table:<40} {count:>10}")

    # 2. 检查核心业务表数据量
    print("\n" + "="*70)
    print("2. 核心业务表数据量检查")
    print("-"*70)

    issues = []
    for table, min_count in EXPECTED_MIN_COUNTS.items():
        actual = table_counts.get(table, 0)
        if isinstance(actual, int):
            status = "✅" if actual >= min_count else "⚠️"
            if actual < min_count:
                issues.append(f"{table}: 实际 {actual} < 预期最小值 {min_count}")
            print(f"  {status} {table}: {actual} 条 (预期 >= {min_count})")

    # 3. 检查关键外键关系完整性
    print("\n" + "="*70)
    print("3. 关键数据关系完整性检查")
    print("-"*70)

    # 先检查quotation_details的列结构
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'quotation_details'
        ORDER BY ordinal_position
    """)
    qd_columns = [row[0] for row in cursor.fetchall()]
    print(f"  quotation_details 列: {', '.join(qd_columns[:10])}...")

    relation_checks = [
        ("报价明细引用的报价单是否存在",
         "SELECT COUNT(*) FROM quotation_details qd LEFT JOIN quotations q ON qd.quotation_id = q.id WHERE q.id IS NULL"),
        ("报价单引用的客户是否存在",
         "SELECT COUNT(*) FROM quotations q LEFT JOIN companies c ON q.customer_id = c.id WHERE c.id IS NULL"),
        ("项目引用的客户是否存在",
         "SELECT COUNT(*) FROM projects p LEFT JOIN companies c ON p.customer_id = c.id WHERE p.customer_id IS NOT NULL AND c.id IS NULL"),
        ("报销明细引用的报销单是否存在",
         "SELECT COUNT(*) FROM expense_details ed LEFT JOIN expenses e ON ed.expense_id = e.id WHERE e.id IS NULL"),
        ("结算单引用的报价单是否存在",
         "SELECT COUNT(*) FROM settlement_orders so LEFT JOIN quotations q ON so.quotation_id = q.id WHERE so.quotation_id IS NOT NULL AND q.id IS NULL"),
    ]

    for desc, sql in relation_checks:
        result = run_query(cursor, sql)
        if isinstance(result, int):
            status = "✅" if result == 0 else "❌"
            if result != 0:
                issues.append(f"{desc}: 发现 {result} 条孤立记录")
            print(f"  {status} {desc}: {result} 条孤立记录")
        else:
            print(f"  ⚠️ {desc}: {result}")

    # 4. 检查关键字段数据完整性
    print("\n" + "="*70)
    print("4. 关键字段数据完整性检查")
    print("-"*70)

    field_checks = [
        ("users.username 非空", "SELECT COUNT(*) FROM users WHERE username IS NULL OR username = ''"),
        ("users.email 非空", "SELECT COUNT(*) FROM users WHERE email IS NULL OR email = ''"),
        ("companies.name 非空", "SELECT COUNT(*) FROM companies WHERE name IS NULL OR name = ''"),
        ("products.name 非空", "SELECT COUNT(*) FROM products WHERE name IS NULL OR name = ''"),
        ("quotations.quotation_no 非空", "SELECT COUNT(*) FROM quotations WHERE quotation_no IS NULL OR quotation_no = ''"),
        ("quotation_details.quantity > 0", "SELECT COUNT(*) FROM quotation_details WHERE quantity IS NULL OR quantity <= 0"),
        ("quotation_details.unit_price >= 0", "SELECT COUNT(*) FROM quotation_details WHERE unit_price IS NULL OR unit_price < 0"),
    ]

    for desc, sql in field_checks:
        result = run_query(cursor, sql)
        if isinstance(result, int):
            status = "✅" if result == 0 else "⚠️"
            if result > 0:
                issues.append(f"{desc}: 发现 {result} 条异常记录")
            print(f"  {status} {desc}: {result} 条异常")
        else:
            print(f"  ⚠️ {desc}: {result}")

    # 5. 检查迁移影响的表数据
    print("\n" + "="*70)
    print("5. 迁移涉及表的数据检查")
    print("-"*70)

    migration_tables = [
        'product_relations',
        'specification_dictionary',
        'product_categories',
        'product_subcategories',
        'approval_branch_condition',
        'approval_record',
        'approval_step',
    ]

    for table in migration_tables:
        count = table_counts.get(table, 'N/A')
        print(f"  {table}: {count} 条")

    # 6. 检查约束修改影响的数据
    print("\n" + "="*70)
    print("6. 约束修改涉及表的数据验证")
    print("-"*70)

    constraint_checks = [
        ("quotations.customer_id 非空", "SELECT COUNT(*) FROM quotations WHERE customer_id IS NULL"),
        ("expense_details.currency 非空", "SELECT COUNT(*) FROM expense_details WHERE currency IS NULL"),
        ("expenses.currency 非空", "SELECT COUNT(*) FROM expenses WHERE currency IS NULL"),
        ("settlement_orders.currency 非空", "SELECT COUNT(*) FROM settlement_orders WHERE currency IS NULL"),
        ("product_categories.display_order 非空", "SELECT COUNT(*) FROM product_categories WHERE display_order IS NULL"),
        ("specification_dictionary.display_order 非空", "SELECT COUNT(*) FROM specification_dictionary WHERE display_order IS NULL"),
        ("product_relations.is_active 非空", "SELECT COUNT(*) FROM product_relations WHERE is_active IS NULL"),
        ("quotation_details.is_accessory 非空", "SELECT COUNT(*) FROM quotation_details WHERE is_accessory IS NULL"),
    ]

    for desc, sql in constraint_checks:
        result = run_query(cursor, sql)
        if isinstance(result, int):
            status = "✅" if result == 0 else "❌"
            print(f"  {status} {desc}: {result} 条NULL")
        else:
            print(f"  ⚠️ {desc}: {result}")

    # 7. 总结
    print("\n" + "="*70)
    print("检查结果总结")
    print("="*70)

    total_records = sum(c for c in table_counts.values() if isinstance(c, int))
    print(f"\n数据库总记录数: {total_records:,}")
    print(f"表总数: {len(tables)}")

    if issues:
        print(f"\n⚠️ 发现 {len(issues)} 个潜在问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 所有检查通过，数据完整性良好！")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
