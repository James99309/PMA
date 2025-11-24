#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目报备审批诊断脚本

功能：调查指定项目的报备审批数据，诊断提交失败的原因
用途：临时调试脚本，用于排查审批流程问题
"""
import sys
import os
from datetime import datetime

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

# 加载环境变量
from dotenv import load_dotenv
env_path = os.path.join(get_project_root(), '.env.sp8d.backup')
if not os.path.exists(env_path):
    print(f"❌ 错误：找不到环境配置文件 {env_path}")
    sys.exit(1)

load_dotenv(env_path)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 数据库连接
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ 错误：未找到 DATABASE_URL 环境变量")
    sys.exit(1)

print(f"🔗 正在连接数据库...")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def print_header(title):
    """打印分节标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_row(label, value, indent=0):
    """打印数据行"""
    indent_str = "  " * indent
    print(f"{indent_str}{label}: {value}")

def investigate_project_registration(project_name):
    """调查项目报备审批问题"""

    print_header("🔍 项目报备审批诊断工具")
    print(f"🎯 目标项目: {project_name}\n")

    # 1. 查找项目
    print_header("1. 查找项目记录")

    query = text("""
        SELECT id, project_name, status, registration_status, created_at, created_by
        FROM projects
        WHERE project_name LIKE :project_name
        ORDER BY created_at DESC
    """)

    projects = session.execute(query, {'project_name': f'%{project_name}%'}).fetchall()

    if not projects:
        print(f"❌ 未找到匹配的项目: {project_name}")
        return

    if len(projects) > 1:
        print(f"⚠️ 找到 {len(projects)} 个匹配的项目：")
        for i, proj in enumerate(projects, 1):
            print(f"  {i}. ID={proj.id}, 名称={proj.project_name[:50]}...")
        print("\n使用第一个项目进行诊断\n")

    project = projects[0]
    project_id = project.id

    print_row("项目ID", project_id)
    print_row("项目名称", project.project_name)
    print_row("项目状态", project.status or "未设置")
    print_row("报备状态", project.registration_status or "未设置")
    print_row("创建时间", project.created_at)
    print_row("创建人ID", project.created_by)

    # 2. 查找审批实例
    print_header("2. 审批实例列表")

    query = text("""
        SELECT id, object_type, status, current_step,
               created_at, updated_at, created_by
        FROM approval_instances
        WHERE object_type IN ('project', 'project_registration')
          AND object_id = :project_id
        ORDER BY created_at DESC
    """)

    instances = session.execute(query, {'project_id': project_id}).fetchall()

    if not instances:
        print("ℹ️ 未找到任何审批实例")
        print("💡 建议：这是正常情况，项目可以重新提交报备")
        return

    print(f"📋 找到 {len(instances)} 个审批实例：\n")

    active_instances = []
    for i, inst in enumerate(instances, 1):
        print(f"实例 #{i}:")
        print_row("审批实例ID", inst.id, indent=1)
        print_row("对象类型", inst.object_type, indent=1)
        print_row("状态", inst.status, indent=1)
        print_row("当前步骤", inst.current_step or "未设置", indent=1)
        print_row("创建时间", inst.created_at, indent=1)
        print_row("更新时间", inst.updated_at, indent=1)
        print_row("创建人ID", inst.created_by, indent=1)

        # 检查是否为活跃实例
        if inst.status not in ['approved', 'rejected', 'cancelled', 'completed']:
            active_instances.append(inst)
            print_row("⚠️ 状态", "活跃/未完成", indent=1)

        print()

    # 3. 查看审批历史
    print_header("3. 审批历史记录")

    for inst in instances:
        print(f"📝 审批实例 #{inst.id} 的历史记录:")

        query = text("""
            SELECT ah.id, ah.action, ah.comment, ah.created_at,
                   u.username, u.real_name
            FROM approval_history ah
            LEFT JOIN users u ON ah.user_id = u.id
            WHERE ah.instance_id = :instance_id
            ORDER BY ah.created_at DESC
        """)

        histories = session.execute(query, {'instance_id': inst.id}).fetchall()

        if not histories:
            print_row("ℹ️", "无历史记录", indent=1)
        else:
            for j, hist in enumerate(histories, 1):
                print(f"\n  操作 #{j}:")
                print_row("操作类型", hist.action, indent=2)
                print_row("备注/拒绝原因", hist.comment or "无", indent=2)
                print_row("操作人", f"{hist.real_name or hist.username} ({hist.username})", indent=2)
                print_row("操作时间", hist.created_at, indent=2)

        print()

    # 4. 问题诊断
    print_header("4. 问题诊断")

    issues = []
    suggestions = []

    # 检查1: 是否存在多个活跃实例
    if len(active_instances) > 1:
        issues.append(f"❌ 发现 {len(active_instances)} 个活跃的审批实例（应该最多1个）")
        suggestions.append("💡 建议：关闭旧的审批实例，只保留最新的")
    elif len(active_instances) == 1:
        issues.append(f"⚠️ 存在1个活跃的审批实例（状态: {active_instances[0].status}）")
        if active_instances[0].status == 'pending':
            suggestions.append("💡 建议：审批实例处于待审批状态，可能阻止了重新提交")
            suggestions.append("💡 修复：将此实例状态更新为 'rejected' 或 'cancelled'")

    # 检查2: 项目状态与审批状态是否同步
    if instances:
        latest_instance = instances[0]
        if project.registration_status != latest_instance.status:
            issues.append(f"⚠️ 项目报备状态 ({project.registration_status}) 与最新审批实例状态 ({latest_instance.status}) 不一致")
            suggestions.append("💡 建议：同步项目的 registration_status 字段")

    # 检查3: 是否有被拒绝的实例
    rejected_instances = [inst for inst in instances if inst.status == 'rejected']
    if rejected_instances and not active_instances:
        issues.append(f"✅ 找到 {len(rejected_instances)} 个已拒绝的审批实例，且无活跃实例")
        suggestions.append("💡 状态正常：项目应该可以重新提交报备")

    # 输出诊断结果
    if not issues:
        print("✅ 未发现明显问题")
        print("💡 项目应该可以正常重新提交报备")
    else:
        print("发现以下问题：\n")
        for issue in issues:
            print(f"  {issue}")

        print("\n" + "="*80)
        print("  修复建议")
        print("="*80 + "\n")

        for suggestion in suggestions:
            print(f"  {suggestion}")

    # 5. 修复SQL建议
    if active_instances:
        print_header("5. 修复SQL建议")

        print("如果需要关闭活跃的审批实例，可以执行以下SQL：\n")

        for inst in active_instances:
            print(f"-- 关闭审批实例 #{inst.id}")
            print(f"UPDATE approval_instances")
            print(f"SET status = 'cancelled',")
            print(f"    updated_at = NOW()")
            print(f"WHERE id = {inst.id};")
            print()

        print(f"-- 同步项目报备状态")
        print(f"UPDATE projects")
        print(f"SET registration_status = 'rejected'")
        print(f"WHERE id = {project_id};")
        print()

        print("⚠️ 警告：执行前请备份数据，并确认操作的正确性！")

if __name__ == '__main__':
    project_name = "宝山区淞南镇N12-0102单元04-01地块商办项目"

    try:
        investigate_project_registration(project_name)
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()
        print("\n" + "="*80)
        print("  诊断完成")
        print("="*80)
