"""
模块元数据配置

这个文件定义了系统中所有权限模块的元数据信息，包括：
- 模块ID和显示名称
- 模块图标
- 特殊权限能力（折扣权限、拥有人修改权限等）

数据来源：role_permissions 表中实际存储的模块
最后更新：2025-10-15
"""

# 模块元数据配置 - 与数据库实际模块对应（16个有效模块）
MODULE_METADATA = {
    'customer': {
        'name': '客户管理',
        'icon': 'fas fa-building',
        'supports_discount': False,
        'supports_owner_change': True,
        'supports_affiliation': True,  # 业务数据，支持数据归属
        'description': '管理客户信息和联系人'
    },
    'dictionary_management': {
        'name': '字典管理',
        'icon': 'fas fa-book',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理系统字典数据'
    },
    'expense': {
        'name': '报销管理',
        'icon': 'fas fa-receipt',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理员工报销申请'
    },
    'inventory': {
        'name': '库存管理',
        'icon': 'fas fa-warehouse',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理产品库存'
    },
    'order': {
        'name': '订单管理',
        'icon': 'fas fa-shopping-cart',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理销售订单'
    },
    'performance_management': {
        'name': '绩效管理',
        'icon': 'fas fa-chart-bar',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理员工绩效考核'
    },
    'permission_management': {
        'name': '权限管理',
        'icon': 'fas fa-user-lock',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理用户权限'
    },
    'pricing_order': {
        'name': '批价单管理',
        'icon': 'fas fa-tags',
        'supports_discount': True,  # 支持折扣下限权限
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理批价单'
    },
    'product': {
        'name': '产品管理',
        'icon': 'fas fa-box',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理产品信息和价格'
    },
    'product_code': {
        'name': '产品编码',
        'icon': 'fas fa-barcode',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理产品编码系统'
    },
    'project': {
        'name': '项目管理',
        'icon': 'fas fa-project-diagram',
        'supports_discount': False,
        'supports_owner_change': True,
        'supports_affiliation': True,  # 业务数据，支持数据归属
        'description': '管理销售项目和跟进'
    },
    'project_rating': {
        'name': '项目评分',
        'icon': 'fas fa-star',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理项目评分'
    },
    'quotation': {
        'name': '报价管理',
        'icon': 'fas fa-file-invoice-dollar',
        'supports_discount': False,
        'supports_owner_change': True,
        'supports_affiliation': True,  # 业务数据，支持数据归属
        'description': '管理产品报价'
    },
    'settlement': {
        'name': '结算管理',
        'icon': 'fas fa-calculator',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理财务结算'
    },
    'settlement_order': {
        'name': '结算单管理',
        'icon': 'fas fa-credit-card',
        'supports_discount': True,  # 支持折扣下限权限
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理结算单'
    },
    'user_management': {
        'name': '用户管理',
        'icon': 'fas fa-users-cog',
        'supports_discount': False,
        'supports_owner_change': False,
        'supports_affiliation': False,  # 非业务数据，不支持数据归属
        'description': '管理系统用户'
    }
}

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


# 辅助函数
def get_module_metadata(module_id):
    """
    获取指定模块的元数据

    Args:
        module_id: 模块ID

    Returns:
        dict: 模块元数据，如果模块不存在返回默认值
    """
    return MODULE_METADATA.get(module_id, {
        'name': module_id,
        'icon': 'fas fa-cube',
        'supports_discount': False,
        'supports_owner_change': False,
        'description': ''
    })


def get_all_module_ids():
    """
    获取所有有效模块的ID列表

    Returns:
        list: 模块ID列表
    """
    return list(MODULE_METADATA.keys())


def module_supports_discount(module_id):
    """
    检查模块是否支持折扣权限

    Args:
        module_id: 模块ID

    Returns:
        bool: 是否支持折扣权限
    """
    return MODULE_METADATA.get(module_id, {}).get('supports_discount', False)


def module_supports_owner_change(module_id):
    """
    检查模块是否支持拥有人修改权限

    Args:
        module_id: 模块ID

    Returns:
        bool: 是否支持拥有人修改权限
    """
    return MODULE_METADATA.get(module_id, {}).get('supports_owner_change', False)


def get_permission_levels():
    """
    获取权限级别定义

    Returns:
        list: 权限级别列表
    """
    return PERMISSION_LEVELS


def module_supports_affiliation(module_id):
    """
    检查模块是否支持数据归属（Affiliation）

    数据归属仅用于业务数据模块（客户、项目、报价单等），
    不应用于非业务数据模块（用户管理、权限管理等）。

    Args:
        module_id: 模块ID

    Returns:
        bool: 是否支持数据归属

    示例:
        >>> module_supports_affiliation('customer')
        True
        >>> module_supports_affiliation('user_management')
        False
    """
    return MODULE_METADATA.get(module_id, {}).get('supports_affiliation', False)
