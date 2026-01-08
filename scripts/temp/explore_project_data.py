#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目成功率预测模型 - 数据探索脚本
分析SP8D数据库中的项目数据，为构建预测模型提供数据基础
"""
import sys
import os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func, case, distinct
from app import create_app, db
from app.models.project import Project
from app.models.worklog import WorkItem
from app.models.quotation import Quotation
from app.models.projectpm_stage_history import ProjectStageHistory
from app.models.user import User

app = create_app()

def print_section(title):
    """打印分隔标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def explore_project_distribution():
    """探索项目数据分布"""
    print_section("1. 项目数据总览")

    with app.app_context():
        # 总项目数
        total = Project.query.filter(Project.is_deleted == False).count()
        print(f"\n总项目数: {total}")

        # 按阶段分布
        print("\n📊 按阶段分布:")
        stage_stats = db.session.query(
            Project.current_stage,
            func.count(Project.id).label('count'),
            func.sum(Project.quotation_customer).label('total_amount')
        ).filter(
            Project.is_deleted == False
        ).group_by(Project.current_stage).all()

        stage_order = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']
        stage_names = {
            'discover': '发现', 'embed': '植入', 'pre_tender': '标前',
            'tendering': '标中', 'awarded': '中标', 'quoted': '批价',
            'signed': '签约', 'lost': '失败', 'paused': '搁置'
        }

        stage_dict = {s.current_stage: (s.count, s.total_amount or 0) for s in stage_stats}

        print(f"\n{'阶段':<12} {'数量':>8} {'占比':>8} {'总金额(万)':>12}")
        print("-" * 45)

        success_count = 0
        failed_count = 0
        in_progress_count = 0

        for stage in stage_order:
            if stage in stage_dict:
                count, amount = stage_dict[stage]
                pct = count / total * 100 if total > 0 else 0
                amount_wan = amount / 10000 if amount else 0
                name = stage_names.get(stage, stage)
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

        # 按年份分布
        print("\n📅 按年份分布(报备时间):")
        year_stats = db.session.query(
            func.year(Project.report_time).label('year'),
            func.count(Project.id).label('count')
        ).filter(
            Project.is_deleted == False,
            Project.report_time.isnot(None)
        ).group_by(func.year(Project.report_time)).order_by(func.year(Project.report_time)).all()

        for stat in year_stats:
            if stat.year:
                print(f"  {stat.year}: {stat.count} 个项目")

        return total, success_count, failed_count

def explore_workitem_data():
    """探索跟进记录数据"""
    print_section("2. 跟进记录数据分析")

    with app.app_context():
        # 总跟进数
        total_items = WorkItem.query.filter(WorkItem.is_deleted == False).count()
        project_items = WorkItem.query.filter(
            WorkItem.is_deleted == False,
            WorkItem.project_id.isnot(None)
        ).count()

        print(f"\n总跟进记录: {total_items}")
        print(f"关联项目的跟进: {project_items} ({project_items/total_items*100:.1f}%)")

        # 按工作类型分布
        print("\n📋 按工作类型分布(关联项目):")
        type_stats = db.session.query(
            WorkItem.work_type,
            func.count(WorkItem.id).label('count'),
            func.sum(WorkItem.actual_hours).label('total_hours')
        ).filter(
            WorkItem.is_deleted == False,
            WorkItem.project_id.isnot(None)
        ).group_by(WorkItem.work_type).order_by(func.count(WorkItem.id).desc()).all()

        type_labels = WorkItem.TYPE_LABELS
        print(f"\n{'类型':<20} {'数量':>8} {'总工时':>10}")
        print("-" * 42)
        for stat in type_stats[:15]:  # Top 15
            label = type_labels.get(stat.work_type, stat.work_type or '未分类')
            hours = stat.total_hours or 0
            print(f"{label:<20} {stat.count:>8} {hours:>10.1f}h")

        # 按状态分布
        print("\n📊 跟进状态分布:")
        status_stats = db.session.query(
            WorkItem.status,
            func.count(WorkItem.id).label('count')
        ).filter(
            WorkItem.is_deleted == False,
            WorkItem.project_id.isnot(None)
        ).group_by(WorkItem.status).all()

        for stat in status_stats:
            print(f"  {stat.status}: {stat.count}")

        # 出差统计
        trip_count = WorkItem.query.filter(
            WorkItem.is_deleted == False,
            WorkItem.project_id.isnot(None),
            WorkItem.is_business_trip == True
        ).count()
        print(f"\n🚄 出差跟进: {trip_count} ({trip_count/project_items*100:.1f}%)")

        return project_items

