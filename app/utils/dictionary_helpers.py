# app/utils/dictionary_helpers.py
# 用于从数据库dictionaries表获取字典项（如角色显示名），支持Flask g对象缓存

from flask import g
from app.models.dictionary import Dictionary
from app import db

ROLE_TYPE = 'role'


# =============================================================================
# 数据库驱动的字典缓存系统
# =============================================================================

def _get_cached_dict(dict_type):
    """
    获取带缓存的字典数据（从数据库）
    使用 Flask g 对象缓存，避免同一请求内重复查询

    Args:
        dict_type: 字典类型（如 'project_type', 'project_stage' 等）

    Returns:
        dict: {key: {'zh': value, 'en': value_en}, ...}
    """
    cache_key = f'_cached_dict_{dict_type}'
    if not hasattr(g, cache_key):
        items = Dictionary.query.filter_by(type=dict_type, is_active=True)\
            .order_by(Dictionary.sort_order).all()
        setattr(g, cache_key, {
            d.key: {'zh': d.value, 'en': d.value_en or d.value}
            for d in items
        })
    return getattr(g, cache_key)


def _get_dict_label(dict_type, key, lang='zh'):
    """
    从数据库获取字典标签

    Args:
        dict_type: 字典类型
        key: 字典键
        lang: 语言代码（'zh' 或 'en'）

    Returns:
        str: 标签值，如果找不到则返回 key 本身
    """
    if not key:
        return key
    labels = _get_cached_dict(dict_type)
    return labels.get(key, {}).get(lang, key)


def _get_dict_options(dict_type):
    """
    从数据库获取语言感知的字典选项列表

    Args:
        dict_type: 字典类型

    Returns:
        list: [(key, label), ...] 选项列表
    """
    try:
        from app.utils.i18n import get_current_language
        lang = get_current_language()
    except Exception:
        lang = 'zh'

    labels = _get_cached_dict(dict_type)
    return [(k, v.get(lang, v.get('zh', k))) for k, v in labels.items()]


# =============================================================================
# 项目类型、项目阶段、报备来源（从数据库读取）
# =============================================================================

def project_type_label(key, lang='zh'):
    """获取项目类型标签（从数据库）"""
    return _get_dict_label('project_type', key, lang)


def project_stage_label(key, lang='zh'):
    """获取项目阶段标签（从数据库）"""
    return _get_dict_label('project_stage', key, lang)


def report_source_label(key, lang='zh'):
    """获取报备来源标签（从数据库）"""
    return _get_dict_label('report_source', key, lang)


def company_type_label(key, lang='zh'):
    """获取企业类型标签（从数据库）"""
    return _get_dict_label('company_type', key, lang)


def get_project_type_options():
    """获取语言感知的项目类型选项（从数据库）"""
    return _get_dict_options('project_type')


def get_project_stage_options():
    """获取语言感知的项目阶段选项（从数据库）"""
    return _get_dict_options('project_stage')


def get_report_source_options():
    """获取语言感知的报备来源选项（从数据库）"""
    return _get_dict_options('report_source')


def get_company_type_options():
    """获取语言感知的企业类型选项（从数据库）"""
    return _get_dict_options('company_type')

# =============================================================================
# 保留的硬编码标签（业务状态类，不适合用户配置）
# =============================================================================

AUTHORIZATION_STATUS_LABELS = {
    'pending': {'zh': '待审', 'en': 'Pending'},
    'approved': {'zh': '授权', 'en': 'Approve'},
    'rejected': {'zh': '驳回', 'en': 'Reject'}
}

# 企业类型颜色映射（颜色不需要国际化，保留硬编码）
COMPANY_TYPE_COLORS = {
    # 主键（8个）- 用于新数据
    'user': '#0B6EFD',
    'dealer': '#28a745',
    'distributor': '#28a745',
    'integrator': '#fd7e14',
    'designer': '#6f42c1',
    'contractor': '#dc3545',
    'partner': '#20c997',
    'other': '#6c757d',

    # 向后兼容别名（4个）- 仅用于历史数据显示
    'direct_customer': '#0B6EFD',      # 映射到user
    'design_institute': '#6f42c1',      # 映射到designer
    'consultant': '#6f42c1',            # 映射到designer
    'general_contractor': '#dc3545'     # 映射到contractor
}

