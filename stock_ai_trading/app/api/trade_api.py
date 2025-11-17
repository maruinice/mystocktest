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

from app.services.trade_service import TradeService
from app.models.trade import Order, Position, OrderType, OrderStatus, OrderSide


# 创建交易蓝图
trade_bp = Blueprint('trade', __name__, url_prefix='/api/trade')

# 初始化交易服务
trade_service = TradeService()


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
        
        # 验证数据
        validated_data = TradeValidator.validate_order_data(data)
        
        # 下单
        order = trade_service.place_order(
            user_id=g.current_user['id'],
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
        result = trade_service.cancel_order(
            user_id=g.current_user['id'],
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
        
        # 获取订单列表 - 修复返回值处理
        orders, total = trade_service.get_orders(
            user_id=g.current_user['id'],
            status=status,
            code=symbol,  # 注意参数名映射
            page=page,
            size=page_size
        )
        
        # 转换为字典格式
        orders_data = []
        for order in orders:
            orders_data.append({
                'order_id': order.order_id,
                'symbol': order.code,
                'side': order.side.value,
                'order_type': order.order_type.value,
                'quantity': order.quantity,
                'price': order.price,
                'filled_quantity': order.filled_quantity,
                'avg_price': order.avg_price,
                'status': order.status.value,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else None
            })
        
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
        
        # 获取持仓列表
        positions = trade_service.get_positions(
            user_id=g.current_user['id'],
            code=symbol  # 注意参数名映射
        )
        
        # 转换为字典格式
        positions_data = []
        for position in positions:
            positions_data.append({
                'symbol': position.code,
                'quantity': position.quantity,
                'avg_cost': position.avg_cost,
                'last_price': position.last_price,
                'market_value': position.market_value,
                'profit_loss': position.profit_loss,
                'profit_loss_pct': position.profit_loss_pct,
                'available_quantity': position.available_quantity,
                'frozen_quantity': position.frozen_quantity,
                'created_at': position.created_at.isoformat(),
                'updated_at': position.updated_at.isoformat() if position.updated_at else None
            })
        
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
        account_info = trade_service.get_account_info(
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'success': True,
            'message': '获取账户信息成功',
            'data': account_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取账户信息失败: {str(e)}'
        }), 500


@trade_bp.route('/trades', methods=['GET'])
@require_auth
def get_trades():
    """获取成交记录"""
    try:
        # 获取查询参数
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 20)), 100)
        
        # 获取成交记录
        result = trade_service.get_trades(
            user_id=g.current_user['id'],
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
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
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': '交易服务运行正常',
        'data': {
            'service': 'trade_api',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    })








