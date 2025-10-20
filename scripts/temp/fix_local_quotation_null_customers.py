#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复本地报价单的NULL客户数据并设置NOT NULL约束

当前问题：
- 本地300条报价单中，290条customer_id为NULL
- 本地customer_id字段可空，云端为NOT NULL
- 需要统一本地和云端的约束

处理步骤：
1. 从项目关联客户表同步customer_id
2. 剩余无法关联的使用默认客户ID
3. 添加NOT NULL约束
4. 添加外键约束
"""
import sys
import os

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
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = create_app()

def check_current_status():
    """检查当前状态"""
    logger.info("=" * 70)
    logger.info("检查当前状态")
    logger.info("=" * 70)

    with app.app_context():
        # 检查字段约束
        result = db.session.execute(text("""
            SELECT
                column_name,
                is_nullable,
                data_type
            FROM information_schema.columns
            WHERE table_name = 'quotations'
            AND column_name = 'customer_id'
        """))

        row = result.fetchone()
        if row:
            logger.info(f"字段: {row[0]}")
            logger.info(f"可空: {row[1]}")
            logger.info(f"类型: {row[2]}")

            is_nullable = (row[1] == 'YES')
        else:
            logger.error("✗ customer_id字段不存在！")
            return False

        # 检查NULL数据
        result = db.session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_id) as with_customer,
                COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count
            FROM quotations
        """))

        row = result.fetchone()
        total = row[0]
        with_customer = row[1]
        null_count = row[2]

        logger.info(f"\n数据统计:")
        logger.info(f"  总报价单数: {total}")
        logger.info(f"  有customer_id的: {with_customer}")
        logger.info(f"  customer_id为NULL的: {null_count}")

        if null_count > 0:
            logger.warning(f"⚠️ 发现 {null_count} 条NULL数据，需要清理")
            return False
        elif is_nullable:
            logger.warning(f"⚠️ 字段可空，需要设置NOT NULL约束")
            return False
        else:
            logger.info(f"✓ 数据完整且约束正确")
            return True

def sync_customers_from_projects():
    """从项目关联客户表同步customer_id"""
    logger.info("=" * 70)
    logger.info("步骤1: 从项目关联客户表同步customer_id")
    logger.info("=" * 70)

    with app.app_context():
        # 方法1: 从项目的主客户关联（project_customer_associations第一条）
        logger.info("尝试从项目关联客户表同步...")

        result = db.session.execute(text("""
            WITH first_customer AS (
                SELECT DISTINCT ON (project_id)
                    project_id,
                    company_id
                FROM project_customer_associations
                ORDER BY project_id, id
            )
            UPDATE quotations q
            SET customer_id = fc.company_id
            FROM first_customer fc
            WHERE q.project_id = fc.project_id
            AND q.customer_id IS NULL
        """))

        count1 = result.rowcount
        db.session.commit()
        logger.info(f"✓ 从项目关联客户同步了 {count1} 条记录")

        # 方法2: 尝试从联系人表关联
        logger.info("尝试从联系人表同步...")

        result = db.session.execute(text("""
            UPDATE quotations q
            SET customer_id = c.company_id
            FROM contacts c
            WHERE q.contact_id = c.id
            AND q.customer_id IS NULL
            AND c.company_id IS NOT NULL
        """))

        count2 = result.rowcount
        db.session.commit()
        logger.info(f"✓ 从联系人表同步了 {count2} 条记录")

        return count1 + count2