# 货币类型映射（中文显示名称，英文显示代码）
CURRENCY_TYPE_LABELS = {
    'CNY': {'zh': '人民币', 'en': 'CNY'},
    'USD': {'zh': '美元', 'en': 'USD'},
    'HKD': {'zh': '港币', 'en': 'HKD'},
    'TWD': {'zh': '台币', 'en': 'TWD'},
    'SGD': {'zh': '新加坡元', 'en': 'SGD'},
    'MYR': {'zh': '马来西亚林吉特', 'en': 'MYR'},
    'IDR': {'zh': '印尼盾', 'en': 'IDR'},
    'THB': {'zh': '泰铢', 'en': 'THB'},
    'VND': {'zh': '越南盾', 'en': 'VND'}
}

PRODUCT_SITUATION_LABELS = {
    'qualified': {'zh': '入围', 'en': 'Qualfy'},
    'controlled': {'zh': '受控', 'en': 'Control'},
    'not_required': {'zh': '无要求', 'en': 'None'},
    'unqualified': {'zh': '未入围', 'en': 'Exclud'}
}

def authorization_status_label(key, lang='zh'):
    """获取授权状态标签（保留硬编码，业务状态类）"""
    return AUTHORIZATION_STATUS_LABELS.get(key, {}).get(lang, key)

def company_type_color(key):
    """获取企业类型对应的颜色"""
    return COMPANY_TYPE_COLORS.get(key, '#6c757d')

def product_situation_label(key, lang='zh'):
    """获取品牌状况标签（保留硬编码）"""
    return PRODUCT_SITUATION_LABELS.get(key, {}).get(lang, key)

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

def currency_type_label(key, lang='zh'):
    """获取货币类型标签"""
    return CURRENCY_TYPE_LABELS.get(key, {}).get(lang, key)

