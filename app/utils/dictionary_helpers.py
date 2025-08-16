# app/utils/dictionary_helpers.py
# 用于从数据库dictionaries表获取字典项（如角色显示名），支持Flask g对象缓存

from flask import g
from app.models.dictionary import Dictionary
from app import db

ROLE_TYPE = 'role'

# 统一标签字典
PROJECT_TYPE_LABELS = {
    'channel_follow': {'zh': '渠道跟进', 'en': 'Channel Follow'},
    'sales_focus': {'zh': '销售重点', 'en': 'Sales Focus'},
    'business_opportunity': {'zh': '客户服务', 'en': 'Service Opportunity'}
}

PROJECT_STAGE_LABELS = {
    'discover': {'zh': '发现', 'en': 'Discover'},
    'embed': {'zh': '植入', 'en': 'Embed'},
    'pre_tender': {'zh': '招标前', 'en': 'Pre-tender'},
    'tendering': {'zh': '招标中', 'en': 'Tendering'},
    'awarded': {'zh': '中标', 'en': 'Awarded'},
    'quoted': {'zh': '批价', 'en': 'Price approval'},
    'signed': {'zh': '签约', 'en': 'Signed'},
    'lost': {'zh': '失败', 'en': 'Lost'},
    'paused': {'zh': '搁置', 'en': 'Paused'}
}

REPORT_SOURCE_LABELS = {
    'channel': {'zh': '渠道报备', 'en': 'Channel'},
    'sales': {'zh': '销售线索', 'en': 'Sales'},
    'marketing': {'zh': '市场拓展', 'en': 'Marketing'}
}

AUTHORIZATION_STATUS_LABELS = {
    'pending': {'zh': '待审批', 'en': 'Pending'},
    'approved': {'zh': '已授权', 'en': 'Approved'},
    'rejected': {'zh': '已驳回', 'en': 'Rejected'}
}

# 企业类型映射
COMPANY_TYPE_LABELS = {
    'user': {'zh': '用户', 'en': 'User'},
    'dealer': {'zh': '经销商', 'en': 'Dealer'},
    'integrator': {'zh': '系统集成商', 'en': 'System Integrator'},
    'designer': {'zh': '设计院及顾问', 'en': 'Designer'},
    'contractor': {'zh': '总承包单位', 'en': 'Main Contractor'},
    'direct_customer': {'zh': '直接客户', 'en': 'Direct Customer'},
    'partner': {'zh': '合作伙伴', 'en': 'Partner'},
    'system_integrator': {'zh': '系统集成商', 'en': 'System Integrator'},
    'design_institute': {'zh': '设计院', 'en': 'Design Institute'},
    'consultant': {'zh': '顾问', 'en': 'Consultant'},
    'general_contractor': {'zh': '总承包商', 'en': 'General Contractor'},
    'distributor': {'zh': '分销商', 'en': 'Distributor'},
    'other': {'zh': '其他', 'en': 'Other'}
}

# 企业类型颜色映射
COMPANY_TYPE_COLORS = {
    'user': '#0B6EFD',
    'dealer': '#28a745',
    'integrator': '#fd7e14',
    'designer': '#6f42c1',
    'contractor': '#dc3545',
    'direct_customer': '#17a2b8',
    'partner': '#20c997',
    'system_integrator': '#fd7e14',
    'design_institute': '#6f42c1',
    'consultant': '#6f42c1',
    'general_contractor': '#dc3545',
    'distributor': '#28a745',
    'other': '#6c757d'
}

# 货币类型映射
CURRENCY_TYPE_LABELS = {
    'CNY': {'zh': '人民币', 'en': 'Chinese Yuan'},
    'USD': {'zh': '美元', 'en': 'US Dollar'},
    'SGD': {'zh': '新加坡元', 'en': 'Singapore Dollar'},
    'MYR': {'zh': '马来西亚林吉特', 'en': 'Malaysian Ringgit'},
    'IDR': {'zh': '印尼盾', 'en': 'Indonesian Rupiah'},
    'THB': {'zh': '泰铢', 'en': 'Thai Baht'}
}

PRODUCT_SITUATION_LABELS = {
    'qualified': {'zh': '品牌入围', 'en': 'Qualified'},
    'controlled': {'zh': '品牌受控', 'en': 'Controlled'},
    'not_required': {'zh': '无品牌要求', 'en': 'Not Required'},
    'unqualified': {'zh': '品牌未入围', 'en': 'Unqualified'}
}

def project_type_label(key, lang='zh'):
    return PROJECT_TYPE_LABELS.get(key, {}).get(lang, key)

