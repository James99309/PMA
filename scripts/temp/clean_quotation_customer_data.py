#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理报价单customer_id错误数据并修改字段约束

执行内容：
1. 分析当前数据状态
2. 识别并清理错误的customer_id
3. 修改字段为可空
4. 复盘修改结果
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

# 加载云端数据库配置
from dotenv import load_dotenv
dotenv_path = os.path.join(get_project_root(), '.env.sp8d.backup')
load_dotenv(dotenv_path, override=True)

from app import create_app, db
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = create_app()

# 存储修改前后的数据对比
results = {
    'before': {},
    'after': {},
    'modified_quotations': [],
    'backup_table': None
}

def verify_database_connection():
    """验证数据库连接"""
    logger.info("=" * 80)
    logger.info("步骤1: 验证数据库连接")
    logger.info("=" * 80)

    with app.app_context():
        result = db.session.execute(text("SELECT current_database(), version()"))
        row = result.fetchone()
        logger.info(f"✓ 已连接到数据库: {row[0]}")
        logger.info(f"  版本: {row[1][:80]}...")
        return True

def analyze_current_status():
    """分析当前数据状态"""
    logger.info("\n" + "=" * 80)
    logger.info("步骤2: 分析当前数据状态")
    logger.info("=" * 80)

    with app.app_context():
        # 1. 字段约束状态
        result = db.session.execute(text("""
            SELECT is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'quotations' AND column_name = 'customer_id'
        """))
        row = result.fetchone()
        logger.info(f"\n【字段约束】")
        logger.info(f"  是否可空: {row[0]}")
        logger.info(f"  默认值: {row[1]}")
        results['before']['nullable'] = row[0]

        # 2. 报价单总体统计
        result = db.session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_id) as with_customer,
                COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count,
                COUNT(*) FILTER (WHERE customer_id = 4) as customer_4_count
            FROM quotations
        """))
        row = result.fetchone()
        logger.info(f"\n【报价单统计】")
        logger.info(f"  总数: {row[0]}")
        logger.info(f"  有customer_id: {row[1]} ({row[1]*100/row[0]:.1f}%)")
        logger.info(f"  customer_id为NULL: {row[2]}")
        logger.info(f"  关联客户4: {row[3]} ({row[3]*100/row[0]:.1f}%)")

        results['before']['total'] = row[0]
        results['before']['with_customer'] = row[1]
        results['before']['null_count'] = row[2]
        results['before']['customer_4_count'] = row[3]

        # 3. 客户4的详细分析
        logger.info(f"\n【客户4 (SK海力士) 详细分析】")

        # 3.1 项目关联客户包含客户4的（真实关联）
        result = db.session.execute(text("""
            SELECT COUNT(*)
            FROM quotations q
            WHERE q.customer_id = 4
            AND EXISTS (
                SELECT 1
                FROM project_customer_associations pca
                WHERE pca.project_id = q.project_id AND pca.company_id = 4
            )
        """))
        project_match = result.scalar()
        logger.info(f"  项目关联包含客户4: {project_match} 个（真实关联✓）")

        # 3.2 联系人属于客户4的（真实关联）
        result = db.session.execute(text("""
            SELECT COUNT(*)
            FROM quotations q
            JOIN contacts c ON c.id = q.contact_id
            WHERE q.customer_id = 4 AND c.company_id = 4
        """))
        contact_match = result.scalar()
        logger.info(f"  联系人属于客户4: {contact_match} 个（真实关联✓）")

        # 3.3 疑似错误填充（需要清理）
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
        logger.info(f"  ⚠️ 疑似错误填充: {suspect_count} 个（需清理）")

        results['before']['project_match'] = project_match
        results['before']['contact_match'] = contact_match
        results['before']['suspect_count'] = suspect_count

        # 4. 展示疑似错误的报价单示例
        logger.info(f"\n【疑似错误的报价单示例】（前10个）")
        result = db.session.execute(text("""
            SELECT
                q.id,
                q.quotation_number,
                q.project_id,
                p.project_name,
                q.created_at::date,
                (
                    SELECT string_agg(pca.company_id::text, ',')
                    FROM project_customer_associations pca
                    WHERE pca.project_id = q.project_id
                    LIMIT 5
                ) as project_customers
            FROM quotations q
            LEFT JOIN projects p ON p.id = q.project_id
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
            ORDER BY q.id
            LIMIT 10
        """))

        for row in result:
            logger.info(f"  {row[1]} | 项目: {row[3]} | 项目客户IDs: [{row[5]}] | 创建: {row[4]}")

        return suspect_count > 0

def create_backup_table():
    """创建备份表"""
    logger.info("\n" + "=" * 80)
    logger.info("步骤3: 创建备份表")
    logger.info("=" * 80)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_table = f'quotations_customer_backup_{timestamp}'

    with app.app_context():
        logger.info(f"创建备份表: {backup_table}")
        db.session.execute(text(f"""
            DROP TABLE IF EXISTS {backup_table}
        """))

        db.session.execute(text(f"""
            CREATE TABLE {backup_table} AS
            SELECT
                id,
                quotation_number,
                customer_id,
                project_id,
                contact_id,
                created_at,
                updated_at
            FROM quotations
        """))
        db.session.commit()

        # 统计备份数据
        result = db.session.execute(text(f"""
            SELECT COUNT(*) FROM {backup_table}
        """))
        count = result.scalar()
        logger.info(f"✓ 已备份 {count} 条报价单数据")

        results['backup_table'] = backup_table
        return backup_table

def clean_suspect_customer_data():
    """清理疑似错误的customer_id"""
    logger.info("\n" + "=" * 80)
    logger.info("步骤5: 清理疑似错误的customer_id")
    logger.info("=" * 80)

    with app.app_context():
        # 记录即将修改的报价单
        logger.info("记录即将修改的报价单...")
        result = db.session.execute(text("""
            SELECT
                q.id,
                q.quotation_number,
                q.customer_id,
                q.project_id,
                p.project_name
            FROM quotations q
            LEFT JOIN projects p ON p.id = q.project_id
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

        to_modify = result.fetchall()
        logger.info(f"找到 {len(to_modify)} 个需要清理的报价单")

        # 保存修改列表
        for row in to_modify:
            results['modified_quotations'].append({
                'id': row[0],
                'quotation_number': row[1],
                'old_customer_id': row[2],
                'project_id': row[3],
                'project_name': row[4]
            })

        # 执行清理
        logger.info("执行清理操作...")
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

        modified_count = result.rowcount
        db.session.commit()

        logger.info(f"✓ 已将 {modified_count} 个报价单的customer_id改为NULL")
        results['modified_count'] = modified_count

        return modified_count

