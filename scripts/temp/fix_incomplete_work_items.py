#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量标记历史行程为完成

问题描述：
由于之前代码bug导致"标记完成"按钮不显示，用户无法手动标记行程完成。
现在bug已修复，需要将今天之前所有未完成的行程批量标记为完成。
"""
import sys
import os
from datetime import datetime

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text

# SP8D云端数据库连接
SP8D_DATABASE_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    print("=" * 70)
    print("🔧 批量标记历史行程为完成")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    engine = create_engine(SP8D_DATABASE_URL)

    with engine.connect() as conn:
        # 1. 统计修复前的数量
        print("\n📊 修复前统计:")
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM work_items
            WHERE status = 'planned'
            AND is_deleted = false
            AND planned_date < CURRENT_DATE
        """))
        before_count = result.scalar()
        print(f"   今天之前未完成的行程: {before_count} 条")

        if before_count == 0:
            print("\n✅ 没有需要修复的行程！")
            return True

        # 显示详情
        print("\n📋 将要修复的行程:")
        result = conn.execute(text("""
            SELECT
                wi.id,
                wi.title,
                wi.planned_date,
                u.real_name
            FROM work_items wi
            JOIN users u ON wi.owner_id = u.id
            WHERE wi.status = 'planned'
            AND wi.is_deleted = false
            AND wi.planned_date < CURRENT_DATE
            ORDER BY wi.planned_date DESC, u.real_name
        """))
        rows = result.fetchall()
        for row in rows:
            print(f"   ID:{row[0]} | {row[3]} | {row[2]} | {row[1][:35]}...")

        # 确认执行
        print(f"\n⚠️  将要修复 {before_count} 条行程")
        if '--yes' not in sys.argv and '-y' not in sys.argv:
            confirm = input("确认执行修复？(y/N): ")
            if confirm.lower() != 'y':
                print("❌ 已取消")
                return False
        else:
            print("   (自动确认模式)")

        # 2. 执行修复
        try:
            # 2.1 标记所有今天之前的未完成行程为完成
            print("\n🔄 步骤1: 标记行程为完成...")
            result = conn.execute(text("""
                UPDATE work_items
                SET
                    status = 'completed',
                    completed_at = NOW()
                WHERE status = 'planned'
                AND is_deleted = false
                AND planned_date < CURRENT_DATE
            """))
            updated_count = result.rowcount
            print(f"   ✅ 已标记 {updated_count} 条行程为完成")

            # 2.2 关联未绑定日志的行程到对应日志
            print("\n🔄 步骤2: 关联行程到日志...")
            result = conn.execute(text("""
                UPDATE work_items wi
                SET worklog_id = wl.id
                FROM worklogs wl
                WHERE wi.owner_id = wl.owner_id
                AND wi.planned_date = wl.log_date
                AND wi.worklog_id IS NULL
                AND wi.status = 'completed'
                AND wi.planned_date < CURRENT_DATE
            """))
            linked_count = result.rowcount
            print(f"   ✅ 已关联 {linked_count} 条行程到日志")

            # 提交事务
            conn.commit()

            # 3. 验证结果
            print("\n📊 修复后验证:")
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM work_items
                WHERE status = 'planned'
                AND is_deleted = false
                AND planned_date < CURRENT_DATE
            """))
            after_count = result.scalar()
            print(f"   今天之前未完成的行程: {after_count} 条")

            print("\n" + "=" * 70)
            if after_count == 0:
                print("🎉 修复成功！所有历史行程已标记为完成")
            else:
                print(f"⚠️  仍有 {after_count} 条行程未修复，请检查")
            print("=" * 70)

            return after_count == 0

        except Exception as e:
            conn.rollback()
            print(f"\n❌ 修复失败: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
