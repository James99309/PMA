#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
角色映射模块
用于统一前端显示和后端处理中的角色标识
"""

# 此文件已废弃！请使用 app/utils/dictionary_helpers.py 中的数据库字典方法获取角色显示名。
# 保留文件仅为兼容历史代码，后续可安全移入 /legacy 目录。

# 角色映射表: 标准键名 -> 中文显示名
ROLE_NAME_MAPPINGS = {
    'admin': '系统管理员',
    'user': '普通用户',
    'customer_sales': '客户销售',
    'product_manager': '产品经理',
    'solution_manager': '解决方案经理',
    'service': '服务人员',
    'service_manager': '服务经理',
    'channel_manager': '渠道经理',
    'sales_director': '营销总监',
    'dealer': '代理商',
    'finance_director': '财务总监',
    
    # 兼容系统中已有的其他角色
    'ceo': '总经理',
    'hr': '绩效经理',
    'business_admin': '商务助理',
    'finace_manager': '财务总监',
    'sales_manager': '销售经理'
}

def get_role_display_name(role_key):
    """
    获取角色的显示名称
    
    参数:
        role_key: 角色键名
        
    返回:
        角色的显示名称，如果没有映射则返回键名本身
    """
    if not role_key:
        return '未知角色'
    
    # 统一转为小写处理，避免大小写问题
    role_key_lower = role_key.lower() if isinstance(role_key, str) else ''
    
    # 查找匹配的角色（不区分大小写）
    for key, display_name in ROLE_NAME_MAPPINGS.items():
        if key.lower() == role_key_lower:
            return display_name
    
    # 如果找不到匹配，返回原始值
    return role_key 

def get_role_special_permissions(role=None):
    """
    获取各角色的特殊权限说明
    
    参数:
        role: 角色名称，如果提供则返回特定角色的权限，否则返回所有角色权限
        
    返回:
        特定角色的权限列表或者所有角色的权限字典
    """
    role_permissions = {
        'admin': {
            'description': '系统管理员拥有所有权限，包括系统设置、用户管理等',
            'special_permissions': [
                '系统参数设置',
                '用户和权限管理', 
                '所有数据查看权限',
                '项目评分权限（默认开启）'
            ],
            'has_special': True
        },
        'sales_director': {
            'description': '销售总监负责销售团队管理和重要项目决策',
            'special_permissions': [
                '部门成员数据查看权限',
                '销售数据统计查看',
                '项目审批权限',
                '项目评分权限（可配置）'
            ],
            'has_special': True
        },
        'service_manager': {
            'description': '服务经理负责客户服务和项目跟进',
            'special_permissions': [
                '客户服务记录管理',
                '项目跟进和更新',
                '项目评分权限（可配置）'
            ],
            'has_special': True
        },
        'channel_manager': {
            'description': '渠道经理负责渠道合作伙伴管理',
            'special_permissions': [
                '渠道合作伙伴管理',
                '渠道项目跟进',
                '项目评分权限（可配置）'
            ],
            'has_special': True
        },
        'product_manager': {
            'description': '产品经理负责产品规划和管理',
            'special_permissions': [
                '产品信息管理',
                '产品价格设置',
                '项目评分权限（可配置）'
            ],
            'has_special': True
        },
        'solution_manager': {
            'description': '解决方案经理负责技术方案设计',
            'special_permissions': [
                '技术方案设计',
                '产品技术支持',
                '项目评分权限（可配置）'
            ],
            'has_special': True
        },
        'sales': {
            'description': '销售人员负责客户开发和项目跟进',
            'special_permissions': [],
            'has_special': False
        },
        'service': {
            'description': '服务人员负责客户服务和技术支持',
            'special_permissions': [],
            'has_special': False
        }
    }
    
    # 如果指定了角色，返回该角色的特殊权限列表
    if role:
        role_info = role_permissions.get(role.lower() if isinstance(role, str) else '', {})
        return role_info.get('special_permissions', []) if role_info.get('has_special', False) else []
    
    # 否则返回所有角色的权限信息
    return role_permissions 