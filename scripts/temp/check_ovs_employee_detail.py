#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS员工详细业务表现分析
针对 roy.lim(BD), quah, alesandro, ryan.lim(区域销售) 的深度分析

角色定位：
- roy.lim (BD): 发现新业务机会，为团队提供业务开拓能力
- quah, alesandro, ryan.lim (区域销售): 直接接触业务机会，推进到中端或成交阶段
"""
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

import psycopg2
from psycopg2.extras import RealDictCursor

# OVS数据库连接
OVS_DB_URL = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

# 项目阶段定义（从早期到成交）
STAGE_ORDER = {
    'discover': 1,      # 发现
    'embed': 2,         # 品牌植入
    'pre_tender': 3,    # 招标前
    'tendering': 4,     # 招标中
    'awarded': 5,       # 中标
    'quoted': 6,        # 已报价
    'signed': 7,        # 签约
    'lost': 0,          # 失败
}

STAGE_NAMES = {
    'discover': '发现',
    'embed': '品牌植入',
    'pre_tender': '招标前',
    'tendering': '招标中',
    'awarded': '中标',
    'quoted': '已报价',
    'signed': '签约',
    'lost': '失败',
    None: '未设置',
    '': '未设置'
}

def get_connection():
    return psycopg2.connect(OVS_DB_URL, cursor_factory=RealDictCursor)

def analyze_employee(cur, emp_id, emp_name, role_type):
    """分析单个员工的详细业务表现"""

    print(f"\n{'='*80}")
    print(f"📊 {emp_name} 详细业务分析")
    print(f"   角色定位: {role_type}")
    print(f"{'='*80}")

    # 1. 基本信息和工作起始时间
    cur.execute("""
        SELECT id, username, real_name, email, department, role,
               created_at, last_login
        FROM users WHERE id = %s
    """, (emp_id,))
    user = cur.fetchone()

    # 获取第一次业务活动时间（作为实际工作起始点）
    cur.execute("""
        SELECT MIN(created_at) as first_activity FROM (
            SELECT created_at FROM projects WHERE owner_id = %s OR created_by = %s
            UNION ALL
            SELECT created_at FROM quotations WHERE owner_id = %s
            UNION ALL
            SELECT created_at FROM companies WHERE owner_id = %s
            UNION ALL
            SELECT created_at FROM worklogs WHERE owner_id = %s
        ) activities
    """, (emp_id, emp_id, emp_id, emp_id, emp_id))
    first_activity = cur.fetchone()['first_activity']

    account_created = user['created_at']
    if isinstance(account_created, (int, float)):
        account_created = datetime.fromtimestamp(account_created)

    work_start = first_activity or account_created
    # 处理时区问题
    if work_start:
        if hasattr(work_start, 'tzinfo') and work_start.tzinfo is not None:
            work_start = work_start.replace(tzinfo=None)
        days_working = (datetime.now() - work_start).days
    else:
        days_working = 0

    # 格式化时间显示
    if first_activity and hasattr(first_activity, 'tzinfo') and first_activity.tzinfo:
        first_activity = first_activity.replace(tzinfo=None)
    if account_created and hasattr(account_created, 'tzinfo') and account_created.tzinfo:
        account_created = account_created.replace(tzinfo=None)

    print(f"\n📅 工作时间线")
    print(f"   账号创建: {account_created.strftime('%Y-%m-%d') if account_created else 'N/A'}")
    print(f"   首次业务活动: {first_activity.strftime('%Y-%m-%d') if first_activity else '无记录'}")
    print(f"   工作天数: {days_working} 天")

    # 2. 项目阶段分布分析
    print(f"\n📈 项目阶段分布")
    print("-" * 60)

    cur.execute("""
        SELECT p.id, p.project_name, p.current_stage, p.created_at, p.updated_at,
               p.dealer, p.contractor, p.system_integrator, p.end_user,
               p.quotation_customer, p.quotation_currency, p.status,
               p.is_active, p.last_activity_date
        FROM projects p
        WHERE p.owner_id = %s
        ORDER BY p.created_at DESC
    """, (emp_id,))
    projects = cur.fetchall()

    # 阶段统计
    stage_counts = defaultdict(int)
    stage_projects = defaultdict(list)
    for proj in projects:
        stage = proj['current_stage'] or '未设置'
        stage_counts[stage] += 1
        stage_projects[stage].append(proj)

    total_projects = len(projects)

    # 计算中后期项目比例（招标前及以后）
    mid_late_stages = ['pre_tender', 'tendering', 'awarded', 'quoted', 'signed']
    mid_late_count = sum(stage_counts.get(s, 0) for s in mid_late_stages)
    mid_late_ratio = (mid_late_count / total_projects * 100) if total_projects > 0 else 0

    print(f"   项目总数: {total_projects}")
    print(f"   中后期项目(招标前及以后): {mid_late_count} ({mid_late_ratio:.1f}%)")
    print()

    # 按阶段显示
    for stage in ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', None, '']:
        count = stage_counts.get(stage, 0)
        if count > 0:
            stage_name = STAGE_NAMES.get(stage, stage or '未设置')
            bar = '█' * min(count, 20)
            indicator = "🎯" if stage in mid_late_stages else "  "
            print(f"   {indicator} {stage_name:8}: {count:3} {bar}")

    # 3. 合作伙伴参与度分析
    print(f"\n🤝 合作伙伴参与度")
    print("-" * 60)

    partner_stats = {
        'has_dealer': 0,        # 有经销商
        'has_contractor': 0,    # 有总包商
        'has_si': 0,            # 有系统集成商
        'has_end_user': 0,      # 有最终用户
        'multi_partner': 0,     # 多方参与
    }

    for proj in projects:
        partners = 0
        if proj['dealer']:
            partner_stats['has_dealer'] += 1
            partners += 1
        if proj['contractor']:
            partner_stats['has_contractor'] += 1
            partners += 1
        if proj['system_integrator']:
            partner_stats['has_si'] += 1
            partners += 1
        if proj['end_user']:
            partner_stats['has_end_user'] += 1
            partners += 1
        if partners >= 2:
            partner_stats['multi_partner'] += 1

    if total_projects > 0:
        print(f"   有经销商参与: {partner_stats['has_dealer']:3} ({partner_stats['has_dealer']/total_projects*100:.1f}%)")
        print(f"   有总包商参与: {partner_stats['has_contractor']:3} ({partner_stats['has_contractor']/total_projects*100:.1f}%)")
        print(f"   有集成商参与: {partner_stats['has_si']:3} ({partner_stats['has_si']/total_projects*100:.1f}%)")
        print(f"   有最终用户:   {partner_stats['has_end_user']:3} ({partner_stats['has_end_user']/total_projects*100:.1f}%)")
        print(f"   多方合作项目: {partner_stats['multi_partner']:3} ({partner_stats['multi_partner']/total_projects*100:.1f}%)")
    else:
        print("   无项目数据")

    # 4. 业务活跃度分析
    print(f"\n🔥 业务活跃度分析")
    print("-" * 60)

    # 按月统计项目创建
    cur.execute("""
        SELECT DATE_TRUNC('month', created_at) as month, COUNT(*) as count
        FROM projects WHERE owner_id = %s
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month DESC
        LIMIT 6
    """, (emp_id,))
    monthly_projects = cur.fetchall()

    print("   近6个月项目创建:")
    for mp in monthly_projects:
        month_str = mp['month'].strftime('%Y-%m') if mp['month'] else 'N/A'
        bar = '█' * mp['count']
        print(f"      {month_str}: {mp['count']:2} {bar}")

    # 按月统计报价
    cur.execute("""
        SELECT DATE_TRUNC('month', created_at) as month,
               COUNT(*) as count,
               COALESCE(SUM(amount), 0) as total_amount
        FROM quotations WHERE owner_id = %s
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY month DESC
        LIMIT 6
    """, (emp_id,))
    monthly_quotes = cur.fetchall()

    print("\n   近6个月报价活动:")
    for mq in monthly_quotes:
        month_str = mq['month'].strftime('%Y-%m') if mq['month'] else 'N/A'
        amount = mq['total_amount'] / 100 if mq['total_amount'] else 0
        print(f"      {month_str}: {mq['count']:2}单 ${amount:>10,.2f}")

    if not monthly_quotes:
        print("      无报价记录")

    # 5. 工作日志分析
    print(f"\n📝 工作日志记录")
    print("-" * 60)

    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as last_30,
               COUNT(CASE WHEN created_at >= NOW() - INTERVAL '90 days' THEN 1 END) as last_90,
               MAX(created_at) as last_log
        FROM worklogs WHERE owner_id = %s
    """, (emp_id,))
    worklog_stats = cur.fetchone()

    print(f"   日志总数: {worklog_stats['total']}")
    print(f"   近30天: {worklog_stats['last_30']}")
    print(f"   近90天: {worklog_stats['last_90']}")
    last_log = worklog_stats['last_log']
    print(f"   最后记录: {last_log.strftime('%Y-%m-%d') if last_log else '无'}")

    # 计算日志频率
    if days_working > 0 and worklog_stats['total'] > 0:
        log_frequency = days_working / worklog_stats['total']
        print(f"   平均频率: 每 {log_frequency:.1f} 天一条")

    # 6. 客户开发分析
    print(f"\n👥 客户开发分析")
    print("-" * 60)

    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as last_30,
               COUNT(CASE WHEN created_at >= NOW() - INTERVAL '90 days' THEN 1 END) as last_90
        FROM companies WHERE owner_id = %s AND is_deleted = FALSE
    """, (emp_id,))
    customer_stats = cur.fetchone()

    print(f"   客户总数: {customer_stats['total']}")
    print(f"   近30天新增: {customer_stats['last_30']}")
    print(f"   近90天新增: {customer_stats['last_90']}")

    # 客户类型分布
    cur.execute("""
        SELECT company_type, COUNT(*) as count
        FROM companies WHERE owner_id = %s AND is_deleted = FALSE
        GROUP BY company_type
        ORDER BY count DESC
    """, (emp_id,))
    customer_types = cur.fetchall()

    if customer_types:
        print("\n   客户类型分布:")
        for ct in customer_types:
            type_name = ct['company_type'] or '未分类'
            print(f"      {type_name}: {ct['count']}")

    # 7. 项目详情列表（最近10个）
    print(f"\n📋 最近项目详情 (最新10个)")
    print("-" * 60)

    for i, proj in enumerate(projects[:10], 1):
        stage_name = STAGE_NAMES.get(proj['current_stage'], proj['current_stage'] or '未设置')
        created = proj['created_at'].strftime('%Y-%m-%d') if proj['created_at'] else 'N/A'
        updated = proj['updated_at'].strftime('%Y-%m-%d') if proj['updated_at'] else 'N/A'
        amount = proj['quotation_customer'] / 100 if proj['quotation_customer'] else 0
        currency = proj['quotation_currency'] or 'USD'

        # 合作伙伴标记
        partners = []
        if proj['dealer']: partners.append('经销商')
        if proj['contractor']: partners.append('总包')
        if proj['system_integrator']: partners.append('集成商')
        partner_str = ', '.join(partners) if partners else '无'

        print(f"   {i}. {proj['project_name'][:30]}")
        print(f"      阶段: {stage_name} | 创建: {created} | 更新: {updated}")
        print(f"      金额: {currency} {amount:,.2f} | 合作伙伴: {partner_str}")

    # 8. 综合评估
    print(f"\n{'='*60}")
    print(f"📊 综合评估 - {emp_name}")
    print(f"{'='*60}")

    issues = []
    positives = []

    if role_type == "BD (业务开发)":
        # BD角色评估标准
        if total_projects >= 10:
            positives.append(f"✅ 项目数量充足 ({total_projects}个)")
        else:
            issues.append(f"⚠️ 项目数量偏少 ({total_projects}个)，BD应发现更多机会")

        if customer_stats['total'] >= 30:
            positives.append(f"✅ 客户资源丰富 ({customer_stats['total']}个)")
        else:
            issues.append(f"⚠️ 客户积累不足 ({customer_stats['total']}个)")

        if customer_stats['last_30'] >= 3:
            positives.append(f"✅ 近期客户开发活跃 (30天+{customer_stats['last_30']})")
        else:
            issues.append(f"⚠️ 近期客户开发放缓 (30天+{customer_stats['last_30']})")

    else:
        # 区域销售评估标准
        if mid_late_ratio >= 30:
            positives.append(f"✅ 中后期项目比例良好 ({mid_late_ratio:.1f}%)")
        else:
            issues.append(f"⚠️ 中后期项目比例偏低 ({mid_late_ratio:.1f}%)，需推进项目阶段")

        if partner_stats['multi_partner'] / total_projects >= 0.3 if total_projects > 0 else False:
            positives.append(f"✅ 多方合作项目比例良好")
        else:
            issues.append(f"⚠️ 多方合作项目偏少，需加强合作伙伴参与")

        if monthly_quotes:
            recent_quotes = sum(mq['count'] for mq in monthly_quotes[:3])
            if recent_quotes >= 3:
                positives.append(f"✅ 近3月报价活跃 ({recent_quotes}单)")
            else:
                issues.append(f"⚠️ 近3月报价较少 ({recent_quotes}单)")
        else:
            issues.append(f"❌ 无报价记录，销售需产出报价")

    # 通用评估
    if worklog_stats['last_30'] >= 4:
        positives.append(f"✅ 工作日志记录及时")
    elif worklog_stats['last_30'] > 0:
        issues.append(f"⚠️ 工作日志记录偏少 (30天{worklog_stats['last_30']}条)")
    else:
        issues.append(f"❌ 近30天无工作日志")

    for p in positives:
        print(f"   {p}")
    for i in issues:
        print(f"   {i}")

    return {
        'name': emp_name,
        'role': role_type,
        'days_working': days_working,
        'total_projects': total_projects,
        'mid_late_ratio': mid_late_ratio,
        'issues': issues,
        'positives': positives
    }


def main():
    conn = get_connection()
    cur = conn.cursor()

    print("=" * 80)
    print("OVS 员工详细业务表现分析报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 目标员工及其角色定位
    target_employees = [
        ('roy', 'roy.lim', 'BD (业务开发)'),
        ('quah', 'quah', '区域销售'),
        ('alesandro', 'alesandro', '区域销售'),
        ('ryanlim', 'ryan.lim', '区域销售'),
    ]

    results = []

    for username, display_name, role_type in target_employees:
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user:
            result = analyze_employee(cur, user['id'], display_name, role_type)
            results.append(result)
        else:
            print(f"\n⚠️ 未找到用户: {username}")

    # 总结对比
    print("\n" + "=" * 80)
    print("📊 团队整体对比总结")
    print("=" * 80)

    print("\n┌─────────────┬──────────┬──────────┬────────────┬──────────────┐")
    print("│ 员工        │ 工作天数 │ 项目总数 │ 中后期比例 │ 主要问题数   │")
    print("├─────────────┼──────────┼──────────┼────────────┼──────────────┤")
    for r in results:
        print(f"│ {r['name']:11} │ {r['days_working']:>8} │ {r['total_projects']:>8} │ {r['mid_late_ratio']:>9.1f}% │ {len(r['issues']):>12} │")
    print("└─────────────┴──────────┴──────────┴────────────┴──────────────┘")

    print("\n" + "=" * 80)
    print("报告生成完成")
    print("=" * 80)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
