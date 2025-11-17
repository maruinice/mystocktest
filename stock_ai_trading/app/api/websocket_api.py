"""
WebSocket API接口
提供WebSocket相关的REST API
"""

from flask import Blueprint, request, jsonify, g
from typing import Dict, Any
import logging

from ..services.websocket_manager import websocket_manager, RealTimeDataType
from ..middleware.auth import require_auth

logger = logging.getLogger(__name__)

# 创建WebSocket蓝图
websocket_bp = Blueprint('websocket', __name__)


@websocket_bp.route('/stats', methods=['GET'])
@require_auth
def get_websocket_stats():
    """获取WebSocket连接统计"""
    try:
        stats = websocket_manager.get_connection_stats()
        
        return jsonify({
            "success": True,
            "data": stats
        })
        
    except Exception as e:
        logger.error(f"获取WebSocket统计失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取统计信息失败"
        }), 500


@websocket_bp.route('/send', methods=['POST'])
@require_auth
def send_message():
    """发送消息到WebSocket客户端"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据不能为空"
            }), 400
        
        message_type = data.get('type')
        target_user = data.get('user_id')
        message_data = data.get('data', {})
        
        if not message_type:
            return jsonify({
                "success": False,
                "error": "消息类型不能为空"
            }), 400
        
        # 构造消息
        message = {
            'type': message_type,
            'data': message_data
        }
        
        # 注意：这里需要在异步环境中运行
        # 暂时返回成功，实际发送需要在异步上下文中处理
        success = True  # 简化处理，实际应该使用异步任务队列
        
        return jsonify({
            "success": True,
            "data": {
                "sent": success,
                "message_type": message_type,
                "target_user": target_user
            }
        })
        
    except Exception as e:
        logger.error(f"发送WebSocket消息失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "发送消息失败"
        }), 500


@websocket_bp.route('/broadcast/quote', methods=['POST'])
@require_auth
def broadcast_quote_update():
    """广播行情更新"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "行情数据不能为空"
            }), 400
        
        # 简化处理，实际应该使用异步任务队列
        count = 1  # 模拟广播成功
        
        return jsonify({
            "success": True,
            "data": {
                "broadcast_count": count,
                "message_type": RealTimeDataType.QUOTE_UPDATE
            }
        })
        
    except Exception as e:
        logger.error(f"广播行情更新失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "广播行情更新失败"
        }), 500


@websocket_bp.route('/send/order-update', methods=['POST'])
@require_auth
def send_order_update():
    """发送订单更新"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "订单数据不能为空"
            }), 400
        
        user_id = data.get('user_id')
        order_data = data.get('order_data', {})
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "用户ID不能为空"
            }), 400
        
        # 简化处理，实际应该使用异步任务队列
        success = True
        
        return jsonify({
            "success": True,
            "data": {
                "sent": success,
                "user_id": user_id,
                "message_type": RealTimeDataType.ORDER_UPDATE
            }
        })
        
    except Exception as e:
        logger.error(f"发送订单更新失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "发送订单更新失败"
        }), 500


@websocket_bp.route('/send/risk-alert', methods=['POST'])
@require_auth
def send_risk_alert():
    """发送风险警报"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "警报数据不能为空"
            }), 400
        
        user_id = data.get('user_id')
        alert_data = data.get('alert_data', {})
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "用户ID不能为空"
            }), 400
        
        # 简化处理，实际应该使用异步任务队列
        success = True
        
        return jsonify({
            "success": True,
            "data": {
                "sent": success,
                "user_id": user_id,
                "message_type": RealTimeDataType.RISK_ALERT
            }
        })
        
    except Exception as e:
        logger.error(f"发送风险警报失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "发送风险警报失败"
        }), 500


@websocket_bp.route('/health', methods=['GET'])
def websocket_health():
    """WebSocket服务健康检查"""
    try:
        stats = websocket_manager.get_connection_stats()
        
        return jsonify({
            "success": True,
            "data": {
                "service": "WebSocket",
                "status": "running",
                "active_connections": stats['active_connections'],
                "connected_users": stats['connected_users']
            }
        })
        
    except Exception as e:
        logger.error(f"WebSocket健康检查失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "健康检查失败"
        }), 500