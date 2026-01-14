#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库目标配置
定义各个部署环境的数据库连接信息
"""

# 数据库连接配置
# 注意：敏感信息，请勿提交到版本控制
TARGETS = {
    'ovs': {
        'url': 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres',
        'name': 'OVS (Supabase)',
        'description': 'OVS 云端数据库'
    },
    'sp8d': {
        'url': 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres',
        'name': 'SP8D (Supabase)',
        'description': 'SP8D 云端数据库'
    },
    'synology': {
        'url': 'postgresql://pma:pma_secure_password_2024@192.168.1.100:5432/pma',
        'name': 'Synology NAS',
        'description': '群晖本地数据库（需要根据实际情况修改）'
    },
    'local': {
        'url': 'postgresql://nijie@localhost:5432/pma_db',
        'name': 'Local Development',
        'description': '本地开发数据库'
    }
}


def get_target(name):
    """获取目标数据库配置"""
    if name not in TARGETS:
        raise ValueError(f"未知的目标数据库: {name}. 可选: {', '.join(TARGETS.keys())}")
    return TARGETS[name]


def list_targets():
    """列出所有可用目标"""
    print("\n可用的数据库目标:")
    print("-" * 50)
    for key, config in TARGETS.items():
        print(f"  {key:12} - {config['name']}")
        print(f"               {config['description']}")
    print()
