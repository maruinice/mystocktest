# -*- coding: utf-8 -*-
"""
交易API模块

提供交易相关的REST API接口，包括下单、撤单、查询等功能
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from app.middleware.auth import require_auth
from app.docs.swagger_config import get_swagger_spec

# 使用基于数据库的交易服务
from app.services.trade_service_db import db_trade_service
from app.models.trade import Order, Position, OrderType, OrderStatus, OrderSide


# 创建交易蓝图
trade_bp = Blueprint('trade', __name__, url_prefix='/api/trade')

# 使用数据库交易服务
trade_service = db_trade_service


class TradeValidator:
    """交易数据验证器"""
    
    @staticmethod
    def validate_order_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """验证下单数据"""
        required_fields = ['symbol', 'side', 'order_type', 'quantity']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 验证数量
        if data['quantity'] <= 0:
            raise ValueError("数量必须大于0")
        
        # 验证价格（限价单）
        if data['order_type'] == 'limit' and ('price' not in data or data['price'] <= 0):
            raise ValueError("限价单必须指定有效价格")
        
        return data


@trade_bp.route('/order', methods=['POST'])
@require_auth
def place_order():
    """下单"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证交易时间
        from app.services.data_service import DataService
        is_trading, time_msg = DataService.is_trading_time()
        if not is_trading:
            return jsonify({
                'success': False,
                'message': f'当前不可交易：{time_msg}',
                'error_code': 'MARKET_CLOSED'
            }), 400
        
        # 字段名映射（兼容前端）
        # 前端使用: stock_code, direction, order_type, price, quantity
        # 后端使用: symbol, side, order_type, price, quantity
        if 'stock_code' in data:
            data['symbol'] = data.pop('stock_code')
        if 'direction' in data:
            data['side'] = data.pop('direction')
        
        # 验证数据
        validated_data = TradeValidator.validate_order_data(data)
        
        # 确保user_id是字符串类型
        user_id = str(g.current_user.get('id') or g.current_user.get('user_id', '1'))
        
        # 下单
        order = trade_service.place_order(
            user_id=user_id,
            symbol=validated_data['symbol'],
            side=validated_data['side'],
            order_type=validated_data['order_type'],
            quantity=validated_data['quantity'],
            price=validated_data.get('price')
        )
        
        return jsonify({
            'success': True,
            'message': '下单成功',
            'data': order
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下单失败: {str(e)}'
        }), 500


@trade_bp.route('/order/<order_id>', methods=['DELETE'])
@require_auth
def cancel_order(order_id: str):
    """撤单"""
    try:
        # 确保user_id是字符串类型
        user_id = str(g.current_user.get('id') or g.current_user.get('user_id', '1'))
        
        result = trade_service.cancel_order(
            user_id=user_id,
            order_id=order_id
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': '撤单成功',
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'message': '订单不存在或无法撤销'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'撤单失败: {str(e)}'
        }), 500


@trade_bp.route('/orders', methods=['GET'])
@require_auth
def get_orders():
    """获取订单列表"""
    try:
        # 获取查询参数
        status = request.args.get('status')
        symbol = request.args.get('symbol')
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        
        # 确保user_id是字符串类型
        user_id = str(g.current_user.get('id') or g.current_user.get('user_id', '1'))
        
        # 获取订单列表 - 修复返回值处理
        orders, total = trade_service.get_orders(
            user_id=user_id,
            status=status,
            code=symbol,  # 注意参数名映射
            page=page,
            size=page_size
        )
        
        # 转换为字典格式
        orders_data = []
        for order in orders:
            # 数据库模型直接调用to_dict()
            orders_data.append(order.to_dict())
        
        result = {
            'orders': orders_data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
        
        return jsonify({
            'success': True,
            'message': '获取订单列表成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取订单列表失败: {str(e)}'
        }), 500


@trade_bp.route('/positions', methods=['GET'])
@require_auth
def get_positions():
    """获取持仓列表"""
    try:
        symbol = request.args.get('symbol')
        
        # 确保user_id是字符串类型
        user_id = str(g.current_user.get('id') or g.current_user.get('user_id', '1'))
        
        # 获取持仓列表（已经是字典列表）
        positions_data = trade_service.get_positions(
            user_id=user_id,
            code=symbol  # 注意参数名映射
        )
        
        return jsonify({
            'success': True,
            'message': '获取持仓列表成功',
            'data': {
                'positions': positions_data,
                'total': len(positions_data)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取持仓列表失败: {str(e)}'
        }), 500


@trade_bp.route('/trades', methods=['GET'])
@require_auth
def get_trade_records():
    """获取成交记录"""
    try:
        # 获取查询参数
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        
        # 获取成交记录 - 使用模拟数据
        trades_data = []
        for i in range(5):  # 模拟5条成交记录
            trades_data.append({
                'trade_id': f'trade_{i+1}',
                'order_id': f'order_{i+1}',
                'symbol': symbol or '000001.SZ',
                'side': 'buy' if i % 2 == 0 else 'sell',
                'quantity': 100 * (i + 1),
                'price': 10.50 + i * 0.1,
                'amount': (100 * (i + 1)) * (10.50 + i * 0.1),
                'fee': 5.0,
                'trade_time': datetime.now().isoformat()
            })
        
        result = {
            'trades': trades_data,
            'total': len(trades_data),
            'page': page,
            'page_size': page_size,
            'total_pages': 1
        }
        
        return jsonify({
            'success': True,
            'message': '获取成交记录成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取成交记录失败: {str(e)}'
        }), 500


@trade_bp.route('/health', methods=['GET'])
def trade_health_check():
    """交易服务健康检查"""
    return jsonify({
        'success': True,
        'message': '交易服务运行正常',
        'data': {
            'service': 'trade_api',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    })


@trade_bp.route('/account', methods=['GET'])
@require_auth
def get_account_info():
    """获取账户信息"""
    try:
        # 确保user_id是字符串类型
        user_id = str(g.current_user.get('id') or g.current_user.get('user_id', '1'))
        
        account_info = trade_service.get_account_info(user_id=user_id)
        
        return jsonify({
            'success': True,
            'message': '获取账户信息成功',
            'data': account_info
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"获取账户信息失败: {error_detail}")
        return jsonify({
            'success': False,
            'message': f'获取账户信息失败: {str(e)}'
        }), 500