def project_stage_label(key, lang='zh'):
    return PROJECT_STAGE_LABELS.get(key, {}).get(lang, key)

# 语言感知的包装器函数，用于模板过滤器
def project_type_label_i18n(key, lang=None):
    """语言感知的项目类型标签，如果不提供语言参数则自动检测当前语言"""
    if lang is None:
        try:
            from app.utils.i18n import get_current_language
            lang = get_current_language()
        except:
            lang = 'zh'  # 默认中文
    return project_type_label(key, lang)

def project_stage_label_i18n(key, lang=None):
    """语言感知的项目阶段标签，如果不提供语言参数则自动检测当前语言"""
    if lang is None:
        try:
            from app.utils.i18n import get_current_language
            lang = get_current_language()
        except:
            lang = 'zh'  # 默认中文
    return project_stage_label(key, lang)

def report_source_label(key, lang='zh'):
    return REPORT_SOURCE_LABELS.get(key, {}).get(lang, key)

def authorization_status_label(key, lang='zh'):
    return AUTHORIZATION_STATUS_LABELS.get(key, {}).get(lang, key)

def company_type_label(key, lang='zh'):
    return COMPANY_TYPE_LABELS.get(key, {}).get(lang, key)

def company_type_color(key):
    """获取企业类型对应的颜色"""
    return COMPANY_TYPE_COLORS.get(key, '#6c757d')

def product_situation_label(key, lang='zh'):
    return PRODUCT_SITUATION_LABELS.get(key, {}).get(lang, key)

# 语言感知选项生成函数
def get_project_type_options():
    """获取语言感知的项目类型选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in PROJECT_TYPE_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_project_type_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in PROJECT_TYPE_LABELS.items()]

def get_report_source_options():
    """获取语言感知的报备来源选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in REPORT_SOURCE_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_report_source_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in REPORT_SOURCE_LABELS.items()]

def get_product_situation_options():
    """获取语言感知的品牌状况选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in PRODUCT_SITUATION_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_product_situation_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in PRODUCT_SITUATION_LABELS.items()]

def get_project_stage_options():
    """获取语言感知的项目阶段选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in PROJECT_STAGE_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_project_stage_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in PROJECT_STAGE_LABELS.items()]

def currency_type_label(key, lang='zh'):
    """获取货币类型标签"""
    return CURRENCY_TYPE_LABELS.get(key, {}).get(lang, key)

def get_currency_symbol(currency_code='CNY'):
    """获取货币符号"""
    currency_symbols = {
        'CNY': '¥',
        'USD': '$',
        'SGD': 'S$',
        'MYR': 'RM',
        'IDR': 'Rp',
        'THB': '฿'
    }
    return currency_symbols.get(currency_code, '¥')  # 默认返回人民币符号

def get_default_currency():
    """获取系统默认货币"""
    try:
        # 尝试从Product表获取默认货币（如报价单模块的逻辑）
        from app.models.product import Product
        reference_product = Product.query.filter_by(id=1).first()
        if reference_product and hasattr(reference_product, 'currency') and reference_product.currency:
            return reference_product.currency
    except Exception:
        pass
    
    # 如果没有找到，返回默认的人民币
    return 'CNY'

def get_amount_unit_config(language=None):
    """获取基于语言环境的金额单位配置（用于统计卡片language_aware模式）"""
    if language is None:
        try:
            from app.utils.i18n import get_current_language
            language = get_current_language()
        except:
            language = 'zh'  # 默认中文
    
    if language == 'zh' or language.startswith('zh'):
        return {
            'divisor': 1,           # 大部分模块数据已经是万元，不需要转换
            'unit': '万元',
            'decimal_places': 2,
            'format_type': 'wan',
            'currency_symbol': '¥'
        }
    else:
        return {
            'divisor': 100,         # 万元转百万：万元/100 = M
            'unit': 'M',
            'decimal_places': 2,
            'format_type': 'million',
            'currency_symbol': '¥'
        }

def format_amount_with_unit(amount, currency_symbol, language=None):
    """基于语言环境格式化金额显示"""
    try:
        unit_config = get_amount_unit_config(language)
        
        # 计算显示金额
        display_amount = amount / unit_config['divisor']
        
        # 格式化数字（添加千位分隔符）
        formatted_number = f"{display_amount:,.{unit_config['decimal_places']}f}"
        
        return {
            'formatted': f"{currency_symbol}{formatted_number}",
            'unit': unit_config['unit'],
            'full_display': f"{currency_symbol}{formatted_number}{unit_config['unit']}",
            'format_type': unit_config['format_type']
        }
    except Exception as e:
        # 错误情况下返回默认格式
        return {
            'formatted': f"{currency_symbol}{amount:.2f}",
            'unit': '万元',
            'full_display': f"{currency_symbol}{amount:.2f}万元",
            'format_type': 'wan'
        }

