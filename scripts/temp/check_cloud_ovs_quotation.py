#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查云端OVS数据库的customer_id问题（只读查询）
"""
import os
import sys
import psycopg2
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OVS云端数据库连接URL
OVS_URL = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

def connect_to_ovs():
    """连接到OVS云端数据库"""
    from urllib.parse import urlparse
    parsed = urlparse(OVS_URL)

    db_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'dbname': parsed.path.lstrip('/'),
        'sslmode': 'require'
    }

    return psycopg2.connect(**db_params)

def main():
    logger.info("=" * 80)
    logger.info("检查云端OVS数据库的customer_id问题")
    logger.info("=" * 80)

    try:
        conn = connect_to_ovs()
        cursor = conn.cursor()

        # 1. 验证连接
        logger.info("\n【验证数据库连接】")
        cursor.execute("SELECT current_database(), version()")
        db_name, version = cursor.fetchone()
        logger.info(f"  数据库: {db_name}")
        logger.info(f"  版本: {version[:80]}...")

        # 2. 检查customer_id字段
        logger.info("\n【检查customer_id字段】")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'quotations' AND column_name = 'customer_id'
        """)
        field_info = cursor.fetchone()

        if not field_info:
            logger.info("  ✓ OVS数据库的quotations表没有customer_id字段")
            logger.info("  ✓ 不存在SP8D的问题")
            conn.close()
            return 0

        logger.info(f"  字段名: {field_info[0]}")
        logger.info(f"  类型: {field_info[1]}")
        logger.info(f"  可空: {field_info[2]}")
        logger.info(f"  默认值: {field_info[3]}")

        # 3. 统计报价单
        logger.info("\n【报价单统计】")
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_id) as with_customer,
                COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count
            FROM quotations
        """)
        total, with_customer, null_count = cursor.fetchone()
        logger.info(f"  总数: {total}")
        logger.info(f"  有customer_id: {with_customer} ({with_customer*100/total if total > 0 else 0:.1f}%)")
        logger.info(f"  customer_id为NULL: {null_count} ({null_count*100/total if total > 0 else 0:.1f}%)")

        # 4. 客户分布Top 10
        logger.info("\n【客户分布Top 10】")
        cursor.execute("""
            SELECT
                q.customer_id,
                c.company_name,
                COUNT(*) as count
            FROM quotations q
            LEFT JOIN companies c ON c.id = q.customer_id
            WHERE q.customer_id IS NOT NULL
            GROUP BY q.customer_id, c.company_name
            ORDER BY count DESC
            LIMIT 10
        """)

        for i, (cid, cname, count) in enumerate(cursor.fetchall(), 1):
            logger.info(f"  {i}. 客户ID {cid} ({cname}): {count} 个报价单")

        # 5. 检查客户4
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE customer_id = 4")
        customer_4_count = cursor.fetchone()[0]

        if customer_4_count > 0:
            logger.info(f"\n【客户4分析】")
            logger.info(f"  关联客户4的报价单: {customer_4_count} 个")

            # 查询客户4名称
            cursor.execute("SELECT company_name FROM companies WHERE id = 4")
            company_name_row = cursor.fetchone()
            if company_name_row:
                logger.info(f"  客户4名称: {company_name_row[0]}")

            # 疑似错误填充
            cursor.execute("""
                SELECT COUNT(*)
                FROM quotations q
                WHERE q.customer_id = 4
                AND NOT EXISTS (
                    SELECT 1 FROM project_customer_associations pca
                    WHERE pca.project_id = q.project_id AND pca.company_id = 4
                )
                AND (
                    q.contact_id IS NULL
                    OR NOT EXISTS (
                        SELECT 1 FROM contacts c
                        WHERE c.id = q.contact_id AND c.company_id = 4
                    )
                )
            """)
            suspect_count = cursor.fetchone()[0]
            logger.info(f"  疑似错误填充: {suspect_count} 个")

            if suspect_count > 0:
                logger.info(f"\n  ⚠️ OVS数据库也存在同样的问题！")
            else:
                logger.info(f"\n  ✓ 客户4的关联都是有效的")
        else:
            logger.info(f"\n【客户4检查】")
            logger.info(f"  ✓ 未发现客户4的关联")

        # 6. 检查迁移版本
        logger.info("\n【数据库迁移版本】")
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()[0]
        logger.info(f"  当前版本: {version}")

        # 7. 总结
        logger.info("\n" + "=" * 80)
        logger.info("📊 OVS vs SP8D 对比")
        logger.info("=" * 80)

        logger.info(f"\n【OVS云端数据库】")
        logger.info(f"  迁移版本: {version}")
        logger.info(f"  customer_id字段: 存在")
        logger.info(f"  字段可空: {field_info[2]}")
        logger.info(f"  报价单总数: {total}")
        logger.info(f"  有customer_id: {with_customer}")
        logger.info(f"  customer_id为NULL: {null_count}")
        logger.info(f"  关联客户4: {customer_4_count}")

        logger.info(f"\n【SP8D云端数据库】（参考）")
        logger.info(f"  customer_id字段: 存在")
        logger.info(f"  字段可空: YES（已修复）")
        logger.info(f"  报价单总数: 467")
        logger.info(f"  有customer_id: 9")
        logger.info(f"  customer_id为NULL: 458")
        logger.info(f"  关联客户4: 0（已清理）")

        conn.close()
        return 0

    except Exception as e:
        logger.error(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
