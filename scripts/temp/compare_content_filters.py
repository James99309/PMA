#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""比较OVS和本地数据库的content_filters配置"""
import sys
import os

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
import json

# OVS数据库连接
OVS_DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

# 本地数据库连接
LOCAL_DB_URL = 'postgresql://nijie@localhost:5432/pma_local'

def get_content_filters(conn, db_name):
    """获取所有模块的content_filters配置"""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"【{db_name}】content_filters配置")
    print('='*60)

    # 1. 获取角色权限的content_filters
    print(f"\n--- 角色权限 (role_permissions) ---")
    cursor.execute("""
        SELECT role, module, content_filters
        FROM role_permissions
        WHERE module IN ('project', 'quotation', 'customer', 'order', 'expense', 'pricing_order')
        ORDER BY role, module
    """)

    role_filters = {}
    results = cursor.fetchall()

    for role, module, filters in results:
        key = f"{role}:{module}"
        role_filters[key] = filters

        has_filters = filters is not None and len(filters) > 0 if filters else False
        status = "✓ 有配置" if has_filters else "✗ 空"

        if has_filters:
            filter_summary = []
            for k, v in filters.items():
                if v:
                    filter_summary.append(f"{k}({len(v)}项)")
            print(f"  {role:20} | {module:15} | {status} | {', '.join(filter_summary)}")
        else:
            print(f"  {role:20} | {module:15} | {status}")

    # 2. 检查支持content_filter的模块
    print(f"\n--- 支持内容筛选的模块 (permission_modules) ---")
    cursor.execute("""
        SELECT module_id, name, supports_content_filter
        FROM permission_modules
        WHERE supports_content_filter = true
        ORDER BY module_id
    """)

    modules_with_filter = cursor.fetchall()
    if modules_with_filter:
        for module_id, name, supports in modules_with_filter:
            print(f"  {module_id:20} | {name}")
    else:
        print("  没有找到支持内容筛选的模块")

    cursor.close()
    return role_filters


def compare_filters(local_filters, ovs_filters):
    """比较两个数据库的content_filters"""
    print(f"\n{'='*60}")
    print("【比较结果】")
    print('='*60)

    # 获取所有唯一的key
    all_keys = set(local_filters.keys()) | set(ovs_filters.keys())

    # 关注的模块
    focus_modules = ['project', 'quotation']

    print(f"\n--- 项目和报价单模块对比 ---")

    differences = []
    for key in sorted(all_keys):
        role, module = key.split(':')

        if module not in focus_modules:
            continue

        local_val = local_filters.get(key)
        ovs_val = ovs_filters.get(key)

        local_empty = local_val is None or (isinstance(local_val, dict) and len(local_val) == 0)
        ovs_empty = ovs_val is None or (isinstance(ovs_val, dict) and len(ovs_val) == 0)

        if local_empty and ovs_empty:
            status = "两边都为空"
            icon = "⚪"
        elif local_empty and not ovs_empty:
            status = "本地为空, OVS有配置"
            icon = "🔴"
            differences.append((key, "本地为空", ovs_val))
        elif not local_empty and ovs_empty:
            status = "本地有配置, OVS为空"
            icon = "🟡"
            differences.append((key, local_val, "OVS为空"))
        elif local_val == ovs_val:
            status = "两边相同"
            icon = "🟢"
        else:
            status = "两边不同"
            icon = "🔵"
            differences.append((key, local_val, ovs_val))

        print(f"  {icon} {role:20} | {module:15} | {status}")

    # 显示差异详情
    if differences:
        print(f"\n--- 差异详情 ---")
        for key, local_val, ovs_val in differences:
            print(f"\n  【{key}】")
            print(f"    本地: {json.dumps(local_val, ensure_ascii=False, indent=4) if isinstance(local_val, dict) else local_val}")
            print(f"    OVS:  {json.dumps(ovs_val, ensure_ascii=False, indent=4) if isinstance(ovs_val, dict) else ovs_val}")

    # 显示所有模块的概览
    print(f"\n--- 所有模块概览 ---")
    for key in sorted(all_keys):
        role, module = key.split(':')

        if module in focus_modules:
            continue  # 已经显示过了

        local_val = local_filters.get(key)
        ovs_val = ovs_filters.get(key)

        local_empty = local_val is None or (isinstance(local_val, dict) and len(local_val) == 0)
        ovs_empty = ovs_val is None or (isinstance(ovs_val, dict) and len(ovs_val) == 0)

        if not local_empty or not ovs_empty:
            print(f"  {role:20} | {module:15} | 本地:{not local_empty} | OVS:{not ovs_empty}")


def main():
    print("比较OVS和本地数据库的content_filters配置")
    print("="*60)

    # 连接本地数据库
    try:
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        print("✓ 本地数据库连接成功")
    except Exception as e:
        print(f"✗ 本地数据库连接失败: {e}")
        return

    # 连接OVS数据库
    try:
        ovs_conn = psycopg2.connect(OVS_DB_URL)
        print("✓ OVS数据库连接成功")
    except Exception as e:
        print(f"✗ OVS数据库连接失败: {e}")
        local_conn.close()
        return

    try:
        # 获取两边的配置
        local_filters = get_content_filters(local_conn, "本地数据库")
        ovs_filters = get_content_filters(ovs_conn, "OVS数据库")

        # 比较
        compare_filters(local_filters, ovs_filters)

    finally:
        local_conn.close()
        ovs_conn.close()
        print("\n数据库连接已关闭")


if __name__ == '__main__':
    main()