def explore_quotation_data():
    """探索报价单数据"""
    print_section("3. 报价单数据分析")

    with app.app_context():
        total_quotes = Quotation.query.count()
        print(f"\n总报价单数: {total_quotes}")

        # 有报价的项目数
        projects_with_quote = db.session.query(
            func.count(distinct(Quotation.project_id))
        ).scalar()
        print(f"有报价单的项目数: {projects_with_quote}")

        # 报价单审批状态分布
        print("\n📋 报价单审批状态:")
        approval_stats = db.session.query(
            Quotation.approval_status,
            func.count(Quotation.id).label('count')
        ).group_by(Quotation.approval_status).all()

        for stat in approval_stats:
            status = stat.approval_status or '未提交'
            print(f"  {status}: {stat.count}")

        return total_quotes

def explore_stage_history():
    """探索阶段历史数据"""
    print_section("4. 阶段变更历史分析")

    with app.app_context():
        total_changes = ProjectStageHistory.query.count()
        print(f"\n总阶段变更记录: {total_changes}")

        # 平均每个项目的阶段变更次数
        projects_with_history = db.session.query(
            func.count(distinct(ProjectStageHistory.project_id))
        ).scalar()

        if projects_with_history > 0:
            avg_changes = total_changes / projects_with_history
            print(f"有历史记录的项目数: {projects_with_history}")
            print(f"平均每项目变更次数: {avg_changes:.2f}")

        # 阶段转换统计
        print("\n📊 阶段转换统计(Top 10):")
        transition_stats = db.session.query(
            ProjectStageHistory.from_stage,
            ProjectStageHistory.to_stage,
            func.count(ProjectStageHistory.id).label('count')
        ).group_by(
            ProjectStageHistory.from_stage,
            ProjectStageHistory.to_stage
        ).order_by(func.count(ProjectStageHistory.id).desc()).limit(10).all()

        stage_names = {
            'discover': '发现', 'embed': '植入', 'pre_tender': '标前',
            'tendering': '标中', 'awarded': '中标', 'quoted': '批价',
            'signed': '签约', 'lost': '失败', 'paused': '搁置',
            None: '(无)'
        }

        for stat in transition_stats:
            from_name = stage_names.get(stat.from_stage, stat.from_stage)
            to_name = stage_names.get(stat.to_stage, stat.to_stage)
            print(f"  {from_name} → {to_name}: {stat.count}")

        return total_changes

def analyze_successful_projects():
    """分析成功项目特征"""
    print_section("5. 成功项目特征分析")

    with app.app_context():
        # 成功项目定义：signed 或 quoted
        success_projects = Project.query.filter(
            Project.is_deleted == False,
            Project.current_stage.in_(['signed', 'quoted'])
        ).all()

        print(f"\n成功项目数: {len(success_projects)}")

        if not success_projects:
            print("暂无成功项目数据")
            return {}

        # 分析成功项目的特征
        stats = {
            'has_quotation': 0,
            'has_authorization': 0,
            'has_end_user': 0,
            'has_contractor': 0,
            'has_integrator': 0,
            'total_followups': 0,
            'total_hours': 0,
            'visit_count': 0,
            'trip_count': 0,
            'days_to_success': []
        }

        for project in success_projects:
            # 基本信息完整度
            if project.quotation_customer and project.quotation_customer > 0:
                stats['has_quotation'] += 1
            if project.authorization_code:
                stats['has_authorization'] += 1
            if project.end_user:
                stats['has_end_user'] += 1
            if project.contractor:
                stats['has_contractor'] += 1
            if project.system_integrator:
                stats['has_integrator'] += 1

            # 跟进记录统计
            followups = WorkItem.query.filter(
                WorkItem.project_id == project.id,
                WorkItem.is_deleted == False
            ).all()

            stats['total_followups'] += len(followups)
            stats['total_hours'] += sum(f.actual_hours or 0 for f in followups)
            stats['visit_count'] += sum(1 for f in followups if f.work_type == 'customer_visit')
            stats['trip_count'] += sum(1 for f in followups if f.is_business_trip)

            # 项目周期（从报备到当前的天数）
            if project.report_time:
                days = (datetime.now().date() - project.report_time).days
                stats['days_to_success'].append(days)

        n = len(success_projects)
        print("\n✅ 成功项目特征:")
        print(f"  有报价金额: {stats['has_quotation']} ({stats['has_quotation']/n*100:.1f}%)")
        print(f"  有授权编号: {stats['has_authorization']} ({stats['has_authorization']/n*100:.1f}%)")
        print(f"  有最终用户: {stats['has_end_user']} ({stats['has_end_user']/n*100:.1f}%)")
        print(f"  有总承包方: {stats['has_contractor']} ({stats['has_contractor']/n*100:.1f}%)")
        print(f"  有集成商: {stats['has_integrator']} ({stats['has_integrator']/n*100:.1f}%)")

        print(f"\n📊 跟进投入(平均):")
        print(f"  跟进次数: {stats['total_followups']/n:.1f} 次/项目")
        print(f"  投入工时: {stats['total_hours']/n:.1f} 小时/项目")
        print(f"  拜访次数: {stats['visit_count']/n:.1f} 次/项目")
        print(f"  出差次数: {stats['trip_count']/n:.1f} 次/项目")

        if stats['days_to_success']:
            avg_days = sum(stats['days_to_success']) / len(stats['days_to_success'])
            print(f"\n⏱️ 平均项目周期: {avg_days:.0f} 天")

        return stats

