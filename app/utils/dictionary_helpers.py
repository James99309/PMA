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
    'business_opportunity': {'zh': '业务机会', 'en': 'Business Opportunity'}
}

PROJECT_STAGE_LABELS = {
    'discover': {'zh': '发现', 'en': 'Discover'},
    'embed': {'zh': '植入', 'en': 'Embed'},
    'pre_tender': {'zh': '招标前', 'en': 'Pre-tender'},
    'tendering': {'zh': '招标中', 'en': 'Tendering'},
    'quoted': {'zh': '批价', 'en': 'Quoted'},
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
    'contractor': {'zh': '总承包单位', 'en': 'General Contractor'}
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

def report_source_label(key, lang='zh'):
    return REPORT_SOURCE_LABELS.get(key, {}).get(lang, key)

def authorization_status_label(key, lang='zh'):
    return AUTHORIZATION_STATUS_LABELS.get(key, {}).get(lang, key)

def company_type_label(key, lang='zh'):
    return COMPANY_TYPE_LABELS.get(key, {}).get(lang, key)

def product_situation_label(key, lang='zh'):
    return PRODUCT_SITUATION_LABELS.get(key, {}).get(lang, key)

# 下拉选项生成
PROJECT_TYPE_OPTIONS = [(k, v['zh']) for k, v in PROJECT_TYPE_LABELS.items()]
REPORT_SOURCE_OPTIONS = [(k, v['zh']) for k, v in REPORT_SOURCE_LABELS.items()]
AUTHORIZATION_STATUS_OPTIONS = [(k, v['zh']) for k, v in AUTHORIZATION_STATUS_LABELS.items()]
COMPANY_TYPE_OPTIONS = [(k, v['zh']) for k, v in COMPANY_TYPE_LABELS.items()]
PRODUCT_SITUATION_OPTIONS = [(k, v['zh']) for k, v in PRODUCT_SITUATION_LABELS.items()]

# 行业分类映射
INDUSTRY_LABELS = {
    'manufacturing': {'zh': '制造业', 'en': 'Manufacturing'},
    'real_estate': {'zh': '商业地产', 'en': 'Real Estate'},
    'energy': {'zh': '石油能源', 'en': 'Energy'},
    'chemical': {'zh': '化工医药', 'en': 'Chemicals & Pharma'},
    'health': {'zh': '医疗卫生', 'en': 'Healthcare'},
    'transport': {'zh': '交通运输', 'en': 'Transportation'},
    'government': {'zh': '政府机构', 'en': 'Government'},
    'education': {'zh': '教育', 'en': 'Education'},
    'other': {'zh': '其他选择', 'en': 'Other'}
}

def industry_label(key, lang='zh'):
    return INDUSTRY_LABELS.get(key, {}).get(lang, key)

INDUSTRY_OPTIONS = [(k, v['zh']) for k, v in INDUSTRY_LABELS.items()]

# 客户状态映射
STATUS_LABELS = {
    'active': {'zh': '活跃', 'en': 'Active'},
    'inactive': {'zh': '非活跃', 'en': 'Inactive'}
}

def status_label(key, lang='zh'):
    return STATUS_LABELS.get(key, {}).get(lang, key)

STATUS_OPTIONS = [(k, v['zh']) for k, v in STATUS_LABELS.items()]

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




# TODO: 可扩展更多字典类型的获取方法 