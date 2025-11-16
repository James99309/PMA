#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用纯SQL为产品快照添加单位信息
不依赖Flask应用,避免WeasyPrint加载问题
"""
import psycopg2
import json
import os
import sys


def get_field_unit_from_db(conn, field_name):
    """直接从数据库查询规格单位"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unit FROM specification_dictionary WHERE name = %s",
        (field_name,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None


def update_product_snapshots():
    """更新所有产品快照添加单位"""
    # 从环境变量获取数据库连接
    db_url = os.environ.get('DATABASE_URL', 'postgresql://nijie@localhost:5432/pma_local')

    print("=" * 70)
    print("为产品编码快照添加单位信息 (纯SQL版本)")
    print("=" * 70)
    print(f"数据库: {db_url}")
    print()

    try:
        # 连接数据库
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # 查询所有有快照的产品
        cursor.execute("""
            SELECT id, product_mn, code_definition_snapshot
            FROM products
            WHERE code_definition_snapshot IS NOT NULL
            ORDER BY id
        """)

        products = cursor.fetchall()
        total_count = len(products)

        print(f"📊 找到 {total_count} 个产品有快照\n")

        if total_count == 0:
            print("✅ 没有产品需要处理")
            conn.close()
            return

        # 显示前10个示例
        print("示例产品（前10个）：")
        for i, (product_id, mn, _) in enumerate(products[:10], 1):
            print(f"  {i}. ID={product_id}, MN={mn}")
        if total_count > 10:
            print(f"  ... 还有 {total_count - 10} 个产品")
        print()

        # 确认执行
        confirmation = input(f"是否继续处理这 {total_count} 个产品？(yes/no): ").strip().lower()
        if confirmation not in ['yes', 'y']:
            print("❌ 操作已取消")
            conn.close()
            return

        print()
        print("开始处理...")
        print("-" * 70)

        updated_count = 0
        skipped_count = 0
        failed_count = 0

        # 处理每个产品
        for i, (product_id, mn, snapshot_json) in enumerate(products, 1):
            try:
                # 解析快照
                snapshot = json.loads(snapshot_json) if isinstance(snapshot_json, str) else snapshot_json

                if not snapshot or 'code_parts' not in snapshot:
                    skipped_count += 1
                    print(f"[{i}/{total_count}] ⚠️  跳过 - ID={product_id}, MN={mn} (快照格式不正确)")
                    continue

                # 检查是否需要添加单位
                modified = False
                parts_updated = 0

                for part in snapshot['code_parts']:
                    if 'unit' not in part and 'field_name' in part:
                        # 查询单位
                        unit = get_field_unit_from_db(conn, part['field_name'])
                        part['unit'] = unit
                        modified = True
                        parts_updated += 1

                if modified:
                    # 更新快照
                    updated_snapshot = json.dumps(snapshot, ensure_ascii=False)
                    cursor.execute(
                        "UPDATE products SET code_definition_snapshot = %s WHERE id = %s",
                        (updated_snapshot, product_id)
                    )

                    updated_count += 1
                    status = "✅ 成功"
                    detail = f"更新了{parts_updated}个规格字段的单位"
                else:
                    skipped_count += 1
                    status = "⚠️  跳过"
                    detail = "快照已包含单位信息"

                print(f"[{i}/{total_count}] {status} - ID={product_id}, MN={mn}, {detail}")

            except Exception as e:
                failed_count += 1
                print(f"[{i}/{total_count}] ❌ 失败 - ID={product_id}, MN={mn}, 错误: {str(e)}")

        # 提交更改
        if updated_count > 0:
            conn.commit()
            print()
            print("-" * 70)
            print("✅ 数据库已更新")
        else:
            print()
            print("-" * 70)
            print("⚠️  没有记录被更新")

        cursor.close()
        conn.close()

        # 显示统计结果
        print()
        print("=" * 70)
        print("处理完成 - 统计结果")
        print("=" * 70)
        print(f"  总数: {total_count}")
        print(f"  ✅ 成功更新: {updated_count}")
        print(f"  ⚠️  跳过: {skipped_count}")
        print(f"  ❌ 失败: {failed_count}")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 数据库操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        update_product_snapshots()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(1)
