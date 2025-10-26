#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调查OVS数据库是否存在同样的customer_id问题（只读查询）
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

# 加载OVS数据库配置
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

def check_database_connection():
    """验证数据库连接"""
    logger.info("=" * 80)
    logger.info("验证OVS数据库连接")
    logger.info("=" * 80)

    with app.app_context():
        result = db.session.execute(text("SELECT current_database(), version()"))
        row = result.fetchone()
        logger.info(f"✓ 已连接到数据库: {row[0]}")
        logger.info(f"  版本: {row[1][:80]}...")
        return row[0]

def check_customer_id_field():
    """检查customer_id字段是否存在"""
    logger.info("\n" + "=" * 80)
    logger.info("检查quotations表的customer_id字段")
    logger.info("=" * 80)

    with app.app_context():
        result = db.session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'quotations' AND column_name = 'customer_id'
        """))

        row = result.fetchone()
        if row:
            logger.info(f"✓ customer_id字段存在")
            logger.info(f"  字段名: {row[0]}")
            logger.info(f"  数据类型: {row[1]}")
            logger.info(f"  是否可空: {row[2]}")
            logger.info(f"  默认值: {row[3]}")
            return True, row[2]
        else:
            logger.info("✗ customer_id字段不存在")
            return False, None

def analyze_quotation_data():
    """分析报价单数据"""
    logger.info("\n" + "=" * 80)
    logger.info("分析报价单数据")
    logger.info("=" * 80)

    with app.app_context():
        # 1. 总体统计
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

        logger.info(f"\n【报价单统计】")
        logger.info(f"  总数: {total}")
        logger.info(f"  有customer_id: {with_customer} ({with_customer*100/total if total > 0 else 0:.1f}%)")
        logger.info(f"  customer_id为NULL: {null_count} ({null_count*100/total if total > 0 else 0:.1f}%)")

        # 2. 客户分布
        logger.info(f"\n【客户分布Top 10】")
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

        for i, row in enumerate(result, 1):
            logger.info(f"  {i}. 客户ID {row[0]} ({row[1]}): {row[2]} 个报价单")

        # 3. 检查客户4
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM quotations WHERE customer_id = 4
        """))
        customer_4_count = result.scalar()

        if customer_4_count > 0:
            logger.info(f"\n【客户4 (SK海力士) 分析】")
            logger.info(f"  关联客户4的报价单: {customer_4_count} 个")

            # 查询客户4的名称
            result = db.session.execute(text("""
                SELECT company_name FROM companies WHERE id = 4
            """))
            company_name = result.scalar()
            if company_name:
                logger.info(f"  客户4名称: {company_name}")

            # 分析是否也是错误填充
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
                logger.info(f"\n  ⚠️ OVS数据库也存在同样的问题！")
                logger.info(f"  建议: 需要对OVS执行同样的清理操作")
        else:
            logger.info(f"\n【客户4检查】")
            logger.info(f"  ✓ 未发现客户4的异常关联")

        return total, with_customer, null_count, customer_4_count

def check_alembic_version():
    """检查数据库迁移版本"""
    logger.info("\n" + "=" * 80)
    logger.info("检查数据库迁移版本")
    logger.info("=" * 80)

    with app.app_context():
        result = db.session.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        logger.info(f"  当前版本: {version}")
        return version

def main():
    logger.info("=" * 80)
    logger.info("调查OVS数据库的customer_id问题")
    logger.info("=" * 80)

    try:
        # 1. 检查连接
        db_name = check_database_connection()

        # 2. 检查字段
        has_field, is_nullable = check_customer_id_field()

        if not has_field:
            logger.info("\n✓ OVS数据库的quotations表没有customer_id字段")
            logger.info("  不存在SP8D的问题")
            return 0

        # 3. 分析数据
        total, with_customer, null_count, customer_4_count = analyze_quotation_data()

        # 4. 检查版本
        version = check_alembic_version()

        # 5. 总结对比
        logger.info("\n" + "=" * 80)
        logger.info("📊 OVS vs SP8D 对比")
        logger.info("=" * 80)

        logger.info(f"\n【OVS数据库】")
        logger.info(f"  数据库名: {db_name}")
        logger.info(f"  迁移版本: {version}")
        logger.info(f"  customer_id字段: {'存在' if has_field else '不存在'}")
        logger.info(f"  字段可空: {is_nullable}")
        logger.info(f"  报价单总数: {total}")
        logger.info(f"  有customer_id: {with_customer}")
        logger.info(f"  customer_id为NULL: {null_count}")
        logger.info(f"  关联客户4: {customer_4_count}")

        logger.info(f"\n【SP8D数据库】（参考）")
        logger.info(f"  customer_id字段: 存在")
        logger.info(f"  字段可空: YES（已修复）")
        logger.info(f"  报价单总数: 467")
        logger.info(f"  有customer_id: 9")
        logger.info(f"  customer_id为NULL: 458")
        logger.info(f"  关联客户4: 0（已清理）")

        # 6. 建议
        logger.info("\n" + "=" * 80)
        logger.info("💡 建议")
        logger.info("=" * 80)

        if customer_4_count > 0:
            logger.info("⚠️ OVS数据库存在同样的问题！")
            logger.info("\n需要执行的操作：")
            logger.info("1. 备份OVS数据库")
            logger.info("2. 修改customer_id字段为可空")
            logger.info("3. 清理错误的customer_id数据")
            logger.info("4. 更新代码模型定义")
        else:
            logger.info("✓ OVS数据库状态正常")
            logger.info(f"  但需要确认字段约束是否一致: 当前为{is_nullable}")

        return 0

    except Exception as e:
        logger.error(f"\n❌ 调查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
