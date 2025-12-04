#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS数据库序列修复脚本
检查并修复所有表的序列，确保序列值大于现有最大ID

执行说明：
    python scripts/temp/fix_ovs_sequences.py

创建日期: 2025-12-03
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
    print("="*70)
    print("OVS 数据库序列检查与修复")
    print("="*70)

    conn = psycopg2.connect(**OVS_DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()

    # 获取所有有id列的表
    cursor.execute("""
        SELECT c.table_name
        FROM information_schema.columns c
        JOIN information_schema.tables t
            ON c.table_name = t.table_name
            AND c.table_schema = t.table_schema
        WHERE c.table_schema = 'public'
          AND c.column_name = 'id'
          AND t.table_type = 'BASE TABLE'
          AND c.table_name NOT LIKE 'pg_%'
          AND c.table_name NOT IN ('alembic_version', 'spatial_ref_sys')
        ORDER BY c.table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]

    print(f"\n找到 {len(tables)} 个有id列的表\n")

    # 检查每个表的序列状态
    print(f"{'表名':<40} {'MAX(id)':<10} {'序列值':<10} {'状态'}")
    print("-"*75)

    issues = []
    fixed = []

    for table in tables:
        try:
            # 获取MAX(id)
            cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
            max_id = cursor.fetchone()[0]

            # 获取序列值
            seq_name = f"{table}_id_seq"
            try:
                cursor.execute(f"SELECT last_value, is_called FROM {seq_name}")
                result = cursor.fetchone()
                if result:
                    seq_value = result[0]
                    is_called = result[1]

                    # 如果is_called为false，说明序列还没被使用过，下一个值是last_value
                    # 如果is_called为true，下一个值是last_value + 1
                    next_value = seq_value if not is_called else seq_value + 1

                    if next_value <= max_id:
                        status = "❌ 需修复"
                        issues.append((table, max_id, seq_value, next_value))
                    else:
                        status = "✅ 正常"

                    print(f"{table:<40} {max_id:<10} {seq_value:<10} {status}")
                else:
                    print(f"{table:<40} {max_id:<10} {'N/A':<10} ⚠️ 无序列")
            except Exception as e:
                if "does not exist" in str(e):
                    print(f"{table:<40} {max_id:<10} {'N/A':<10} ⚠️ 无序列")
                else:
                    print(f"{table:<40} {max_id:<10} {'Error':<10} ⚠️ {str(e)[:20]}")

        except Exception as e:
            print(f"{table:<40} {'Error':<10} {'N/A':<10} ⚠️ {str(e)[:30]}")

    # 修复问题序列
    if issues:
        print("\n" + "="*70)
        print(f"发现 {len(issues)} 个序列需要修复")
        print("="*70)

        for table, max_id, seq_value, next_value in issues:
            seq_name = f"{table}_id_seq"
            new_value = max_id + 1

            print(f"\n修复 {table}:")
            print(f"  当前: MAX(id)={max_id}, 序列下一值={next_value}")
            print(f"  修复: 设置序列值为 {new_value}")

            try:
                # setval的第三个参数false表示下一次nextval会返回设置的值
                cursor.execute(f"SELECT setval('{seq_name}', {new_value}, false)")

                # 验证修复
                cursor.execute(f"SELECT last_value FROM {seq_name}")
                new_seq = cursor.fetchone()[0]
                print(f"  ✅ 修复成功，新序列值: {new_seq}")
                fixed.append(table)
            except Exception as e:
                print(f"  ❌ 修复失败: {e}")

    # 总结
    print("\n" + "="*70)
    print("修复结果总结")
    print("="*70)

    print(f"\n检查表数: {len(tables)}")
    print(f"发现问题: {len(issues)}")
    print(f"修复成功: {len(fixed)}")

    if fixed:
        print(f"\n已修复的表:")
        for table in fixed:
            print(f"  ✅ {table}")

    if len(fixed) == len(issues):
        print("\n🎉 所有序列已修复！")
    elif issues and len(fixed) < len(issues):
        print(f"\n⚠️ 有 {len(issues) - len(fixed)} 个序列修复失败")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    main()
