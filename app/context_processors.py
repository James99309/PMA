from flask import current_app
from app.utils.access_control import (
    can_view_company, can_edit_company_info, can_edit_company_sharing,
    can_delete_company, can_view_contact, can_edit_contact, can_delete_contact,
    can_view_project
)

def inject_permission_functions():
    """
    向模板上下文注入权限辅助函数，供模板使用
    """
    return {
        'can_view_company': can_view_company,
        'can_edit_company_info': can_edit_company_info,
        'can_edit_company_sharing': can_edit_company_sharing,
        'can_delete_company': can_delete_company,
        'can_view_contact': can_view_contact,
        'can_edit_contact': can_edit_contact, 
        'can_delete_contact': can_delete_contact,
        'can_view_project': can_view_project
    }