def alter_column_to_nullable():
    """修改字段为可空"""
    logger.info("\n" + "=" * 80)
    logger.info("步骤4: 修改customer_id字段为可空")
    logger.info("=" * 80)

    with app.app_context():
        # 检查当前约束
        result = db.session.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'quotations' AND column_name = 'customer_id'
        """))

        row = result.fetchone()
        if row and row[0] == 'YES':
            logger.info("✓ 字段已经是可空的，跳过")
            return True

        # 修改为可空
        logger.info("执行: ALTER TABLE quotations ALTER COLUMN customer_id DROP NOT NULL")
        db.session.execute(text("""
            ALTER TABLE quotations
            ALTER COLUMN customer_id DROP NOT NULL
        """))
        db.session.commit()

        logger.info("✓ customer_id字段已改为可空")
        return True

def analyze_after_status():
    """分析修改后的状态"""
    logger.info("\n" + "=" * 80)
    logger.info("步骤6: 分析修改后的数据状态")
    logger.info("=" * 80)

    with app.app_context():
        # 1. 字段约束状态
        result = db.session.execute(text("""
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'quotations' AND column_name = 'customer_id'
        """))
        row = result.fetchone()
        logger.info(f"\n【字段约束】")
        logger.info(f"  是否可空: {row[0]}")
        results['after']['nullable'] = row[0]

        # 2. 报价单总体统计
        result = db.session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(customer_id) as with_customer,
                COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count,
                COUNT(*) FILTER (WHERE customer_id = 4) as customer_4_count
            FROM quotations
        """))
        row = result.fetchone()
        logger.info(f"\n【报价单统计】")
        logger.info(f"  总数: {row[0]}")
        logger.info(f"  有customer_id: {row[1]} ({row[1]*100/row[0]:.1f}%)")
        logger.info(f"  customer_id为NULL: {row[2]} ({row[2]*100/row[0]:.1f}%)")
        logger.info(f"  关联客户4: {row[3]} ({row[3]*100/row[0] if row[0] > 0 else 0:.1f}%)")

        results['after']['total'] = row[0]
        results['after']['with_customer'] = row[1]
        results['after']['null_count'] = row[2]
        results['after']['customer_4_count'] = row[3]

        # 3. 验证保留的客户4报价单
        if row[3] > 0:
            logger.info(f"\n【保留的客户4报价单验证】")
            result = db.session.execute(text("""
                SELECT
                    q.id,
                    q.quotation_number,
                    p.project_name,
                    CASE
                        WHEN EXISTS (
                            SELECT 1 FROM project_customer_associations pca
                            WHERE pca.project_id = q.project_id AND pca.company_id = 4
                        ) THEN '项目关联✓'
                        WHEN EXISTS (
                            SELECT 1 FROM contacts c
                            WHERE c.id = q.contact_id AND c.company_id = 4
                        ) THEN '联系人关联✓'
                        ELSE '未知原因⚠️'
                    END as reason
                FROM quotations q
                LEFT JOIN projects p ON p.id = q.project_id
                WHERE q.customer_id = 4
                LIMIT 20
            """))

            for row in result:
                logger.info(f"  {row[1]} | 项目: {row[2]} | 原因: {row[3]}")