def prepare_stats_card_amount(amount_yuan, language=None):
    """
    为统计卡片准备金额数据（从人民币元转换）
    
    参数：
    - amount_yuan: 人民币金额（元）
    - language: 语言代码，默认自动检测
    
    返回：
    - 包含value、unit等字段的字典，可直接用于stats_card配置
    """
    try:
        # 确保输入值是数值类型
        if amount_yuan is None:
            amount_yuan = 0
        amount_yuan = float(amount_yuan)
        
        if language is None:
            try:
                from app.utils.i18n import get_current_language
                language = get_current_language()
            except:
                language = 'zh'
        
        # 调试信息
        print(f"💰 prepare_stats_card_amount 调用: amount_yuan={amount_yuan}, language={language}")
        
        if language == 'zh' or language.startswith('zh'):
            # 中文：元 -> 万元
            display_value = amount_yuan / 10000
            unit = '万元'
            print(f"💰 中文转换: {amount_yuan}元 ÷ 10000 = {display_value}万元")
        else:
            # 英文：元 -> M（百万）
            display_value = amount_yuan / 1000000
            unit = 'M'
            print(f"💰 英文转换: {amount_yuan}元 ÷ 1000000 = {display_value}M")
        
        result = {
            'value': round(display_value, 2),
            'unit': unit,
            'currency_symbol': '¥',
            'format_type': 'wan' if language == 'zh' else 'million'
        }
        
        print(f"💰 转换结果: {result}")
        return result
        
    except Exception as e:
        print(f"❌ prepare_stats_card_amount 异常: {e}")
        # 返回默认值，确保不会返回 None
        return {
            'value': 0.0,
            'unit': '万元',
            'currency_symbol': '¥',
            'format_type': 'wan'
        }

def prepare_stats_card_amount_from_wan(amount_wan, language=None):
    """
    为统计卡片准备金额数据（从万元转换）
    
    参数：
    - amount_wan: 金额（万元）
    - language: 语言代码，默认自动检测
    
    返回：
    - 包含value、unit等字段的字典，可直接用于stats_card配置
    """
    if language is None:
        try:
            from app.utils.i18n import get_current_language
            language = get_current_language()
        except:
            language = 'zh'
    
    if language == 'zh' or language.startswith('zh'):
        # 中文：万元 -> 万元（保持不变）
        display_value = amount_wan
        unit = '万元'
    else:
        # 英文：万元 -> M（万元 ÷ 100 = 百万）
        display_value = amount_wan / 100
        unit = 'M'
    
    return {
        'value': round(display_value, 2),
        'unit': unit,
        'currency_symbol': '¥',
        'format_type': 'wan' if language == 'zh' else 'million'
    }

