#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为 approval_record 表添加 status 字段"""
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
from sqlalchemy import text, inspect

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 为 approval_record 表添加 status 字段 ===\n")

        inspector = inspect(db.engine)
        columns = inspector.get_columns('approval_record')
        column_names = [col['name'] for col in columns]

        # 检查是否已有 status 字段
        if 'status' in column_names:
            print("✓ status 字段已存在，无需添加")
            return

        print("1. 添加 status 字段...")

        try:
            # 添加字段，默认值为 'approved'（因为所有历史记录都是已批准的）
            db.session.execute(text("""
                ALTER TABLE approval_record
                ADD COLUMN status VARCHAR(20) DEFAULT 'approved'
            """))

            db.session.commit()
            print("   ✓ 字段添加成功")

        except Exception as e:
            db.session.rollback()
            print(f"   ❌ 添加失败: {str(e)}")
            return

        print("\n2. 更新历史数据...")

        try:
            # 将所有 action='approve' 的记录 status 设为 'approved'
            # 将所有 action='reject' 的记录 status 设为 'rejected'
            db.session.execute(text("""
                UPDATE approval_record
                SET status = CASE
                    WHEN action = 'approve' THEN 'approved'
                    WHEN action = 'reject' THEN 'rejected'
                    ELSE 'pending'
                END
            """))

            updated_count = db.session.execute(text(
                "SELECT COUNT(*) FROM approval_record"
            )).scalar()

            db.session.commit()
            print(f"   ✓ 更新了 {updated_count} 条记录")

        except Exception as e:
            db.session.rollback()
            print(f"   ❌ 更新失败: {str(e)}")
            return

        print("\n3. 验证结果...")

        # 验证字段已添加
        columns = inspector.get_columns('approval_record')
        column_names = [col['name'] for col in columns]

        if 'status' in column_names:
            print("   ✓ status 字段已成功添加到表结构")

            # 检查数据
            result = db.session.execute(text("""
                SELECT status, COUNT(*) as count
                FROM approval_record
                GROUP BY status
            """)).fetchall()

            print("\n   状态统计:")
            for row in result:
                print(f"     {row[0]:10}: {row[1]} 条")

            # 检查gxh的记录
            gxh_result = db.session.execute(text("""
                SELECT ar.id, ar.action, ar.status
                FROM approval_record ar
                JOIN users u ON ar.approver_id = u.id
                WHERE u.real_name = '郭小会'
                ORDER BY ar.timestamp DESC
                LIMIT 3
            """)).fetchall()

            if gxh_result:
                print("\n   gxh最近3条记录:")
                for row in gxh_result:
                    print(f"     记录{row[0]:4}: action={row[1]:10} status={row[2]}")
        else:
            print("   ❌ 验证失败，字段未添加成功")

        print("\n=== 修复完成 ===")
        print("\n下一步：刷新批价单详情页，流程图应该显示绿色打勾\n")

if __name__ == '__main__':
    main()
