"""
模块元数据配置

这个文件定义了系统中所有权限模块的元数据信息，包括：
- 模块ID和显示名称
- 模块图标
- 特殊权限能力（折扣权限、拥有人修改权限等）

数据来源：permission_modules 表（数据库驱动），硬编码作为回退
最后更新：2025-12-28
"""

from flask import g, has_request_context


# =============================================================================
# 硬编码模块元数据（回退用，数据库为空时使用）
# =============================================================================
MODULE_METADATA_FALLBACK = {
    'customer': {
        'name': '客户管理',
        'icon': 'contacts',
        'supports_discount': False,
        'supports_owner_change': True,
        'supports_affiliation': True,
        'supports_content_filter': True,
        'description': '管理客户信息和联系人'
    },
    'dictionary_management': {
        'name': '字典管理',
        'icon': 'menu_book',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理系统字典数据'
    },
    'expense': {
        'name': '报销管理',
        'icon': 'receipt_long',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理员工报销申请'
    },
    'inventory': {
        'name': '库存管理',
        'icon': 'warehouse',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理产品库存'
    },
    'order': {
        'name': '订单管理',
        'icon': 'list_alt',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理销售订单'
    },
    'pricing_order': {
        'name': '批价单管理',
        'icon': 'sell',
        'supports_discount': True,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理批价单'
    },
    'product': {
        'name': '产品管理',
        'icon': 'inventory_2',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理产品信息和价格'
    },
    'product_code': {
        'name': '产品编码',
        'icon': 'category',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理产品编码系统'
    },
    'project': {
        'name': '项目管理',
        'icon': 'cases',
        'supports_discount': False,
        'supports_owner_change': True,
        'supports_affiliation': True,
        'supports_content_filter': True,
        'description': '管理销售项目和跟进'
    },
    'quotation': {
        'name': '报价管理',
        'icon': 'request_quote',
        'supports_discount': False,
        'supports_owner_change': True,
        'supports_affiliation': True,
        'supports_content_filter': False,
        'description': '管理产品报价'
    },
    'settlement': {
        'name': '结算管理',
        'icon': 'payments',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理财务结算'
    },
    'settlement_order': {
        'name': '结算单管理',
        'icon': 'credit_card',
        'supports_discount': True,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理结算单'
    },
    'user_management': {
        'name': '用户管理',
        'icon': 'group',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理系统用户'
    },
    'config_management': {
        'name': '配置管理',
        'icon': 'settings',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理系统权限和配置'
    },
    'approval': {
        'name': '审批中心',
        'icon': 'task_alt',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理审批流程和审批记录'
    },
    'system_settings': {
        'name': '系统参数设置',
        'icon': 'settings_applications',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理系统参数配置'
    },
    'version_management': {
        'name': '版本管理',
        'icon': 'update',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理系统版本'
    },
    'approval_config': {
        'name': '审批流程配置',
        'icon': 'rule',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '配置审批流程模板'
    },
    'notification': {
        'name': '通知中心',
        'icon': 'notifications',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理系统通知'
    },
    'change_history': {
        'name': '历史记录',
        'icon': 'history',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '查看操作历史记录'
    },
    'backup': {
        'name': '数据库备份',
        'icon': 'cloud_upload',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': '管理数据库备份'
    }
}

# 向后兼容：保留 MODULE_METADATA 变量名
MODULE_METADATA = MODULE_METADATA_FALLBACK


# 权限级别定义
PERMISSION_LEVELS = [
    {
        'value': 'none',
        'label': '未启用',
        'desc': '不启用此模块'
    },
    {
        'value': 'personal',
        'label': '本人',
        'desc': '只能访问自己创建的数据'
    },
    {
        'value': 'department',
        'label': '本部门',
        'desc': '可以访问本部门所有数据'
    },
    {
        'value': 'company',
        'label': '全公司',
        'desc': '可以访问全公司所有数据'
    },
    {
        'value': 'system',
        'label': '系统级',
        'desc': '可以访问系统所有数据'
    }
]


# =============================================================================
# 数据库缓存函数
# =============================================================================

