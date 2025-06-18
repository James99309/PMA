#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际化的国家名称映射工具
"""

def get_country_names(language='zh-CN'):
    """根据语言获取国家代码到名称的映射"""
    if language == 'en':
        return {
            "CN": "China", "US": "United States", "JP": "Japan", "DE": "Germany", "FR": "France", 
            "GB": "United Kingdom", "CA": "Canada", "AU": "Australia", "NZ": "New Zealand", 
            "IN": "India", "RU": "Russia", "BR": "Brazil", "ZA": "South Africa", "SG": "Singapore", 
            "MY": "Malaysia", "TH": "Thailand", "ID": "Indonesia", "PH": "Philippines", "VN": "Vietnam", 
            "KR": "South Korea", "AE": "UAE", "SA": "Saudi Arabia", "IT": "Italy", "ES": "Spain", 
            "NL": "Netherlands", "CH": "Switzerland", "SE": "Sweden", "NO": "Norway", "FI": "Finland", 
            "DK": "Denmark", "BE": "Belgium"
        }
    else:  # 默认中文
        return {
            "CN": "中国", "US": "美国", "JP": "日本", "DE": "德国", "FR": "法国", "GB": "英国", 
            "CA": "加拿大", "AU": "澳大利亚", "NZ": "新西兰", "IN": "印度", "RU": "俄罗斯", 
            "BR": "巴西", "ZA": "南非", "SG": "新加坡", "MY": "马来西亚", "TH": "泰国", 
            "ID": "印度尼西亚", "PH": "菲律宾", "VN": "越南", "KR": "韩国", "AE": "阿联酋", 
            "SA": "沙特阿拉伯", "IT": "意大利", "ES": "西班牙", "NL": "荷兰", "CH": "瑞士", 
            "SE": "瑞典", "NO": "挪威", "FI": "芬兰", "DK": "丹麦", "BE": "比利时"
        } 