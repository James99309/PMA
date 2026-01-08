#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查OVS和本地数据库的dictionaries表"""
import psycopg2
import json

# OVS数据库连接
OVS_DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

# 本地数据库连接
LOCAL_DB_URL = 'postgresql://nijie@localhost:5432/pma_local'


def check_dictionaries(conn, db_name):
    """检查dictionaries表中的内容筛选相关类型"""
    cursor = conn.cursor()

    print(f"\n{'='*60}")
    print(f"【{db_name}】dictionaries表检查")
    print('='*60)

    # 检查的字典类型
    dict_types = ['project_type', 'project_stage', 'report_source', 'company_type', 'industry', 'business_type']

    for dict_type in dict_types:
        cursor.execute("""
            SELECT key, value, value_en, is_active
            FROM dictionaries
            WHERE type = %s
            ORDER BY sort_order, id
        """, (dict_type,))

        results = cursor.fetchall()
        print(f"\n--- {dict_type} ---")
        if results:
            for key, value, value_en, is_active in results:
                status = "✓" if is_active else "✗"
                print(f"  {status} {key:25} | {value:15} | {value_en or '-'}")
        else:
            print(f"  ⚠️  没有找到任何记录！")

    cursor.close()


def main():
    print("检查OVS和本地数据库的dictionaries表")
    print("="*60)

    # 连接本地数据库
    try:
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        print("✓ 本地数据库连接成功")
        check_dictionaries(local_conn, "本地数据库")
        local_conn.close()
    except Exception as e:
        print(f"✗ 本地数据库连接失败: {e}")

    # 连接OVS数据库
    try:
        ovs_conn = psycopg2.connect(OVS_DB_URL)
        print("\n✓ OVS数据库连接成功")
        check_dictionaries(ovs_conn, "OVS数据库")
        ovs_conn.close()
    except Exception as e:
        print(f"✗ OVS数据库连接失败: {e}")

    print("\n数据库连接已关闭")


if __name__ == '__main__':
    main()
