#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS数据库约束同步脚本
根据本地数据库约束标准，同步OVS数据库的nullable和default约束

执行说明：
    python scripts/temp/sync_ovs_constraints.py

创建日期: 2025-12-03
"""
import os
import sys

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

PROJECT_ROOT = get_project_root()
sys.path.insert(0, PROJECT_ROOT)

import psycopg2
from psycopg2 import sql

# 正确的OVS数据库连接配置（根据CLAUDE-DATABASE.md）
OVS_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.pqzviljbpfoqvyfulakl',
    'password': 'nyjrIc-gubcu4-rukhoc',
    'sslmode': 'require'
}


def execute_sql(cursor, sql_statement, description):
    """执行SQL语句并打印结果"""
    try:
        cursor.execute(sql_statement)
        print(f"  ✅ {description}")
        return True
    except Exception as e:
        print(f"  ❌ {description}: {e}")
        return False


def fix_nullable_constraints(cursor):
    """修复nullable约束"""
    print("\n" + "="*60)
    print("1. 修复 nullable 约束")
    print("="*60)

    success_count = 0
    total_count = 0

    # ========================================
    # 1.1 DROP NOT NULL (本地允许NULL, OVS不允许)
    # ========================================
    print("\n--- 1.1 允许NULL (DROP NOT NULL) ---")

    drop_not_null_columns = [
        ('companies', 'share_enabled'),
        ('dev_products', 'currency'),
        ('permissions', 'permission_level'),
        ('product_code_field_options', 'code'),
        ('product_code_field_options', 'value'),
        ('product_code_fields', 'subcategory_id'),
        ('quotations', 'currency'),
    ]

    for table, column in drop_not_null_columns:
        total_count += 1
        if execute_sql(cursor,
                      f"ALTER TABLE {table} ALTER COLUMN {column} DROP NOT NULL",
                      f"{table}.{column} DROP NOT NULL"):
            success_count += 1

    # ========================================
    # 1.2 SET NOT NULL (本地不允许NULL, OVS允许)
    # ========================================
    print("\n--- 1.2 禁止NULL (SET NOT NULL) ---")

    # expense_details
    print("\n  [expense_details 表]")
    expense_detail_columns = [
        ('currency', "'CNY'"),
        ('exchange_rate', '1.0'),
        ('invoice_amount', '0'),
        ('current_amount', '0'),
    ]

    for column, default_value in expense_detail_columns:
        total_count += 1
        execute_sql(cursor,
                   f"UPDATE expense_details SET {column} = {default_value} WHERE {column} IS NULL",
                   f"填充 expense_details.{column} 空值")
        if execute_sql(cursor,
                      f"ALTER TABLE expense_details ALTER COLUMN {column} SET NOT NULL",
                      f"expense_details.{column} SET NOT NULL"):
            success_count += 1

    # expenses
    print("\n  [expenses 表]")
    total_count += 1
    execute_sql(cursor, "UPDATE expenses SET currency = 'CNY' WHERE currency IS NULL",
               "填充 expenses.currency 空值")
    if execute_sql(cursor, "ALTER TABLE expenses ALTER COLUMN currency SET NOT NULL",
                  "expenses.currency SET NOT NULL"):
        success_count += 1

    # product_categories
    print("\n  [product_categories 表]")
    total_count += 1
    execute_sql(cursor, "UPDATE product_categories SET display_order = id WHERE display_order IS NULL",
               "填充 product_categories.display_order 空值")
    if execute_sql(cursor, "ALTER TABLE product_categories ALTER COLUMN display_order SET NOT NULL",
                  "product_categories.display_order SET NOT NULL"):
        success_count += 1

    # product_relations
    print("\n  [product_relations 表]")
    pr_columns = [
        ('default_quantity', '1'),
        ('display_order', '0'),
        ('is_active', 'true'),
        ('is_required', 'false'),
    ]

    for column, default_value in pr_columns:
        total_count += 1
        execute_sql(cursor,
                   f"UPDATE product_relations SET {column} = {default_value} WHERE {column} IS NULL",
                   f"填充 product_relations.{column} 空值")
        if execute_sql(cursor,
                      f"ALTER TABLE product_relations ALTER COLUMN {column} SET NOT NULL",
                      f"product_relations.{column} SET NOT NULL"):
            success_count += 1

    total_count += 1
    execute_sql(cursor, "UPDATE product_relations SET created_at = NOW() WHERE created_at IS NULL",
               "填充 product_relations.created_at 空值")
    if execute_sql(cursor, "ALTER TABLE product_relations ALTER COLUMN created_at SET NOT NULL",
                  "product_relations.created_at SET NOT NULL"):
        success_count += 1

    # quotation_details
    print("\n  [quotation_details 表]")
    qd_columns = [
        ('quantity_synced', 'false'),
        ('is_editable', 'true'),
        ('is_accessory', 'false'),
    ]

    for column, default_value in qd_columns:
        total_count += 1
        execute_sql(cursor,
                   f"UPDATE quotation_details SET {column} = {default_value} WHERE {column} IS NULL",
                   f"填充 quotation_details.{column} 空值")
        if execute_sql(cursor,
                      f"ALTER TABLE quotation_details ALTER COLUMN {column} SET NOT NULL",
                      f"quotation_details.{column} SET NOT NULL"):
            success_count += 1

    # quotations
    print("\n  [quotations 表]")
    total_count += 1
    # 先检查是否有NULL的customer_id
    cursor.execute("SELECT COUNT(*) FROM quotations WHERE customer_id IS NULL")
    null_count = cursor.fetchone()[0]
    if null_count > 0:
        print(f"  ⚠️ 发现 {null_count} 条 quotations.customer_id 为 NULL")
        # 使用第一个有效的company_id
        cursor.execute("SELECT id FROM companies WHERE is_deleted = false LIMIT 1")
        result = cursor.fetchone()
        if result:
            execute_sql(cursor, f"UPDATE quotations SET customer_id = {result[0]} WHERE customer_id IS NULL",
                       f"填充 quotations.customer_id 空值为 {result[0]}")
    if execute_sql(cursor, "ALTER TABLE quotations ALTER COLUMN customer_id SET NOT NULL",
                  "quotations.customer_id SET NOT NULL"):
        success_count += 1

    # settlement_orders
    print("\n  [settlement_orders 表]")
    so_columns = [
        ('is_direct_contract', 'false'),
        ('is_factory_pickup', 'false'),
        ('currency', "'CNY'"),
    ]

    for column, default_value in so_columns:
        total_count += 1
        execute_sql(cursor,
                   f"UPDATE settlement_orders SET {column} = {default_value} WHERE {column} IS NULL",
                   f"填充 settlement_orders.{column} 空值")
        if execute_sql(cursor,
                      f"ALTER TABLE settlement_orders ALTER COLUMN {column} SET NOT NULL",
                      f"settlement_orders.{column} SET NOT NULL"):
            success_count += 1

    # specification_dictionary
    print("\n  [specification_dictionary 表]")
    total_count += 1
    execute_sql(cursor, "UPDATE specification_dictionary SET display_order = id WHERE display_order IS NULL",
               "填充 specification_dictionary.display_order 空值")
    if execute_sql(cursor, "ALTER TABLE specification_dictionary ALTER COLUMN display_order SET NOT NULL",
                  "specification_dictionary.display_order SET NOT NULL"):
        success_count += 1

    print(f"\n--- nullable 约束修复完成: {success_count}/{total_count} ---")
    return success_count, total_count


def fix_default_constraints(cursor):
    """修复default约束"""
    print("\n" + "="*60)
    print("2. 修复 default 值约束")
    print("="*60)

    success_count = 0
    total_count = 0

    # ========================================
    # 2.1 SET DEFAULT (本地有默认值, OVS没有)
    # ========================================
    print("\n--- 2.1 设置默认值 (SET DEFAULT) ---")

    set_default_sqls = [
        # approval_branch_condition
        ("ALTER TABLE approval_branch_condition ALTER COLUMN condition_order SET DEFAULT 0",
         "approval_branch_condition.condition_order DEFAULT 0"),
        ("ALTER TABLE approval_branch_condition ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP",
         "approval_branch_condition.created_at DEFAULT CURRENT_TIMESTAMP"),
        ("ALTER TABLE approval_branch_condition ALTER COLUMN approver_type SET DEFAULT 'user'",
         "approval_branch_condition.approver_type DEFAULT 'user'"),
        ("ALTER TABLE approval_branch_condition ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP",
         "approval_branch_condition.updated_at DEFAULT CURRENT_TIMESTAMP"),

        # approval_record
        ("ALTER TABLE approval_record ALTER COLUMN status SET DEFAULT 'approved'",
         "approval_record.status DEFAULT 'approved'"),

        # companies
        ("ALTER TABLE companies ALTER COLUMN share_enabled SET DEFAULT false",
         "companies.share_enabled DEFAULT false"),

        # dev_product_milestones
        ("ALTER TABLE dev_product_milestones ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP",
         "dev_product_milestones.created_at DEFAULT CURRENT_TIMESTAMP"),
        ("ALTER TABLE dev_product_milestones ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP",
         "dev_product_milestones.updated_at DEFAULT CURRENT_TIMESTAMP"),
        ("ALTER TABLE dev_product_milestones ALTER COLUMN status SET DEFAULT 'planned'",
         "dev_product_milestones.status DEFAULT 'planned'"),
        ("ALTER TABLE dev_product_milestones ALTER COLUMN priority SET DEFAULT 3",
         "dev_product_milestones.priority DEFAULT 3"),
        ("ALTER TABLE dev_product_milestones ALTER COLUMN progress SET DEFAULT 0",
         "dev_product_milestones.progress DEFAULT 0"),
        ("ALTER TABLE dev_product_milestones ALTER COLUMN order_index SET DEFAULT 0",
         "dev_product_milestones.order_index DEFAULT 0"),

        # expense_details
        ("ALTER TABLE expense_details ALTER COLUMN amount SET DEFAULT 0.0",
         "expense_details.amount DEFAULT 0.0"),

        # expenses
        ("ALTER TABLE expenses ALTER COLUMN total_amount SET DEFAULT 0.0",
         "expenses.total_amount DEFAULT 0.0"),
        ("ALTER TABLE expenses ALTER COLUMN is_locked SET DEFAULT false",
         "expenses.is_locked DEFAULT false"),

        # product_specs
        ("ALTER TABLE product_specs ALTER COLUMN include_in_description SET DEFAULT true",
         "product_specs.include_in_description DEFAULT true"),

        # projects
        ("ALTER TABLE projects ALTER COLUMN shared_with_users SET DEFAULT '[]'::json",
         "projects.shared_with_users DEFAULT '[]'::json"),
        ("ALTER TABLE projects ALTER COLUMN share_enabled SET DEFAULT false",
         "projects.share_enabled DEFAULT false"),

        # settlement_orders (修复多引号问题)
        ("ALTER TABLE settlement_orders ALTER COLUMN settlement_status SET DEFAULT 'pending'",
         "settlement_orders.settlement_status DEFAULT 'pending'"),

        # stage_attachments
        ("ALTER TABLE stage_attachments ALTER COLUMN uploaded_at SET DEFAULT CURRENT_TIMESTAMP",
         "stage_attachments.uploaded_at DEFAULT CURRENT_TIMESTAMP"),

        # stage_dependencies
        ("ALTER TABLE stage_dependencies ALTER COLUMN lag_days SET DEFAULT 0",
         "stage_dependencies.lag_days DEFAULT 0"),
        ("ALTER TABLE stage_dependencies ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP",
         "stage_dependencies.created_at DEFAULT CURRENT_TIMESTAMP"),
        ("ALTER TABLE stage_dependencies ALTER COLUMN dependency_type SET DEFAULT 'finish_to_start'",
         "stage_dependencies.dependency_type DEFAULT 'finish_to_start'"),

        # stage_reviews
        ("ALTER TABLE stage_reviews ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP",
         "stage_reviews.created_at DEFAULT CURRENT_TIMESTAMP"),
        ("ALTER TABLE stage_reviews ALTER COLUMN review_type SET DEFAULT 'stage_gate'",
         "stage_reviews.review_type DEFAULT 'stage_gate'"),
    ]

    for sql_stmt, desc in set_default_sqls:
        total_count += 1
        if execute_sql(cursor, sql_stmt, desc):
            success_count += 1

    # ========================================
    # 2.2 DROP DEFAULT (OVS有默认值, 本地没有)
    # ========================================
    print("\n--- 2.2 删除默认值 (DROP DEFAULT) ---")

    drop_default_sqls = [
        # approval_step
        ("ALTER TABLE approval_step ALTER COLUMN branch_group_id DROP DEFAULT",
         "approval_step.branch_group_id DROP DEFAULT"),
        ("ALTER TABLE approval_step ALTER COLUMN branch_path DROP DEFAULT",
         "approval_step.branch_path DROP DEFAULT"),

        # product_relations (本地没有这些默认值)
        ("ALTER TABLE product_relations ALTER COLUMN default_quantity DROP DEFAULT",
         "product_relations.default_quantity DROP DEFAULT"),
        ("ALTER TABLE product_relations ALTER COLUMN created_at DROP DEFAULT",
         "product_relations.created_at DROP DEFAULT"),
        ("ALTER TABLE product_relations ALTER COLUMN display_order DROP DEFAULT",
         "product_relations.display_order DROP DEFAULT"),
        ("ALTER TABLE product_relations ALTER COLUMN is_active DROP DEFAULT",
         "product_relations.is_active DROP DEFAULT"),
        ("ALTER TABLE product_relations ALTER COLUMN is_required DROP DEFAULT",
         "product_relations.is_required DROP DEFAULT"),

        # specification_dictionary
        ("ALTER TABLE specification_dictionary ALTER COLUMN created_at DROP DEFAULT",
         "specification_dictionary.created_at DROP DEFAULT"),
        ("ALTER TABLE specification_dictionary ALTER COLUMN display_order DROP DEFAULT",
         "specification_dictionary.display_order DROP DEFAULT"),
        ("ALTER TABLE specification_dictionary ALTER COLUMN is_active DROP DEFAULT",
         "specification_dictionary.is_active DROP DEFAULT"),
    ]

    for sql_stmt, desc in drop_default_sqls:
        total_count += 1
        if execute_sql(cursor, sql_stmt, desc):
            success_count += 1

    print(f"\n--- default 值约束修复完成: {success_count}/{total_count} ---")
    return success_count, total_count


def main():
    print("="*60)
    print("OVS 数据库约束同步脚本")
    print("="*60)
    print(f"\n目标数据库: {OVS_DB_CONFIG['host']}")

    try:
        # 连接数据库
        print("\n连接OVS数据库...")
        conn = psycopg2.connect(**OVS_DB_CONFIG)
        conn.autocommit = False  # 使用事务
        cursor = conn.cursor()
        print("✅ 连接成功")

        # 修复nullable约束
        null_success, null_total = fix_nullable_constraints(cursor)

        # 修复default约束
        default_success, default_total = fix_default_constraints(cursor)

        # 统计结果
        total_success = null_success + default_success
        total_count = null_total + default_total

        print("\n" + "="*60)
        print("执行结果汇总")
        print("="*60)
        print(f"  nullable 约束: {null_success}/{null_total}")
        print(f"  default 约束:  {default_success}/{default_total}")
        print(f"  总计:          {total_success}/{total_count}")

        if total_success == total_count:
            print("\n✅ 所有约束修复成功！正在提交事务...")
            conn.commit()
            print("✅ 事务已提交")
        else:
            print(f"\n⚠️ 有 {total_count - total_success} 个约束修复失败")
            user_input = input("是否仍然提交成功的修改? (y/n): ").strip().lower()
            if user_input == 'y':
                conn.commit()
                print("✅ 事务已提交")
            else:
                conn.rollback()
                print("❌ 事务已回滚")

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            print("❌ 事务已回滚")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            print("\n数据库连接已关闭")


if __name__ == '__main__':
    main()
