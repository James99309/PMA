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
    'contractor': {'zh': '总承包单位', 'en': 'Main Contractor'}
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

def industry_label(key, lang='zh'):
    return INDUSTRY_LABELS.get(key, {}).get(lang, key)

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

# TODO: 可扩展更多字典类型的获取方法 