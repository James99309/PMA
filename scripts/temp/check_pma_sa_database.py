#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查PMA-SA数据库的数据质量问题"""
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

OVS_DB_URL = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def check_pma_sa_database():
    """检查PMA-SA数据库的数据质量"""

    engine = create_engine(OVS_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("=" * 140)
    print("PMA-SA 数据库质量检查报告")
    print("=" * 140)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: OVS (PMA-SA)")
    print()

    check_results = {
        'timestamp': datetime.now().isoformat(),
        'database': 'PMA-SA (OVS)',
        'checks': []
    }

    try:
        # ============================================
        # 检查1：重复客户数据
        # ============================================
        print("=" * 140)
        print("【检查1】重复客户数据分析")
        print("=" * 140)
        print()

        query = text("""
            SELECT
                company_name,
                COUNT(*) as count,
                array_agg(id ORDER BY created_at) as company_ids,
                array_agg(owner_id ORDER BY created_at) as owner_ids
            FROM companies
            WHERE is_deleted = FALSE
            GROUP BY company_name
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, company_name
        """)

        duplicates = session.execute(query).fetchall()

        if duplicates:
            print(f"⚠️  发现 {len(duplicates)} 组重复公司名称")
            print(f"📋 涉及 {sum(d.count for d in duplicates)} 条公司记录")
            print()

            duplicate_details = []
            for idx, dup in enumerate(duplicates, 1):
                print(f"【{idx}/{len(duplicates)}】{dup.company_name}")
                print(f"    重复数量: {dup.count} 条")
                print(f"    公司ID: {dup.company_ids}")
                print()

                # 获取详细信息
                detail_query = text("""
                    SELECT
                        c.id,
                        c.company_code,
                        c.owner_id,
                        u.real_name as owner_name,
                        u.is_active as owner_active,
                        (SELECT COUNT(*) FROM project_customer_associations WHERE company_id = c.id) as project_count,
                        (SELECT COUNT(*) FROM contacts WHERE company_id = c.id) as contact_count
                    FROM companies c
                    LEFT JOIN users u ON u.id = c.owner_id
                    WHERE c.id = ANY(:ids)
                    ORDER BY c.created_at
                """)

                details = session.execute(detail_query, {'ids': list(dup.company_ids)}).fetchall()

                company_info = []
                for d in details:
                    info = {
                        'id': d.id,
                        'code': d.company_code,
                        'owner_id': d.owner_id,
                        'owner_name': d.owner_name,
                        'owner_active': d.owner_active,
                        'project_count': d.project_count,
                        'contact_count': d.contact_count
                    }
                    company_info.append(info)
                    status = "✅在职" if d.owner_active else "❌离职"
                    print(f"      ID:{d.id} | 负责人:{d.owner_name} {status} | 项目:{d.project_count} | 联系人:{d.contact_count}")

                print()

                duplicate_details.append({
                    'company_name': dup.company_name,
                    'count': dup.count,
                    'companies': company_info
                })

            check_results['checks'].append({
                'check_name': '重复客户数据',
                'status': 'found_issues',
                'total_groups': len(duplicates),
                'total_records': sum(d.count for d in duplicates),
                'details': duplicate_details
            })
        else:
            print("✅ 未发现重复的公司名称！")
            check_results['checks'].append({
                'check_name': '重复客户数据',
                'status': 'clean',
                'message': '未发现重复公司'
            })

        print()

        # ============================================
        # 检查2：项目customer_id与关联表一致性
        # ============================================
        print("=" * 140)
        print("【检查2】项目客户字段与关联表一致性分析")
        print("=" * 140)
        print()

        # 检查projects表是否有customer_id字段
        check_column = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'projects'
            AND column_name = 'customer_id'
        """)

        has_customer_field = session.execute(check_column).fetchone()

        if has_customer_field:
            print("📋 检测到 projects.customer_id 字段存在")
            print()

            # 查找customer_id有值但关联表中没有对应记录的项目
            missing_in_assoc = text("""
                SELECT
                    p.id as project_id,
                    p.project_name,
                    p.customer_id,
                    c.company_name
                FROM projects p
                LEFT JOIN companies c ON c.id = p.customer_id
                LEFT JOIN project_customer_associations pca
                    ON pca.project_id = p.id
                    AND pca.company_id = p.customer_id
                WHERE p.customer_id IS NOT NULL
                AND pca.id IS NULL
                AND p.is_deleted = FALSE
                ORDER BY p.id
                LIMIT 20
            """)

            missing_records = session.execute(missing_in_assoc).fetchall()

            if missing_records:
                print(f"⚠️  发现 {len(missing_records)} 个项目的customer_id在关联表中缺失")
                print()
                print("前20条示例:")
                for rec in missing_records[:20]:
                    print(f"  项目ID:{rec.project_id} | {rec.project_name[:40]} | 客户:{rec.company_name}")
                print()

                # 统计总数
                count_query = text("""
                    SELECT COUNT(*)
                    FROM projects p
                    LEFT JOIN project_customer_associations pca
                        ON pca.project_id = p.id
                        AND pca.company_id = p.customer_id
                    WHERE p.customer_id IS NOT NULL
                    AND pca.id IS NULL
                    AND p.is_deleted = FALSE
                """)
                total_missing = session.execute(count_query).scalar()

                check_results['checks'].append({
                    'check_name': '项目客户字段一致性',
                    'status': 'found_issues',
                    'total_inconsistent': total_missing,
                    'sample': [{
                        'project_id': rec.project_id,
                        'project_name': rec.project_name,
                        'customer_id': rec.customer_id,
                        'company_name': rec.company_name
                    } for rec in missing_records[:20]]
                })
            else:
                print("✅ 所有projects.customer_id都在关联表中有对应记录！")
                check_results['checks'].append({
                    'check_name': '项目客户字段一致性',
                    'status': 'clean',
                    'message': '所有项目客户字段与关联表一致'
                })
        else:
            print("ℹ️  projects表中没有customer_id字段（已迁移到关联表）")
            check_results['checks'].append({
                'check_name': '项目客户字段一致性',
                'status': 'not_applicable',
                'message': 'projects表中没有customer_id字段'
            })

        print()

        # ============================================
        # 检查3：项目关联表重复记录
        # ============================================
        print("=" * 140)
        print("【检查3】项目关联表重复记录分析")
        print("=" * 140)
        print()

        duplicate_assoc_query = text("""
            SELECT
                project_id,
                company_id,
                p.project_name,
                c.company_name,
                COUNT(*) as count,
                array_agg(pca.id ORDER BY pca.created_at) as assoc_ids,
                array_agg(pca.created_at ORDER BY pca.created_at) as created_times
            FROM project_customer_associations pca
            JOIN projects p ON p.id = pca.project_id
            JOIN companies c ON c.id = pca.company_id
            GROUP BY project_id, company_id, p.project_name, c.company_name
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, project_id
        """)

        duplicate_assocs = session.execute(duplicate_assoc_query).fetchall()

        if duplicate_assocs:
            print(f"⚠️  发现 {len(duplicate_assocs)} 组重复的项目-客户关联")
            print(f"📋 涉及 {sum(d.count for d in duplicate_assocs)} 条关联记录")
            print()

            duplicate_assoc_details = []
            for idx, dup in enumerate(duplicate_assocs, 1):
                print(f"【{idx}/{len(duplicate_assocs)}】项目ID:{dup.project_id} | {dup.project_name[:40]}")
                print(f"    客户: {dup.company_name[:40]} (ID:{dup.company_id})")
                print(f"    重复次数: {dup.count}")
                print(f"    关联ID: {dup.assoc_ids}")
                print(f"    建议: 保留 {dup.assoc_ids[0]}，删除 {dup.assoc_ids[1:]}")
                print()

                duplicate_assoc_details.append({
                    'project_id': dup.project_id,
                    'project_name': dup.project_name,
                    'company_id': dup.company_id,
                    'company_name': dup.company_name,
                    'count': dup.count,
                    'keep_id': dup.assoc_ids[0],
                    'delete_ids': list(dup.assoc_ids[1:])
                })

            check_results['checks'].append({
                'check_name': '项目关联表重复',
                'status': 'found_issues',
                'total_groups': len(duplicate_assocs),
                'total_records': sum(d.count for d in duplicate_assocs),
                'details': duplicate_assoc_details
            })
        else:
            print("✅ 未发现重复的项目-客户关联！")
            check_results['checks'].append({
                'check_name': '项目关联表重复',
                'status': 'clean',
                'message': '未发现重复关联'
            })

        print()

        # ============================================
        # 汇总报告
        # ============================================
        print("=" * 140)
        print("📊 检查汇总")
        print("=" * 140)

        issues_found = sum(1 for check in check_results['checks'] if check['status'] == 'found_issues')
        clean_checks = sum(1 for check in check_results['checks'] if check['status'] == 'clean')

        print(f"总检查项: {len(check_results['checks'])}")
        print(f"✅ 干净: {clean_checks} 项")
        print(f"⚠️  发现问题: {issues_found} 项")
        print()

        for check in check_results['checks']:
            status_icon = "⚠️" if check['status'] == 'found_issues' else "✅"
            print(f"{status_icon} {check['check_name']}: {check.get('message', check['status'])}")

        print()

        # 保存结果
        result_file = os.path.join(get_project_root(), 'scripts/temp/pma_sa_check_result.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(check_results, f, ensure_ascii=False, indent=2)

        print(f"📄 详细检查结果已保存到: {result_file}")
        print()

        # 修复建议
        if issues_found > 0:
            print("=" * 140)
            print("💡 修复建议")
            print("=" * 140)
            print()

            for check in check_results['checks']:
                if check['status'] == 'found_issues':
                    print(f"【{check['check_name']}】")

                    if check['check_name'] == '重复客户数据':
                        print(f"  问题: 发现 {check['total_groups']} 组重复公司")
                        print(f"  建议: 参考 merge_duplicate_companies.py 创建类似脚本合并重复客户")
                        print(f"  策略: 离职负责人的记录合并到在职负责人")

                    elif check['check_name'] == '项目客户字段一致性':
                        print(f"  问题: {check['total_inconsistent']} 个项目的customer_id未同步到关联表")
                        print(f"  建议: 创建迁移脚本将projects.customer_id同步到project_customer_associations")

                    elif check['check_name'] == '项目关联表重复':
                        print(f"  问题: 发现 {check['total_groups']} 组重复的项目-客户关联")
                        print(f"  建议: 参考 fix_same_company_duplicates.py 创建类似脚本删除重复")
                        print(f"  策略: 保留最早创建的记录，删除后续重复")

                    print()

        return check_results

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()
        engine.dispose()

if __name__ == '__main__':
    print()
    result = check_pma_sa_database()

    if result:
        print("=" * 140)
        print("✅ 检查完成！")
        print("=" * 140)
