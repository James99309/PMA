#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OVS员工业务表现分析脚本
检查evertacsolutions公司员工（排除patrick, james.ni, peizhen）的近期业务表现
"""
import sys
import os
from datetime import datetime, timedelta

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

import psycopg2
from psycopg2.extras import RealDictCursor

# OVS数据库连接
OVS_DB_URL = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

def get_connection():
    """获取数据库连接"""
    return psycopg2.connect(OVS_DB_URL, cursor_factory=RealDictCursor)

def check_employee_performance():
    """检查员工业务表现"""
    conn = get_connection()
    cur = conn.cursor()

    # 排除的用户名（不区分大小写）
    excluded_users = ['patrick', 'james.ni', 'peizhen']

    print("=" * 80)
    print("OVS 员工业务表现分析报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 1. 获取evertacsolutions公司的员工（排除指定人员）
    print("\n📋 一、员工列表")
    print("-" * 80)

    cur.execute("""
        SELECT id, username, real_name, email, department, role,
               is_active, last_login, created_at
        FROM users
        WHERE LOWER(company_name) LIKE '%evertac%'
        ORDER BY username
    """)

    all_employees = cur.fetchall()
    target_employees = []

    for emp in all_employees:
        username_lower = emp['username'].lower() if emp['username'] else ''
        real_name_lower = emp['real_name'].lower() if emp['real_name'] else ''
        # 排除用户名或真实姓名匹配的用户
        if username_lower not in excluded_users and real_name_lower not in excluded_users:
            target_employees.append(emp)
            last_login = datetime.fromtimestamp(emp['last_login']).strftime('%Y-%m-%d %H:%M') if emp['last_login'] else '从未登录'
            print(f"  {emp['real_name'] or emp['username']:15} | {emp['username']:15} | {emp['department'] or 'N/A':12} | {emp['role']:15} | 最后登录: {last_login}")

    print(f"\n  共 {len(target_employees)} 名员工（已排除 {', '.join(excluded_users)}）")

    if not target_employees:
        print("\n❌ 未找到符合条件的员工")
        cur.close()
        conn.close()
        return

    # 获取员工ID列表
    employee_ids = [emp['id'] for emp in target_employees]

    # 2. 近期项目活动（最近90天）
    print("\n\n📊 二、近期项目活动（最近90天）")
    print("-" * 80)

    ninety_days_ago = datetime.now() - timedelta(days=90)

    for emp in target_employees:
        emp_name = emp['real_name'] or emp['username']
        emp_id = emp['id']

        # 创建的项目
        cur.execute("""
            SELECT COUNT(*) as count FROM projects
            WHERE created_by = %s AND created_at >= %s
        """, (emp_id, ninety_days_ago))
        created_projects = cur.fetchone()['count']

        # 负责的项目（owner）
        cur.execute("""
            SELECT COUNT(*) as count FROM projects
            WHERE owner_id = %s
        """, (emp_id,))
        owned_projects = cur.fetchone()['count']

        # 活跃项目（最近有更新的）
        cur.execute("""
            SELECT COUNT(*) as count FROM projects
            WHERE owner_id = %s AND updated_at >= %s
        """, (emp_id, ninety_days_ago))
        active_projects = cur.fetchone()['count']

        print(f"  {emp_name:15} | 近90天创建: {created_projects:3} | 负责项目总数: {owned_projects:3} | 近90天活跃: {active_projects:3}")

    # 3. 报价活动分析
    print("\n\n💰 三、报价活动分析")
    print("-" * 80)

    for emp in target_employees:
        emp_name = emp['real_name'] or emp['username']
        emp_id = emp['id']

        # 创建的报价单
        cur.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
            FROM quotations
            WHERE owner_id = %s AND created_at >= %s
        """, (emp_id, ninety_days_ago))
        result = cur.fetchone()
        recent_quotations = result['count']
        recent_amount = result['total_amount'] if result['total_amount'] else 0  # 原始金额（不需要转换）

        # 总报价单数量
        cur.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total_amount
            FROM quotations
            WHERE owner_id = %s
        """, (emp_id,))
        result = cur.fetchone()
        total_quotations = result['count']
        total_amount = result['total_amount'] if result['total_amount'] else 0

        print(f"  {emp_name:15} | 近90天报价: {recent_quotations:3}单 ${recent_amount:>12,.2f} | 总计: {total_quotations:3}单 ${total_amount:>12,.2f}")

    # 4. 客户管理分析
    print("\n\n👥 四、客户管理分析")
    print("-" * 80)

    for emp in target_employees:
        emp_name = emp['real_name'] or emp['username']
        emp_id = emp['id']

        # 拥有的客户数
        cur.execute("""
            SELECT COUNT(*) as count FROM companies
            WHERE owner_id = %s AND is_deleted = FALSE
        """, (emp_id,))
        owned_customers = cur.fetchone()['count']

        # 近期创建的客户
        cur.execute("""
            SELECT COUNT(*) as count FROM companies
            WHERE owner_id = %s AND is_deleted = FALSE AND created_at >= %s
        """, (emp_id, ninety_days_ago))
        recent_customers = cur.fetchone()['count']

        # 联系人数量
        cur.execute("""
            SELECT COUNT(*) as count FROM contacts c
            JOIN companies co ON c.company_id = co.id
            WHERE co.owner_id = %s AND co.is_deleted = FALSE
        """, (emp_id,))
        contacts_count = cur.fetchone()['count']

        print(f"  {emp_name:15} | 客户总数: {owned_customers:3} | 近90天新增: {recent_customers:3} | 联系人: {contacts_count:3}")

    # 5. 工作日志分析
    print("\n\n📝 五、工作日志分析（最近30天）")
    print("-" * 80)

    thirty_days_ago = datetime.now() - timedelta(days=30)

    for emp in target_employees:
        emp_name = emp['real_name'] or emp['username']
        emp_id = emp['id']

        # 工作日志数量
        cur.execute("""
            SELECT COUNT(*) as count FROM worklogs
            WHERE owner_id = %s AND created_at >= %s
        """, (emp_id, thirty_days_ago))
        worklog_count = cur.fetchone()['count']

        # 最后一次工作日志
        cur.execute("""
            SELECT created_at FROM worklogs
            WHERE owner_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (emp_id,))
        last_worklog = cur.fetchone()
        last_worklog_date = last_worklog['created_at'].strftime('%Y-%m-%d') if last_worklog else '无记录'

        print(f"  {emp_name:15} | 近30天日志: {worklog_count:3}条 | 最后日志: {last_worklog_date}")

    # 6. 系统活跃度分析
    print("\n\n🔥 六、系统活跃度分析")
    print("-" * 80)

    for emp in target_employees:
        emp_name = emp['real_name'] or emp['username']
        emp_id = emp['id']

        # 最后登录时间
        last_login = datetime.fromtimestamp(emp['last_login']).strftime('%Y-%m-%d %H:%M') if emp['last_login'] else '从未登录'

        # 计算距今天数
        if emp['last_login']:
            days_since_login = (datetime.now() - datetime.fromtimestamp(emp['last_login'])).days
            activity_status = "🟢 活跃" if days_since_login <= 7 else ("🟡 一般" if days_since_login <= 30 else "🔴 不活跃")
        else:
            days_since_login = "N/A"
            activity_status = "⚫ 从未登录"

        print(f"  {emp_name:15} | 最后登录: {last_login:16} | 距今: {str(days_since_login):>4}天 | {activity_status}")

    # 7. 综合业绩汇总
    print("\n\n📈 七、综合业绩汇总（按报价金额排序）")
    print("-" * 80)

    performance_data = []
    for emp in target_employees:
        emp_name = emp['real_name'] or emp['username']
        emp_id = emp['id']

        # 获取各项数据
        cur.execute("SELECT COUNT(*) FROM projects WHERE owner_id = %s", (emp_id,))
        projects = cur.fetchone()['count']

        cur.execute("SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total FROM quotations WHERE owner_id = %s", (emp_id,))
        result = cur.fetchone()
        quotations = result['count']
        amount = result['total'] if result['total'] else 0

        cur.execute("SELECT COUNT(*) FROM companies WHERE owner_id = %s AND is_deleted = FALSE", (emp_id,))
        customers = cur.fetchone()['count']

        performance_data.append({
            'name': emp_name,
            'projects': projects,
            'quotations': quotations,
            'amount': amount,
            'customers': customers,
            'last_login': emp['last_login']
        })

    # 按报价金额排序
    performance_data.sort(key=lambda x: x['amount'], reverse=True)

    print(f"  {'姓名':15} | {'项目':>6} | {'报价单':>6} | {'报价金额':>15} | {'客户':>6}")
    print("  " + "-" * 60)
    for p in performance_data:
        print(f"  {p['name']:15} | {p['projects']:>6} | {p['quotations']:>6} | ${p['amount']:>13,.2f} | {p['customers']:>6}")

    print("\n" + "=" * 80)
    print("报告生成完成")
    print("=" * 80)

    cur.close()
    conn.close()

if __name__ == "__main__":
    check_employee_performance()
