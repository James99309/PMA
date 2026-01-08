#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接模拟API调用，检查content_filter_options"""
import psycopg2
import json

OVS_DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

conn = psycopg2.connect(OVS_DB_URL)
cursor = conn.cursor()

print("="*60)
print("模拟 API /config-management/api/role-permissions/<role> 响应")
print("="*60)

# 1. 检查 dictionaries 表数据
print("\n【1】检查 dictionaries 表数据")
for dict_type in ['project_type', 'project_stage', 'report_source']:
    cursor.execute("""
        SELECT key, value, value_en, is_active
        FROM dictionaries
        WHERE type = %s
        ORDER BY sort_order
    """, (dict_type,))
    results = cursor.fetchall()
    print(f"\n  {dict_type}:")
    for key, value, value_en, is_active in results:
        status = "✓" if is_active else "✗ (inactive)"
        print(f"    {status} {key}: {value} / {value_en}")

# 2. 模拟 _get_cached_dict 和 _get_dict_options 的返回
print("\n\n【2】模拟 _get_dict_options 返回格式")

def get_dict_options_simulated(cursor, dict_type, lang='zh'):
    """模拟 _get_dict_options 函数"""
    cursor.execute("""
        SELECT key, value, value_en
        FROM dictionaries
        WHERE type = %s AND is_active = true
        ORDER BY sort_order
    """, (dict_type,))
    results = cursor.fetchall()

    # 模拟 _get_cached_dict 的返回格式
    labels = {row[0]: {'zh': row[1], 'en': row[2] or row[1]} for row in results}

    # 模拟 _get_dict_options 的返回格式
    return [(k, v.get(lang, v.get('zh', k))) for k, v in labels.items()]

for dict_type in ['project_type', 'project_stage', 'report_source']:
    options = get_dict_options_simulated(cursor, dict_type, 'en')
    print(f"\n  {dict_type} (英文):")
    print(f"    options = {options}")
    print(f"    长度 = {len(options)}")

# 3. 模拟完整的 content_filter_options 结构
print("\n\n【3】模拟完整的 content_filter_options 结构")

content_filter_options = {
    'project': {
        'project_type': {
            'label': 'Type',  # 英文翻译
            'options': get_dict_options_simulated(cursor, 'project_type', 'en')
        },
        'current_stage': {
            'label': 'Project Stage',  # 英文翻译
            'options': get_dict_options_simulated(cursor, 'project_stage', 'en')
        },
        'report_source': {
            'label': 'Source',  # 英文翻译
            'options': get_dict_options_simulated(cursor, 'report_source', 'en')
        }
    }
}

print(json.dumps(content_filter_options, ensure_ascii=False, indent=2))

# 4. 检查关键问题：options 是否为空
print("\n\n【4】检查 options 是否为空")
for module, config in content_filter_options.items():
    for filter_key, filter_config in config.items():
        opts = filter_config.get('options', [])
        if len(opts) == 0:
            print(f"  ⚠️ {module}.{filter_key}.options 为空!")
        else:
            print(f"  ✓ {module}.{filter_key}.options 有 {len(opts)} 个选项")

cursor.close()
conn.close()
