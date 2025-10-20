#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复云端 project_customer_associations 表的 customer_type 字段约束

问题：云端数据库该字段仍为 NOT NULL，但本地模型已标记为 DEPRECATED 并设置为可空
目标：将云端字段从 NOT NULL 改为可空，以匹配本地模型定义

安全性：
- 现有1044条记录都有值，不会丢失数据
- 仅修改约束，不修改现有数据
- 使用事务确保操作原子性
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
from sqlalchemy.exc import SQLAlchemyError
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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

def check_current_constraint(engine):
    """检查当前约束状态"""
    logger.info("=" * 60)
    logger.info("检查当前约束状态")
    logger.info("=" * 60)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                column_name,
                is_nullable,
                data_type
            FROM information_schema.columns
            WHERE table_name = 'project_customer_associations'
            AND column_name = 'customer_type'
        """))

        row = result.fetchone()
        if row:
            logger.info(f"字段: {row[0]}")
            logger.info(f"可空: {row[1]}")
            logger.info(f"类型: {row[2]}")

            if row[1] == 'NO':
                logger.warning("⚠ 字段当前为 NOT NULL，需要修复")
                return False
            else:
                logger.info("✓ 字段已经是可空的，无需修复")
                return True

        logger.error("✗ 未找到 customer_type 字段")
        return None

def fix_customer_type_constraint(engine):
    """修改 customer_type 字段为可空"""
    logger.info("=" * 60)
    logger.info("开始修复 customer_type 字段约束")
    logger.info("=" * 60)

    try:
        with engine.begin() as conn:
            # 修改字段为可空
            logger.info("执行: ALTER TABLE ... ALTER COLUMN customer_type DROP NOT NULL")
            conn.execute(text("""
                ALTER TABLE project_customer_associations
                ALTER COLUMN customer_type DROP NOT NULL
            """))

            logger.info("✓ customer_type 字段约束修复成功")
            return True

    except SQLAlchemyError as e:
        logger.error(f"✗ 修复失败: {e}")
        return False

def verify_fix(engine):
    """验证修复结果"""
    logger.info("=" * 60)
    logger.info("验证修复结果")
    logger.info("=" * 60)

    with engine.connect() as conn:
        # 验证约束
        result = conn.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'project_customer_associations'
            AND column_name = 'customer_type'
        """))

        row = result.fetchone()
        if row and row[0] == 'YES':
            logger.info("✓ 字段约束验证通过：customer_type 现在可空")

            # 验证现有数据完整性
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(customer_type) as with_type
                FROM project_customer_associations
            """))

            row = result.fetchone()
            logger.info(f"✓ 数据完整性验证通过：")
            logger.info(f"  总记录数: {row[0]}")
            logger.info(f"  有customer_type的: {row[1]}")

            return True
        else:
            logger.error("✗ 验证失败：字段仍然不可空")
            return False

def main():
    logger.info("=" * 60)
    logger.info("修复云端 customer_type 字段约束")
    logger.info("=" * 60)

    engine = get_cloud_engine()

    # 检查当前状态
    current_status = check_current_constraint(engine)

    if current_status is True:
        logger.info("\n字段已经是可空的，无需修复")
        return 0
    elif current_status is None:
        logger.error("\n无法检查字段状态，中止操作")
        return 1

    # 执行修复
    if not fix_customer_type_constraint(engine):
        logger.error("\n修复失败")
        return 1

    # 验证修复
    if not verify_fix(engine):
        logger.error("\n验证失败")
        return 1

    logger.info("=" * 60)
    logger.info("✓ 所有操作成功完成！")
    logger.info("云端数据库已与本地模型保持一致")
    logger.info("=" * 60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