def get_currency_type_options():
    """获取语言感知的货币类型选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in CURRENCY_TYPE_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_currency_type_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in CURRENCY_TYPE_LABELS.items()]

# 向后兼容性选项
PROJECT_TYPE_OPTIONS = [(k, v['zh']) for k, v in PROJECT_TYPE_LABELS.items()]
REPORT_SOURCE_OPTIONS = [(k, v['zh']) for k, v in REPORT_SOURCE_LABELS.items()]
AUTHORIZATION_STATUS_OPTIONS = [(k, v['zh']) for k, v in AUTHORIZATION_STATUS_LABELS.items()]
COMPANY_TYPE_OPTIONS = [(k, v['zh']) for k, v in COMPANY_TYPE_LABELS.items()]
PRODUCT_SITUATION_OPTIONS = [(k, v['zh']) for k, v in PRODUCT_SITUATION_LABELS.items()]
CURRENCY_TYPE_OPTIONS = [(k, v['zh']) for k, v in CURRENCY_TYPE_LABELS.items()]

# 行业分类映射
INDUSTRY_LABELS = {
    # 制造业相关
    'manufacturing': {'zh': '制造业', 'en': 'Manufacturing'},
    'datacenter': {'zh': '数据中心', 'en': 'Data Center'},
    'shipbuilding': {'zh': '造船业', 'en': 'Shipbuilding'},
    'semiconductor': {'zh': '半导体', 'en': 'Semiconductor'},
    'chemical': {'zh': '化工医药', 'en': 'Chemicals & Pharma'},
    # 能源交通相关
    'energy': {'zh': '石油能源', 'en': 'Energy'},
    'transportation': {'zh': '交通枢纽', 'en': 'Transportation'},
    'tunnel_underground': {'zh': '隧道及地下道路', 'en': 'Tunnel & Underground Roads'},
    # 商业服务相关
    'real_estate': {'zh': '商业地产', 'en': 'Real Estate'},
    'hospitality': {'zh': '酒店餐饮', 'en': 'Hospitality'},
    # 公共服务相关
    'government': {'zh': '政府机构', 'en': 'Government'},
    'education': {'zh': '教育', 'en': 'Education'},
    # 其他
    'other': {'zh': '其他选择', 'en': 'Other'},
}

# 行业颜色映射
INDUSTRY_COLORS = {
    'manufacturing': '#0B6EFD',
    'datacenter': '#5BC0DE', 
    'shipbuilding': '#198754',
    'semiconductor': '#fd7e14',
    'chemical': '#dc3545',
    'energy': '#ffc107',
    'transportation': '#6f42c1',
    'tunnel_underground': '#6c757d',
    'real_estate': '#20c997',
    'hospitality': '#e83e8c',
    'government': '#007bff',
    'education': '#28a745',
    'other': '#6c757d'
}

def industry_label(key, lang='zh'):
    return INDUSTRY_LABELS.get(key, {}).get(lang, key)

def industry_color(key):
    """获取行业对应的颜色"""
    return INDUSTRY_COLORS.get(key, '#6c757d')

def get_industry_options():
    """获取语言感知的行业选项"""
    try:
        from app.utils.i18n import get_current_language
        # 根据当前语言选择合适的语言代码
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in INDUSTRY_LABELS.items()]
    except Exception as e:
        # 记录错误日志以便调试
        import logging
        logging.warning(f"get_industry_options 获取语言失败: {e}")
        # 如果获取语言失败，默认使用中文
        return [(k, v['zh']) for k, v in INDUSTRY_LABELS.items()]

# 保持向后兼容性
INDUSTRY_OPTIONS = [(k, v['zh']) for k, v in INDUSTRY_LABELS.items()]

# 客户状态映射
STATUS_LABELS = {
    'active': {'zh': '活跃', 'en': 'Active'},
    'inactive': {'zh': '非活跃', 'en': 'Inactive'}
}

def status_label(key, lang='zh'):
    return STATUS_LABELS.get(key, {}).get(lang, key)

STATUS_OPTIONS = [(k, v['zh']) for k, v in STATUS_LABELS.items()]

def get_company_type_options():
    """获取语言感知的企业类型选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in COMPANY_TYPE_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_company_type_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in COMPANY_TYPE_LABELS.items()]

def get_status_options():
    """获取语言感知的状态选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in STATUS_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_status_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in STATUS_LABELS.items()]

# 国家映射
COUNTRY_LABELS = {
    'CN': {'zh': '中国', 'en': 'China'},
    'US': {'zh': '美国', 'en': 'United States'}, 
    'DE': {'zh': '德国', 'en': 'Germany'},
    'JP': {'zh': '日本', 'en': 'Japan'},
    'KR': {'zh': '韩国', 'en': 'South Korea'},
    'SG': {'zh': '新加坡', 'en': 'Singapore'},
    'MY': {'zh': '马来西亚', 'en': 'Malaysia'},
    'TH': {'zh': '泰国', 'en': 'Thailand'},
    'OTHER': {'zh': '其他', 'en': 'Other'}
}

def get_country_options():
    """获取语言感知的国家选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in COUNTRY_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_country_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in COUNTRY_LABELS.items()]

def get_role_display_name(role_key):
    """
    根据角色key从数据库字典表获取角色显示名称。
    优先从Flask g对象缓存获取，避免重复查询。
    """
    if not role_key:
        return '未知角色'
    
    # 统一小写处理
    role_key = role_key.lower()
    
    # 缓存机制
    if not hasattr(g, '_role_display_cache'):
        # 查询所有角色字典项
        role_dicts = db.session.query(Dictionary).filter_by(type=ROLE_TYPE, is_active=True).all()
        g._role_display_cache = {item.key.lower(): item.value for item in role_dicts}
    
    return g._role_display_cache.get(role_key, role_key)


def get_dictionary_value(dict_type, key):
    """
    通用方法：根据type和key获取字典项value
    """
    if not key:
        return ''
    key = key.lower()
    cache_name = f'_dict_{dict_type}_cache'
    if not hasattr(g, cache_name):
        dicts = db.session.query(Dictionary).filter_by(type=dict_type, is_active=True).all()
        setattr(g, cache_name, {item.key.lower(): item.value for item in dicts})
    cache = getattr(g, cache_name)
    return cache.get(key, key)

