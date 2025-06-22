"""
汇率服务模块
提供实时汇率查询功能
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ExchangeRateService:
    """汇率服务类"""
    
    # 支持的货币类型
    SUPPORTED_CURRENCIES = {
        'USD': '美元',
        'CNY': '人民币', 
        'SGD': '新加坡元',
        'MYR': '马来西亚林吉特',
        'IDR': '印尼盾',
        'THB': '泰铢'
    }
    
    # 免费汇率API - 使用exchangerate-api.com
    API_BASE_URL = "https://api.exchangerate-api.com/v4/latest"
    
    # 备用API - 使用fixer.io (需要注册获取API key)
    # FIXER_API_URL = "http://data.fixer.io/api/latest"
    # FIXER_API_KEY = "your_api_key_here"
    
    def __init__(self):
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = 3600  # 缓存1小时
    
    def get_exchange_rates(self, base_currency: str = 'CNY') -> Dict[str, float]:
        """
        获取汇率数据
        
        Args:
            base_currency: 基准货币，默认为人民币
            
        Returns:
            Dict[str, float]: 汇率字典，格式为 {货币代码: 汇率}
        """
        cache_key = f"rates_{base_currency}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            # 尝试从API获取汇率
            rates = self._fetch_from_api(base_currency)
            if rates:
                self._update_cache(cache_key, rates)
                return rates
            else:
                # API失败时使用默认汇率
                return self._get_default_rates(base_currency)
                
        except Exception as e:
            logger.error(f"获取汇率失败: {e}")
            return self._get_default_rates(base_currency)
    
    def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        货币转换
        
        Args:
            amount: 金额
            from_currency: 源货币
            to_currency: 目标货币
            
        Returns:
            float: 转换后的金额
        """
        if from_currency == to_currency:
            return amount
        
        # 获取以人民币为基准的汇率
        rates = self.get_exchange_rates('CNY')
        
        # 如果源货币不是人民币，先转换为人民币
        if from_currency != 'CNY':
            if from_currency in rates:
                amount = amount / rates[from_currency]
            else:
                logger.warning(f"不支持的货币类型: {from_currency}")
                return amount
        
        # 如果目标货币不是人民币，再转换为目标货币
        if to_currency != 'CNY':
            if to_currency in rates:
                amount = amount * rates[to_currency]
            else:
                logger.warning(f"不支持的货币类型: {to_currency}")
                return amount
        
        return round(amount, 2)
    
    def _fetch_from_api(self, base_currency: str) -> Optional[Dict[str, float]]:
        """从API获取汇率数据"""
        try:
            url = f"{self.API_BASE_URL}/{base_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            
            # 只返回我们支持的货币
            filtered_rates = {}
            for currency in self.SUPPORTED_CURRENCIES.keys():
                if currency in rates:
                    filtered_rates[currency] = rates[currency]
                elif currency == base_currency:
                    filtered_rates[currency] = 1.0
            
            return filtered_rates
            
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            return None
    
    def _get_default_rates(self, base_currency: str = 'CNY') -> Dict[str, float]:
        """获取默认汇率（当API不可用时使用）"""
        # 以人民币为基准的默认汇率
        default_rates_cny = {
            'CNY': 1.0,
            'USD': 0.14,     # 1 CNY = 0.14 USD
            'SGD': 0.19,     # 1 CNY = 0.19 SGD
            'MYR': 0.65,     # 1 CNY = 0.65 MYR
            'IDR': 2100.0,   # 1 CNY = 2100 IDR
            'THB': 5.0       # 1 CNY = 5.0 THB
        }
        
        if base_currency == 'CNY':
            return default_rates_cny
        
        # 如果基准货币不是人民币，需要转换
        if base_currency in default_rates_cny:
            base_rate = default_rates_cny[base_currency]
            converted_rates = {}
            for currency, rate in default_rates_cny.items():
                converted_rates[currency] = rate / base_rate
            return converted_rates
        
        return default_rates_cny
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache:
            return False
        
        if cache_key not in self._cache_expiry:
            return False
        
        return datetime.now() < self._cache_expiry[cache_key]
    
    def _update_cache(self, cache_key: str, data: Dict[str, float]):
        """更新缓存"""
        self._cache[cache_key] = data
        self._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=self._cache_duration)
    
    def get_currency_options(self) -> list:
        """获取货币选项列表，用于前端下拉框"""
        return [
            {'code': code, 'name': name, 'display': f"{name} ({code})"}
            for code, name in self.SUPPORTED_CURRENCIES.items()
        ]
    
    def get_currency_name(self, currency_code: str) -> str:
        """获取货币名称"""
        return self.SUPPORTED_CURRENCIES.get(currency_code, currency_code)


# 全局实例
exchange_rate_service = ExchangeRateService() 