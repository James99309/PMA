#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复报价单customer_id=382的错误数据

问题：440个报价单被错误地批量设置为customer_id=382
解决：将这些报价单的customer_id设置为NULL，让用户手动选择正确客户

步骤：
1. 创建备份
2. 修改字段约束为可空
3. 将customer_id=382的报价单设为NULL
4. 验证修复结果
"""

from sqlalchemy import create_engine, text
from datetime import datetime

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def fix_customer_382(dry_run=True):
    engine = create_engine(DB_URL)

    mode = "预览模式" if dry_run else "执行模式"
    print("=" * 70)
    print(f"修复报价单 customer_id=382 的错误数据 [{mode}]")
    print("=" * 70)

    with engine.begin() as conn:
        # 1. 统计当前状态
        print("\n【1. 当前状态】")
        result = conn.execute(text("""
            SELECT COUNT(*) FROM quotations WHERE customer_id = 382
        """))
        count_382 = result.scalar()
        print(f"  customer_id=382 的报价单: {count_382} 个")

        if count_382 == 0:
            print("\n✓ 没有需要修复的数据")
            return True

        # 2. 检查字段约束
        print("\n【2. 字段约束】")
        result = conn.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'quotations' AND column_name = 'customer_id'
        """))
        is_nullable = result.scalar()
        print(f"  当前是否可空: {is_nullable}")

        if dry_run:
            print("\n【3. 预览将要执行的操作】")
            print(f"  - 创建备份表")
            print(f"  - 修改customer_id字段为可空")
            print(f"  - 将 {count_382} 个报价单的customer_id设为NULL")
            print("\n" + "=" * 70)
            print("这是预览模式，没有实际修改数据")
            print("要执行修复，请运行: python fix_quotation_customer_382.py --execute")
            print("=" * 70)
            return True

        # === 以下是实际执行 ===
        try:
            # 3. 创建备份表
            print("\n【3. 创建备份表】")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_table = f'quotations_customer_backup_{timestamp}'

            conn.execute(text(f"""
                CREATE TABLE {backup_table} AS
                SELECT id, quotation_number, customer_id, project_id, contact_id
                FROM quotations
                WHERE customer_id = 382
            """))
            print(f"  ✓ 已创建备份表: {backup_table}")

            # 4. 修改字段约束为可空
            print("\n【4. 修改字段约束为可空】")
            if is_nullable == 'NO':
                conn.execute(text("""
                    ALTER TABLE quotations
                    ALTER COLUMN customer_id DROP NOT NULL
                """))
                print("  ✓ 已将customer_id字段改为可空")
            else:
                print("  字段已经是可空的，跳过")

            # 5. 将customer_id=382的报价单设为NULL
            print("\n【5. 修复数据】")
            result = conn.execute(text("""
                UPDATE quotations
                SET customer_id = NULL
                WHERE customer_id = 382
            """))
            updated_count = result.rowcount
            print(f"  ✓ 已将 {updated_count} 个报价单的customer_id设为NULL")

            # 6. 验证
            print("\n【6. 验证修复结果】")
            result = conn.execute(text("""
                SELECT
                    COUNT(*) FILTER (WHERE customer_id = 382) as still_382,
                    COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count
                FROM quotations
            """))
            row = result.fetchone()
            print(f"  customer_id=382: {row[0]} 个")
            print(f"  customer_id=NULL: {row[1]} 个")

            if row[0] == 0:
                print("\n✓ 修复成功！")

                print("\n" + "=" * 70)
                print("后续步骤:")
                print("1. 前端表单保持客户必填验证")
                print("2. 用户编辑报价单时会被要求选择正确的客户")
                print(f"3. 如需回滚，可从备份表 {backup_table} 恢复")
                print("=" * 70)
                return True
            else:
                print("\n✗ 修复可能不完整")
                raise Exception("Still have records with customer_id=382")

        except Exception as e:
            print(f"\n✗ 执行失败: {e}")
            raise

if __name__ == '__main__':
    import sys
    dry_run = '--execute' not in sys.argv
    success = fix_customer_382(dry_run=dry_run)
    sys.exit(0 if success else 1)
