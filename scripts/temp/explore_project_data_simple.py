#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目成功率预测模型 - 数据探索脚本（简化版）
直接连接数据库，不依赖 Flask 应用
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, text

# 数据库连接
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://nijie:@localhost:5432/pma_local')
engine = create_engine(DATABASE_URL)

def print_section(title):
    """打印分隔标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def explore_project_distribution():
    """探索项目数据分布"""
    print_section("1. 项目数据总览")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM projects"))
        total = result.scalar()
        print(f"\n总项目数: {total}")

        print("\n📊 按阶段分布:")
        result = conn.execute(text("""
            SELECT
                current_stage,
                COUNT(*) as count,
                COALESCE(SUM(quotation_customer), 0) as total_amount
            FROM projects
            GROUP BY current_stage
            ORDER BY COUNT(*) DESC
        """))

        stage_names = {
            'discover': '发现', 'embed': '植入', 'pre_tender': '标前',
            'tendering': '标中', 'awarded': '中标', 'quoted': '批价',
            'signed': '签约', 'lost': '失败', 'paused': '搁置'
        }

        print(f"\n{'阶段':<12} {'数量':>8} {'占比':>8} {'总金额(万)':>12}")
        print("-" * 45)

        success_count = 0
        failed_count = 0
        in_progress_count = 0

        for row in result:
            stage = row[0]
            count = row[1]
            amount = row[2] or 0

            pct = count / total * 100 if total > 0 else 0
            amount_wan = amount / 10000 if amount else 0
            name = stage_names.get(stage, stage or '未知')
            print(f"{name:<12} {count:>8} {pct:>7.1f}% {amount_wan:>12,.1f}")

            if stage in ['quoted', 'signed']:
                success_count += count
            elif stage in ['lost', 'paused']:
                failed_count += count
            else:
                in_progress_count += count

        print("-" * 45)
        print(f"\n✅ 成功项目(签约+批价): {success_count} ({success_count/total*100:.1f}%)")
        print(f"❌ 失败项目(失败+搁置): {failed_count} ({failed_count/total*100:.1f}%)")
        print(f"⏳ 进行中项目: {in_progress_count} ({in_progress_count/total*100:.1f}%)")

        print("\n📅 按年份分布(报备时间):")
        result = conn.execute(text("""
            SELECT EXTRACT(YEAR FROM report_time) as year, COUNT(*) as count
            FROM projects
            WHERE report_time IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM report_time)
            ORDER BY year
        """))

        for row in result:
            if row[0]:
                print(f"  {int(row[0])}: {row[1]} 个项目")

        return total, success_count, failed_count

def explore_workitem_data():
    """探索跟进记录数据"""
    print_section("2. 跟进记录数据分析")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM work_items"))
        total_items = result.scalar()

        result = conn.execute(text("SELECT COUNT(*) FROM work_items WHERE project_id IS NOT NULL"))
        project_items = result.scalar()

        print(f"\n总跟进记录: {total_items}")
        if total_items > 0:
            print(f"关联项目的跟进: {project_items} ({project_items/total_items*100:.1f}%)")

        if project_items == 0:
            print("暂无关联项目的跟进记录")
            return 0

        print("\n📋 按工作类型分布(关联项目):")
        result = conn.execute(text("""
            SELECT work_type, COUNT(*) as count, COALESCE(SUM(actual_hours), 0) as total_hours
            FROM work_items
            WHERE project_id IS NOT NULL
            GROUP BY work_type
            ORDER BY COUNT(*) DESC
            LIMIT 15
        """))

        type_labels = {
            'meeting': '会议', 'customer_visit': '拜访客户', 'presales_support': '售前支持',
            'business_negotiation': '商务洽谈', 'customer_maintenance': '客户维护',
            'onsite_maintenance': '现场运维', 'technical_support': '技术支持',
            'internal_training': '内部培训', 'other': '其他'
        }

        print(f"\n{'类型':<20} {'数量':>8} {'总工时':>10}")
        print("-" * 42)
        for row in result:
            label = type_labels.get(row[0], row[0] or '未分类')
            hours = row[2] or 0
            print(f"{label:<20} {row[1]:>8} {hours:>10.1f}h")

        print("\n📊 跟进状态分布:")
        result = conn.execute(text("""
            SELECT status, COUNT(*) as count
            FROM work_items WHERE project_id IS NOT NULL
            GROUP BY status
        """))

        for row in result:
            print(f"  {row[0]}: {row[1]}")

        result = conn.execute(text("""
            SELECT COUNT(*) FROM work_items
            WHERE project_id IS NOT NULL AND is_business_trip = TRUE
        """))
        trip_count = result.scalar()
        if project_items > 0:
            print(f"\n🚄 出差跟进: {trip_count} ({trip_count/project_items*100:.1f}%)")

        return project_items

def explore_quotation_data():
    """探索报价单数据"""
    print_section("3. 报价单数据分析")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM quotations"))
        total_quotes = result.scalar()
        print(f"\n总报价单数: {total_quotes}")

        result = conn.execute(text("SELECT COUNT(DISTINCT project_id) FROM quotations"))
        projects_with_quote = result.scalar()
        print(f"有报价单的项目数: {projects_with_quote}")

        print("\n📋 报价单审批状态:")
        result = conn.execute(text("""
            SELECT COALESCE(approval_status, '未提交') as status, COUNT(*) as count
            FROM quotations GROUP BY approval_status
        """))

        for row in result:
            print(f"  {row[0]}: {row[1]}")

        return total_quotes

def explore_stage_history():
    """探索阶段历史数据"""
    print_section("4. 阶段变更历史分析")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM project_stage_history"))
        total_changes = result.scalar()
        print(f"\n总阶段变更记录: {total_changes}")

        result = conn.execute(text("SELECT COUNT(DISTINCT project_id) FROM project_stage_history"))
        projects_with_history = result.scalar()

        if projects_with_history > 0:
            avg_changes = total_changes / projects_with_history
            print(f"有历史记录的项目数: {projects_with_history}")
            print(f"平均每项目变更次数: {avg_changes:.2f}")

        print("\n📊 阶段转换统计(Top 10):")
        result = conn.execute(text("""
            SELECT from_stage, to_stage, COUNT(*) as count
            FROM project_stage_history
            GROUP BY from_stage, to_stage
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """))

        stage_names = {
            'discover': '发现', 'embed': '植入', 'pre_tender': '标前',
            'tendering': '标中', 'awarded': '中标', 'quoted': '批价',
            'signed': '签约', 'lost': '失败', 'paused': '搁置'
        }

        for row in result:
            from_name = stage_names.get(row[0], row[0] or '(无)')
            to_name = stage_names.get(row[1], row[1] or '(无)')
            print(f"  {from_name} → {to_name}: {row[2]}")

        return total_changes

def analyze_successful_projects():
    """分析成功项目特征"""
    print_section("5. 成功项目特征分析")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM projects WHERE current_stage IN ('signed', 'quoted')
        """))
        success_count = result.scalar()
        print(f"\n成功项目数: {success_count}")

        if success_count == 0:
            print("暂无成功项目数据")
            return {}

        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN quotation_customer > 0 THEN 1 ELSE 0 END) as has_quote,
                SUM(CASE WHEN authorization_code IS NOT NULL AND authorization_code != '' THEN 1 ELSE 0 END) as has_auth,
                SUM(CASE WHEN end_user IS NOT NULL AND end_user != '' THEN 1 ELSE 0 END) as has_user,
                SUM(CASE WHEN contractor IS NOT NULL AND contractor != '' THEN 1 ELSE 0 END) as has_contractor,
                SUM(CASE WHEN system_integrator IS NOT NULL AND system_integrator != '' THEN 1 ELSE 0 END) as has_integrator
            FROM projects WHERE current_stage IN ('signed', 'quoted')
        """))
        row = result.fetchone()
        n = row[0]

        print("\n✅ 成功项目特征:")
        print(f"  有报价金额: {row[1]} ({row[1]/n*100:.1f}%)")
        print(f"  有授权编号: {row[2]} ({row[2]/n*100:.1f}%)")
        print(f"  有最终用户: {row[3]} ({row[3]/n*100:.1f}%)")
        print(f"  有总承包方: {row[4]} ({row[4]/n*100:.1f}%)")
        print(f"  有集成商: {row[5]} ({row[5]/n*100:.1f}%)")

        result = conn.execute(text("""
            SELECT
                COUNT(w.id) as total_followups,
                COALESCE(SUM(w.actual_hours), 0) as total_hours,
                SUM(CASE WHEN w.work_type = 'customer_visit' THEN 1 ELSE 0 END) as visit_count,
                SUM(CASE WHEN w.is_business_trip = TRUE THEN 1 ELSE 0 END) as trip_count
            FROM projects p
            LEFT JOIN work_items w ON w.project_id = p.id
            WHERE p.current_stage IN ('signed', 'quoted')
        """))
        row = result.fetchone()

        print(f"\n📊 跟进投入(平均):")
        print(f"  跟进次数: {row[0]/n:.1f} 次/项目")
        print(f"  投入工时: {row[1]/n:.1f} 小时/项目")
        print(f"  拜访次数: {row[2]/n:.1f} 次/项目")
        print(f"  出差次数: {row[3]/n:.1f} 次/项目")

        result = conn.execute(text("""
            SELECT AVG(CURRENT_DATE - report_time) as avg_days
            FROM projects WHERE current_stage IN ('signed', 'quoted') AND report_time IS NOT NULL
        """))
        avg_days = result.scalar()
        if avg_days:
            print(f"\n⏱️ 平均项目周期: {float(avg_days):.0f} 天")

        return {'count': success_count}

def analyze_failed_projects():
    """分析失败项目特征"""
    print_section("6. 失败项目特征分析")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM projects WHERE current_stage IN ('lost', 'paused')
        """))
        failed_count = result.scalar()
        print(f"\n失败项目数: {failed_count}")

        if failed_count == 0:
            print("暂无失败项目数据")
            return {}

        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN quotation_customer > 0 THEN 1 ELSE 0 END) as has_quote,
                SUM(CASE WHEN authorization_code IS NOT NULL AND authorization_code != '' THEN 1 ELSE 0 END) as has_auth,
                SUM(CASE WHEN end_user IS NOT NULL AND end_user != '' THEN 1 ELSE 0 END) as has_user
            FROM projects WHERE current_stage IN ('lost', 'paused')
        """))
        row = result.fetchone()
        n = row[0]

        print("\n❌ 失败项目特征:")
        print(f"  有报价金额: {row[1]} ({row[1]/n*100:.1f}%)")
        print(f"  有授权编号: {row[2]} ({row[2]/n*100:.1f}%)")
        print(f"  有最终用户: {row[3]} ({row[3]/n*100:.1f}%)")

        result = conn.execute(text("""
            SELECT
                COUNT(w.id) as total_followups,
                COALESCE(SUM(w.actual_hours), 0) as total_hours,
                SUM(CASE WHEN w.work_type = 'customer_visit' THEN 1 ELSE 0 END) as visit_count
            FROM projects p
            LEFT JOIN work_items w ON w.project_id = p.id
            WHERE p.current_stage IN ('lost', 'paused')
        """))
        row = result.fetchone()

        print(f"\n📊 跟进投入(平均):")
        print(f"  跟进次数: {row[0]/n:.1f} 次/项目")
        print(f"  投入工时: {row[1]/n:.1f} 小时/项目")
        print(f"  拜访次数: {row[2]/n:.1f} 次/项目")

        return {'count': failed_count}

def analyze_top_salespeople():
    """分析优秀销售特征"""
    print_section("7. 优秀销售分析")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                p.owner_id,
                COALESCE(u.real_name, u.username) as name,
                COUNT(p.id) as total_projects,
                SUM(CASE WHEN p.current_stage IN ('signed', 'quoted') THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN p.current_stage IN ('lost', 'paused') THEN 1 ELSE 0 END) as failed_count,
                COALESCE(SUM(p.quotation_customer), 0) as total_amount
            FROM projects p
            JOIN users u ON p.owner_id = u.id
            GROUP BY p.owner_id, u.real_name, u.username
            HAVING COUNT(p.id) >= 3
            ORDER BY SUM(CASE WHEN p.current_stage IN ('signed', 'quoted') THEN 1 ELSE 0 END) DESC
            LIMIT 15
        """))

        print("\n🏆 Top 15 销售(按成功项目数):")
        print(f"\n{'姓名':<12} {'总项目':>8} {'成功':>6} {'失败':>6} {'成功率':>8} {'总金额(万)':>12}")
        print("-" * 60)

        top_sales_ids = []
        rows = result.fetchall()
        for row in rows:
            name = row[1] or '未知'
            total = row[2]
            success = row[3]
            failed = row[4]
            amount = row[5] or 0
            success_rate = success / total * 100 if total > 0 else 0
            amount_wan = amount / 10000
            print(f"{name:<12} {total:>8} {success:>6} {failed:>6} {success_rate:>7.1f}% {amount_wan:>12,.1f}")

            if success >= 2:
                top_sales_ids.append(row[0])

        if top_sales_ids:
            ids_str = ','.join(str(id) for id in top_sales_ids)
            print(f"\n📊 优秀销售(成功>=2)的成功项目特征:")

            result = conn.execute(text(f"""
                SELECT
                    COUNT(DISTINCT p.id) as project_count,
                    COUNT(w.id) as total_followups,
                    COALESCE(SUM(w.actual_hours), 0) as total_hours,
                    SUM(CASE WHEN w.work_type = 'customer_visit' THEN 1 ELSE 0 END) as visit_count,
                    SUM(CASE WHEN w.is_business_trip = TRUE THEN 1 ELSE 0 END) as trip_count
                FROM projects p
                LEFT JOIN work_items w ON w.project_id = p.id
                WHERE p.owner_id IN ({ids_str}) AND p.current_stage IN ('signed', 'quoted')
            """))
            row = result.fetchone()

            if row[0] > 0:
                n = row[0]
                print(f"  分析项目数: {n}")
                print(f"  平均跟进次数: {row[1]/n:.1f} 次/项目")
                print(f"  平均投入工时: {row[2]/n:.1f} 小时/项目")
                print(f"  平均拜访次数: {row[3]/n:.1f} 次/项目")
                print(f"  平均出差次数: {row[4]/n:.1f} 次/项目")

        return top_sales_ids

