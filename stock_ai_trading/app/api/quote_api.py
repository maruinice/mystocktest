"""
实时行情API
提供股票实时行情查询接口
"""

from flask import Blueprint, request, jsonify, g
import logging
from typing import List

from ..middleware.auth import require_auth
from ..services.realtime_quote_service import realtime_quote_service

logger = logging.getLogger(__name__)

# 创建蓝图
quote_bp = Blueprint('quote', __name__)


@quote_bp.route('/realtime/<path:stock_code>', methods=['GET'])
def get_realtime_quote(stock_code: str):
    """
    获取单个股票的实时行情
    
    Args:
        stock_code: 股票代码，如 000001 或 600519
        
    Returns:
        {
            "success": true,
            "data": {
                "code": "000001",
                "name": "平安银行",
                "current": 11.74,
                "open": 11.81,
                "close": 11.80,
                "high": 11.85,
                "low": 11.72,
                "volume": 304354,
                "amount": 35789000.0,
                "change": -0.06,
                "change_pct": -0.51,
                "time": "10:29:24"
            }
        }
    """
    try:
        # 获取实时行情
        quote_data = realtime_quote_service.get_realtime_price(stock_code)
        
        if not quote_data:
            return jsonify({
                'success': False,
                'message': f'无法获取股票 {stock_code} 的实时行情'
            }), 404
        
        return jsonify({
            'success': True,
            'data': quote_data
        })
        
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取实时行情失败: {str(e)}'
        }), 500


@quote_bp.route('/realtime/batch', methods=['POST'])
def get_batch_realtime_quotes():
    """
    批量获取股票实时行情
    
    Request Body:
        {
            "codes": ["000001", "600519", "600036"]
        }
        
    Returns:
        {
            "success": true,
            "data": {
                "000001": {...},
                "600519": {...},
                "600036": {...}
            }
        }
    """
    try:
        data = request.get_json()
        if not data or 'codes' not in data:
            return jsonify({
                'success': False,
                'message': '请提供股票代码列表'
            }), 400
        
        codes = data['codes']
        if not isinstance(codes, list) or len(codes) == 0:
            return jsonify({
                'success': False,
                'message': '股票代码列表格式错误'
            }), 400
        
        # 限制批量查询数量
        if len(codes) > 50:
            return jsonify({
                'success': False,
                'message': '单次最多查询50个股票'
            }), 400
        
        # 批量获取行情
        quotes = realtime_quote_service.get_batch_realtime_prices(codes)
        
        return jsonify({
            'success': True,
            'data': quotes,
            'total': len(quotes)
        })
        
    except Exception as e:
        logger.error(f"批量获取实时行情失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'批量获取实时行情失败: {str(e)}'
        }), 500


@quote_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': '实时行情服务正常',
        'service': 'realtime_quote'
    })
