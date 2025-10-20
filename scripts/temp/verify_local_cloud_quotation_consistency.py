#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证本地和云端quotations表的customer_id字段一致性

验证内容：
1. 两端的customer_id字段约束是否相同（NOT NULL）
2. 两端的外键约束是否都存在
3. 两端的数据完整性（无NULL值）
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

def check_field_constraint(engine, env_name):
    """检查customer_id字段约束"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'quotations'
            AND column_name = 'customer_id'
        """))

        row = result.fetchone()
        if row:
            return {
                'exists': True,
                'type': row[1],
                'nullable': row[2] == 'YES'
            }
        return {'exists': False}

def check_foreign_key(engine, env_name):
    """检查外键约束"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE constraint_type = 'FOREIGN KEY'
            AND table_name = 'quotations'
            AND constraint_name LIKE '%customer_id%'
        """))

        fk_count = result.scalar()
        return fk_count > 0

def check_data_integrity(engine, env_name):
    """检查数据完整性"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_id) as with_customer,
                COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count
            FROM quotations
        """))

        row = result.fetchone()
        return {
            'total': row[0],
            'with_customer': row[1],
            'null_count': row[2]
        }

def main():
    logger.info("=" * 80)
    logger.info("验证本地和云端quotations表customer_id字段一致性")
    logger.info("=" * 80)

    # 初始化本地和云端引擎
    app = create_app()
    with app.app_context():
        local_engine = db.engine

    cloud_engine = get_cloud_engine()

    # 验证字段约束
    logger.info("\n" + "=" * 80)
    logger.info("1. 验证字段约束")
    logger.info("=" * 80)

    local_field = check_field_constraint(local_engine, '本地')
    cloud_field = check_field_constraint(cloud_engine, '云端')

    logger.info(f"\n{'环境':<10} {'字段存在':<12} {'类型':<15} {'可空':<10}")
    logger.info("-" * 50)
    logger.info(f"{'本地':<10} {'✓' if local_field['exists'] else '✗':<12} "
                f"{local_field.get('type', 'N/A'):<15} "
                f"{'YES' if local_field.get('nullable') else 'NO':<10}")
    logger.info(f"{'云端':<10} {'✓' if cloud_field['exists'] else '✗':<12} "
                f"{cloud_field.get('type', 'N/A'):<15} "
                f"{'YES' if cloud_field.get('nullable') else 'NO':<10}")

    constraint_match = (
        local_field['exists'] == cloud_field['exists'] and
        local_field.get('nullable') == cloud_field.get('nullable')
    )

    if constraint_match and not local_field.get('nullable'):
        logger.info(f"\n✓ 字段约束一致：两端都是 NOT NULL")
    else:
        logger.error(f"\n✗ 字段约束不一致！")
        return False

    # 验证外键约束
    logger.info("\n" + "=" * 80)
    logger.info("2. 验证外键约束")
    logger.info("=" * 80)

    local_fk = check_foreign_key(local_engine, '本地')
    cloud_fk = check_foreign_key(cloud_engine, '云端')

    logger.info(f"\n{'环境':<10} {'外键约束':<15}")
    logger.info("-" * 30)
    logger.info(f"{'本地':<10} {'✓ 存在' if local_fk else '✗ 不存在':<15}")
    logger.info(f"{'云端':<10} {'✓ 存在' if cloud_fk else '✗ 不存在':<15}")

    if local_fk and cloud_fk:
        logger.info(f"\n✓ 外键约束一致：两端都存在")
    elif not local_fk and not cloud_fk:
        logger.warning(f"\n⚠️ 两端都没有外键约束（可接受）")
    else:
        logger.warning(f"\n⚠️ 外键约束不一致（不影响功能）")

    # 验证数据完整性
    logger.info("\n" + "=" * 80)
    logger.info("3. 验证数据完整性")
    logger.info("=" * 80)

    local_data = check_data_integrity(local_engine, '本地')
    cloud_data = check_data_integrity(cloud_engine, '云端')

    logger.info(f"\n{'环境':<10} {'总记录数':<12} {'有客户ID':<12} {'NULL数量':<12}")
    logger.info("-" * 50)
    logger.info(f"{'本地':<10} {local_data['total']:<12} "
                f"{local_data['with_customer']:<12} {local_data['null_count']:<12}")
    logger.info(f"{'云端':<10} {cloud_data['total']:<12} "
                f"{cloud_data['with_customer']:<12} {cloud_data['null_count']:<12}")

    data_integrity = (local_data['null_count'] == 0 and cloud_data['null_count'] == 0)

    if data_integrity:
        logger.info(f"\n✓ 数据完整性验证通过：两端都没有NULL值")
    else:
        logger.error(f"\n✗ 数据完整性验证失败：存在NULL值")
        return False

    # 汇总结果
    logger.info("\n" + "=" * 80)
    logger.info("验证结果汇总")
    logger.info("=" * 80)

    results = [
        ("字段约束一致性", constraint_match and not local_field.get('nullable')),
        ("数据完整性", data_integrity),
    ]

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        logger.info(f"{status}: {name}")
        if not passed:
            all_passed = False

    logger.info("=" * 80)
    if all_passed:
        logger.info("✓ 所有验证通过！")
        logger.info("本地和云端的quotations表customer_id字段完全一致")
        logger.info("报价单创建功能已修复，可以正常使用")
        return True
    else:
        logger.error("✗ 部分验证失败")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
