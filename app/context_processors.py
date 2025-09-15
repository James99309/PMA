from flask import current_app
from app.utils.access_control import (
    can_view_company, can_edit_company_info, can_edit_company_sharing,
    can_delete_company, can_view_contact, can_edit_contact, can_delete_contact,
    can_view_project, can_view_in_approval_context, has_approval_view_permission
)
from app.helpers.approval_helpers import (
    check_template_in_use,
    check_template_has_instances,
    get_object_approval_instance,
    get_available_templates,
    can_user_approve,
    get_current_step_info,
    get_last_approver,
    get_object_type_display,
    get_rejected_approval_history,
    get_template_steps,
    get_workflow_steps,
    render_approval_code,
    get_approval_object_url
)
# 从ui_helpers导入函数，避免冲突
from app.helpers.ui_helpers import (
    format_datetime, 
    render_action_button, 
    render_user_badge, 
    get_user_display_name,
    render_filter_button,
    render_standard_tabs
)
from app.models.approval import ApprovalStatus
from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS

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
        'can_view_project': can_view_project,
        'can_view_in_approval_context': can_view_in_approval_context,
        'has_approval_view_permission': has_approval_view_permission
    }

def inject_approval_functions():
    """
    向模板上下文注入审批辅助函数，供模板使用
    """
    from app.helpers.approval_helpers import (
        check_template_in_use,
        check_template_has_instances,
        get_object_approval_instance,
        get_available_templates,
        can_user_approve,
        get_current_step_info,
        get_last_approver,
        get_object_type_display,
        get_rejected_approval_history,
        get_template_steps,
        get_workflow_steps,
        render_approval_code,
        get_approval_object_url,
        get_quotation_by_id,
        get_customer_by_id
    )
    from app.models.approval import ApprovalStatus
    from app.helpers.ui_helpers import (
        render_user_badge,
        get_user_display_name,
        format_datetime,
        render_filter_button,
        render_standard_tabs
    )
    from app.utils.filters import format_datetime_local
    
    def get_pricing_order_by_id(pricing_order_id):
        """从数据库获取批价单详情，供模板使用
        
        Args:
            pricing_order_id: 批价单ID
            
        Returns:
            批价单对象，如果不存在则返回None
        """
        from app.models.pricing_order import PricingOrder
        return PricingOrder.query.get(pricing_order_id)
    
    return {
        'check_template_in_use': check_template_in_use,
        'check_template_has_instances': check_template_has_instances,
        'get_object_approval_instance': get_object_approval_instance,
        'get_available_templates': get_available_templates,
        'can_user_approve': can_user_approve,
        'get_current_step_info': get_current_step_info,
        'get_last_approver': get_last_approver,
        'ApprovalStatus': ApprovalStatus,
        'get_object_type_display': get_object_type_display,
        'render_user_badge': render_user_badge,
        'get_user_display_name': get_user_display_name,
        'format_datetime': format_datetime,
        'format_datetime_local': format_datetime_local,
        'render_filter_button': render_filter_button,
        'render_standard_tabs': render_standard_tabs,
        'get_rejected_approval_history': get_rejected_approval_history,
        'get_template_steps': get_template_steps,
        'get_workflow_steps': get_workflow_steps,
        'render_approval_code': render_approval_code,
        'get_approval_object_url': get_approval_object_url,
        'get_quotation_by_id': get_quotation_by_id,
        'get_customer_by_id': get_customer_by_id,
        'get_pricing_order_by_id': get_pricing_order_by_id,
    }

# 添加项目相关的上下文处理器
def inject_project_functions():
    """
    向模板上下文注入项目相关的辅助函数，供模板使用
    """
    from app.models.project import Project
    
    def get_project_by_id(project_id):
        """从数据库获取项目详情，供模板使用
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目对象，如果不存在则返回None
        """
        return Project.query.get(project_id)
    
    return {
        'get_project_by_id': get_project_by_id,
    }

# 用户辅助函数注入
def inject_user_helpers():
    """
    向模板上下文注入用户相关辅助函数
    """
    from app.models.user import User
    
    def get_user_by_id(user_id):
        """获取用户对象，根据用户ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        if not user_id:
            return None
        return User.query.get(int(user_id))
    
    return {
        'get_user_by_id': get_user_by_id,
    }

# 添加语言相关上下文处理器
def inject_language_functions():
    """
    向模板上下文注入语言相关函数，供模板使用
    """
    from app.utils.i18n import get_current_language
    from flask_babel import gettext, ngettext
    
    return {
        'get_current_language': get_current_language,
        '_': gettext,
        'gettext': gettext,
        'ngettext': ngettext
    }

# 添加项目阶段配置上下文处理器
# 添加通用阶段配置上下文处理器
def inject_stage_configs():
    """
    向模板上下文注入通用阶段配置信息，供前端使用
    """
    from app.config.stage_configs import get_stage_config, get_i18n_texts
    
    def get_stage_config_for_template(object_type='project'):
        """
        生成指定对象类型的阶段配置，包括主线阶段和分支阶段
        支持国际化，根据当前语言返回相应的阶段名称
        
        Args:
            object_type: 对象类型，如 'project', 'rd_product' 等
        
        Returns:
            dict: 包含主线阶段和分支阶段的配置信息
        """
        # 获取当前语言
        try:
            from app.utils.i18n import get_current_language
            lang = get_current_language()
        except:
            lang = 'zh'  # 默认中文
        
        # 从配置文件获取阶段配置
        config = get_stage_config(object_type)
        
        # 处理主线阶段
        mainStages = []
        for stage in config.get('mainStages', []):
            stage_info = {
                'id': stage['id'],
                'key': stage['key'],
                'name': stage.get(f'{lang}_name', stage['name']),
                'zh_name': stage.get('zh_name', stage['name']),
                'en_name': stage.get('en_name', stage['name']),
                'description': stage.get('description', ''),
                'order': stage.get('order', 0),
                'colors': stage.get('colors')  # 透传颜色配置（可选）
            }
            mainStages.append(stage_info)
        
        # 处理分支阶段
        branchStages = []
        for stage in config.get('branchStages', []):
            stage_info = {
                'id': stage['id'],
                'key': stage['key'],
                'name': stage.get(f'{lang}_name', stage['name']),
                'zh_name': stage.get('zh_name', stage['name']),
                'en_name': stage.get('en_name', stage['name']),
                'description': stage.get('description', ''),
                'order': stage.get('order', 0),
                'type': stage.get('type', 'branch')
            }
            branchStages.append(stage_info)
        
        return {
            'mainStages': mainStages,
            'branchStages': branchStages
        }
    
    def project_stages_config():
        """保持向后兼容的项目阶段配置函数"""
        return get_stage_config_for_template('project')
    
    def get_stage_i18n_texts():
        """获取阶段相关的国际化文本"""
        try:
            from app.utils.i18n import get_current_language
            lang = get_current_language()
        except:
            lang = 'zh'  # 默认中文
        
        return get_i18n_texts(lang)
    
    return {
        'get_stage_config_for_template': get_stage_config_for_template,
        'project_stages_config': project_stages_config,  # 保持向后兼容
        'get_stage_i18n_texts': get_stage_i18n_texts
    }
