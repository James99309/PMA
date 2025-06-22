"""
汇率API路由
"""

from flask import Blueprint, jsonify, request
from app.services.exchange_rate_service import exchange_rate_service
import logging

logger = logging.getLogger(__name__)

exchange_rate_bp = Blueprint('exchange_rate_api', __name__, url_prefix='/api/v1/exchange-rate')

@exchange_rate_bp.route('/rates', methods=['GET'])
def get_exchange_rates():
    """获取汇率数据"""
    try:
        base_currency = request.args.get('base', 'CNY')
        rates = exchange_rate_service.get_exchange_rates(base_currency)
        
        return jsonify({
            'success': True,
            'data': {
                'base_currency': base_currency,
                'rates': rates,
                'timestamp': rates.get('timestamp', None)
            }
        })
    except Exception as e:
        logger.error(f"获取汇率失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取汇率失败'
        }), 500

@exchange_rate_bp.route('/convert', methods=['POST'])
def convert_currency():
    """货币转换"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        from_currency = data.get('from_currency', 'CNY')
        to_currency = data.get('to_currency', 'CNY')
        
        converted_amount = exchange_rate_service.convert_amount(
            amount, from_currency, to_currency
        )
        
        return jsonify({
            'success': True,
            'data': {
                'original_amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'converted_amount': converted_amount,
                'rate': converted_amount / amount if amount > 0 else 0
            }
        })
    except Exception as e:
        logger.error(f"货币转换失败: {e}")
        return jsonify({
            'success': False,
            'message': '货币转换失败'
        }), 500

@exchange_rate_bp.route('/currencies', methods=['GET'])
def get_supported_currencies():
    """获取支持的货币列表"""
    try:
        currencies = exchange_rate_service.get_currency_options()
        
        return jsonify({
            'success': True,
            'data': currencies
        })
    except Exception as e:
        logger.error(f"获取货币列表失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取货币列表失败'
        }), 500 