#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理本地数据库的quotations表customer_id错误数据
"""
import sys
import os
from datetime import datetime

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
    print(f"✅ 已加载配置文件: {dotenv_path}")
else:
    print("❌ 未找到.env配置文件")
    sys.exit(1)

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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_table_name = f'quotations_customer_backup_{timestamp}'

    logger.info("=" * 80)
    logger.info("清理本地数据库的quotations表customer_id错误数据")
    logger.info("=" * 80)

    try:
        with app.app_context():
            # 1. 验证连接
            logger.info("\n【步骤1：验证数据库连接】")
            result = db.session.execute(text("SELECT current_database(), version()"))
            db_name, version = result.fetchone()
            logger.info(f"  ✓ 数据库: {db_name}")
            logger.info(f"  ✓ 版本: {version[:80]}...")

            # 2. 创建备份表
            logger.info(f"\n【步骤2：创建备份表 {backup_table_name}】")
            db.session.execute(text(f"""
                CREATE TABLE {backup_table_name} AS
                SELECT * FROM quotations
            """))
            db.session.commit()

            result = db.session.execute(text(f"SELECT COUNT(*) FROM {backup_table_name}"))
            backup_count = result.scalar()
            logger.info(f"  ✓ 备份完成: {backup_count} 条记录")

            # 3. 查询需要清理的数据
            logger.info("\n【步骤3：查询需要清理的数据】")
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
            logger.info(f"  ✓ 发现疑似错误填充的记录: {suspect_count} 条")

            if suspect_count == 0:
                logger.info("  ✓ 无需清理，数据正常")
                return 0

            # 4. 修改字段为可空
            logger.info("\n【步骤4：修改customer_id字段为可空】")
            db.session.execute(text("""
                ALTER TABLE quotations
                ALTER COLUMN customer_id DROP NOT NULL
            """))
            db.session.commit()
            logger.info("  ✓ 字段已修改为可空")

            # 5. 清理错误数据
            logger.info("\n【步骤5：清理错误数据】")
            result = db.session.execute(text("""
                UPDATE quotations
                SET customer_id = NULL
                WHERE customer_id = 4
                AND NOT EXISTS (
                    SELECT 1 FROM project_customer_associations pca
                    WHERE pca.project_id = quotations.project_id AND pca.company_id = 4
                )
                AND (
                    contact_id IS NULL
                    OR NOT EXISTS (
                        SELECT 1 FROM contacts c
                        WHERE c.id = contact_id AND c.company_id = 4
                    )
                )
            """))
            db.session.commit()
            logger.info(f"  ✓ 已清理 {suspect_count} 条错误记录")

            # 6. 验证结果
            logger.info("\n【步骤6：验证清理结果】")

            # 检查客户4
            result = db.session.execute(text("SELECT COUNT(*) FROM quotations WHERE customer_id = 4"))
            customer_4_count = result.scalar()
            logger.info(f"  关联客户4的报价单: {customer_4_count} 条")

            # 统计总体情况
            result = db.session.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(customer_id) as with_customer,
                    COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count
                FROM quotations
            """))
            total, with_customer, null_count = result.fetchone()
            logger.info(f"  报价单总数: {total}")
            logger.info(f"  有customer_id: {with_customer} ({with_customer*100/total if total > 0 else 0:.1f}%)")
            logger.info(f"  customer_id为NULL: {null_count} ({null_count*100/total if total > 0 else 0:.1f}%)")

            # 7. 总结
            logger.info("\n" + "=" * 80)
            logger.info("✅ 清理完成")
            logger.info("=" * 80)
            logger.info(f"\n备份表: {backup_table_name}")
            logger.info(f"已清理: {suspect_count} 条错误记录")
            logger.info(f"客户4关联: {customer_4_count} 条（仅保留有效关联）")
            logger.info(f"\n如需回滚，执行以下SQL:")
            logger.info(f"  DROP TABLE quotations;")
            logger.info(f"  ALTER TABLE {backup_table_name} RENAME TO quotations;")
            logger.info("\n⚠️ 注意：代码模型已修改为nullable=True，需要重启应用生效")

            return 0

    except Exception as e:
        logger.error(f"\n❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()

        # 尝试回滚
        try:
            db.session.rollback()
            logger.info("  事务已回滚")
        except:
            pass

        return 1

if __name__ == '__main__':
    sys.exit(main())