def compare_success_vs_failed():
    """对比成功vs失败项目"""
    print_section("8. 成功 vs 失败项目对比")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(DISTINCT p.id) as project_count,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    SUM(CASE WHEN p.quotation_customer > 0 THEN 1 ELSE 0 END)::float / COUNT(DISTINCT p.id) * 100
                ELSE 0 END as has_quote_pct,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    SUM(CASE WHEN p.authorization_code IS NOT NULL AND p.authorization_code != '' THEN 1 ELSE 0 END)::float / COUNT(DISTINCT p.id) * 100
                ELSE 0 END as has_auth_pct,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    COUNT(w.id)::float / COUNT(DISTINCT p.id)
                ELSE 0 END as avg_followups,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    SUM(CASE WHEN w.work_type = 'customer_visit' THEN 1 ELSE 0 END)::float / COUNT(DISTINCT p.id)
                ELSE 0 END as avg_visits,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    COALESCE(SUM(w.actual_hours), 0)::float / COUNT(DISTINCT p.id)
                ELSE 0 END as avg_hours
            FROM projects p
            LEFT JOIN work_items w ON w.project_id = p.id
            WHERE p.current_stage IN ('signed', 'quoted')
        """))
        success = result.fetchone()

        result = conn.execute(text("""
            SELECT
                COUNT(DISTINCT p.id) as project_count,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    SUM(CASE WHEN p.quotation_customer > 0 THEN 1 ELSE 0 END)::float / COUNT(DISTINCT p.id) * 100
                ELSE 0 END as has_quote_pct,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    SUM(CASE WHEN p.authorization_code IS NOT NULL AND p.authorization_code != '' THEN 1 ELSE 0 END)::float / COUNT(DISTINCT p.id) * 100
                ELSE 0 END as has_auth_pct,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    COUNT(w.id)::float / COUNT(DISTINCT p.id)
                ELSE 0 END as avg_followups,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    SUM(CASE WHEN w.work_type = 'customer_visit' THEN 1 ELSE 0 END)::float / COUNT(DISTINCT p.id)
                ELSE 0 END as avg_visits,
                CASE WHEN COUNT(DISTINCT p.id) > 0 THEN
                    COALESCE(SUM(w.actual_hours), 0)::float / COUNT(DISTINCT p.id)
                ELSE 0 END as avg_hours
            FROM projects p
            LEFT JOIN work_items w ON w.project_id = p.id
            WHERE p.current_stage IN ('lost', 'paused')
        """))
        failed = result.fetchone()

        if not success[0] or not failed[0]:
            print("数据不足，无法对比")
            return

        print(f"\n{'指标':<20} {'成功项目':>12} {'失败项目':>12} {'差异':>10}")
        print("-" * 58)
        print(f"{'项目数量':<20} {success[0]:>12} {failed[0]:>12}")
        print(f"{'有报价金额%':<20} {success[1]:>11.1f}% {failed[1]:>11.1f}% {success[1]-failed[1]:>+9.1f}%")
        print(f"{'有授权编号%':<20} {success[2]:>11.1f}% {failed[2]:>11.1f}% {success[2]-failed[2]:>+9.1f}%")
        print(f"{'平均跟进次数':<20} {success[3]:>12.1f} {failed[3]:>12.1f} {success[3]-failed[3]:>+10.1f}")
        print(f"{'平均拜访次数':<20} {success[4]:>12.1f} {failed[4]:>12.1f} {success[4]-failed[4]:>+10.1f}")
        print(f"{'平均投入工时':<20} {success[5]:>12.1f} {failed[5]:>12.1f} {success[5]-failed[5]:>+10.1f}")

        # 计算关键差异倍数
        print("\n📈 关键发现:")
        if failed[3] > 0:
            print(f"  成功项目的跟进次数是失败项目的 {success[3]/failed[3]:.1f} 倍")
        if failed[4] > 0:
            print(f"  成功项目的拜访次数是失败项目的 {success[4]/failed[4]:.1f} 倍")
        if failed[5] > 0:
            print(f"  成功项目的投入工时是失败项目的 {success[5]/failed[5]:.1f} 倍")

def main():
    print("\n" + "="*60)
    print("  项目成功率预测模型 - 数据探索报告")
    print("  生成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    explore_project_distribution()
    explore_workitem_data()
    explore_quotation_data()
    explore_stage_history()
    analyze_successful_projects()
    analyze_failed_projects()
    analyze_top_salespeople()
    compare_success_vs_failed()

    print("\n" + "="*60)
    print("  数据探索完成")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
