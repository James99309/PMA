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

def get_role_special_permissions(role_key):
    """
    获取角色的特殊权限描述
    
    参数:
        role_key: 角色键名
        
    返回:
        角色的特殊权限描述列表
    """
    if not role_key:
        return []
    
    # 统一转为小写处理，避免大小写问题
    role_key_lower = role_key.lower().strip() if isinstance(role_key, str) else ''
    
    # 特殊权限映射
    special_permissions = {
        'finance_director': [
            '可查看所有项目列表和详情（只读）',
            '可查看所有报价单列表和详情（只读）',
            '不允许编辑或删除项目和报价单',
            '只能查看自己的客户信息'
        ],
        'finace_director': [
            '可查看所有项目列表和详情（只读）',
            '可查看所有报价单列表和详情（只读）',
            '不允许编辑或删除项目和报价单',
            '只能查看自己的客户信息'
        ],
        'solution_manager': [
            '可查看所有项目列表和详情（只读）',
            '可查看所有报价单列表和详情',
            '可编辑所有报价单，但不允许删除',
            '不允许编辑或删除项目',
            '可查看所有客户信息'
        ],
        'product_manager': [
            '可查看所有项目列表和详情（只读）',
            '可查看所有报价单列表和详情（只读）',
            '不允许编辑或删除项目和报价单',
            '只能查看自己的客户信息'
        ],
        'product': [
            '可查看所有项目列表和详情（只读）',
            '可查看所有报价单列表和详情（只读）',
            '不允许编辑或删除项目和报价单',
            '只能查看自己的客户信息'
        ],
        'solution': [
            '可查看所有项目列表和详情（只读）',
            '可查看所有报价单列表和详情',
            '可编辑所有报价单，但不允许删除',
            '不允许编辑或删除项目',
            '可查看所有客户信息'
        ]
    }
    
    return special_permissions.get(role_key_lower, []) 