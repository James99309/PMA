#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS云端数据库英文字段迁移脚本

执行以下操作：
1. 添加 name_en 字段到 product_code_fields 表
2. 同步 product_categories 英文名称
3. 同步 product_code_fields (origin_location) 英文名称
4. 同步 product_subcategories 英文名称（从本地数据库）
5. 更新 alembic_version

使用方式：
    python scripts/temp/migrate_ovs_name_en_fields.py
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

import psycopg2
from psycopg2.extras import DictCursor

# 本地数据库配置
LOCAL_DB_URL = "postgresql://nijie@localhost:5432/pma_local"

# 云端 OVS 数据库配置
OVS_CLOUD_DB_URL = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

# 新的 alembic 版本号
NEW_ALEMBIC_VERSION = "add_product_code_field_name_en_20260118"


def step1_add_name_en_column():
    """Step 1: 添加 name_en 字段到 product_code_fields 表"""
    print("\n" + "=" * 60)
    print("Step 1: 添加 name_en 字段到 product_code_fields")
    print("=" * 60)

    conn = psycopg2.connect(OVS_CLOUD_DB_URL)
    try:
        with conn.cursor() as cur:
            # 检查字段是否已存在
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'product_code_fields'
                AND column_name = 'name_en'
            """)

            if cur.fetchone():
                print("  ⏭️ name_en 字段已存在，跳过")
                return True

            # 添加字段
            cur.execute("""
                ALTER TABLE product_code_fields
                ADD COLUMN name_en VARCHAR(100)
            """)
            conn.commit()
            print("  ✅ 成功添加 name_en 字段")
            return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def step2_sync_categories_english_names():
    """Step 2: 同步 product_categories 英文名称"""
    print("\n" + "=" * 60)
    print("Step 2: 同步 product_categories 英文名称")
    print("=" * 60)

    # 分类英文名称映射
    category_names = {
        'B': 'Base Station',
        'M': 'Hybrid Combiner',
        'O': 'BDA',
        'R': 'Two-Way Radio',
        'S': 'Power & Coupler',
        'A': 'Antenna',
        'L': 'Application',
        'Y': 'Accessory',
        'F': 'Service',
    }

    conn = psycopg2.connect(OVS_CLOUD_DB_URL)
    try:
        with conn.cursor() as cur:
            updated = 0
            for code_letter, name_en in category_names.items():
                cur.execute("""
                    UPDATE product_categories
                    SET name_en = %s
                    WHERE code_letter = %s
                    AND (name_en IS NULL OR name_en = '')
                """, (name_en, code_letter))

                if cur.rowcount > 0:
                    updated += 1
                    print(f"  ✅ 更新: {code_letter} -> {name_en}")
                else:
                    # 检查是否因为已有值而跳过
                    cur.execute("""
                        SELECT name_en FROM product_categories
                        WHERE code_letter = %s
                    """, (code_letter,))
                    result = cur.fetchone()
                    if result and result[0]:
                        print(f"  ⏭️ 已有: {code_letter} = {result[0]}")
                    else:
                        print(f"  ⚠️ 未找到: {code_letter}")

            conn.commit()
            print(f"\n  共更新 {updated} 条分类记录")
            return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def step3_sync_origin_location_english_names():
    """Step 3: 同步 product_code_fields (origin_location) 英文名称"""
    print("\n" + "=" * 60)
    print("Step 3: 同步 product_code_fields (origin_location) 英文名称")
    print("=" * 60)

    # 产地英文名称映射
    origin_names = {
        '中国': 'China',
        '亚太': 'Asia Pacific',
    }

    conn = psycopg2.connect(OVS_CLOUD_DB_URL)
    try:
        with conn.cursor() as cur:
            updated = 0
            for name, name_en in origin_names.items():
                cur.execute("""
                    UPDATE product_code_fields
                    SET name_en = %s
                    WHERE field_type = 'origin_location' AND name = %s
                    AND (name_en IS NULL OR name_en = '')
                """, (name_en, name))

                if cur.rowcount > 0:
                    updated += 1
                    print(f"  ✅ 更新: {name} -> {name_en}")
                else:
                    # 检查是否因为已有值而跳过
                    cur.execute("""
                        SELECT name_en FROM product_code_fields
                        WHERE field_type = 'origin_location' AND name = %s
                    """, (name,))
                    result = cur.fetchone()
                    if result and result[0]:
                        print(f"  ⏭️ 已有: {name} = {result[0]}")
                    else:
                        print(f"  ⚠️ 未找到: {name}")

            conn.commit()
            print(f"\n  共更新 {updated} 条产地记录")
            return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def step4_sync_subcategories_english_names():
    """Step 4: 同步 product_subcategories 英文名称（从本地数据库）"""
    print("\n" + "=" * 60)
    print("Step 4: 同步 product_subcategories 英文名称")
    print("=" * 60)

    # 从本地数据库获取英文名称
    print("\n  4.1 从本地数据库获取英文名称...")
    try:
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        with local_conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT category_id, name, name_en, code_letter
                FROM product_subcategories
                WHERE name_en IS NOT NULL AND name_en != ''
                ORDER BY category_id, id
            """)
            subcategories = [dict(row) for row in cur.fetchall()]
        local_conn.close()
        print(f"      获取到 {len(subcategories)} 条记录")
    except Exception as e:
        print(f"  ❌ 连接本地数据库失败: {e}")
        return False

    # 同步到云端数据库
    print("\n  4.2 同步到云端 OVS 数据库...")
    try:
        cloud_conn = psycopg2.connect(OVS_CLOUD_DB_URL)
        with cloud_conn.cursor() as cur:
            updated = 0
            not_found = []

            for sub in subcategories:
                cur.execute("""
                    UPDATE product_subcategories
                    SET name_en = %s
                    WHERE category_id = %s AND name = %s
                    AND (name_en IS NULL OR name_en = '')
                """, (sub['name_en'], sub['category_id'], sub['name']))

                if cur.rowcount > 0:
                    updated += 1
                    print(f"      ✅ 更新: {sub['name']} -> {sub['name_en']}")
                else:
                    # 检查是否因为已有英文名而跳过
                    cur.execute("""
                        SELECT name_en FROM product_subcategories
                        WHERE category_id = %s AND name = %s
                    """, (sub['category_id'], sub['name']))
                    result = cur.fetchone()
                    if result:
                        if result[0]:
                            pass  # 已有英文名，静默跳过
                        else:
                            not_found.append(sub['name'])
                    else:
                        not_found.append(sub['name'])

            cloud_conn.commit()
            print(f"\n  共更新 {updated} 条子分类记录")
            if not_found:
                print(f"  未找到 {len(not_found)} 条: {', '.join(not_found[:5])}{'...' if len(not_found) > 5 else ''}")
            return True
    except Exception as e:
        print(f"  ❌ 同步失败: {e}")
        cloud_conn.rollback()
        return False
    finally:
        cloud_conn.close()


