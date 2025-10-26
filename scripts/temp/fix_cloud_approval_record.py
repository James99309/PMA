#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接连接云端sp8d数据库，修复 approval_record 表的 status 字段"""
import psycopg2
from psycopg2 import sql

# 云端sp8d数据库连接信息
CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n=== 连接云端sp8d数据库 ===\n")

    try:
        # 连接数据库
        conn = psycopg2.connect(CLOUD_DB_URL)
        conn.autocommit = False
        cursor = conn.cursor()

        print("✓ 成功连接到云端数据库\n")

        # 1. 检查 approval_record 表是否有 status 字段
        print("1. 检查 approval_record 表结构...")

        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'approval_record'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]

        print(f"   表字段数: {len(columns)}")
        for col in columns:
            print(f"   - {col[0]:20} {col[1]}")

        has_status = 'status' in column_names

        print(f"\n   status 字段: {'✓ 存在' if has_status else '❌ 不存在'}")

        # 2. 如果没有 status 字段，添加它
        if not has_status:
            print("\n2. 添加 status 字段...")

            try:
                cursor.execute("""
                    ALTER TABLE approval_record
                    ADD COLUMN status VARCHAR(20) DEFAULT 'approved'
                """)

                print("   ✓ 字段添加成功")

            except Exception as e:
                print(f"   ❌ 添加失败: {str(e)}")
                conn.rollback()
                return
        else:
            print("\n2. status 字段已存在，跳过添加步骤")

        # 3. 更新历史数据
        print("\n3. 更新历史数据...")

        try:
            cursor.execute("""
                UPDATE approval_record
                SET status = CASE
                    WHEN action = 'approve' THEN 'approved'
                    WHEN action = 'reject' THEN 'rejected'
                    ELSE 'pending'
                END
                WHERE status IS NULL OR status = 'approved'
            """)

            updated_count = cursor.rowcount
            print(f"   ✓ 更新了 {updated_count} 条记录")

        except Exception as e:
            print(f"   ❌ 更新失败: {str(e)}")
            conn.rollback()
            return

        # 4. 提交事务
        conn.commit()
        print("\n✓ 事务已提交")

        # 5. 验证修复结果 - 检查PO202510-004的记录
        print("\n4. 验证修复结果（PO202510-004）...\n")

        cursor.execute("""
            SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.status, ar.timestamp
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            JOIN approval_instance ai ON ar.instance_id = ai.id
            JOIN pricing_orders po ON ai.object_id = po.id AND ai.object_type = 'pricing_order'
            WHERE po.order_number = 'PO202510-004'
            ORDER BY ar.timestamp
        """)

        records = cursor.fetchall()

        if records:
            print(f"   找到 {len(records)} 条审批记录:\n")
            for rec in records:
                marker = "👉" if rec[2] == "郭小会" else "  "
                status_icon = "✓" if rec[4] == "approved" else "❌" if rec[4] == "rejected" else "⏰"
                print(f"   {marker} 记录{rec[0]:4}: {rec[2]:10} - step{rec[1]:3}")
                print(f"       {status_icon} action={rec[3]:10} status={rec[4]:10}")
                print(f"       时间: {rec[5]}")
                print()

            # 检查gxh的记录
            gxh_record = next((r for r in records if r[2] == "郭小会"), None)
            if gxh_record:
                if gxh_record[4] == "approved":
                    print("   ✅ gxh的记录状态正确！")
                    print("   → 现在刷新批价单详情页应该显示绿色打勾")
                else:
                    print(f"   ⚠️ gxh的记录状态异常: {gxh_record[4]}")
        else:
            print("   ⚠️ 未找到PO202510-004的审批记录")

        # 6. 检查整体统计
        print("\n5. 整体状态统计...\n")

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM approval_record
            GROUP BY status
            ORDER BY count DESC
        """)

        stats = cursor.fetchall()
        print("   状态分布:")
        for stat in stats:
            print(f"     {stat[0]:15}: {stat[1]} 条")

        cursor.close()
        conn.close()

        print("\n=== 修复完成 ===")
        print("\n下一步：")
        print("1. 刷新批价单详情页（Ctrl + Shift + R）")
        print("2. 检查郭小会的步骤是否显示绿色打勾")
        print("3. 如果仍然显示等待，清除浏览器缓存后重试\n")

    except Exception as e:
        print(f"\n❌ 连接或操作失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