def print_comparison_report():
    """打印对比报告"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 修改前后数据对比报告")
    logger.info("=" * 80)

    before = results['before']
    after = results['after']

    logger.info(f"\n【字段约束变化】")
    logger.info(f"  修改前: {before['nullable']}")
    logger.info(f"  修改后: {after['nullable']}")
    logger.info(f"  状态: {'✓ 已改为可空' if after['nullable'] == 'YES' else '⚠️ 仍为必填'}")

    logger.info(f"\n【数据统计变化】")
    logger.info(f"  报价单总数: {before['total']} → {after['total']} (变化: {after['total'] - before['total']})")
    logger.info(f"  有customer_id: {before['with_customer']} → {after['with_customer']} (变化: {after['with_customer'] - before['with_customer']})")
    logger.info(f"  customer_id为NULL: {before['null_count']} → {after['null_count']} (变化: +{after['null_count'] - before['null_count']})")
    logger.info(f"  关联客户4: {before['customer_4_count']} → {after['customer_4_count']} (变化: {after['customer_4_count'] - before['customer_4_count']})")

    logger.info(f"\n【清理效果】")
    logger.info(f"  疑似错误: {before['suspect_count']} 个")
    logger.info(f"  已清理: {results.get('modified_count', 0)} 个")
    logger.info(f"  保留真实关联: {before['project_match']} (项目关联) + {before['contact_match']} (联系人关联)")

    logger.info(f"\n【备份信息】")
    logger.info(f"  备份表: {results['backup_table']}")
    logger.info(f"  备份记录数: {before['total']}")

    if results['modified_quotations']:
        logger.info(f"\n【修改的报价单详情】（前20个）")
        for i, q in enumerate(results['modified_quotations'][:20], 1):
            logger.info(f"  {i}. {q['quotation_number']} | 项目: {q['project_name']} | 客户ID: {q['old_customer_id']} → NULL")

def verify_specific_quotation():
    """验证特定报价单（QU202405-022）"""
    logger.info("\n" + "=" * 80)
    logger.info("🔍 验证报价单 QU202405-022")
    logger.info("=" * 80)

    with app.app_context():
        result = db.session.execute(text("""
            SELECT
                q.id,
                q.quotation_number,
                q.customer_id,
                q.project_id,
                p.project_name,
                (
                    SELECT string_agg(c.company_name, ', ')
                    FROM project_customer_associations pca
                    JOIN companies c ON c.id = pca.company_id
                    WHERE pca.project_id = q.project_id
                ) as project_customers
            FROM quotations q
            LEFT JOIN projects p ON p.id = q.project_id
            WHERE q.quotation_number = 'QU202405-022'
        """))

        row = result.fetchone()
        if row:
            logger.info(f"  报价单号: {row[1]}")
            logger.info(f"  customer_id: {row[2] if row[2] else 'NULL ✓'}")
            logger.info(f"  项目ID: {row[3]}")
            logger.info(f"  项目名称: {row[4]}")
            logger.info(f"  项目客户: {row[5]}")

            if row[2] is None:
                logger.info(f"\n  ✓ 已成功清理，customer_id改为NULL")
                logger.info(f"  ✓ 用户编辑时会被要求选择正确的客户")
            else:
                logger.info(f"\n  ⚠️ customer_id仍为 {row[2]}")

def main():
    logger.info("=" * 80)
    logger.info("清理报价单customer_id错误数据")
    logger.info("=" * 80)
    logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 验证连接
        if not verify_database_connection():
            return 1

        # 2. 分析当前状态
        has_suspect = analyze_current_status()

        if not has_suspect:
            logger.info("\n✓ 未发现需要清理的数据，操作终止")
            return 0

        # 3. 创建备份
        create_backup_table()

        # 4. 先修改字段约束为可空（必须先做，否则无法设置NULL）
        alter_column_to_nullable()

        # 5. 清理错误数据
        modified_count = clean_suspect_customer_data()

        # 6. 分析修改后状态
        analyze_after_status()

        # 7. 打印对比报告
        print_comparison_report()

        # 8. 验证特定报价单
        verify_specific_quotation()

        logger.info("\n" + "=" * 80)
        logger.info("✓ 所有操作成功完成！")
        logger.info("=" * 80)

        logger.info("\n【后续步骤】")
        logger.info("1. ✓ 数据库字段已改为可空")
        logger.info("2. ✓ 错误数据已清理为NULL")
        logger.info("3. ⏳ 确保前端表单保持必填验证")
        logger.info("4. ⏳ 用户编辑历史报价单时会被要求选择客户")
        logger.info("5. ✓ 备份数据已保存，可用于回滚")

        logger.info("\n【回滚方法】（如需要）")
        logger.info(f"UPDATE quotations q")
        logger.info(f"SET customer_id = b.customer_id")
        logger.info(f"FROM {results['backup_table']} b")
        logger.info(f"WHERE q.id = b.id;")

        return 0

    except Exception as e:
        logger.error(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

        logger.error("\n如果已执行部分修改，可以从备份表恢复:")
        if results.get('backup_table'):
            logger.error(f"  备份表: {results['backup_table']}")

        return 1

if __name__ == '__main__':
    sys.exit(main())
