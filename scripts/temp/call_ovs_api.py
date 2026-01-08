#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接调用OVS API获取角色权限"""
import requests
import json

# OVS 服务器地址
OVS_BASE_URL = 'https://ovs.sp8d.com'

# 登录获取session
session = requests.Session()

# 尝试获取一个公开的API端点来测试
print("测试OVS API连接...")

# 由于需要登录，我们直接用psycopg2模拟API的返回逻辑
import psycopg2

OVS_DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

conn = psycopg2.connect(OVS_DB_URL)
cursor = conn.cursor()

print("="*60)
print("模拟 get_content_filter_options() 返回值")
print("="*60)

# 模拟 _get_dict_options 函数
def get_dict_options(cursor, dict_type):
    cursor.execute("""
        SELECT key, value, value_en
        FROM dictionaries
        WHERE type = %s AND is_active = true
        ORDER BY sort_order
    """, (dict_type,))
    return [(row[0], row[1]) for row in cursor.fetchall()]

# 构建 content_filter_options
content_filter_options = {
    'project': {
        'project_type': {
            'label': '项目类型',
            'options': get_dict_options(cursor, 'project_type')
        },
        'current_stage': {
            'label': '项目阶段',
            'options': get_dict_options(cursor, 'project_stage')
        },
        'report_source': {
            'label': '报备来源',
            'options': get_dict_options(cursor, 'report_source')
        }
    },
    'quotation': {
        'project_type': {
            'label': '项目类型',
            'options': get_dict_options(cursor, 'project_type')
        }
    },
    'customer': {
        'company_type': {
            'label': '企业类型',
            'options': get_dict_options(cursor, 'company_type')
        }
    }
}

print("\nJSON格式输出（这是API应该返回的格式）:")
print(json.dumps(content_filter_options, ensure_ascii=False, indent=2))

# 检查选项是否为空
print("\n" + "="*60)
print("检查各模块的选项数量")
print("="*60)

for module, config in content_filter_options.items():
    print(f"\n【{module}】")
    for filter_key, filter_config in config.items():
        opts = filter_config.get('options', [])
        print(f"  {filter_key}: {len(opts)} 个选项")
        if len(opts) == 0:
            print(f"    ⚠️ 选项为空!")

cursor.close()
conn.close()
