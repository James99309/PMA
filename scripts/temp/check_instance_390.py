#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查实例390的当前状态"""
import psycopg2
from psycopg2.extras import RealDictCursor

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n" + "="*80)
    print("检查实例390状态".center(80))
    print("="*80 + "\n")

    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 查询实例390
        cursor.execute("""
            SELECT id, current_step, status, started_at
            FROM approval_instance
            WHERE id = 390
        """)
        instance = cursor.fetchone()

        if instance:
            print(f"实例ID: {instance['id']}")
            print(f"当前步骤ID: {instance['current_step']}")
            print(f"状态: {instance['status']}")
            print(f"开始时间: {instance['started_at']}")
        else:
            print("❌ 未找到实例390")
            return

        # 查询审批记录
        print(f"\n审批记录:")
        cursor.execute("""
            SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.timestamp
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            WHERE ar.instance_id = 390
            ORDER BY ar.timestamp
        """)
        records = cursor.fetchall()

        if records:
            for rec in records:
                print(f"  记录{rec['id']}: 步骤{rec['step_id']}, {rec['real_name']}, {rec['action']}, {rec['timestamp']}")
        else:
            print("  ❌ 没有审批记录")

        # 分析
        print(f"\n" + "="*80)
        print("分析结果".center(80))
        print("="*80 + "\n")

        if instance['current_step'] == 13:
            print("✓ current_step = 13（正确转到了gxh的步骤）")
            if len(records) == 1:
                print("✓ 有1条审批记录（童蕾的）")
                print("\n结论: 步骤转换成功，等待gxh审批")
            else:
                print(f"⚠️ 有{len(records)}条审批记录")
        elif instance['current_step'] == 14:
            print("❌ current_step = 14（又跳过了步骤13！）")
            print("\n结论: 问题重现，步骤13被跳过")
        elif instance['current_step'] == 12:
            print("❌ current_step = 12（没有转到下一步！）")
            print("\n结论: 步骤转换失败")
        else:
            print(f"⚠️ current_step = {instance['current_step']}（异常值）")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

    print("\n" + "="*80)
    print("检查完成".center(80))
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
