# -*- coding: utf-8 -*-
"""国定假期数据加载器

按年份和国家加载假期数据，支持 lru_cache 缓存。
数据文件格式: app/data/holidays/{year}.json
"""
import json
import os
from functools import lru_cache

_HOLIDAYS_DIR = os.path.dirname(__file__)

# 支持的国家列表（code → 中文名/英文名/emoji）
SUPPORTED_COUNTRIES = {
    'CN': {'zh': '中国', 'en': 'China', 'emoji': '🇨🇳'},
    'SG': {'zh': '新加坡', 'en': 'Singapore', 'emoji': '🇸🇬'},
    'MY': {'zh': '马来西亚', 'en': 'Malaysia', 'emoji': '🇲🇾'},
    'TH': {'zh': '泰国', 'en': 'Thailand', 'emoji': '🇹🇭'},
    'ID': {'zh': '印尼', 'en': 'Indonesia', 'emoji': '🇮🇩'},
}


@lru_cache(maxsize=8)
def load_holidays(year: int) -> dict:
    """加载指定年份的假期数据（带缓存）

    Returns:
        dict: {country_code: [{date, name_zh, name_en}, ...]}
    """
    path = os.path.join(_HOLIDAYS_DIR, f'{year}.json')
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_holidays_for_api(year: int, countries: list = None) -> dict:
    """获取 API 格式的假期数据

    Args:
        year: 年份
        countries: 国家代码列表，None 表示全部

    Returns:
        dict: {date_str: [{country, name_zh, name_en}, ...]}
    """
    raw = load_holidays(year)
    if not raw:
        return {}

    result = {}
    for country_code, holidays in raw.items():
        if countries and country_code not in countries:
            continue
        for h in holidays:
            date_str = h['date']
            entry = {
                'country': country_code,
                'name_zh': h['name_zh'],
                'name_en': h['name_en'],
            }
            if date_str not in result:
                result[date_str] = []
            result[date_str].append(entry)

    return result
