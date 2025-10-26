#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只读诊断：检查云端sp8d数据库中PO202510-004为什么显示等待"""
import psycopg2

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("\n=== 诊断云端PO202510-004流程图显示问题 ===\n")

    try:
        conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = conn.cursor()

        print("✓ 已连接云端sp8d数据库\n")

        # 1. 检查approval_record表是否有status字段
        print("1. 检查 approval_record 表结构...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'approval_record'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]

        print(f"   表字段: {', '.join(column_names)}")

        has_status = 'status' in column_names
        print(f"\n   {'✓' if has_status else '❌'} status 字段: {'存在' if has_status else '不存在'}\n")

        if not has_status:
            print("   ⚠️ 这是问题根源！没有status字段，前端无法判断步骤状态")
            print("   → 需要执行修复：添加status字段\n")

        # 2. 查询PO202510-004的审批记录
        print("2. 查询 PO202510-004 的审批记录...\n")

        if has_status:
            query = """
                SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.status, ar.timestamp,
                       ai.id as instance_id, ai.status as instance_status
                FROM approval_record ar
                JOIN users u ON ar.approver_id = u.id
                JOIN approval_instance ai ON ar.instance_id = ai.id
                JOIN pricing_orders po ON ai.object_id = po.id AND ai.object_type = 'pricing_order'
                WHERE po.order_number = 'PO202510-004'
                ORDER BY ar.timestamp
            """
        else:
            query = """
                SELECT ar.id, ar.step_id, u.real_name, ar.action, ar.timestamp,
                       ai.id as instance_id, ai.status as instance_status
                FROM approval_record ar
                JOIN users u ON ar.approver_id = u.id
                JOIN approval_instance ai ON ar.instance_id = ai.id
                JOIN pricing_orders po ON ai.object_id = po.id AND ai.object_type = 'pricing_order'
                WHERE po.order_number = 'PO202510-004'
                ORDER BY ar.timestamp
            """

        cursor.execute(query)
        records = cursor.fetchall()

        if not records:
            print("   ❌ 未找到审批记录！")
            cursor.close()
            conn.close()
            return

        print(f"   找到 {len(records)} 条审批记录:\n")

        gxh_record = None
        for rec in records:
            approver = rec[2]
            action = rec[3]

            if has_status:
                status = rec[4]
                timestamp = rec[5]
                marker = "👉" if approver == "郭小会" else "  "
                status_icon = "✓" if status == "approved" else "⏰" if status in ["pending", "waiting"] else "❌"

                print(f"   {marker} {approver:10} | step {rec[1]:3} | action={action:10} | status={status:10} | {timestamp}")

                if approver == "郭小会":
                    gxh_record = rec
            else:
                timestamp = rec[4]
                marker = "👉" if approver == "郭小会" else "  "

                print(f"   {marker} {approver:10} | step {rec[1]:3} | action={action:10} | (无status字段) | {timestamp}")

                if approver == "郭小会":
                    gxh_record = rec

        # 3. 分析问题
        print("\n" + "="*80)
        print("问题分析".center(80))
        print("="*80 + "\n")

        if not has_status:
            print("❌ 根本原因: approval_record 表缺少 status 字段")
            print()
            print("   影响:")
            print("   1. 前端API无法获取步骤的审批状态")
            print("   2. approval_flow.js 渲染逻辑依赖 status 字段")
            print("   3. 即使 action='approve'，前端也无法知道是否已批准")
            print()
            print("   修复方案:")
            print("   执行 scripts/temp/fix_cloud_approval_record.py")
            print("   该脚本会:")
            print("   - 添加 status 字段")
            print("   - 根据 action 字段设置正确的 status 值")
            print("   - approve → approved, reject → rejected")

        elif gxh_record:
            gxh_action = gxh_record[3]
            gxh_status = gxh_record[4]

            print(f"郭小会的审批记录:")
            print(f"  - 记录ID: {gxh_record[0]}")
            print(f"  - 步骤ID: {gxh_record[1]}")
            print(f"  - action: {gxh_action}")
            print(f"  - status: {gxh_status}")
            print()

            if gxh_action == "approve" and gxh_status != "approved":
                print(f"❌ 数据不一致问题:")
                print(f"   action 是 'approve' 但 status 是 '{gxh_status}'")
                print(f"   → 需要将 status 更新为 'approved'")
                print()
                print(f"   修复SQL:")
                print(f"   UPDATE approval_record SET status = 'approved' WHERE id = {gxh_record[0]};")

            elif gxh_status == "approved":
                print(f"✓ 数据库记录正确")
                print(f"  → action='approve', status='approved'")
                print()
                print(f"⚠️ 但前端仍显示等待，可能原因:")
                print(f"   1. 浏览器缓存了旧的API响应")
                print(f"   2. CDN缓存了旧的JavaScript文件")
                print(f"   3. 前端渲染逻辑有bug")
                print()
                print(f"   建议:")
                print(f"   1. 强制刷新页面（Ctrl+Shift+R）")
                print(f"   2. 清除浏览器缓存")
                print(f"   3. 检查浏览器Network标签，查看API返回的实际数据")

            else:
                print(f"⚠️ 状态值异常: {gxh_status}")
                print(f"   预期值: approved 或 rejected")

        cursor.close()
        conn.close()

        print("\n=== 诊断完成 ===\n")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
