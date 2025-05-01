#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
角色映射模块
用于统一前端显示和后端处理中的角色标识
"""

# 角色映射表: 标准键名 -> 中文显示名
ROLE_NAME_MAPPINGS = {
    'admin': '系统管理员',
    'user': '普通用户',
    'sales': '销售人员',
    'product_manager': '产品经理',
    'solution_manager': '解决方案经理',
    'service': '服务人员',
    'service_manager': '服务经理',
    'channel_manager': '渠道经理',
    'marketing_director': '营销总监',
    'dealer': '代理商',
    
    # 兼容系统中已有的其他角色
    'CEO': '总经理',
    'HR': '绩效经理',
    'business_admin': '商务助理',
    'finace_manager': '财务总监',
    'sales_manager': '销售经理'
}

# 角色键名标准化映射: 非标准键名 -> 标准键名
ROLE_KEY_NORMALIZATION = {
    'channel_manager ': 'channel_manager',  # 处理多余空格
    'sales_director': 'marketing_director',  # 处理名称不一致
    'CEO': 'admin',  # 总经理映射为管理员
    'HR': 'admin',  # 绩效经理映射为管理员
    'business_admin': 'admin',  # 商务助理映射为管理员
    'finace_manager': 'admin',  # 财务总监映射为管理员
    'sales_manager': 'sales',  # 销售经理映射为销售人员
    'customer_sales': 'sales',  # 客户销售映射为销售人员
}

def normalize_role_key(role_key):
    """
    标准化角色键名，处理可能存在的键名不一致问题
    
    参数:
        role_key: 原始角色键名
        
    返回:
        标准化后的角色键名
    """
    if not role_key:
        return role_key
        
    # 处理空格
    cleaned_key = role_key.strip()
    
    # 应用映射
    return ROLE_KEY_NORMALIZATION.get(cleaned_key, cleaned_key)
    
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
        
    # 先标准化角色键名
    normalized_key = normalize_role_key(role_key)
    
    # 获取显示名称
    return ROLE_NAME_MAPPINGS.get(normalized_key, normalized_key) 