def get_currency_symbol(currency_code='CNY'):
    """获取货币符号"""
    currency_symbols = {
        'CNY': '¥',
        'USD': '$',
        'HKD': 'HK$',
        'TWD': 'NT$',
        'SGD': 'S$',
        'MYR': 'RM',
        'IDR': 'Rp',
        'THB': '฿',
        'VND': '₫'
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
        import os
        db_type = os.environ.get('PMA_DB_TYPE', os.environ.get('SUPABASE_DB_TYPE', 'sp8d'))
        symbol = '$' if db_type == 'ovs' else '¥'
        return {
            'divisor': 100,         # 万元转百万：万元/100 = M
            'unit': 'M',
            'decimal_places': 2,
            'format_type': 'million',
            'currency_symbol': symbol
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


def format_money(amount_yuan, currency_code='CNY'):
    """币种驱动的金额显示(单一来源,复用 get_currency_symbol)。

    输入: amount_yuan = 主币种单位的金额(元/USD/MYR/...),currency_code = 货币代码。
    输出: 已格式化的显示字符串。
      - CNY: ≥10000 元 → '¥{n}万' (一位~两位小数,去尾零); 否则 '¥X,XXX.XX' 千位分隔
      - USD/SGD/HKD/TWD/EUR/MYR/IDR/THB/VND 等: ≥1,000,000 → '{sym}{n}M';
        ≥1,000 → '{sym}{n}K'; 否则 '{sym}X,XXX.XX' 千位分隔
    任何输入异常 → 兜底 '{sym}{原值}' 不抛错(绝不丢/盖输入)。

    用途: mobile_projects 等多模块「直接消费 display 字符串」的单一来源;
    web 后续如需统一币种驱动展示也可调本函数。
    """
    try:
        if amount_yuan in (None, '') :
            return ''
        v = float(amount_yuan)
        sym = get_currency_symbol(currency_code or 'CNY')
        if v == 0:
            return f'{sym}0'
        if (currency_code or 'CNY').upper() == 'CNY':
            if abs(v) >= 10000:
                w = v / 10000.0
                # 万: 2 位小数, 去掉无意义尾零
                s = f'{w:.2f}'.rstrip('0').rstrip('.')
                return f'{sym}{s}万'
            return f'{sym}{v:,.2f}'
        # 非 CNY: K/M 紧凑(西式)
        if abs(v) >= 1_000_000:
            s = f'{v / 1_000_000:.2f}'.rstrip('0').rstrip('.')
            return f'{sym}{s}M'
        if abs(v) >= 1_000:
            s = f'{v / 1_000:.2f}'.rstrip('0').rstrip('.')
            return f'{sym}{s}K'
        return f'{sym}{v:,.2f}'
    except Exception:
        try:
            return f"{get_currency_symbol(currency_code or 'CNY')}{amount_yuan}"
        except Exception:
            return str(amount_yuan if amount_yuan is not None else '')


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


def get_available_quotation_currencies():
    """获取报价单可选的货币列表

    只返回：
    1. 系统默认货币（CNY for SP8D, USD for OVS）
    2. ProductRegionPrice 表中已配置的 distinct 货币

    不包括没有任何产品面价的货币 —— 因为系统不做汇率换算，
    选了也会导致所有产品面价为空，没有实际意义。

    Returns:
        list of (code, name) tuples
    """
    try:
        from app.utils.i18n import get_current_language
        from app.models.product import ProductRegionPrice
        from app.models.company_entity import CompanyEntity
        from config import Config
        from app import db

        lang_code = get_current_language()
        available_codes = {Config.DEFAULT_CURRENCY}

        # 查询 region_prices 表中存在的 distinct 货币
        try:
            rows = db.session.query(ProductRegionPrice.currency).distinct().all()
            for (cur,) in rows:
                if cur:
                    available_codes.add(cur.upper())
        except Exception:
            # 表不存在或查询失败时，降级为只返回默认货币
            pass

        # 纳入所有公司主体配置的开票币种 —— 即使该币种在产品库尚无面价，
        # 主体默认币种也必须出现在下拉里，否则前端 entity 切换时 select 无匹配项
        try:
            entity_rows = db.session.query(CompanyEntity.currency_code).distinct().all()
            for (cur,) in entity_rows:
                if cur:
                    available_codes.add(cur.upper())
        except Exception:
            pass

        # 按 CURRENCY_TYPE_LABELS 的顺序返回，过滤掉不可用的
        return [
            (k, v[lang_code]) for k, v in CURRENCY_TYPE_LABELS.items()
            if k in available_codes
        ]
    except Exception as e:
        import logging
        logging.warning(f"get_available_quotation_currencies 失败: {e}")
        # 异常时返回所有货币，不影响系统正常使用
        return get_currency_type_options()

# 向后兼容性选项 - 使用 property 类实现懒加载，避免启动时查询数据库
class _LazyOptions:
    """延迟加载选项类，仅在访问时查询数据库"""

    @property
    def PROJECT_TYPE_OPTIONS(self):
        return get_project_type_options()

    @property
    def PROJECT_STAGE_OPTIONS(self):
        return get_project_stage_options()

    @property
    def REPORT_SOURCE_OPTIONS(self):
        return get_report_source_options()

    @property
    def COMPANY_TYPE_OPTIONS(self):
        return get_company_type_options()

    # 向后兼容的 LABELS 字典（从数据库动态获取）
    @property
    def PROJECT_TYPE_LABELS(self):
        return _get_cached_dict('project_type')

    @property
    def PROJECT_STAGE_LABELS(self):
        return _get_cached_dict('project_stage')

    @property
    def REPORT_SOURCE_LABELS(self):
        return _get_cached_dict('report_source')

    @property
    def COMPANY_TYPE_LABELS(self):
        return _get_cached_dict('company_type')

_lazy = _LazyOptions()

# 保留硬编码的选项（业务状态类，不适合用户配置）
AUTHORIZATION_STATUS_OPTIONS = [(k, v['zh']) for k, v in AUTHORIZATION_STATUS_LABELS.items()]
PRODUCT_SITUATION_OPTIONS = [(k, v['zh']) for k, v in PRODUCT_SITUATION_LABELS.items()]
CURRENCY_TYPE_OPTIONS = [(k, v['zh']) for k, v in CURRENCY_TYPE_LABELS.items()]

# =============================================================================
# 向后兼容的硬编码字典（已废弃，保留仅为兼容旧代码导入）
# 新代码请使用 project_type_label()、get_project_type_options() 等函数
# =============================================================================
PROJECT_TYPE_LABELS = {
    'channel_follow': {'zh': '渠道', 'en': 'Channel'},
    'sales_focus': {'zh': '销售', 'en': 'Sales'},
    'business_opportunity': {'zh': '服务', 'en': 'Service'},
}

PROJECT_STAGE_LABELS = {
    'discover': {'zh': '发现', 'en': 'Discovery'},
    'embed': {'zh': '植入', 'en': 'Embedding'},
    'pre_tender': {'zh': '标前', 'en': 'Pre-tender'},
    'tendering': {'zh': '标中', 'en': 'Tendering'},
    'awarded': {'zh': '中标', 'en': 'Awarded'},
    'quoted': {'zh': '批价', 'en': 'Pricing'},
    'signed': {'zh': '签约', 'en': 'Contracted'},
    'lost': {'zh': '失败', 'en': 'Failed'},
    'paused': {'zh': '搁置', 'en': 'Paused'},
}

REPORT_SOURCE_LABELS = {
    'channel': {'zh': '渠道', 'en': 'Channel'},
    'sales': {'zh': '销售', 'en': 'Sales'},
    'marketing': {'zh': '市场', 'en': 'Market'},
}

COMPANY_TYPE_LABELS = {
    # 英文 key（标准）
    'user': {'zh': '用户', 'en': 'User'},
    'designer': {'zh': '顾问', 'en': 'Conslt'},
    'contractor': {'zh': '总包', 'en': 'Contrc'},
    'integrator': {'zh': '集成', 'en': 'Integr'},
    'dealer': {'zh': '经销', 'en': 'Dealer'},
    'distributor': {'zh': '分销', 'en': 'Distri'},
    'partner': {'zh': '伙伴', 'en': 'Partner'},
    'supplier': {'zh': '供应商', 'en': 'Supplier'},
    'other': {'zh': '其他', 'en': 'Other'},
    # 中文 key 别名（兼容旧数据）
    '用户': {'zh': '用户', 'en': 'User'},
    '最终用户': {'zh': '最终用户', 'en': 'User'},
    '经销商': {'zh': '经销商', 'en': 'Dealer'},
    '集成商': {'zh': '集成商', 'en': 'Integr'},
    '设计院': {'zh': '设计院', 'en': 'Conslt'},
    '总包商': {'zh': '总包商', 'en': 'Contrc'},
    '代理商': {'zh': '代理商', 'en': 'Distri'},
    '合作伙伴': {'zh': '合作伙伴', 'en': 'Partner'},
    '其他': {'zh': '其他', 'en': 'Other'},
}

# 向后兼容选项（基于硬编码字典）
PROJECT_TYPE_OPTIONS = [(k, v['zh']) for k, v in PROJECT_TYPE_LABELS.items()]
PROJECT_STAGE_OPTIONS = [(k, v['zh']) for k, v in PROJECT_STAGE_LABELS.items()]
REPORT_SOURCE_OPTIONS = [(k, v['zh']) for k, v in REPORT_SOURCE_LABELS.items()]
COMPANY_TYPE_OPTIONS = [(k, v['zh']) for k, v in COMPANY_TYPE_LABELS.items()]

# 行业分类映射
INDUSTRY_LABELS = {
    # 制造业相关
    'manufacturing': {'zh': '制造', 'en': 'Manufac'},
    'datacenter': {'zh': '数据', 'en': 'DataCtr'},
    'shipbuilding': {'zh': '造船', 'en': 'Ship'},
    'semiconductor': {'zh': '半导体', 'en': 'SemiCon'},
    'chemical': {'zh': '化工', 'en': 'Chemical'},
    # 能源交通相关
    'energy': {'zh': '能源', 'en': 'Energy'},
    'transportation': {'zh': '交通', 'en': 'Transp'},
    'transport': {'zh': '交通', 'en': 'Transp'},  # 别名兼容
    'tunnel_underground': {'zh': '隧道', 'en': 'Tunnel'},
    # 商业服务相关
    'real_estate': {'zh': '地产', 'en': 'Estate'},
    'hospitality': {'zh': '酒店', 'en': 'Hotel'},
    'finance': {'zh': '金融', 'en': 'Finance'},
    'retail': {'zh': '零售', 'en': 'Retail'},
    # 公共服务相关
    'government': {'zh': '政府', 'en': 'Govt'},
    'education': {'zh': '教育', 'en': 'Educate'},
    'healthcare': {'zh': '医疗', 'en': 'Health'},
    'health': {'zh': '医疗', 'en': 'Health'},  # 别名兼容
    # 科技相关
    'technology': {'zh': '科技', 'en': 'Tech'},
    # 其他/未分类
    'other': {'zh': '其他', 'en': 'Other'},
    'uncategorized': {'zh': '未分类', 'en': 'N/A'},
    '未分类': {'zh': '未分类', 'en': 'N/A'},  # 中文别名兼容
}

# 行业别名集合（仅用于向后兼容显示，不应出现在筛选选项中）
INDUSTRY_ALIASES = {'transport', 'health', '未分类'}

# 行业颜色映射
INDUSTRY_COLORS = {
    'manufacturing': '#0B6EFD',
    'datacenter': '#5BC0DE',
    'shipbuilding': '#198754',
    'semiconductor': '#fd7e14',
    'chemical': '#dc3545',
    'energy': '#ffc107',
    'transportation': '#6f42c1',
    'transport': '#6f42c1',  # 别名兼容
    'tunnel_underground': '#6c757d',
    'real_estate': '#20c997',
    'hospitality': '#e83e8c',
    'finance': '#17a2b8',
    'government': '#007bff',
    'education': '#28a745',
    'healthcare': '#dc3545',
    'health': '#dc3545',  # 别名兼容
    'technology': '#6366f1',  # indigo 科技色
    'other': '#6c757d'
}

def industry_label(key, lang='zh'):
    return INDUSTRY_LABELS.get(key, {}).get(lang, key)

def industry_color(key):
    """获取行业对应的颜色"""
    return INDUSTRY_COLORS.get(key, '#6c757d')

def get_industry_options():
    """获取语言感知的行业选项（排除别名）"""
    try:
        from app.utils.i18n import get_current_language
        # 根据当前语言选择合适的语言代码
        lang_code = get_current_language()
        # 排除别名，只返回主键
        return [(k, v[lang_code]) for k, v in INDUSTRY_LABELS.items()
                if k not in INDUSTRY_ALIASES]
    except Exception as e:
        # 记录错误日志以便调试
        import logging
        logging.warning(f"get_industry_options 获取语言失败: {e}")
        # 如果获取语言失败，默认使用中文
        return [(k, v['zh']) for k, v in INDUSTRY_LABELS.items()
                if k not in INDUSTRY_ALIASES]

# 保持向后兼容性（排除别名）
INDUSTRY_OPTIONS = [(k, v['zh']) for k, v in INDUSTRY_LABELS.items()
                    if k not in INDUSTRY_ALIASES]

# =============================================================================
# 客户活跃度6级状态定义
# =============================================================================

# 客户活跃度状态映射（6级）
ACTIVITY_STATUS_LABELS = {
    'highly_active': {'zh': '高度活跃', 'en': 'Highly Active'},
    'active': {'zh': '活跃', 'en': 'Active'},
    'normal': {'zh': '正常', 'en': 'Normal'},
    'to_follow': {'zh': '待跟进', 'en': 'To Follow'},
    'dormant': {'zh': '休眠', 'en': 'Dormant'},
    'churned': {'zh': '流失', 'en': 'Churned'},
    'frozen': {'zh': '已冻结', 'en': 'Frozen'},
}

# 客户活跃度状态颜色映射（用于徽章显示）
ACTIVITY_STATUS_COLORS = {
    'highly_active': {'bg': 'rgba(134,239,172,0.2)', 'border': '#86efac', 'text': '#166534'},
    'active': {'bg': 'rgba(147,197,253,0.2)', 'border': '#93c5fd', 'text': '#1e40af'},
    'normal': {'bg': 'rgba(125,211,252,0.2)', 'border': '#7dd3fc', 'text': '#0369a1'},
    'to_follow': {'bg': 'rgba(253,224,71,0.2)', 'border': '#fde047', 'text': '#a16207'},
    'dormant': {'bg': 'rgba(253,186,116,0.2)', 'border': '#fdba74', 'text': '#c2410c'},
    'churned': {'bg': 'rgba(209,213,219,0.2)', 'border': '#d1d5db', 'text': '#4b5563'},
    'frozen': {'bg': 'rgba(148,163,184,0.2)', 'border': '#94a3b8', 'text': '#475569'},
}

# 状态优先级（数值越高越好）
ACTIVITY_STATUS_PRIORITY = {
    'highly_active': 6,
    'active': 5,
    'normal': 4,
    'to_follow': 3,
    'dormant': 2,
    'churned': 1,
    'frozen': 0,
}

def activity_status_label(key, lang='zh'):
    """获取活跃度状态标签"""
    return ACTIVITY_STATUS_LABELS.get(key, {}).get(lang, key)

def activity_status_color(key):
    """获取活跃度状态颜色配置"""
    return ACTIVITY_STATUS_COLORS.get(key, ACTIVITY_STATUS_COLORS['churned'])

def get_activity_status_options():
    """获取语言感知的活跃度状态选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in ACTIVITY_STATUS_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_activity_status_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in ACTIVITY_STATUS_LABELS.items()]

ACTIVITY_STATUS_OPTIONS = [(k, v['zh']) for k, v in ACTIVITY_STATUS_LABELS.items()]

# 客户状态映射（保留向后兼容，映射到新的6级状态）
STATUS_LABELS = {
    'highly_active': {'zh': '高度活跃', 'en': 'Highly Active'},
    'active': {'zh': '活跃', 'en': 'Active'},
    'normal': {'zh': '正常', 'en': 'Normal'},
    'to_follow': {'zh': '待跟进', 'en': 'To Follow'},
    'dormant': {'zh': '休眠', 'en': 'Dormant'},
    'churned': {'zh': '流失', 'en': 'Churned'},
    # 向后兼容旧状态
    'inactive': {'zh': '流失', 'en': 'Churned'},
}

# 活跃状态映射（布尔值）
ACTIVE_STATUS_LABELS = {
    True: {'zh': '活跃', 'en': 'active'},
    False: {'zh': '非活跃', 'en': 'idle'},
}

def active_status_label(key, lang='zh'):
    return ACTIVE_STATUS_LABELS.get(key, {}).get(lang, str(key))

def status_label(key, lang='zh'):
    return STATUS_LABELS.get(key, {}).get(lang, key)

STATUS_OPTIONS = [(k, v['zh']) for k, v in ACTIVITY_STATUS_LABELS.items()]

def get_status_options():
    """获取语言感知的状态选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in ACTIVITY_STATUS_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_status_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in ACTIVITY_STATUS_LABELS.items()]

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


# 产品类型映射
PRODUCT_TYPE_LABELS = {
    'third_party': {'zh': '三方', 'en': '3rd party'},
    'third party': {'zh': '三方', 'en': '3rd party'},  # 数据库存储值兼容
    'channel': {'zh': '渠道', 'en': 'channel'},
    'project': {'zh': '项目', 'en': 'project'}
}

def product_type_label(key, lang='zh'):
    return PRODUCT_TYPE_LABELS.get(key, {}).get(lang, key)

PRODUCT_TYPE_OPTIONS = [(k, v['zh']) for k, v in PRODUCT_TYPE_LABELS.items()]

# 产品状态映射
PRODUCT_STATUS_LABELS = {
    'active': {'zh': '生产', 'en': 'active'},
    'discontinued': {'zh': '停产', 'en': 'discont'},
    'upcoming': {'zh': '待上', 'en': 'soon'}
}

def product_status_label(key, lang='zh'):
    return PRODUCT_STATUS_LABELS.get(key, {}).get(lang, key)

PRODUCT_STATUS_OPTIONS = [(k, v['zh']) for k, v in PRODUCT_STATUS_LABELS.items()]

# 研发产品状态映射
DEV_PRODUCT_STATUS_LABELS = {
    # 英文 key
    'research': {'zh': '调研', 'en': 'resrch'},
    'planning': {'zh': '立项', 'en': 'setup'},
    'development': {'zh': '研发', 'en': 'dev'},
    'apply_storage': {'zh': '申请', 'en': 'apply'},
    'stored': {'zh': '入库', 'en': 'stored'},
    # 中文 key（数据库存储值兼容）
    '调研中': {'zh': '调研', 'en': 'resrch'},
    '立项中': {'zh': '立项', 'en': 'setup'},
    '研发中': {'zh': '研发', 'en': 'dev'},
    '申请入库': {'zh': '申请', 'en': 'apply'},
    '已入库': {'zh': '入库', 'en': 'stored'},
}

def dev_product_status_label(key, lang='zh'):
    return DEV_PRODUCT_STATUS_LABELS.get(key, {}).get(lang, key)

DEV_PRODUCT_STATUS_OPTIONS = [(k, v['zh']) for k, v in DEV_PRODUCT_STATUS_LABELS.items()]


# 审批状态映射
APPROVAL_STATUS_LABELS = {
    'pending': {'zh': '审批', 'en': 'Pending'},
    'approved': {'zh': '通过', 'en': 'Approve'},
    'rejected': {'zh': '拒绝', 'en': 'Reject'},
    'recalled': {'zh': '召回', 'en': 'Recall'},
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

# 业务类型映射（批价单和结算单）
BUSINESS_TYPE_LABELS = {
    'direct_contract': {'zh': '厂商直签', 'en': 'Direct Contract'},
    'factory_pickup': {'zh': '厂家提货', 'en': 'Factory Pickup'},
    'channel': {'zh': '常规渠道', 'en': 'Channel'}
}

def business_type_label(key, lang='zh'):
    """获取业务类型标签"""
    return BUSINESS_TYPE_LABELS.get(key, {}).get(lang, key)

def get_business_type_options():
    """获取语言感知的业务类型选项"""
    try:
        from app.utils.i18n import get_current_language
        lang_code = get_current_language()
        return [(k, v[lang_code]) for k, v in BUSINESS_TYPE_LABELS.items()]
    except Exception as e:
        import logging
        logging.warning(f"get_business_type_options 获取语言失败: {e}")
        return [(k, v['zh']) for k, v in BUSINESS_TYPE_LABELS.items()]

BUSINESS_TYPE_OPTIONS = [(k, v['zh']) for k, v in BUSINESS_TYPE_LABELS.items()]

# 厂商企业信息获取函数
def get_vendor_company():
    """
    获取默认厂商企业信息（从Dictionary表）

    返回Dictionary对象，包含完整的企业信息：
    - value: 企业全称
    - address: 详细地址
    - postal_code: 邮政编码
    - phone: 企业电话
    - website: 网站地址
    - logo_content: Logo Base64内容
    等
    """
    from app.models.dictionary import Dictionary

    # 使用 Flask g 对象缓存，避免重复查询
    if 'vendor_company' not in g:
        g.vendor_company = Dictionary.query.filter_by(
            type='company',
            is_vendor=True,
            is_active=True
        ).first()

    return g.vendor_company


def get_vendor_company_by_user(user):
    """
    根据用户的company_name获取对应的厂商企业信息

    参数:
        user: User对象

    返回:
        Dictionary对象（企业字典），如果找不到则返回默认厂商企业

    用途:
        PDF模板中根据项目拥有人获取厂商信息，支持多厂商场景
    """
    from app.models.dictionary import Dictionary

    # 如果没有用户或用户没有设置公司名称，返回默认厂商
    if not user or not user.company_name:
        return get_vendor_company()

    # 尝试精确匹配用户的公司名称
    vendor = Dictionary.query.filter_by(
        type='company',
        value=user.company_name,
        is_vendor=True,
        is_active=True
    ).first()

    if not vendor:
        # 如果精确匹配失败，尝试模糊匹配
        vendor = Dictionary.query.filter(
            Dictionary.type == 'company',
            Dictionary.is_vendor == True,
            Dictionary.is_active == True,
            Dictionary.value.ilike(f'%{user.company_name}%')
        ).first()

    # 如果还是找不到，返回默认厂商企业
    return vendor or get_vendor_company()

# TODO: 可扩展更多字典类型的获取方法

# =============================================================================
# 语言感知过滤器工厂函数
# =============================================================================
def make_i18n_filter(label_func):
    """
    创建语言感知的 Jinja2 过滤器包装器

    用法示例（在 __init__.py 中）：
        app.jinja_env.filters['product_situation_label'] = make_i18n_filter(product_situation_label)

    Args:
        label_func: 接受 (key, lang) 参数的标签函数

    Returns:
        包装后的函数，自动获取当前语言（也支持手动传递 lang 参数）
    """
    def wrapper(key, lang=None):
        if lang is None:
            try:
                # 直接从 session 获取语言，避免复杂的上下文查找
                from flask import session, has_request_context
                if has_request_context():
                    lang = session.get('language', 'zh')
                else:
                    lang = 'zh'
            except Exception:
                lang = 'zh'
        return label_func(key, lang)
    return wrapper


# =============================================================================
# 预定义的 i18n 过滤器版本（供模板直接使用）
# =============================================================================
project_type_label_i18n = make_i18n_filter(project_type_label)
project_stage_label_i18n = make_i18n_filter(project_stage_label)
report_source_label_i18n = make_i18n_filter(report_source_label)
company_type_label_i18n = make_i18n_filter(company_type_label)