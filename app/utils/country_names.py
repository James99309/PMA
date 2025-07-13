#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际化的国家名称映射工具
"""

def get_country_names(language='zh'):
    """根据语言获取国家代码到名称的映射，按地区排序"""
    if language == 'en':
        # 按地区排序：亚洲 -> 欧洲 -> 美洲 -> 非洲/大洋洲
        return {
            # 亚洲
            "CN": "China", "JP": "Japan", "KR": "South Korea", "IN": "India", "SG": "Singapore", 
            "MY": "Malaysia", "TH": "Thailand", "ID": "Indonesia", "VN": "Vietnam", "PH": "Philippines", 
            "AE": "UAE", "SA": "Saudi Arabia",
            # 欧洲
            "DE": "Germany", "GB": "United Kingdom", "FR": "France", "IT": "Italy", "ES": "Spain", 
            "NL": "Netherlands", "CH": "Switzerland", "SE": "Sweden", "NO": "Norway", "FI": "Finland", 
            "DK": "Denmark", "BE": "Belgium", "RU": "Russia",
            # 美洲
            "US": "United States", "CA": "Canada", "BR": "Brazil",
            # 大洋洲/非洲
            "AU": "Australia", "NZ": "New Zealand", "ZA": "South Africa"
        }
    else:  # 默认中文
        return {
            # 亚洲
            "CN": "中国", "JP": "日本", "KR": "韩国", "IN": "印度", "SG": "新加坡", 
            "MY": "马来西亚", "TH": "泰国", "ID": "印度尼西亚", "VN": "越南", "PH": "菲律宾", 
            "AE": "阿联酋", "SA": "沙特阿拉伯",
            # 欧洲
            "DE": "德国", "GB": "英国", "FR": "法国", "IT": "意大利", "ES": "西班牙", 
            "NL": "荷兰", "CH": "瑞士", "SE": "瑞典", "NO": "挪威", "FI": "芬兰", 
            "DK": "丹麦", "BE": "比利时", "RU": "俄罗斯",
            # 美洲
            "US": "美国", "CA": "加拿大", "BR": "巴西",
            # 大洋洲/非洲
            "AU": "澳大利亚", "NZ": "新西兰", "ZA": "南非"
        } 