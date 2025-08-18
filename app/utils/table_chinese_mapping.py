"""
全局表名中文映射配置
统一管理所有数据表的中文显示名称
"""

# 核心业务表映射
BUSINESS_TABLES = {
    'projects': '项目',
    'companies': '公司客户',
    'contacts': '联系人',
    'quotations': '报价单',
    'quotation_details': '报价明细',
    'pricing_orders': '批价单',
    'pricing_order_details': '批价明细',
    'purchase_orders': '采购单',
    'purchase_order_details': '采购明细',
    'settlement_orders': '结算单',
    'settlement_order_details': '结算明细',
    'settlements': '结算',
    'settlement_details': '结算明细',
    'expenses': '费用',
    'expense_details': '费用明细',
    'products': '产品',
    'product_categories': '产品类别',
    'product_subcategories': '产品子类别',
    'product_regions': '产品区域',
    'inventory': '库存',
    'inventory_transactions': '库存流水',
}

# 用户权限相关表映射
USER_PERMISSION_TABLES = {
    'users': '用户',
    'departments': '部门',
    'roles': '角色',
    'permissions': '权限',
    'role_permissions': '角色权限',
    'affiliations': '归属关系',
    'user_event_subscriptions': '用户事件订阅',
}

# 审批流程相关表映射
APPROVAL_TABLES = {
    'approval_process_template': '审批流程模板',
    'approval_step': '审批步骤',
    'approval_instance': '审批实例',
    'approval_record': '审批记录',
    'pricing_order_approval_records': '批价单审批记录',
    'actions': '审批动作',
    'action_reply': '动作回复',
}

# 项目管理相关表映射
PROJECT_MANAGEMENT_TABLES = {
    'project_members': '项目成员',
    'project_customer_associations': '项目客户关联',
    'project_stage_history': '项目阶段历史',
    'project_rating_records': '项目评级记录',
    'project_scoring_records': '项目评分记录',
    'project_total_scores': '项目总分',
    'project_scoring_config': '项目评分配置',
    'five_star_project_baselines': '五星项目基线',
}

# 产品开发相关表映射
PRODUCT_DEV_TABLES = {
    'dev_products': '研发产品',
    'dev_product_specs': '研发产品规格',
    'product_codes': '产品代码',
    'product_code_fields': '产品代码字段',
    'product_code_field_options': '产品代码字段选项',
    'product_code_field_values': '产品代码字段值',
    'temp_products': '临时产品',
}

# 绩效管理相关表映射
PERFORMANCE_TABLES = {
    'performance_statistics': '绩效统计',
    'performance_targets': '绩效目标',
    'performance_metrics_definition': '绩效指标定义',
    'performance_formula_templates': '绩效公式模板',
    'formula_templates_extended': '扩展公式模板',
    'role_performance_config': '角色绩效配置',
    'role_performance_access': '角色绩效访问',
    'role_performance_items': '角色绩效项目',
}

# 系统管理相关表映射
SYSTEM_TABLES = {
    'dictionaries': '字典',
    'data_table_config': '数据表配置',
    'data_field_config': '数据字段配置',
    'system_settings': '系统设置',
    'system_metrics': '系统指标',
    'change_logs': '变更日志',
    'upgrade_logs': '升级日志',
    'version_records': '版本记录',
    'feature_changes': '功能变更',
    'event_registry': '事件注册',
    'solution_manager_email_settings': '解决方案经理邮件设置',
}

# 资产管理相关表映射
ASSET_TABLES = {
    'company_assets': '公司资产',
}

# 数据库系统表（通常不需要中文映射）
SYSTEM_META_TABLES = {
    'alembic_version': '数据库版本',
}

# 合并所有映射
ALL_TABLE_MAPPINGS = {
    **BUSINESS_TABLES,
    **USER_PERMISSION_TABLES,
    **APPROVAL_TABLES,
    **PROJECT_MANAGEMENT_TABLES,
    **PRODUCT_DEV_TABLES,
    **PERFORMANCE_TABLES,
    **SYSTEM_TABLES,
    **ASSET_TABLES,
    **SYSTEM_META_TABLES,
}

def get_table_chinese_name(table_name):
    """
    获取表的中文名称
    
    Args:
        table_name (str): 英文表名
    
    Returns:
        str: 中文表名，如果未找到映射则返回原表名
    """
    return ALL_TABLE_MAPPINGS.get(table_name, table_name)

def get_all_table_mappings():
    """
    获取所有表映射
    
    Returns:
        dict: 完整的表名映射字典
    """
    return ALL_TABLE_MAPPINGS.copy()

def get_tables_by_category():
    """
    按类别获取表映射
    
    Returns:
        dict: 按类别分组的表映射
    """
    return {
        'business': BUSINESS_TABLES,
        'user_permission': USER_PERMISSION_TABLES,
        'approval': APPROVAL_TABLES,
        'project_management': PROJECT_MANAGEMENT_TABLES,
        'product_dev': PRODUCT_DEV_TABLES,
        'performance': PERFORMANCE_TABLES,
        'system': SYSTEM_TABLES,
        'asset': ASSET_TABLES,
        'system_meta': SYSTEM_META_TABLES,
    }

def is_table_mapped(table_name):
    """
    检查表是否已有中文映射
    
    Args:
        table_name (str): 表名
    
    Returns:
        bool: 是否已映射
    """
    return table_name in ALL_TABLE_MAPPINGS

def get_unmapped_tables(existing_tables):
    """
    获取未映射的表列表
    
    Args:
        existing_tables (list): 数据库中存在的表列表
    
    Returns:
        list: 未映射的表名列表
    """
    return [table for table in existing_tables if not is_table_mapped(table)]