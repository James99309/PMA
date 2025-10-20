#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库同步验证脚本

验证云端SP8D数据库是否已成功同步所有关键字段
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

from sqlalchemy import create_engine, text, inspect
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

def check_field(engine, table, column):
    """检查字段是否存在并返回详细信息"""
    inspector = inspect(engine)
    columns = {col['name']: col for col in inspector.get_columns(table)}

    if column in columns:
        col_info = columns[column]
        return True, col_info
    return False, None

def verify_quotations_customer_id(engine):
    """验证quotations.customer_id字段"""
    logger.info("=" * 70)
    logger.info("1. 验证 quotations.customer_id 字段")
    logger.info("=" * 70)

    exists, col_info = check_field(engine, 'quotations', 'customer_id')

    if exists:
        logger.info(f"✓ 字段存在")
        logger.info(f"  类型: {col_info['type']}")
        logger.info(f"  可空: {col_info['nullable']}")

        # 检查数据完整性
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(customer_id) as with_customer,
                    COUNT(DISTINCT customer_id) as unique_customers
                FROM quotations
            """))
            row = result.fetchone()
            logger.info(f"  总报价单数: {row[0]}")
            logger.info(f"  有客户ID的: {row[1]}")
            logger.info(f"  关联客户数: {row[2]}")

            # 检查外键约束
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_name = 'quotations'
                AND constraint_name LIKE '%customer_id%'
            """))
            fk_count = result.scalar()
            if fk_count > 0:
                logger.info(f"  ✓ 外键约束已建立")
            else:
                logger.warning(f"  ⚠ 未找到外键约束")

        return True
    else:
        logger.error("✗ 字段不存在")
        return False

def verify_companies_source(engine):
    """验证companies.source字段"""
    logger.info("\n" + "=" * 70)
    logger.info("2. 验证 companies.source 字段")
    logger.info("=" * 70)

    exists, col_info = check_field(engine, 'companies', 'source')

    if exists:
        logger.info(f"✓ 字段存在")
        logger.info(f"  类型: {col_info['type']}")
        logger.info(f"  可空: {col_info['nullable']}")

        # 检查数据分布
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    source,
                    COUNT(*) as count
                FROM companies
                WHERE source IS NOT NULL
                GROUP BY source
                ORDER BY count DESC
            """))

            source_data = result.fetchall()
            if source_data:
                logger.info(f"  数据分布:")
                for source, count in source_data:
                    logger.info(f"    {source}: {count}")
            else:
                logger.info(f"  暂无数据")

        return True
    else:
        logger.error("✗ 字段不存在")
        return False

def verify_role_permissions_content_filters(engine):
    """验证role_permissions.content_filters字段"""
    logger.info("\n" + "=" * 70)
    logger.info("3. 验证 role_permissions.content_filters 字段")
    logger.info("=" * 70)

    exists, col_info = check_field(engine, 'role_permissions', 'content_filters')

    if exists:
        logger.info(f"✓ 字段存在")
        logger.info(f"  类型: {col_info['type']}")
        logger.info(f"  可空: {col_info['nullable']}")

        # 检查数据使用情况
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(content_filters) as with_filters
                FROM role_permissions
            """))
            row = result.fetchone()
            logger.info(f"  总权限记录: {row[0]}")
            logger.info(f"  设置过滤的: {row[1]}")

        return True
    else:
        logger.error("✗ 字段不存在")
        return False

def verify_settlement_orders_business_type(engine):
    """验证settlement_orders业务类型字段"""
    logger.info("\n" + "=" * 70)
    logger.info("4. 验证 settlement_orders 业务类型字段")
    logger.info("=" * 70)

    fields = ['is_direct_contract', 'is_factory_pickup']
    all_exist = True

    for field in fields:
        exists, col_info = check_field(engine, 'settlement_orders', field)

        if exists:
            logger.info(f"✓ {field} 字段存在")
            logger.info(f"  类型: {col_info['type']}")
            logger.info(f"  可空: {col_info['nullable']}")
            logger.info(f"  默认值: {col_info.get('default', 'N/A')}")
        else:
            logger.error(f"✗ {field} 字段不存在")
            all_exist = False

    # 检查数据统计
    if all_exist:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_direct_contract THEN 1 ELSE 0 END) as direct_count,
                    SUM(CASE WHEN is_factory_pickup THEN 1 ELSE 0 END) as pickup_count
                FROM settlement_orders
            """))
            row = result.fetchone()
            logger.info(f"\n  数据统计:")
            logger.info(f"    总结算单数: {row[0]}")
            logger.info(f"    厂商直签: {row[1]}")
            logger.info(f"    厂家提货: {row[2]}")

    return all_exist

def main():
    logger.info("=" * 70)
    logger.info("云端数据库同步验证")
    logger.info("=" * 70)

    engine = get_cloud_engine()

    results = []
    results.append(("quotations.customer_id", verify_quotations_customer_id(engine)))
    results.append(("companies.source", verify_companies_source(engine)))
    results.append(("role_permissions.content_filters", verify_role_permissions_content_filters(engine)))
    results.append(("settlement_orders 业务类型字段", verify_settlement_orders_business_type(engine)))

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
        logger.info("✓ 所有验证通过！云端数据库已成功同步")
        return 0
    else:
        logger.error("✗ 部分验证失败，请检查上述错误")
        return 1

if __name__ == '__main__':
    sys.exit(main())
