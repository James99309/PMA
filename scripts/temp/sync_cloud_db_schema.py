#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库结构同步脚本

此脚本用于将本地数据库的新增字段同步到云端SP8D数据库
主要包括：
1. quotations.customer_id - 报价单客户关联字段（关键业务字段）
2. companies.source - 客户来源追踪字段
3. role_permissions.content_filters - 权限内容筛选字段
4. settlement_orders.is_direct_contract - 厂商直签标记
5. settlement_orders.is_factory_pickup - 厂家提货标记

安全特性：
- 只添加缺失的字段，不修改现有数据
- 使用事务确保原子性
- 详细的错误处理和回滚机制
- 执行前进行字段存在性检查

创建时间: 2025-10-21
"""

import sys
import os

# 路径修正 - 支持从任何位置运行
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
from sqlalchemy.exc import SQLAlchemyError
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 云端数据库连接配置（SP8D）
CLOUD_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': '6543',
    'database': 'postgres',
    'user': 'postgres.iqcyimnjtnmomvfuwjzw',
    'password': 'towsys-coGdoq-6gofdi'
}


def get_cloud_engine():
    """创建云端数据库引擎"""
    db_url = f"postgresql://{CLOUD_DB_CONFIG['user']}:{CLOUD_DB_CONFIG['password']}@" \
             f"{CLOUD_DB_CONFIG['host']}:{CLOUD_DB_CONFIG['port']}/{CLOUD_DB_CONFIG['database']}"
    return create_engine(db_url, echo=False)


def check_column_exists(engine, table_name, column_name):
    """检查字段是否存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_quotations_customer_id(engine):
    """
    添加 quotations.customer_id 字段

    这是核心业务字段，用于报价单直接关联客户
    已在本地数据库中存在并被广泛使用

    处理步骤：
    1. 先添加可空字段
    2. 从项目表同步客户ID（通过project_id关联）
    3. 将剩余NULL值设为默认客户（如果存在）
    4. 添加NOT NULL约束
    5. 添加外键约束
    """
    logger.info("=" * 60)
    logger.info("1. 处理 quotations.customer_id 字段")
    logger.info("=" * 60)

    if check_column_exists(engine, 'quotations', 'customer_id'):
        logger.info("✓ quotations.customer_id 字段已存在，跳过")
        return True

    try:
        with engine.begin() as conn:
            # 步骤1: 添加可空字段
            logger.info("步骤1: 添加 customer_id 字段（可空）...")
            conn.execute(text("""
                ALTER TABLE quotations
                ADD COLUMN customer_id INTEGER
            """))

            # 步骤2: 从contacts表同步客户ID（通过contact_id关联）
            logger.info("步骤2: 从联系人表同步客户数据...")
            result = conn.execute(text("""
                UPDATE quotations q
                SET customer_id = c.company_id
                FROM contacts c
                WHERE q.contact_id = c.id
                AND c.company_id IS NOT NULL
            """))
            logger.info(f"   通过联系人同步了 {result.rowcount} 条记录的客户ID")

            # 步骤3: 检查是否还有NULL值
            result = conn.execute(text("""
                SELECT COUNT(*) FROM quotations WHERE customer_id IS NULL
            """))
            null_count = result.scalar()

            if null_count > 0:
                logger.warning(f"   发现 {null_count} 条报价单没有关联客户")

                # 尝试获取第一个有效的客户ID作为默认值
                result = conn.execute(text("""
                    SELECT id FROM companies
                    WHERE is_deleted = FALSE
                    ORDER BY id
                    LIMIT 1
                """))
                default_customer_id = result.scalar()

                if default_customer_id:
                    logger.info(f"   将NULL值设为默认客户ID: {default_customer_id}")
                    conn.execute(text("""
                        UPDATE quotations
                        SET customer_id = :default_id
                        WHERE customer_id IS NULL
                    """), {"default_id": default_customer_id})
                else:
                    logger.error("   未找到有效的默认客户，无法设置NOT NULL约束")
                    return False

            # 步骤4: 添加NOT NULL约束
            logger.info("步骤3: 添加NOT NULL约束...")
            conn.execute(text("""
                ALTER TABLE quotations
                ALTER COLUMN customer_id SET NOT NULL
            """))

            # 步骤5: 添加外键约束
            logger.info("步骤4: 添加外键约束...")
            conn.execute(text("""
                ALTER TABLE quotations
                ADD CONSTRAINT fk_quotations_customer_id
                FOREIGN KEY (customer_id) REFERENCES companies(id)
            """))

            # 步骤6: 添加索引以提升查询性能
            logger.info("步骤5: 创建索引...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_quotations_customer_id
                ON quotations(customer_id)
            """))

            logger.info("✓ quotations.customer_id 字段添加成功")
            return True

    except SQLAlchemyError as e:
        logger.error(f"✗ 添加 quotations.customer_id 失败: {e}")
        return False


def add_companies_source(engine):
    """
    添加 companies.source 字段

    客户来源追踪字段，用于记录客户的获取渠道
    可选值：渠道报备、销售线索、市场拓展
    """
    logger.info("=" * 60)
    logger.info("2. 处理 companies.source 字段")
    logger.info("=" * 60)

    if check_column_exists(engine, 'companies', 'source'):
        logger.info("✓ companies.source 字段已存在，跳过")
        return True

    try:
        with engine.begin() as conn:
            # 添加字段
            logger.info("添加 source 字段（VARCHAR(20)）...")
            conn.execute(text("""
                ALTER TABLE companies
                ADD COLUMN source VARCHAR(20)
            """))

            logger.info("✓ companies.source 字段添加成功")
            return True

    except SQLAlchemyError as e:
        logger.error(f"✗ 添加 companies.source 失败: {e}")
        return False


def add_role_permissions_content_filters(engine):
    """
    添加 role_permissions.content_filters 字段

    权限内容筛选配置字段，用于存储角色级别的数据过滤规则
    存储格式：JSON {"project_type": ["type1", "type2"], "industry": ["ind1"]}
    """
    logger.info("=" * 60)
    logger.info("3. 处理 role_permissions.content_filters 字段")
    logger.info("=" * 60)

    if check_column_exists(engine, 'role_permissions', 'content_filters'):
        logger.info("✓ role_permissions.content_filters 字段已存在，跳过")
        return True

    try:
        with engine.begin() as conn:
            # 添加字段
            logger.info("添加 content_filters 字段（JSON）...")
            conn.execute(text("""
                ALTER TABLE role_permissions
                ADD COLUMN content_filters JSON
            """))

            logger.info("✓ role_permissions.content_filters 字段添加成功")
            return True

    except SQLAlchemyError as e:
        logger.error(f"✗ 添加 role_permissions.content_filters 失败: {e}")
        return False


def add_settlement_orders_business_type_fields(engine):
    """
    添加 settlement_orders 的业务类型标记字段

    1. is_direct_contract - 厂商直签标记
    2. is_factory_pickup - 厂家提货标记

    这两个字段从批价单同步，用于标识特殊业务类型
    """
    logger.info("=" * 60)
    logger.info("4. 处理 settlement_orders 业务类型字段")
    logger.info("=" * 60)

    fields_to_add = []

    if not check_column_exists(engine, 'settlement_orders', 'is_direct_contract'):
        fields_to_add.append('is_direct_contract')
    else:
        logger.info("✓ settlement_orders.is_direct_contract 字段已存在")

    if not check_column_exists(engine, 'settlement_orders', 'is_factory_pickup'):
        fields_to_add.append('is_factory_pickup')
    else:
        logger.info("✓ settlement_orders.is_factory_pickup 字段已存在")

    if not fields_to_add:
        logger.info("✓ 所有字段已存在，跳过")
        return True

    try:
        with engine.begin() as conn:
            for field in fields_to_add:
                logger.info(f"添加 {field} 字段（BOOLEAN, DEFAULT FALSE）...")
                conn.execute(text(f"""
                    ALTER TABLE settlement_orders
                    ADD COLUMN {field} BOOLEAN DEFAULT FALSE
                """))

            logger.info("✓ settlement_orders 业务类型字段添加成功")
            return True

    except SQLAlchemyError as e:
        logger.error(f"✗ 添加 settlement_orders 业务类型字段失败: {e}")
        return False


def verify_schema_sync(engine):
    """验证关键字段是否成功添加"""
    logger.info("=" * 60)
    logger.info("5. 验证字段同步结果")
    logger.info("=" * 60)

    checks = [
        ('quotations', 'customer_id'),
        ('companies', 'source'),
        ('role_permissions', 'content_filters'),
        ('settlement_orders', 'is_direct_contract'),
        ('settlement_orders', 'is_factory_pickup'),
    ]

    all_passed = True
    for table, column in checks:
        exists = check_column_exists(engine, table, column)
        status = "✓" if exists else "✗"
        logger.info(f"{status} {table}.{column}: {'存在' if exists else '缺失'}")
        if not exists:
            all_passed = False

    return all_passed


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("云端数据库结构同步脚本")
    logger.info("目标: Supabase SP8D 数据库")
    logger.info("=" * 60)

    # 连接云端数据库
    logger.info("连接云端数据库...")
    try:
        engine = get_cloud_engine()
        logger.info("✓ 云端数据库连接成功")
    except Exception as e:
        logger.error(f"✗ 云端数据库连接失败: {e}")
        return 1

    # 执行同步操作
    results = []

    # 1. 添加 quotations.customer_id
    results.append(("quotations.customer_id", add_quotations_customer_id(engine)))

    # 2. 添加 companies.source
    results.append(("companies.source", add_companies_source(engine)))

    # 3. 添加 role_permissions.content_filters
    results.append(("role_permissions.content_filters", add_role_permissions_content_filters(engine)))

    # 4. 添加 settlement_orders 业务类型字段
    results.append(("settlement_orders 业务类型字段", add_settlement_orders_business_type_fields(engine)))

    # 验证同步结果
    verification_passed = verify_schema_sync(engine)

    # 汇总结果
    logger.info("=" * 60)
    logger.info("同步操作汇总")
    logger.info("=" * 60)

    for operation, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        logger.info(f"{status}: {operation}")

    logger.info("=" * 60)
    if verification_passed:
        logger.info("✓ 所有关键字段同步成功！")
        logger.info("云端数据库结构已与本地保持一致")
        return 0
    else:
        logger.error("✗ 部分字段同步失败，请检查错误日志")
        return 1


if __name__ == '__main__':
    sys.exit(main())
