#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查本地数据库的customer_id问题（只读查询）
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

# 加载本地数据库配置（默认.env）
from dotenv import load_dotenv
dotenv_path = os.path.join(get_project_root(), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True)
else:
    print("⚠️ 未找到.env配置文件")

from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = create_app()

def main():
    logger.info("=" * 80)
    logger.info("检查本地数据库的customer_id问题")
    logger.info("=" * 80)

    try:
        with app.app_context():
            # 1. 验证连接
            logger.info("\n【验证数据库连接】")
            result = db.session.execute(text("SELECT current_database(), version()"))
            db_name, version = result.fetchone()
            logger.info(f"  数据库: {db_name}")
            logger.info(f"  版本: {version[:80]}...")

            # 2. 检查customer_id字段
            logger.info("\n【检查customer_id字段】")
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'quotations' AND column_name = 'customer_id'
            """))
            field_info = result.fetchone()

            if not field_info:
                logger.info("  ✓ 本地数据库的quotations表没有customer_id字段")
                logger.info("  ✓ 不存在SP8D的问题")
                return 0

            logger.info(f"  字段名: {field_info[0]}")
            logger.info(f"  类型: {field_info[1]}")
            logger.info(f"  可空: {field_info[2]}")
            logger.info(f"  默认值: {field_info[3]}")

            # 3. 统计报价单
            logger.info("\n【报价单统计】")
            result = db.session.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(customer_id) as with_customer,
                    COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count
                FROM quotations
            """))
            total, with_customer, null_count = result.fetchone()
            logger.info(f"  总数: {total}")
            logger.info(f"  有customer_id: {with_customer} ({with_customer*100/total if total > 0 else 0:.1f}%)")
            logger.info(f"  customer_id为NULL: {null_count} ({null_count*100/total if total > 0 else 0:.1f}%)")

            # 4. 客户分布Top 10
            logger.info("\n【客户分布Top 10】")
            result = db.session.execute(text("""
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
            """))

            for i, (cid, cname, count) in enumerate(result.fetchall(), 1):
                logger.info(f"  {i}. 客户ID {cid} ({cname}): {count} 个报价单")

            # 5. 检查客户4
            result = db.session.execute(text("SELECT COUNT(*) FROM quotations WHERE customer_id = 4"))
            customer_4_count = result.scalar()

            if customer_4_count > 0:
                logger.info(f"\n【客户4分析】")
                logger.info(f"  关联客户4的报价单: {customer_4_count} 个")

                # 查询客户4名称
                result = db.session.execute(text("SELECT company_name FROM companies WHERE id = 4"))
                company_name_row = result.fetchone()
                if company_name_row:
                    logger.info(f"  客户4名称: {company_name_row[0]}")

                # 疑似错误填充
                result = db.session.execute(text("""
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
                """))
                suspect_count = result.scalar()
                logger.info(f"  疑似错误填充: {suspect_count} 个")

                if suspect_count > 0:
                    logger.info(f"\n  ⚠️ 本地数据库也存在同样的问题！")
                else:
                    logger.info(f"\n  ✓ 客户4的关联都是有效的")
            else:
                logger.info(f"\n【客户4检查】")
                logger.info(f"  ✓ 未发现客户4的关联")

            # 6. 检查迁移版本
            logger.info("\n【数据库迁移版本】")
            result = db.session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            logger.info(f"  当前版本: {version}")

            # 7. 三库对比总结
            logger.info("\n" + "=" * 80)
            logger.info("📊 三个数据库对比")
            logger.info("=" * 80)

            logger.info(f"\n【本地数据库 (pma_local)】")
            logger.info(f"  迁移版本: {version}")
            logger.info(f"  customer_id字段: 存在")
            logger.info(f"  字段可空: {field_info[2]}")
            logger.info(f"  报价单总数: {total}")
            logger.info(f"  有customer_id: {with_customer}")
            logger.info(f"  customer_id为NULL: {null_count}")
            logger.info(f"  关联客户4: {customer_4_count}")

            logger.info(f"\n【SP8D云端数据库】（已修复）")
            logger.info(f"  customer_id字段: 存在")
            logger.info(f"  字段可空: YES（已修改）")
            logger.info(f"  报价单总数: 467")
            logger.info(f"  有customer_id: 9")
            logger.info(f"  customer_id为NULL: 458（已清理）")
            logger.info(f"  关联客户4: 0（已清理）")

            logger.info(f"\n【OVS云端数据库】（正常）")
            logger.info(f"  customer_id字段: 存在")
            logger.info(f"  字段可空: YES")
            logger.info(f"  报价单总数: 28")
            logger.info(f"  有customer_id: 7")
            logger.info(f"  customer_id为NULL: 21")
            logger.info(f"  关联客户4: 0（无问题）")

            return 0

    except Exception as e:
        logger.error(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