# 品牌状态映射
BRAND_STATUS_LABELS = {
    'qualified': {'zh': '品牌入围', 'en': 'Qualified'},
    'controlled': {'zh': '品牌受控', 'en': 'Controlled'},
    'not_required': {'zh': '无品牌要求', 'en': 'Not Required'},
    'unqualified': {'zh': '品牌未入围', 'en': 'Unqualified'}
}

def brand_status_label(key, lang='zh'):
    return BRAND_STATUS_LABELS.get(key, {}).get(lang, key)

# 产品类型映射
PRODUCT_TYPE_LABELS = {
    'third_party': {'zh': '第三方产品', 'en': 'Third Party'},
    'channel': {'zh': '渠道产品', 'en': 'Channel'},
    'project': {'zh': '项目产品', 'en': 'Project'}
}

def product_type_label(key, lang='zh'):
    return PRODUCT_TYPE_LABELS.get(key, {}).get(lang, key)

PRODUCT_TYPE_OPTIONS = [(k, v['zh']) for k, v in PRODUCT_TYPE_LABELS.items()]

# 产品状态映射
PRODUCT_STATUS_LABELS = {
    'active': {'zh': '生产中', 'en': 'Active'},
    'discontinued': {'zh': '已停产', 'en': 'Discontinued'},
    'upcoming': {'zh': '待上市', 'en': 'Upcoming'}
}

def product_status_label(key, lang='zh'):
    return PRODUCT_STATUS_LABELS.get(key, {}).get(lang, key)

PRODUCT_STATUS_OPTIONS = [(k, v['zh']) for k, v in PRODUCT_STATUS_LABELS.items()]

# 报备来源映射
REPORTING_SOURCE_LABELS = {
    'channel': {'zh': '渠道报备', 'en': 'Channel'},
    'sales': {'zh': '销售线索', 'en': 'Sales Lead'},
    'marketing': {'zh': '市场拓展', 'en': 'Marketing'}
}

def reporting_source_label(key, lang='zh'):
    return REPORTING_SOURCE_LABELS.get(key, {}).get(lang, key)

# 审批状态映射
APPROVAL_STATUS_LABELS = {
    'pending': {'zh': '审批中', 'en': 'Pending'},
    'approved': {'zh': '已通过', 'en': 'Approved'},
    'rejected': {'zh': '已拒绝', 'en': 'Rejected'},
    'recalled': {'zh': '已召回', 'en': 'Recalled'},
    'draft': {'zh': '草稿', 'en': 'Draft'}
}

def approval_status_label(key, lang='zh'):
    """获取审批状态标签"""
    return APPROVAL_STATUS_LABELS.get(key, {}).get(lang, key)

def get_approval_status_options():
    """获取语言感知的审批状态选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in APPROVAL_STATUS_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_approval_status_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in APPROVAL_STATUS_LABELS.items()]

# 分享权限标签映射
SHARE_PERMISSION_LABELS = {
    "read": {"zh": "只读", "en": "Read"},
    "edit": {"zh": "可编辑", "en": "Edit"}
}

def share_permission_label(permission_key, lang='zh'):
    """
    获取分享权限标签
    
    参数:
        permission_key: 权限键名
        lang: 语言，默认中文
        
    返回:
        权限标签
    """
    if permission_key in SHARE_PERMISSION_LABELS:
        return SHARE_PERMISSION_LABELS[permission_key][lang]
    return permission_key

def user_label(user_id, users_dict=None):
    """
    获取用户标签
    
    参数:
        user_id: 用户ID
        users_dict: 用户字典，可选，格式为 {user_id: user_object}
        
    返回:
        用户名或ID
    """
    if users_dict and user_id in users_dict:
        return users_dict[user_id].username
    # 如果没有传入用户字典，则返回用户ID
    return str(user_id)

def get_role_display_name_from_dict(role_key, roles_dict=None):
    """
    从提供的角色字典获取角色显示名称，如果没有提供字典则从数据库查询
    
    参数:
        role_key: 角色键名
        roles_dict: 角色字典，可选，格式为 {role_key: display_name}
        
    返回:
        角色显示名称
    """
    if not role_key:
        return '未知角色'
    
    # 如果提供了字典，优先使用
    if roles_dict and role_key in roles_dict:
        return roles_dict[role_key]
    
    # 否则使用原有的数据库查询方法
    return get_role_display_name(role_key)

# TODO: 可扩展更多字典类型的获取方法 