def _get_cached_modules():
    """
    获取带缓存的模块列表（从数据库）

    使用 Flask g 对象缓存，每次请求只查询一次

    Returns:
        dict: {module_id: module_dict, ...}
    """
    cache_key = '_cached_permission_modules'

    # 检查是否在请求上下文中
    if not has_request_context():
        # 不在请求上下文中，直接返回回退数据
        return MODULE_METADATA_FALLBACK

    # 检查缓存
    if hasattr(g, cache_key):
        return getattr(g, cache_key)

    try:
        from app.models.permission_module import PermissionModule
        modules = PermissionModule.query.filter_by(is_active=True)\
            .order_by(PermissionModule.sort_order).all()

        if modules:
            result = {}
            for m in modules:
                result[m.module_id] = {
                    'name': m.name,
                    'name_en': m.name_en,
                    'icon': m.icon,
                    'description': m.description,
                    'description_en': m.description_en,
                    'group_name': m.group_name,
                    'group_name_en': m.group_name_en,
                    'sort_order': m.sort_order,
                    'supports_discount': m.supports_discount,
                    'supports_owner_change': m.supports_owner_change,
                    'supports_affiliation': m.supports_affiliation,
                    'supports_content_filter': m.supports_content_filter
                }
            setattr(g, cache_key, result)
            return result
        else:
            # 数据库为空，使用回退
            setattr(g, cache_key, MODULE_METADATA_FALLBACK)
            return MODULE_METADATA_FALLBACK
    except Exception:
        # 查询失败，使用回退
        return MODULE_METADATA_FALLBACK


def _get_cached_module_features(module_id):
    """
    获取模块的子功能列表（带缓存）

    Args:
        module_id: 模块ID

    Returns:
        list: [feature_dict, ...]
    """
    cache_key = f'_cached_module_features_{module_id}'

    if not has_request_context():
        return []

    if hasattr(g, cache_key):
        return getattr(g, cache_key)

    try:
        from app.models.permission_module import PermissionModuleFeature
        features = PermissionModuleFeature.query.filter_by(
            module_id=module_id,
            is_active=True
        ).order_by(PermissionModuleFeature.sort_order).all()

        result = [f.to_dict() for f in features]
        setattr(g, cache_key, result)
        return result
    except Exception:
        return []


# =============================================================================
# 公共 API 函数
# =============================================================================

def get_module_metadata(module_id):
    """
    获取指定模块的元数据

    优先从数据库读取，失败时使用硬编码回退

    Args:
        module_id: 模块ID

    Returns:
        dict: 模块元数据，如果模块不存在返回默认值
    """
    modules = _get_cached_modules()
    return modules.get(module_id, {
        'name': module_id,
        'icon': 'help_outline',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,
        'supports_content_filter': False,
        'description': ''
    })


def get_all_module_ids():
    """
    获取所有有效模块的ID列表

    Returns:
        list: 模块ID列表
    """
    modules = _get_cached_modules()
    return list(modules.keys())


def get_all_modules():
    """
    获取所有模块的完整信息

    Returns:
        dict: {module_id: module_dict, ...}
    """
    return _get_cached_modules()


def get_module_features(module_id):
    """
    获取模块的子功能列表

    Args:
        module_id: 模块ID

    Returns:
        list: 子功能列表
    """
    return _get_cached_module_features(module_id)


def module_supports_discount(module_id):
    """
    检查模块是否支持折扣权限

    Args:
        module_id: 模块ID

    Returns:
        bool: 是否支持折扣权限
    """
    meta = get_module_metadata(module_id)
    return meta.get('supports_discount', False)


def module_supports_owner_change(module_id):
    """
    检查模块是否支持拥有人修改权限

    Args:
        module_id: 模块ID

    Returns:
        bool: 是否支持拥有人修改权限
    """
    meta = get_module_metadata(module_id)
    return meta.get('supports_owner_change', False)


def module_supports_affiliation(module_id):
    """
    检查模块是否支持数据归属（Affiliation）

    数据归属仅用于业务数据模块（客户、项目、报价单等），
    不应用于非业务数据模块（用户管理、权限管理等）。

    Args:
        module_id: 模块ID

    Returns:
        bool: 是否支持数据归属
    """
    meta = get_module_metadata(module_id)
    return meta.get('supports_affiliation', False)


def module_supports_content_filter(module_id):
    """
    检查模块是否支持内容筛选

    Args:
        module_id: 模块ID

    Returns:
        bool: 是否支持内容筛选
    """
    meta = get_module_metadata(module_id)
    return meta.get('supports_content_filter', False)


def get_permission_levels():
    """
    获取权限级别定义

    Returns:
        list: 权限级别列表
    """
    return PERMISSION_LEVELS