def analyze_failed_projects():
    """分析失败项目特征"""
    print_section("6. 失败项目特征分析")

    with app.app_context():
        # 失败项目定义：lost 或 paused
        failed_projects = Project.query.filter(
            Project.is_deleted == False,
            Project.current_stage.in_(['lost', 'paused'])
        ).all()

        print(f"\n失败项目数: {len(failed_projects)}")

        if not failed_projects:
            print("暂无失败项目数据")
            return {}

        stats = {
            'has_quotation': 0,
            'has_authorization': 0,
            'has_end_user': 0,
            'total_followups': 0,
            'total_hours': 0,
            'visit_count': 0,
            'days_to_fail': []
        }

        for project in failed_projects:
            if project.quotation_customer and project.quotation_customer > 0:
                stats['has_quotation'] += 1
            if project.authorization_code:
                stats['has_authorization'] += 1
            if project.end_user:
                stats['has_end_user'] += 1

            followups = WorkItem.query.filter(
                WorkItem.project_id == project.id,
                WorkItem.is_deleted == False
            ).all()

            stats['total_followups'] += len(followups)
            stats['total_hours'] += sum(f.actual_hours or 0 for f in followups)
            stats['visit_count'] += sum(1 for f in followups if f.work_type == 'customer_visit')

            if project.report_time:
                days = (datetime.now().date() - project.report_time).days
                stats['days_to_fail'].append(days)

        n = len(failed_projects)
        print("\n❌ 失败项目特征:")
        print(f"  有报价金额: {stats['has_quotation']} ({stats['has_quotation']/n*100:.1f}%)")
        print(f"  有授权编号: {stats['has_authorization']} ({stats['has_authorization']/n*100:.1f}%)")
        print(f"  有最终用户: {stats['has_end_user']} ({stats['has_end_user']/n*100:.1f}%)")

        print(f"\n📊 跟进投入(平均):")
        print(f"  跟进次数: {stats['total_followups']/n:.1f} 次/项目")
        print(f"  投入工时: {stats['total_hours']/n:.1f} 小时/项目")
        print(f"  拜访次数: {stats['visit_count']/n:.1f} 次/项目")

        return stats

def analyze_top_salespeople():
    """分析优秀销售特征"""
    print_section("7. 优秀销售分析")

    with app.app_context():
        # 按owner统计成功项目数
        sales_stats = db.session.query(
            Project.owner_id,
            User.real_name,
            User.username,
            func.count(Project.id).label('total_projects'),
            func.sum(case((Project.current_stage.in_(['signed', 'quoted']), 1), else_=0)).label('success_count'),
            func.sum(case((Project.current_stage.in_(['lost', 'paused']), 1), else_=0)).label('failed_count'),
            func.sum(Project.quotation_customer).label('total_amount')
        ).join(User, Project.owner_id == User.id).filter(
            Project.is_deleted == False
        ).group_by(
            Project.owner_id, User.real_name, User.username
        ).having(
            func.count(Project.id) >= 5  # 至少5个项目
        ).order_by(
            func.sum(case((Project.current_stage.in_(['signed', 'quoted']), 1), else_=0)).desc()
        ).limit(10).all()

        print("\n🏆 Top 10 销售(按成功项目数):")
        print(f"\n{'姓名':<12} {'总项目':>8} {'成功':>6} {'失败':>6} {'成功率':>8} {'总金额(万)':>12}")
        print("-" * 60)

        top_sales_ids = []
        for stat in sales_stats:
            name = stat.real_name or stat.username
            success_rate = stat.success_count / stat.total_projects * 100 if stat.total_projects > 0 else 0
            amount_wan = (stat.total_amount or 0) / 10000
            print(f"{name:<12} {stat.total_projects:>8} {stat.success_count:>6} {stat.failed_count:>6} {success_rate:>7.1f}% {amount_wan:>12,.1f}")

            if stat.success_count >= 3:  # 成功项目>=3的为优秀销售
                top_sales_ids.append(stat.owner_id)

        # 分析优秀销售的项目特征
        if top_sales_ids:
            print(f"\n📊 优秀销售(成功>=3)的项目特征:")

            top_projects = Project.query.filter(
                Project.is_deleted == False,
                Project.owner_id.in_(top_sales_ids),
                Project.current_stage.in_(['signed', 'quoted'])
            ).all()

            if top_projects:
                total_followups = 0
                total_visits = 0
                total_trips = 0
                total_hours = 0

                for project in top_projects:
                    followups = WorkItem.query.filter(
                        WorkItem.project_id == project.id,
                        WorkItem.is_deleted == False
                    ).all()

                    total_followups += len(followups)
                    total_visits += sum(1 for f in followups if f.work_type == 'customer_visit')
                    total_trips += sum(1 for f in followups if f.is_business_trip)
                    total_hours += sum(f.actual_hours or 0 for f in followups)

                n = len(top_projects)
                print(f"  分析项目数: {n}")
                print(f"  平均跟进次数: {total_followups/n:.1f} 次/项目")
                print(f"  平均拜访次数: {total_visits/n:.1f} 次/项目")
                print(f"  平均出差次数: {total_trips/n:.1f} 次/项目")
                print(f"  平均投入工时: {total_hours/n:.1f} 小时/项目")

        return sales_stats