def step5_update_alembic_version():
    """Step 5: 更新 alembic_version"""
    print("\n" + "=" * 60)
    print("Step 5: 更新 alembic_version")
    print("=" * 60)

    conn = psycopg2.connect(OVS_CLOUD_DB_URL)
    try:
        with conn.cursor() as cur:
            # 获取当前版本
            cur.execute("SELECT version_num FROM alembic_version")
            current = cur.fetchone()
            if current:
                print(f"  当前版本: {current[0]}")

            # 更新版本
            cur.execute("""
                UPDATE alembic_version
                SET version_num = %s
            """, (NEW_ALEMBIC_VERSION,))

            conn.commit()
            print(f"  ✅ 更新为: {NEW_ALEMBIC_VERSION}")
            return True
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_migration():
    """验证迁移结果"""
    print("\n" + "=" * 60)
    print("验证迁移结果")
    print("=" * 60)

    conn = psycopg2.connect(OVS_CLOUD_DB_URL)
    try:
        with conn.cursor() as cur:
            # 检查 product_code_fields 的 name_en 字段
            print("\n  1. product_code_fields 表:")
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'product_code_fields'
                AND column_name = 'name_en'
            """)
            if cur.fetchone():
                print("     ✅ name_en 字段存在")
            else:
                print("     ❌ name_en 字段不存在")

            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN name_en IS NOT NULL AND name_en != '' THEN 1 ELSE 0 END) as with_en
                FROM product_code_fields
            """)
            result = cur.fetchone()
            print(f"     总记录: {result[0]}, 有英文名: {result[1]}")

            # 检查 product_categories
            print("\n  2. product_categories 表:")
            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN name_en IS NOT NULL AND name_en != '' THEN 1 ELSE 0 END) as with_en
                FROM product_categories
            """)
            result = cur.fetchone()
            print(f"     总记录: {result[0]}, 有英文名: {result[1]}")

            # 检查 product_subcategories
            print("\n  3. product_subcategories 表:")
            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN name_en IS NOT NULL AND name_en != '' THEN 1 ELSE 0 END) as with_en
                FROM product_subcategories
            """)
            result = cur.fetchone()
            print(f"     总记录: {result[0]}, 有英文名: {result[1]}")

            # 检查 alembic_version
            print("\n  4. alembic_version:")
            cur.execute("SELECT version_num FROM alembic_version")
            result = cur.fetchone()
            print(f"     当前版本: {result[0] if result else '无'}")

    finally:
        conn.close()


def main():
    print("=" * 60)
    print("OVS 云端数据库英文字段迁移")
    print("=" * 60)
    print(f"\n目标数据库: OVS Cloud (Supabase)")
    print(f"新 alembic 版本: {NEW_ALEMBIC_VERSION}")

    # 确认执行
    confirm = input("\n是否继续执行迁移? (y/N): ").strip().lower()
    if confirm != 'y':
        print("\n已取消")
        return

    # 执行各步骤
    results = []

    results.append(("Step 1: 添加 name_en 字段", step1_add_name_en_column()))
    results.append(("Step 2: 同步分类英文名", step2_sync_categories_english_names()))
    results.append(("Step 3: 同步产地英文名", step3_sync_origin_location_english_names()))
    results.append(("Step 4: 同步子分类英文名", step4_sync_subcategories_english_names()))
    results.append(("Step 5: 更新 alembic 版本", step5_update_alembic_version()))

    # 验证结果
    verify_migration()

    # 总结
    print("\n" + "=" * 60)
    print("迁移完成总结")
    print("=" * 60)
    for step_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {status}: {step_name}")

    all_success = all(r[1] for r in results)
    if all_success:
        print("\n✅ 所有迁移步骤执行成功!")
    else:
        print("\n⚠️ 部分步骤执行失败，请检查上述输出")


if __name__ == '__main__':
    main()