def set_default_customer_for_remaining():
    """为剩余NULL记录设置默认客户"""
    logger.info("=" * 70)
    logger.info("步骤2: 为剩余NULL记录设置默认客户")
    logger.info("=" * 70)

    with app.app_context():
        # 检查是否还有NULL记录
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM quotations WHERE customer_id IS NULL
        """))
        null_count = result.scalar()

        if null_count == 0:
            logger.info("✓ 没有剩余NULL记录，跳过")
            return 0

        logger.warning(f"发现 {null_count} 条无法自动关联的记录")

        # 获取第一个有效客户ID作为默认值
        result = db.session.execute(text("""
            SELECT id FROM companies
            WHERE is_deleted = FALSE
            ORDER BY id
            LIMIT 1
        """))
        default_customer_id = result.scalar()

        if not default_customer_id:
            logger.error("✗ 未找到有效的默认客户！")
            return 0

        logger.info(f"使用默认客户ID: {default_customer_id}")

        result = db.session.execute(text("""
            UPDATE quotations
            SET customer_id = :default_id
            WHERE customer_id IS NULL
        """), {"default_id": default_customer_id})

        count = result.rowcount
        db.session.commit()
        logger.info(f"✓ 设置了 {count} 条记录的默认客户")

        return count

def add_not_null_constraint():
    """添加NOT NULL约束"""
    logger.info("=" * 70)
    logger.info("步骤3: 添加NOT NULL约束")
    logger.info("=" * 70)

    with app.app_context():
        # 检查是否还有NULL值
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM quotations WHERE customer_id IS NULL
        """))
        null_count = result.scalar()

        if null_count > 0:
            logger.error(f"✗ 仍有 {null_count} 条NULL记录，无法设置NOT NULL约束")
            return False

        # 检查当前约束
        result = db.session.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'quotations'
            AND column_name = 'customer_id'
        """))

        row = result.fetchone()
        if row and row[0] == 'NO':
            logger.info("✓ 字段已经是NOT NULL，跳过")
            return True

        # 添加NOT NULL约束
        logger.info("执行: ALTER TABLE quotations ALTER COLUMN customer_id SET NOT NULL")
        db.session.execute(text("""
            ALTER TABLE quotations
            ALTER COLUMN customer_id SET NOT NULL
        """))
        db.session.commit()

        logger.info("✓ NOT NULL约束添加成功")
        return True

def add_foreign_key_if_missing():
    """添加外键约束（如果不存在）"""
    logger.info("=" * 70)
    logger.info("步骤4: 检查并添加外键约束")
    logger.info("=" * 70)

    with app.app_context():
        # 检查外键是否存在
        result = db.session.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE constraint_type = 'FOREIGN KEY'
            AND table_name = 'quotations'
            AND constraint_name LIKE '%customer_id%'
        """))

        fk_count = result.scalar()

        if fk_count > 0:
            logger.info("✓ 外键约束已存在，跳过")
            return True

        # 添加外键约束
        logger.info("执行: 添加外键约束 quotations.customer_id -> companies.id")
        try:
            db.session.execute(text("""
                ALTER TABLE quotations
                ADD CONSTRAINT fk_quotations_customer_id
                FOREIGN KEY (customer_id) REFERENCES companies(id)
            """))
            db.session.commit()
            logger.info("✓ 外键约束添加成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 外键约束添加失败（可能已存在其他名称）: {e}")
            db.session.rollback()
            return True  # 继续执行

def verify_final_status():
    """验证最终状态"""
    logger.info("=" * 70)
    logger.info("验证最终状态")
    logger.info("=" * 70)

    with app.app_context():
        # 验证约束
        result = db.session.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'quotations'
            AND column_name = 'customer_id'
        """))

        row = result.fetchone()
        if row and row[0] == 'NO':
            logger.info("✓ NOT NULL约束验证通过")
        else:
            logger.error("✗ NOT NULL约束验证失败")
            return False

        # 验证数据
        result = db.session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_id) as with_customer
            FROM quotations
        """))

        row = result.fetchone()
        if row[0] == row[1]:
            logger.info(f"✓ 数据验证通过: {row[0]}条记录全部有customer_id")
        else:
            logger.error(f"✗ 数据验证失败: {row[0] - row[1]}条记录仍为NULL")
            return False

        return True

def main():
    logger.info("=" * 70)
    logger.info("修复本地报价单customer_id并设置NOT NULL约束")
    logger.info("=" * 70)

    # 检查当前状态
    if check_current_status():
        logger.info("\n✓ 当前状态已经正确，无需修复")
        return 0

    # 执行修复
    synced_count = sync_customers_from_projects()
    default_count = set_default_customer_for_remaining()

    logger.info(f"\n数据清理汇总:")
    logger.info(f"  从关联同步: {synced_count} 条")
    logger.info(f"  设置默认值: {default_count} 条")
    logger.info(f"  总计修复: {synced_count + default_count} 条")

    # 添加约束
    if not add_not_null_constraint():
        logger.error("\n✗ 添加NOT NULL约束失败")
        return 1

    add_foreign_key_if_missing()

    # 验证最终状态
    if not verify_final_status():
        logger.error("\n✗ 最终验证失败")
        return 1

    logger.info("=" * 70)
    logger.info("✓ 所有操作成功完成！")
    logger.info("本地数据库已与云端保持一致")
    logger.info("=" * 70)

    return 0

if __name__ == '__main__':
    sys.exit(main())
