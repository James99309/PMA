"""
全局模板上下文处理器
注册各种权限判断函数到模板环境中，集中管理所有模板可用的权限函数
"""
from flask import current_app
from app.utils.access_control import (
    can_edit_data,
    can_view_project,
    can_view_company,
    can_edit_company_info,
    can_edit_company_sharing,
    can_delete_company,
    can_view_contact,
    can_edit_contact, 
    can_delete_contact
)
from app.views.quotation import can_view_quotation

def inject_permission_functions():
    """
    注册所有权限判断函数到Jinja2模板环境
    所有模板可以直接调用这些函数进行权限控制
    """
    return {
        # 通用数据访问权限
        'can_edit_data': can_edit_data,
        
        # 项目相关权限
        'can_view_project': can_view_project,
        
        # 客户相关权限
        'can_view_company': can_view_company,
        'can_edit_company_info': can_edit_company_info,
        'can_edit_company_sharing': can_edit_company_sharing,
        'can_delete_company': can_delete_company,
        
        # 联系人相关权限
        'can_view_contact': can_view_contact,
        'can_edit_contact': can_edit_contact,
        'can_delete_contact': can_delete_contact,
        
        # 报价单相关权限
        'can_view_quotation': can_view_quotation
    } 