def compare_success_vs_failed():
    """对比成功vs失败项目"""
    print_section("8. 成功 vs 失败项目对比")

    with app.app_context():
        # 成功项目
        success = Project.query.filter(
            Project.is_deleted == False,
            Project.current_stage.in_(['signed', 'quoted'])
        ).all()

        # 失败项目
        failed = Project.query.filter(
            Project.is_deleted == False,
            Project.current_stage.in_(['lost', 'paused'])
        ).all()

        if not success or not failed:
            print("数据不足，无法对比")
            return

        def calc_stats(projects):
            stats = {
                'count': len(projects),
                'has_quote_pct': 0,
                'has_auth_pct': 0,
                'avg_followups': 0,
                'avg_visits': 0,
                'avg_hours': 0
            }

            has_quote = sum(1 for p in projects if p.quotation_customer and p.quotation_customer > 0)
            has_auth = sum(1 for p in projects if p.authorization_code)
            stats['has_quote_pct'] = has_quote / len(projects) * 100
            stats['has_auth_pct'] = has_auth / len(projects) * 100

            total_followups = 0
            total_visits = 0
            total_hours = 0

            for p in projects:
                followups = WorkItem.query.filter(
                    WorkItem.project_id == p.id,
                    WorkItem.is_deleted == False
                ).all()
                total_followups += len(followups)
                total_visits += sum(1 for f in followups if f.work_type == 'customer_visit')
                total_hours += sum(f.actual_hours or 0 for f in followups)

            stats['avg_followups'] = total_followups / len(projects)
            stats['avg_visits'] = total_visits / len(projects)
            stats['avg_hours'] = total_hours / len(projects)

            return stats

        success_stats = calc_stats(success)
        failed_stats = calc_stats(failed)

        print(f"\n{'指标':<20} {'成功项目':>12} {'失败项目':>12} {'差异':>10}")
        print("-" * 58)
        print(f"{'项目数量':<20} {success_stats['count']:>12} {failed_stats['count']:>12}")
        print(f"{'有报价金额%':<20} {success_stats['has_quote_pct']:>11.1f}% {failed_stats['has_quote_pct']:>11.1f}% {success_stats['has_quote_pct']-failed_stats['has_quote_pct']:>+9.1f}%")
        print(f"{'有授权编号%':<20} {success_stats['has_auth_pct']:>11.1f}% {failed_stats['has_auth_pct']:>11.1f}% {success_stats['has_auth_pct']-failed_stats['has_auth_pct']:>+9.1f}%")
        print(f"{'平均跟进次数':<20} {success_stats['avg_followups']:>12.1f} {failed_stats['avg_followups']:>12.1f} {success_stats['avg_followups']-failed_stats['avg_followups']:>+10.1f}")
        print(f"{'平均拜访次数':<20} {success_stats['avg_visits']:>12.1f} {failed_stats['avg_visits']:>12.1f} {success_stats['avg_visits']-failed_stats['avg_visits']:>+10.1f}")
        print(f"{'平均投入工时':<20} {success_stats['avg_hours']:>12.1f} {failed_stats['avg_hours']:>12.1f} {success_stats['avg_hours']-failed_stats['avg_hours']:>+10.1f}")

def main():
    """主函数"""
    print("\n" + "="*60)
    print("  项目成功率预测模型 - 数据探索报告")
    print("  生成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    # 1. 项目分布
    explore_project_distribution()

    # 2. 跟进记录
    explore_workitem_data()

    # 3. 报价单
    explore_quotation_data()

    # 4. 阶段历史
    explore_stage_history()

    # 5. 成功项目特征
    analyze_successful_projects()

    # 6. 失败项目特征
    analyze_failed_projects()

    # 7. 优秀销售分析
    analyze_top_salespeople()

    # 8. 对比分析
    compare_success_vs_failed()

    print("\n" + "="*60)
    print("  数据探索完成")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
