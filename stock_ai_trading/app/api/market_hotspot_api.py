"""
市场热点API
提供市场热点数据的API接口
"""

from flask import Blueprint, request, jsonify
from ..services.market_hotspot_service import market_hotspot_service

market_hotspot_bp = Blueprint('market_hotspot', __name__, url_prefix='/api/market')


@market_hotspot_bp.route('/hotspots', methods=['GET'])
def get_market_hotspots():
    """
    获取市场热点
    
    Query Parameters:
        source: 数据源 (gainers/losers/volume/turnover)，默认 gainers
        limit: 返回数量，默认 10
        
    Returns:
        市场热点数据
    """
    source = request.args.get('source', 'gainers')
    limit = int(request.args.get('limit', 10))
    
    result = market_hotspot_service.get_market_hotspots(source, limit)
    return jsonify(result)


@market_hotspot_bp.route('/gainers', methods=['GET'])
def get_top_gainers():
    """获取涨幅榜"""
    limit = int(request.args.get('limit', 10))
    trade_date = request.args.get('trade_date')
    
    data = market_hotspot_service.get_top_gainers(limit, trade_date)
    return jsonify({
        'success': True,
        'data': data
    })


@market_hotspot_bp.route('/losers', methods=['GET'])
def get_top_losers():
    """获取跌幅榜"""
    limit = int(request.args.get('limit', 10))
    trade_date = request.args.get('trade_date')
    
    data = market_hotspot_service.get_top_losers(limit, trade_date)
    return jsonify({
        'success': True,
        'data': data
    })


@market_hotspot_bp.route('/volume', methods=['GET'])
def get_top_volume():
    """获取成交量榜"""
    limit = int(request.args.get('limit', 10))
    trade_date = request.args.get('trade_date')
    
    data = market_hotspot_service.get_top_volume(limit, trade_date)
    return jsonify({
        'success': True,
        'data': data
    })


@market_hotspot_bp.route('/turnover', methods=['GET'])
def get_top_turnover():
    """获取换手率榜"""
    limit = int(request.args.get('limit', 10))
    trade_date = request.args.get('trade_date')
    
    data = market_hotspot_service.get_top_turnover(limit, trade_date)
    return jsonify({
        'success': True,
        'data': data
    })
