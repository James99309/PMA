# -*- coding: utf-8 -*-
"""报销科目 / 状态 的多语言 label —— web / mobile / pdf 共用的唯一来源。

背景:`EXPENSE_CATEGORIES` / `EXPENSE_STATUS`(models/expense.py) 只有中文 label;
英文翻译此前分散重复在 mobile_expense.py / pdf_generator.py 各写一份。本模块统一收口,
其它地方一律改调这里的函数,不要再各自维护英文映射。

取值:`expense_category_label(key, lang)` / `expense_status_label(key, lang)`
列表:`localized_expense_categories(lang)` / `localized_expense_status(lang)` → [(code, label), ...]
lang 省略时按当前会话语言自动判定(web);mobile 端请显式传入 get_request_lang()。
"""
from app.models.expense import EXPENSE_CATEGORIES, EXPENSE_STATUS

# {code: {'zh': ..., 'en': ...}} —— 英文翻译的权威来源
EXPENSE_CATEGORY_I18N = {
    'entertainment':        {'zh': '招待费',   'en': 'Entertainment'},
    'local_transport':      {'zh': '市内交通', 'en': 'Local Transport'},
    'travel_accommodation': {'zh': '差旅住宿', 'en': 'Travel & Accommodation'},
    'office_supplies':      {'zh': '办公用品', 'en': 'Office Supplies'},
    'communication':        {'zh': '通讯费',   'en': 'Communication'},
    'fuel':                 {'zh': '油费',     'en': 'Fuel'},
    'parking':              {'zh': '停车费',   'en': 'Parking'},
    'meals':                {'zh': '餐费',     'en': 'Meals'},
    'other':                {'zh': '其他',     'en': 'Other'},
}

EXPENSE_STATUS_I18N = {
    'draft':            {'zh': '草稿',   'en': 'Draft'},
    'pending':          {'zh': '待审批', 'en': 'Pending'},
    'approved':         {'zh': '已通过', 'en': 'Approved'},
    'rejected':         {'zh': '已驳回', 'en': 'Rejected'},
    'recalled':         {'zh': '已召回', 'en': 'Recalled'},
    'awaiting_payment': {'zh': '待支付', 'en': 'Awaiting Payment'},
    'paid':             {'zh': '已支付', 'en': 'Paid'},
}


def _resolve_lang(lang=None):
    """归一为 'zh' / 'en'。lang 省略时按当前会话语言判定。"""
    if lang:
        return 'en' if str(lang).lower().startswith('en') else 'zh'
    try:
        from app.utils.i18n import get_current_language
        return 'en' if str(get_current_language()).lower().startswith('en') else 'zh'
    except Exception:
        return 'zh'


def expense_category_label(key, lang=None):
    lang = _resolve_lang(lang)
    meta = EXPENSE_CATEGORY_I18N.get(key)
    if meta:
        return meta.get(lang) or meta.get('zh')
    # 未知 code → 回退 model 的中文 label
    return next((zh for k, zh in EXPENSE_CATEGORIES if k == key), key or '')


def expense_status_label(key, lang=None):
    lang = _resolve_lang(lang)
    meta = EXPENSE_STATUS_I18N.get(key)
    if meta:
        return meta.get(lang) or meta.get('zh')
    return next((zh for k, zh in EXPENSE_STATUS if k == key), key or '')


def localized_expense_categories(lang=None):
    """返回 [(code, label), ...],顺序同 EXPENSE_CATEGORIES。"""
    lang = _resolve_lang(lang)
    return [(code, expense_category_label(code, lang)) for code, _ in EXPENSE_CATEGORIES]


def localized_expense_status(lang=None):
    """返回 [(code, label), ...],顺序同 EXPENSE_STATUS。"""
    lang = _resolve_lang(lang)
    return [(code, expense_status_label(code, lang)) for code, _ in EXPENSE_STATUS]
