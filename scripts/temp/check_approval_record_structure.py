#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端 approval_record 表结构和gxh的记录状态"""
import sys, os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from sqlalchemy import inspect, text

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 检查 approval_record 表结构 ===\n")

        inspector = inspect(db.engine)

        try:
            # 检查表结构
            columns = inspector.get_columns('approval_record')
            column_names = [col['name'] for col in columns]

            print(f"✓ 表字段数: {len(columns)}\n")

            # 检查是否有 status 字段
            has_status = 'status' in column_names
            print(f"{'✓' if has_status else '❌'} status 字段: {'存在' if has_status else '不存在'}")

            # 显示所有字段
            print("\n=== 字段列表 ===\n")
            for col in columns:
                col_type = str(col['type'])
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                print(f"  {col['name']:25} {col_type:20} {nullable}")

            # 查找gxh的审批记录
            print("\n\n=== gxh最近的审批记录 ===\n")

            # 先找gxh的user_id
            result = db.session.execute(
                text("SELECT id, real_name FROM users WHERE username = 'gxh' OR real_name = 'gxh'")
            ).fetchone()

            if not result:
                print("❌ 未找到gxh用户")
                return

            gxh_id = result[0]
            print(f"✓ gxh用户ID: {gxh_id}")

            # 查找最近的审批记录
            if has_status:
                query = text("""
                    SELECT ar.id, ar.instance_id, ar.step_id, ar.action, ar.status, ar.timestamp, ar.comment
                    FROM approval_record ar
                    WHERE ar.approver_id = :gxh_id
                    ORDER BY ar.timestamp DESC
                    LIMIT 3
                """)
            else:
                query = text("""
                    SELECT ar.id, ar.instance_id, ar.step_id, ar.action, ar.timestamp, ar.comment
                    FROM approval_record ar
                    WHERE ar.approver_id = :gxh_id
                    ORDER BY ar.timestamp DESC
                    LIMIT 3
                """)

            records = db.session.execute(query, {'gxh_id': gxh_id}).fetchall()

            print(f"\n✓ 最近 {len(records)} 条审批记录:\n")

            for rec in records:
                print(f"  记录ID: {rec[0]}")
                print(f"    - instance_id: {rec[1]}")
                print(f"    - step_id: {rec[2]}")
                print(f"    - action: {rec[3]}")
                if has_status:
                    print(f"    - status: {rec[4]}")
                    print(f"    - timestamp: {rec[5]}")
                    print(f"    - comment: {rec[6] or '(无)'}")
                else:
                    print(f"    - timestamp: {rec[4]}")
                    print(f"    - comment: {rec[5] or '(无)'}")
                    print(f"    ⚠️ 缺少 status 字段（这会导致流程图显示异常）")
                print()

            # 检查最新批价单审批实例的所有记录
            print("\n=== 最新批价单审批实例的所有记录 ===\n")

            instance_result = db.session.execute(
                text("""
                    SELECT id FROM approval_instance
                    WHERE object_type = 'pricing_order'
                    ORDER BY started_at DESC
                    LIMIT 1
                """)
            ).fetchone()

            if instance_result:
                instance_id = instance_result[0]
                print(f"✓ 实例ID: {instance_id}\n")

                if has_status:
                    records_query = text("""
                        SELECT ar.id, u.real_name, ar.step_id, ar.action, ar.status, ar.timestamp
                        FROM approval_record ar
                        JOIN users u ON ar.approver_id = u.id
                        WHERE ar.instance_id = :instance_id
                        ORDER BY ar.timestamp ASC
                    """)
                else:
                    records_query = text("""
                        SELECT ar.id, u.real_name, ar.step_id, ar.action, ar.timestamp
                        FROM approval_record ar
                        JOIN users u ON ar.approver_id = u.id
                        WHERE ar.instance_id = :instance_id
                        ORDER BY ar.timestamp ASC
                    """)

                all_records = db.session.execute(records_query, {'instance_id': instance_id}).fetchall()

                for rec in all_records:
                    approver = rec[1]
                    marker = "👉" if approver == "郭小会" else "  "
                    print(f"{marker} {approver:10} - ", end="")
                    print(f"记录{rec[0]:3} step{rec[2]:3} action={rec[3]:10}", end="")
                    if has_status:
                        print(f" status={rec[4]:10} {rec[5]}")
                    else:
                        print(f" {rec[4]}")

                # 分析问题
                print("\n=== 问题分析 ===\n")
                if not has_status:
                    print("❌ 主要问题: approval_record 表缺少 status 字段")
                    print("   影响:")
                    print("   1. 流程图无法判断步骤是否完成（显示等待而非绿色打勾）")
                    print("   2. 前端 approval_flow.js 依赖 status === 'approved' 来渲染")
                    print("\n   解决方案:")
                    print("   执行数据库迁移添加 status 字段:")
                    print("   python3 standard_migration_upgrade.py")

        except Exception as e:
            print(f"❌ 检查失败: {str(e)}")
            import traceback
            traceback.print_exc()

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
