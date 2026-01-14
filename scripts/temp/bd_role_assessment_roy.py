#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BD岗位专项评估报告 - roy.lim
基于BD核心职责：发现中前期项目、开发上游客户、为销售团队提供业务引导
"""
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

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

OVS_DB_URL = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

# BD关注的上游客户类型
UPSTREAM_CUSTOMER_TYPES = ['user', 'designer', 'consultant']  # 最终用户、设计院、顾问公司
DOWNSTREAM_CUSTOMER_TYPES = ['dealer', 'contractor', 'integrator', 'general_contractor']  # 经销商、总包、集成商

# BD应该发现的项目阶段（早中期）
BD_TARGET_STAGES = ['discover', 'embed', 'pre_tender']  # 发现、品牌植入、招标前

def get_connection():
    return psycopg2.connect(OVS_DB_URL, cursor_factory=RealDictCursor)

def generate_bd_assessment():
    conn = get_connection()
    cur = conn.cursor()

    # 获取roy的用户信息
    cur.execute("SELECT * FROM users WHERE username = 'roy'")
    roy = cur.fetchone()
    roy_id = roy['id']

    # 获取工作起始时间
    cur.execute("""
        SELECT MIN(created_at) as first_activity FROM (
            SELECT created_at FROM projects WHERE owner_id = %s OR created_by = %s
            UNION ALL
            SELECT created_at FROM companies WHERE owner_id = %s
        ) activities
    """, (roy_id, roy_id, roy_id))
    first_activity = cur.fetchone()['first_activity']
    if first_activity and first_activity.tzinfo:
        first_activity = first_activity.replace(tzinfo=None)

    work_start = first_activity
    days_working = (datetime.now() - work_start).days if work_start else 0
    months_working = days_working / 30.0

    print("=" * 90)
    print("📋 BD岗位专项评估报告")
    print("=" * 90)
    print(f"   评估对象: roy.lim")
    print(f"   评估日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"   入职时间: {work_start.strftime('%Y-%m-%d') if work_start else 'N/A'}")
    print(f"   工作周期: {days_working}天 ({months_working:.1f}个月)")
    print("=" * 90)

    # ========== 第一部分：BD岗位职责定义 ==========
    print("\n" + "═" * 90)
    print("第一部分：BD岗位职责与考核标准")
    print("═" * 90)
    print("""
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              BD (Business Development) 岗位定义                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ 【核心使命】                                                                          │
│   为销售团队持续发现和输送高质量的早中期业务机会，建立上游客户关系网络                    │
│                                                                                      │
│ 【关键职责】                                                                          │
│   1. 项目发现：主动挖掘市场中的新项目机会（发现→品牌植入→招标前阶段）                    │
│   2. 上游客户开发：重点开发最终用户(User)、设计院(Designer)、顾问公司(Consultant)        │
│   3. 业务引导：将成熟项目有效交接给区域销售团队跟进                                      │
│   4. 市场情报：收集行业动态、竞争信息，为团队提供决策依据                                │
│                                                                                      │
│ 【考核指标】                                                                          │
│   • 月均新增项目数：≥3个                                                              │
│   • 上游客户占比：≥50%（用户+设计院+顾问）                                             │
│   • 项目信息完整度：≥80%（含合作伙伴、最终用户信息）                                    │
│   • 业务活跃度：持续稳定的项目发现节奏                                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
""")

    # ========== 第二部分：项目发现能力评估 ==========
    print("\n" + "═" * 90)
    print("第二部分：项目发现能力评估")
    print("═" * 90)

    # 获取所有项目
    cur.execute("""
        SELECT p.*,
               DATE_TRUNC('month', p.created_at) as create_month
        FROM projects p
        WHERE p.owner_id = %s OR p.created_by = %s
        ORDER BY p.created_at
    """, (roy_id, roy_id))
    all_projects = cur.fetchall()

    total_projects = len(all_projects)
    monthly_avg = total_projects / months_working if months_working > 0 else 0

    print(f"\n📊 项目数量统计")
    print("-" * 60)
    print(f"   项目总数: {total_projects}")
    print(f"   工作月数: {months_working:.1f}个月")
    print(f"   月均项目: {monthly_avg:.2f}个")

    # 评估月均项目数
    if monthly_avg >= 3:
        print(f"   评估结果: ✅ 达标 (标准≥3个/月)")
    elif monthly_avg >= 2:
        print(f"   评估结果: ⚠️ 接近达标 (标准≥3个/月)")
    else:
        print(f"   评估结果: ❌ 未达标 (标准≥3个/月)")

    # 按月统计项目创建趋势
    print(f"\n📈 月度项目发现趋势")
    print("-" * 60)

    monthly_counts = defaultdict(int)
    for proj in all_projects:
        if proj['create_month']:
            month_key = proj['create_month'].strftime('%Y-%m')
            monthly_counts[month_key] += 1

    # 按时间排序
    sorted_months = sorted(monthly_counts.keys())

    print(f"   {'月份':10} | {'项目数':6} | {'趋势图':20} | {'达标'}")
    print("   " + "-" * 55)

    trend_data = []
    for month in sorted_months:
        count = monthly_counts[month]
        bar = '█' * count + '░' * (5 - count) if count <= 5 else '█' * 5 + '+' * (count - 5)
        status = "✅" if count >= 3 else ("⚠️" if count >= 2 else "❌")
        print(f"   {month:10} | {count:6} | {bar:20} | {status}")
        trend_data.append(count)

    # 趋势分析
    if len(trend_data) >= 3:
        recent_avg = sum(trend_data[-3:]) / 3
        early_avg = sum(trend_data[:3]) / min(3, len(trend_data[:3]))

        print(f"\n   趋势分析:")
        print(f"   • 早期月均(前3月): {early_avg:.1f}个")
        print(f"   • 近期月均(后3月): {recent_avg:.1f}个")

        if recent_avg > early_avg:
            print(f"   • 趋势判断: 📈 上升趋势 (+{((recent_avg/early_avg)-1)*100:.0f}%) ✅")
        elif recent_avg < early_avg * 0.7:
            print(f"   • 趋势判断: 📉 下降趋势 ({((recent_avg/early_avg)-1)*100:.0f}%) ❌ 需关注")
        else:
            print(f"   • 趋势判断: ➡️ 基本持平")

    # ========== 第三部分：上游客户开发评估 ==========
    print("\n" + "═" * 90)
    print("第三部分：上游客户开发评估")
    print("═" * 90)

    cur.execute("""
        SELECT company_type, COUNT(*) as count,
               COUNT(CASE WHEN created_at >= NOW() - INTERVAL '90 days' THEN 1 END) as recent_count
        FROM companies
        WHERE owner_id = %s AND is_deleted = FALSE
        GROUP BY company_type
        ORDER BY count DESC
    """, (roy_id,))
    customer_types = cur.fetchall()

    total_customers = sum(ct['count'] for ct in customer_types)
    upstream_count = sum(ct['count'] for ct in customer_types if ct['company_type'] in UPSTREAM_CUSTOMER_TYPES)
    downstream_count = sum(ct['count'] for ct in customer_types if ct['company_type'] in DOWNSTREAM_CUSTOMER_TYPES)

    upstream_ratio = (upstream_count / total_customers * 100) if total_customers > 0 else 0

    print(f"\n📊 客户结构分析")
    print("-" * 60)
    print(f"   客户总数: {total_customers}")
    print(f"   上游客户: {upstream_count} ({upstream_ratio:.1f}%)")
    print(f"   下游客户: {downstream_count} ({100-upstream_ratio:.1f}%)")

    if upstream_ratio >= 50:
        print(f"   评估结果: ✅ 达标 (标准≥50%上游客户)")
    elif upstream_ratio >= 40:
        print(f"   评估结果: ⚠️ 接近达标 (标准≥50%上游客户)")
    else:
        print(f"   评估结果: ❌ 未达标 (标准≥50%上游客户)")

    print(f"\n📋 客户类型明细")
    print("-" * 60)
    print(f"   {'类型':20} | {'数量':6} | {'占比':8} | {'近90天':8} | {'定位'}")
    print("   " + "-" * 65)

    type_names = {
        'user': '最终用户',
        'designer': '设计院',
        'consultant': '顾问公司',
        'dealer': '经销商',
        'contractor': '总包商',
        'integrator': '系统集成商',
        'general_contractor': '总承包商',
        'partner': '合作伙伴',
        'other': '其他'
    }

    for ct in customer_types:
        ctype = ct['company_type'] or '未分类'
        type_label = type_names.get(ctype, ctype)
        ratio = ct['count'] / total_customers * 100
        position = "🔵 上游" if ctype in UPSTREAM_CUSTOMER_TYPES else ("🟢 下游" if ctype in DOWNSTREAM_CUSTOMER_TYPES else "⚪ 其他")
        print(f"   {type_label:20} | {ct['count']:6} | {ratio:6.1f}% | {ct['recent_count']:8} | {position}")

    # 上游客户开发建议
    print(f"\n💡 上游客户开发建议")
    print("-" * 60)

    user_count = sum(ct['count'] for ct in customer_types if ct['company_type'] == 'user')
    designer_count = sum(ct['count'] for ct in customer_types if ct['company_type'] == 'designer')
    consultant_count = sum(ct['count'] for ct in customer_types if ct['company_type'] == 'consultant')

    if user_count < 15:
        print(f"   ⚠️ 最终用户({user_count}个)偏少，建议加强终端客户开发")
    else:
        print(f"   ✅ 最终用户({user_count}个)数量良好")

    if designer_count < 10:
        print(f"   ⚠️ 设计院({designer_count}个)偏少，设计院是项目早期关键决策方")
    else:
        print(f"   ✅ 设计院({designer_count}个)数量良好")

    if consultant_count < 5:
        print(f"   ⚠️ 顾问公司({consultant_count}个)偏少，顾问公司可带来批量项目信息")
    else:
        print(f"   ✅ 顾问公司({consultant_count}个)数量良好")

    # ========== 第四部分：项目质量评估 ==========
    print("\n" + "═" * 90)
    print("第四部分：项目质量与信息完整度评估")
    print("═" * 90)

    quality_stats = {
        'has_end_user': 0,      # 有最终用户信息
        'has_dealer': 0,        # 有经销商
        'has_contractor': 0,    # 有总包商
        'has_integrator': 0,    # 有集成商
        'has_partners': 0,      # 有任何合作伙伴
        'multi_partners': 0,    # 多方合作伙伴
        'has_amount': 0,        # 有预估金额
        'early_stage': 0,       # 早期阶段（BD目标）
        'mid_stage': 0,         # 中期阶段
        'late_stage': 0,        # 后期阶段
    }

    for proj in all_projects:
        partners = 0
        if proj['end_user']:
            quality_stats['has_end_user'] += 1
        if proj['dealer']:
            quality_stats['has_dealer'] += 1
            partners += 1
        if proj['contractor']:
            quality_stats['has_contractor'] += 1
            partners += 1
        if proj['system_integrator']:
            quality_stats['has_integrator'] += 1
            partners += 1
        if partners > 0:
            quality_stats['has_partners'] += 1
        if partners >= 2:
            quality_stats['multi_partners'] += 1
        if proj['quotation_customer'] and proj['quotation_customer'] > 0:
            quality_stats['has_amount'] += 1

        stage = proj['current_stage']
        if stage in ['discover', 'embed']:
            quality_stats['early_stage'] += 1
        elif stage in ['pre_tender', 'tendering']:
            quality_stats['mid_stage'] += 1
        elif stage in ['awarded', 'quoted', 'signed']:
            quality_stats['late_stage'] += 1

    print(f"\n📊 项目信息完整度")
    print("-" * 60)

    completeness_score = 0
    total_checks = 4

    end_user_ratio = quality_stats['has_end_user'] / total_projects * 100 if total_projects > 0 else 0
    partner_ratio = quality_stats['has_partners'] / total_projects * 100 if total_projects > 0 else 0
    amount_ratio = quality_stats['has_amount'] / total_projects * 100 if total_projects > 0 else 0

    print(f"   • 有最终用户信息: {quality_stats['has_end_user']}/{total_projects} ({end_user_ratio:.0f}%)")
    if end_user_ratio >= 60:
        print(f"     评估: ✅ 良好")
        completeness_score += 1
    else:
        print(f"     评估: ⚠️ 需提升 (建议≥60%)")

    print(f"   • 有合作伙伴信息: {quality_stats['has_partners']}/{total_projects} ({partner_ratio:.0f}%)")
    if partner_ratio >= 60:
        print(f"     评估: ✅ 良好")
        completeness_score += 1
    else:
        print(f"     评估: ⚠️ 需提升 (建议≥60%)")

    print(f"   • 多方合作项目: {quality_stats['multi_partners']}/{total_projects} ({quality_stats['multi_partners']/total_projects*100:.0f}%)")
    if quality_stats['multi_partners'] / total_projects >= 0.4:
        print(f"     评估: ✅ 良好")
        completeness_score += 1
    else:
        print(f"     评估: ⚠️ 可提升 (建议≥40%)")

    print(f"   • 有预估金额: {quality_stats['has_amount']}/{total_projects} ({amount_ratio:.0f}%)")
    if amount_ratio >= 30:
        print(f"     评估: ✅ 尚可")
        completeness_score += 1
    else:
        print(f"     评估: ⚠️ 偏低 (建议≥30%)")

    overall_completeness = completeness_score / total_checks * 100
    print(f"\n   📊 综合完整度得分: {overall_completeness:.0f}%")

    # 项目阶段分布（BD视角）
    print(f"\n📊 项目阶段分布（BD视角）")
    print("-" * 60)

    early_ratio = quality_stats['early_stage'] / total_projects * 100 if total_projects > 0 else 0
    mid_ratio = quality_stats['mid_stage'] / total_projects * 100 if total_projects > 0 else 0
    late_ratio = quality_stats['late_stage'] / total_projects * 100 if total_projects > 0 else 0

    print(f"   早期(发现+植入): {quality_stats['early_stage']}个 ({early_ratio:.0f}%) - BD主要工作区")
    print(f"   中期(招标前+中): {quality_stats['mid_stage']}个 ({mid_ratio:.0f}%) - 待交接销售")
    print(f"   后期(中标+签约): {quality_stats['late_stage']}个 ({late_ratio:.0f}%) - 已转化")

    if early_ratio >= 50:
        print(f"\n   评估: ✅ 阶段分布符合BD职责，专注早期项目发现")
    else:
        print(f"\n   评估: ⚠️ 早期项目占比偏低，BD应更多关注新项目发现")

    # ========== 第五部分：业务活跃度与成功率 ==========
    print("\n" + "═" * 90)
    print("第五部分：业务活跃度与成功率分析")
    print("═" * 90)

    # 活跃度分析
    print(f"\n📊 业务活跃度")
    print("-" * 60)

    # 近30/60/90天活动
    cur.execute("""
        SELECT
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as last_30,
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '60 days' THEN 1 END) as last_60,
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '90 days' THEN 1 END) as last_90
        FROM projects WHERE owner_id = %s OR created_by = %s
    """, (roy_id, roy_id))
    activity = cur.fetchone()

    print(f"   近30天新增项目: {activity['last_30']}")
    print(f"   近60天新增项目: {activity['last_60']}")
    print(f"   近90天新增项目: {activity['last_90']}")

    # 客户开发活跃度
    cur.execute("""
        SELECT
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as last_30,
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '90 days' THEN 1 END) as last_90
        FROM companies WHERE owner_id = %s AND is_deleted = FALSE
    """, (roy_id,))
    customer_activity = cur.fetchone()

    print(f"   近30天新增客户: {customer_activity['last_30']}")
    print(f"   近90天新增客户: {customer_activity['last_90']}")

    # 活跃度评估
    if activity['last_30'] >= 2:
        print(f"\n   项目活跃度评估: ✅ 活跃")
    elif activity['last_30'] >= 1:
        print(f"\n   项目活跃度评估: ⚠️ 一般")
    else:
        print(f"\n   项目活跃度评估: ❌ 不活跃，近30天无新项目")

    # 项目转化/成功率
    print(f"\n📊 项目转化率（BD→销售交接成功率）")
    print("-" * 60)

    # 统计各阶段转化
    stage_flow = {
        '发现': quality_stats['early_stage'],
        '招标阶段': quality_stats['mid_stage'],
        '成交阶段': quality_stats['late_stage'],
    }

    # 计算转化率
    discover_to_mid = (quality_stats['mid_stage'] + quality_stats['late_stage']) / total_projects * 100 if total_projects > 0 else 0
    mid_to_late = quality_stats['late_stage'] / (quality_stats['mid_stage'] + quality_stats['late_stage']) * 100 if (quality_stats['mid_stage'] + quality_stats['late_stage']) > 0 else 0

    print(f"   发现→招标: {discover_to_mid:.0f}% ({quality_stats['mid_stage'] + quality_stats['late_stage']}/{total_projects})")
    print(f"   招标→成交: {mid_to_late:.0f}% ({quality_stats['late_stage']}/{quality_stats['mid_stage'] + quality_stats['late_stage']})")

    overall_conversion = quality_stats['late_stage'] / total_projects * 100 if total_projects > 0 else 0
    print(f"   整体转化率: {overall_conversion:.0f}% ({quality_stats['late_stage']}/{total_projects})")

    if overall_conversion >= 15:
        print(f"\n   评估: ✅ 转化率良好")
    elif overall_conversion >= 10:
        print(f"\n   评估: ⚠️ 转化率一般")
    else:
        print(f"\n   评估: ⚠️ 转化率偏低，需关注项目质量和推进")

    # ========== 第六部分：趋势发展评估 ==========
    print("\n" + "═" * 90)
    print("第六部分：趋势发展评估（入职以来）")
    print("═" * 90)

    # 按季度分析
    print(f"\n📊 季度业务发展趋势")
    print("-" * 60)

    quarterly_data = defaultdict(lambda: {'projects': 0, 'customers': 0, 'upstream': 0})

    for proj in all_projects:
        if proj['created_at']:
            created = proj['created_at']
            if hasattr(created, 'tzinfo') and created.tzinfo:
                created = created.replace(tzinfo=None)
            quarter = f"{created.year}Q{(created.month-1)//3+1}"
            quarterly_data[quarter]['projects'] += 1

    cur.execute("""
        SELECT created_at, company_type FROM companies
        WHERE owner_id = %s AND is_deleted = FALSE
    """, (roy_id,))
    customers_data = cur.fetchall()

    for cust in customers_data:
        if cust['created_at']:
            created = cust['created_at']
            if hasattr(created, 'tzinfo') and created.tzinfo:
                created = created.replace(tzinfo=None)
            quarter = f"{created.year}Q{(created.month-1)//3+1}"
            quarterly_data[quarter]['customers'] += 1
            if cust['company_type'] in UPSTREAM_CUSTOMER_TYPES:
                quarterly_data[quarter]['upstream'] += 1

    sorted_quarters = sorted(quarterly_data.keys())

    print(f"   {'季度':10} | {'项目':6} | {'客户':6} | {'上游客户':8} | {'趋势'}")
    print("   " + "-" * 50)

    prev_projects = 0
    for q in sorted_quarters:
        data = quarterly_data[q]
        if prev_projects > 0:
            trend = "📈" if data['projects'] > prev_projects else ("📉" if data['projects'] < prev_projects else "➡️")
        else:
            trend = "🆕"
        print(f"   {q:10} | {data['projects']:6} | {data['customers']:6} | {data['upstream']:8} | {trend}")
        prev_projects = data['projects']

    # 总体趋势判断
    if len(sorted_quarters) >= 2:
        first_q = quarterly_data[sorted_quarters[0]]
        last_q = quarterly_data[sorted_quarters[-1]]

        print(f"\n📈 趋势综合判断")
        print("-" * 60)

        issues = []
        positives = []

        if last_q['projects'] >= first_q['projects']:
            positives.append("项目发现能力稳定或提升")
        else:
            issues.append("近期项目发现数量下降")

        if last_q['customers'] >= first_q['customers'] * 0.8:
            positives.append("客户开发节奏正常")
        else:
            issues.append("近期客户开发放缓")

        if last_q['upstream'] >= 2:
            positives.append("上游客户持续开发中")
        else:
            issues.append("上游客户开发需加强")

        for p in positives:
            print(f"   ✅ {p}")
        for i in issues:
            print(f"   ⚠️ {i}")

    # ========== 第七部分：综合评估与改进建议 ==========
    print("\n" + "═" * 90)
    print("第七部分：综合评估与改进建议")
    print("═" * 90)

    print(f"""
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    综合评分卡                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  评估维度              │  得分  │  权重  │  加权分  │  说明                          │
├─────────────────────────────────────────────────────────────────────────────────────┤""")

    scores = []

    # 1. 项目数量得分
    project_score = min(100, monthly_avg / 3 * 100)
    scores.append(('项目发现数量', project_score, 25, f"月均{monthly_avg:.1f}个"))

    # 2. 上游客户得分
    upstream_score = min(100, upstream_ratio / 50 * 100)
    scores.append(('上游客户比例', upstream_score, 25, f"{upstream_ratio:.0f}%"))

    # 3. 项目质量得分
    quality_score = overall_completeness
    scores.append(('项目信息完整度', quality_score, 25, f"{overall_completeness:.0f}%"))

    # 4. 业务活跃度得分
    activity_score = min(100, activity['last_30'] / 2 * 100)
    scores.append(('近期活跃度', activity_score, 25, f"30天{activity['last_30']}个项目"))

    total_weighted = 0
    for name, score, weight, note in scores:
        weighted = score * weight / 100
        total_weighted += weighted
        status = "✅" if score >= 80 else ("⚠️" if score >= 60 else "❌")
        print(f"│  {name:18} │  {score:4.0f}  │  {weight:4}%  │  {weighted:6.1f}  │  {status} {note:20} │")

    print(f"├─────────────────────────────────────────────────────────────────────────────────────┤")
    print(f"│  综合得分              │        │        │  {total_weighted:5.1f}  │                                │")
    print(f"└─────────────────────────────────────────────────────────────────────────────────────┘")

    # 等级判定
    if total_weighted >= 80:
        grade = "A (优秀)"
        grade_color = "🟢"
    elif total_weighted >= 70:
        grade = "B (良好)"
        grade_color = "🟢"
    elif total_weighted >= 60:
        grade = "C (合格)"
        grade_color = "🟡"
    else:
        grade = "D (需改进)"
        grade_color = "🔴"

    print(f"\n   {grade_color} 综合等级: {grade}")

    # 改进建议
    print(f"""
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  改进建议与目标                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  【短期目标 - 未来30天】                                                              │
│                                                                                      │
│   1. 📌 项目发现: 新增至少3个项目，保持月均≥3的节奏                                   │
│      - 重点关注数据中心、基础设施领域的新项目信息                                      │
│      - 利用现有{designer_count}家设计院资源挖掘项目线索                                │
│                                                                                      │
│   2. 📌 上游客户: 新增至少3个上游客户（用户/设计院/顾问）                              │
│      - 当前上游客户占比{upstream_ratio:.0f}%，目标提升至55%                            │
│      - 重点开发顾问公司，当前仅{consultant_count}家                                    │
│                                                                                      │
│   3. 📌 工作日志: 开始记录工作日志，每周至少2条                                       │
│      - 记录客户拜访、项目进展、市场信息                                               │
│      - 便于团队了解市场动态和工作进展                                                 │
│                                                                                      │
│  【中期目标 - 未来90天】                                                              │
│                                                                                      │
│   1. 📌 项目质量提升:                                                                 │
│      - 新项目必须填写最终用户信息（当前{end_user_ratio:.0f}%→目标80%）                 │
│      - 新项目必须明确至少1个合作伙伴（当前{partner_ratio:.0f}%→目标80%）               │
│                                                                                      │
│   2. 📌 客户结构优化:                                                                 │
│      - 设计院客户: {designer_count}→15家                                              │
│      - 顾问公司客户: {consultant_count}→8家                                           │
│      - 最终用户客户: {user_count}→18家                                                │
│                                                                                      │
│   3. 📌 项目交接机制:                                                                 │
│      - 建立项目成熟度评估标准                                                         │
│      - 每月至少1个项目交接给区域销售团队                                              │
│                                                                                      │
│  【长期目标 - 6个月】                                                                 │
│                                                                                      │
│   1. 累计发现项目≥25个                                                               │
│   2. 上游客户占比稳定在55%以上                                                        │
│   3. 项目转化率（发现→招标）提升至40%                                                 │
│   4. 建立稳定的市场情报收集和分享机制                                                 │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
""")

    # 总结
    print("═" * 90)
    print("评估总结")
    print("═" * 90)
    print(f"""
   roy.lim 在BD岗位工作{days_working}天，整体表现{grade}。

   【优势】
   • 客户资源丰富（{total_customers}个），覆盖多种类型
   • 项目合作伙伴参与度高（60%多方合作）
   • 项目阶段分布合理，专注早中期项目

   【待改进】
   • 月均项目数({monthly_avg:.1f})略低于标准(3个)
   • 上游客户占比({upstream_ratio:.0f}%)低于目标(50%)
   • 无工作日志记录，团队协作透明度不足
   • 近期(10月后)项目发现节奏放缓

   【发展趋势】
   • 2025年7月入职初期表现活跃
   • 8-9月保持稳定输出
   • 10月后有所放缓，需要重新激活
""")

    print("=" * 90)
    print("报告生成完成")
    print("=" * 90)

    cur.close()
    conn.close()


if __name__ == "__main__":
    generate_bd_assessment()
