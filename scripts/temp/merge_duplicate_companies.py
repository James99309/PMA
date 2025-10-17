#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并重复客户公司，整合所有关联数据"""
import sys
import os
import json
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

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def merge_duplicate_companies(dry_run=False):
    """合并重复客户公司

    Args:
        dry_run: 如果为True，只显示将要执行的操作，不实际执行
    """

    engine = create_engine(CLOUD_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("=" * 140)
    print("客户重复数据合并脚本")
    print("=" * 140)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模式: {'🔍 预览模式 (不会修改数据)' if dry_run else '⚠️  执行模式 (将修改数据)'}")
    print()

    # 读取分析结果
    analysis_file = os.path.join(get_project_root(), 'scripts/temp/duplicate_companies_analysis.json')
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
    except FileNotFoundError:
        print(f"❌ 错误: 未找到分析结果文件 {analysis_file}")
        print("   请先运行 analyze_duplicate_companies.py")
        return None

    # 合并清单（手动决策已确认）
    merge_plan = []

    # 10组自动合并
    for item in analysis['auto_merge']:
        if item['target_id']:
            merge_plan.append({
                'company_name': item['company_name'],
                'target_id': item['target_id'],
                'source_ids': [cid for cid in item['company_ids'] if cid != item['target_id']],
                'reason': item['reason']
            })

    # 1组人工决策（已确认：保留方玲ID:423，删除徐昊ID:253）
    for item in analysis['risky_merge']:
        if item['company_name'] == '上海久事国际体育中心有限公司':
            merge_plan.append({
                'company_name': item['company_name'],
                'target_id': 423,  # 方玲
                'source_ids': [253],  # 徐昊
                'reason': '人工决策：保留customer_sales方玲的记录，service_manager徐昊可查看'
            })

    print(f"📋 合并计划: {len(merge_plan)} 组")
    print()

    merge_results = {
        'timestamp': datetime.now().isoformat(),
        'dry_run': dry_run,
        'total_groups': len(merge_plan),
        'successful': 0,
        'failed': 0,
        'details': [],
        'rollback_data': []
    }

    try:
        for idx, plan in enumerate(merge_plan, 1):
            print("=" * 140)
            print(f"【{idx}/{len(merge_plan)}】{plan['company_name']}")
            print(f"  保留: 公司ID {plan['target_id']}")
            print(f"  删除: {plan['source_ids']}")
            print(f"  原因: {plan['reason']}")
            print()

            for source_id in plan['source_ids']:
                try:
                    if not dry_run:
                        session.begin_nested()  # 创建保存点

                    merge_detail = {
                        'company_name': plan['company_name'],
                        'target_id': plan['target_id'],
                        'source_id': source_id,
                        'updates': {}
                    }

                    # 1. 处理项目关联表（先删除冲突，再更新）
                    print(f"  🔄 处理项目关联...")

                    # 步骤1：找出会造成冲突的关联记录并删除源公司的记录
                    if not dry_run:
                        result = session.execute(text("""
                            WITH conflicts AS (
                                SELECT s.id as source_assoc_id, t.id as target_assoc_id
                                FROM project_customer_associations s
                                JOIN project_customer_associations t
                                    ON s.project_id = t.project_id
                                    AND t.company_id = :target_id
                                WHERE s.company_id = :source_id
                            )
                            SELECT COUNT(*) FROM conflicts
                        """), {'target_id': plan['target_id'], 'source_id': source_id})
                        conflict_count = result.scalar()

                        if conflict_count > 0:
                            # 删除源公司中会造成冲突的关联记录（保留目标公司的）
                            session.execute(text("""
                                DELETE FROM project_customer_associations
                                WHERE id IN (
                                    SELECT s.id
                                    FROM project_customer_associations s
                                    JOIN project_customer_associations t
                                        ON s.project_id = t.project_id
                                        AND t.company_id = :target_id
                                    WHERE s.company_id = :source_id
                                )
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                            print(f"     🗑️  删除 {conflict_count} 条冲突的项目关联（源公司）")
                            merge_detail['updates']['removed_conflict_associations'] = conflict_count

                    # 步骤2：更新剩余的项目关联
                    result = session.execute(text("""
                        SELECT COUNT(*) FROM project_customer_associations WHERE company_id = :source_id
                    """), {'source_id': source_id})
                    remaining_count = result.scalar()

                    if remaining_count > 0:
                        if not dry_run:
                            session.execute(text("""
                                UPDATE project_customer_associations
                                SET company_id = :target_id
                                WHERE company_id = :source_id
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                        print(f"     ✅ 更新 {remaining_count} 条项目关联记录")
                        merge_detail['updates']['project_associations'] = remaining_count
                    else:
                        print(f"     ⏭️  无剩余项目关联需要更新")
                        merge_detail['updates']['project_associations'] = 0

                    # 2. 更新联系人
                    print(f"  🔄 更新联系人...")
                    result = session.execute(text("""
                        SELECT COUNT(*) FROM contacts WHERE company_id = :source_id
                    """), {'source_id': source_id})
                    count = result.scalar()

                    if count > 0:
                        if not dry_run:
                            session.execute(text("""
                                UPDATE contacts
                                SET company_id = :target_id
                                WHERE company_id = :source_id
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                        print(f"     ✅ 更新 {count} 条联系人记录")
                        merge_detail['updates']['contacts'] = count
                    else:
                        print(f"     ⏭️  无需更新联系人")
                        merge_detail['updates']['contacts'] = 0

                    # 3. 更新报销单
                    print(f"  🔄 更新报销单...")
                    result = session.execute(text("""
                        SELECT COUNT(*) FROM expenses WHERE customer_id = :source_id
                    """), {'source_id': source_id})
                    count = result.scalar()

                    if count > 0:
                        if not dry_run:
                            session.execute(text("""
                                UPDATE expenses
                                SET customer_id = :target_id
                                WHERE customer_id = :source_id
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                        print(f"     ✅ 更新 {count} 条报销单记录")
                        merge_detail['updates']['expenses'] = count
                    else:
                        print(f"     ⏭️  无需更新报销单")
                        merge_detail['updates']['expenses'] = 0

                    # 4. 更新行动记录
                    print(f"  🔄 更新行动记录...")
                    result = session.execute(text("""
                        SELECT COUNT(*) FROM actions WHERE company_id = :source_id
                    """), {'source_id': source_id})
                    count = result.scalar()

                    if count > 0:
                        if not dry_run:
                            session.execute(text("""
                                UPDATE actions
                                SET company_id = :target_id
                                WHERE company_id = :source_id
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                        print(f"     ✅ 更新 {count} 条行动记录")
                        merge_detail['updates']['actions'] = count
                    else:
                        print(f"     ⏭️  无需更新行动记录")
                        merge_detail['updates']['actions'] = 0

                    # 5. 更新批价单（dealer_id）
                    print(f"  🔄 更新批价单(经销商)...")
                    result = session.execute(text("""
                        SELECT COUNT(*) FROM pricing_orders WHERE dealer_id = :source_id
                    """), {'source_id': source_id})
                    count = result.scalar()

                    if count > 0:
                        if not dry_run:
                            session.execute(text("""
                                UPDATE pricing_orders
                                SET dealer_id = :target_id
                                WHERE dealer_id = :source_id
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                        print(f"     ✅ 更新 {count} 条批价单(经销商)记录")
                        merge_detail['updates']['pricing_orders_dealer'] = count
                    else:
                        print(f"     ⏭️  无需更新批价单(经销商)")
                        merge_detail['updates']['pricing_orders_dealer'] = 0

                    # 6. 更新批价单（distributor_id）
                    print(f"  🔄 更新批价单(分销商)...")
                    result = session.execute(text("""
                        SELECT COUNT(*) FROM pricing_orders WHERE distributor_id = :source_id
                    """), {'source_id': source_id})
                    count = result.scalar()

                    if count > 0:
                        if not dry_run:
                            session.execute(text("""
                                UPDATE pricing_orders
                                SET distributor_id = :target_id
                                WHERE distributor_id = :source_id
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                        print(f"     ✅ 更新 {count} 条批价单(分销商)记录")
                        merge_detail['updates']['pricing_orders_distributor'] = count
                    else:
                        print(f"     ⏭️  无需更新批价单(分销商)")
                        merge_detail['updates']['pricing_orders_distributor'] = 0

                    # 7. 更新结算单
                    print(f"  🔄 更新结算单...")
                    result = session.execute(text("""
                        SELECT COUNT(*) FROM settlements WHERE company_id = :source_id
                    """), {'source_id': source_id})
                    count = result.scalar()

                    if count > 0:
                        if not dry_run:
                            session.execute(text("""
                                UPDATE settlements
                                SET company_id = :target_id
                                WHERE company_id = :source_id
                            """), {'target_id': plan['target_id'], 'source_id': source_id})
                        print(f"     ✅ 更新 {count} 条结算单记录")
                        merge_detail['updates']['settlements'] = count
                    else:
                        print(f"     ⏭️  无需更新结算单")
                        merge_detail['updates']['settlements'] = 0

                    # 8. 软删除源公司
                    print(f"  🗑️  软删除源公司...")
                    if not dry_run:
                        session.execute(text("""
                            UPDATE companies
                            SET is_deleted = TRUE
                            WHERE id = :source_id
                        """), {'source_id': source_id})
                    print(f"     ✅ 公司ID {source_id} 已标记为删除")
                    merge_detail['deleted_company_id'] = source_id

                    if not dry_run:
                        session.commit()  # 提交这个源公司的合并

                    print(f"  ✅ 合并完成！")
                    merge_detail['status'] = 'success'
                    merge_results['details'].append(merge_detail)
                    merge_results['successful'] += 1

                except Exception as e:
                    if not dry_run:
                        session.rollback()
                    print(f"  ❌ 合并失败: {e}")
                    merge_detail['status'] = 'failed'
                    merge_detail['error'] = str(e)
                    merge_results['details'].append(merge_detail)
                    merge_results['failed'] += 1
                    import traceback
                    traceback.print_exc()

            print()

        # 保存结果
        if not dry_run:
            result_file = os.path.join(get_project_root(), 'scripts/temp/merge_companies_result.json')
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(merge_results, f, ensure_ascii=False, indent=2)
            print(f"📄 合并结果已保存到: {result_file}")

        # 汇总统计
        print("=" * 140)
        print("📊 合并汇总")
        print("=" * 140)
        print(f"✅ 成功: {merge_results['successful']} 组")
        print(f"❌ 失败: {merge_results['failed']} 组")

        if merge_results['successful'] > 0:
            total_updates = {
                'removed_conflict_associations': 0,
                'project_associations': 0,
                'contacts': 0,
                'expenses': 0,
                'actions': 0,
                'pricing_orders_dealer': 0,
                'pricing_orders_distributor': 0,
                'settlements': 0
            }

            for detail in merge_results['details']:
                if detail['status'] == 'success':
                    for key in total_updates:
                        total_updates[key] += detail['updates'].get(key, 0)

            print()
            print("📋 更新统计:")
            print(f"  - 删除冲突项目关联: {total_updates['removed_conflict_associations']} 条")
            print(f"  - 更新项目关联: {total_updates['project_associations']} 条")
            print(f"  - 联系人: {total_updates['contacts']} 条")
            print(f"  - 报销单: {total_updates['expenses']} 条")
            print(f"  - 行动记录: {total_updates['actions']} 条")
            print(f"  - 批价单(经销商): {total_updates['pricing_orders_dealer']} 条")
            print(f"  - 批价单(分销商): {total_updates['pricing_orders_distributor']} 条")
            print(f"  - 结算单: {total_updates['settlements']} 条")
            print(f"  - 软删除公司: {merge_results['successful']} 条")

        return merge_results

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        if not dry_run:
            session.rollback()
        return None
    finally:
        session.close()
        engine.dispose()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='合并重复客户公司')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改数据')
    parser.add_argument('--execute', action='store_true', help='执行模式，实际修改数据')
    parser.add_argument('--force', action='store_true', help='强制执行，不需要确认')

    args = parser.parse_args()

    if not args.execute and not args.dry_run:
        print("⚠️  请选择执行模式:")
        print("  --dry-run   预览模式（推荐先运行）")
        print("  --execute   执行模式")
        print("  --execute --force   强制执行模式（跳过确认）")
        sys.exit(1)

    if args.execute and not args.force:
        print("⚠️  警告: 即将执行数据合并操作！")
        confirm = input("确认执行? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ 操作已取消")
            sys.exit(0)

    result = merge_duplicate_companies(dry_run=args.dry_run)

    if result:
        print()
        print("=" * 140)
        if args.dry_run:
            print("✅ 预览完成！使用 --execute 参数执行实际合并")
        else:
            print("✅ 合并完成！")
        print("=" * 140)
