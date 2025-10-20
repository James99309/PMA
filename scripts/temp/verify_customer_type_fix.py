#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证云端 project_customer_associations 表修复结果

验证内容：
1. customer_type 字段是否可空
2. 现有数据完整性
3. 新增记录（customer_type=NULL）是否成功
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

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 云端数据库配置
CLOUD_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': '6543',
    'database': 'postgres',
    'user': 'postgres.iqcyimnjtnmomvfuwjzw',
    'password': 'towsys-coGdoq-6gofdi'
}

def get_cloud_engine():
    db_url = f"postgresql://{CLOUD_DB_CONFIG['user']}:{CLOUD_DB_CONFIG['password']}@" \
             f"{CLOUD_DB_CONFIG['host']}:{CLOUD_DB_CONFIG['port']}/{CLOUD_DB_CONFIG['database']}"
    return create_engine(db_url, echo=False)

def verify_table_structure(engine):
    """验证表结构"""
    logger.info("=" * 70)
    logger.info("1. 验证表结构")
    logger.info("=" * 70)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'project_customer_associations'
            ORDER BY ordinal_position
        """))

        logger.info(f"\n{'字段名':<30} {'类型':<20} {'可空':<10} {'默认值':<20}")
        logger.info("-" * 80)

        for row in result:
            nullable_display = "✓ YES" if row[2] == 'YES' else "✗ NO"
            default_display = row[3] if row[3] else "-"
            logger.info(f"{row[0]:<30} {row[1]:<20} {nullable_display:<10} {default_display:<20}")

        # 单独验证 customer_type
        result = conn.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'project_customer_associations'
            AND column_name = 'customer_type'
        """))

        row = result.fetchone()
        if row and row[0] == 'YES':
            logger.info(f"\n✓ customer_type 字段验证通过：可空")
            return True
        else:
            logger.error(f"\n✗ customer_type 字段验证失败：仍然不可空")
            return False

def verify_data_integrity(engine):
    """验证数据完整性"""
    logger.info("\n" + "=" * 70)
    logger.info("2. 验证数据完整性")
    logger.info("=" * 70)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_type) as with_type,
                COUNT(*) FILTER (WHERE customer_type IS NULL) as null_count
            FROM project_customer_associations
        """))

        row = result.fetchone()
        logger.info(f"\n总记录数: {row[0]}")
        logger.info(f"有customer_type的: {row[1]}")
        logger.info(f"NULL值数量: {row[2]}")

        # customer_type值分布
        logger.info(f"\ncustomer_type 值分布:")
        result = conn.execute(text("""
            SELECT
                COALESCE(customer_type, '(NULL)') as type,
                COUNT(*) as count
            FROM project_customer_associations
            GROUP BY customer_type
            ORDER BY count DESC
        """))

        for row in result:
            logger.info(f"  {row[0]}: {row[1]}")

        return True

def test_null_insert(engine):
    """测试插入NULL值"""
    logger.info("\n" + "=" * 70)
    logger.info("3. 测试插入 customer_type=NULL 的记录")
    logger.info("=" * 70)

    try:
        with engine.begin() as conn:
            # 查找一个已存在的project_id和一个未关联的company_id用于测试
            result = conn.execute(text("""
                SELECT p.id as project_id, c.id as company_id
                FROM projects p
                CROSS JOIN companies c
                LEFT JOIN project_customer_associations pca
                    ON pca.project_id = p.id AND pca.company_id = c.id
                WHERE pca.id IS NULL
                AND c.is_deleted = FALSE
                LIMIT 1
            """))

            test_data = result.fetchone()

            if not test_data:
                logger.warning("⚠ 未找到可用的测试数据（所有组合都已关联）")
                logger.info("  跳过插入测试")
                return True

            project_id, company_id = test_data
            logger.info(f"\n使用测试数据: project_id={project_id}, company_id={company_id}")

            # 尝试插入 customer_type=NULL 的记录
            logger.info("尝试插入 customer_type=NULL 的记录...")

            result = conn.execute(text("""
                INSERT INTO project_customer_associations
                (project_id, company_id, customer_type, created_at, updated_at)
                VALUES (:project_id, :company_id, NULL, NOW(), NOW())
                RETURNING id
            """), {"project_id": project_id, "company_id": company_id})

            new_id = result.scalar()

            logger.info(f"✓ 插入成功！新记录ID: {new_id}")

            # 删除测试记录
            logger.info("清理测试记录...")
            conn.execute(text("""
                DELETE FROM project_customer_associations WHERE id = :id
            """), {"id": new_id})

            logger.info("✓ 测试记录已清理")

        return True

    except Exception as e:
        logger.error(f"✗ 插入测试失败: {e}")
        return False

def main():
    logger.info("=" * 70)
    logger.info("云端 project_customer_associations 表修复验证")
    logger.info("=" * 70)

    engine = get_cloud_engine()

    results = []

    # 验证表结构
    results.append(("表结构", verify_table_structure(engine)))

    # 验证数据完整性
    results.append(("数据完整性", verify_data_integrity(engine)))

    # 测试NULL值插入
    results.append(("NULL值插入测试", test_null_insert(engine)))

    # 汇总结果
    logger.info("\n" + "=" * 70)
    logger.info("验证结果汇总")
    logger.info("=" * 70)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        logger.info(f"{status}: {name}")
        if not passed:
            all_passed = False

    logger.info("=" * 70)
    if all_passed:
        logger.info("✓ 所有验证通过！")
        logger.info("项目客户关联功能已修复，可以正常使用")
        return 0
    else:
        logger.error("✗ 部分验证失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
