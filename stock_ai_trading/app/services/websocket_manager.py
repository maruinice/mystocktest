"""
WebSocket管理器服务
提供实时数据推送功能
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Set, Any, Optional
from datetime import datetime
import uuid
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class RealTimeDataType:
    """实时数据推送类型"""
    QUOTE_UPDATE = "quote_update"
    ORDER_UPDATE = "order_update"
    POSITION_UPDATE = "position_update"
    RISK_ALERT = "risk_alert"
    SYSTEM_STATUS = "system_status"
    STRATEGY_UPDATE = "strategy_update"
    AI_DECISION = "ai_decision"


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 用户连接映射: user_id -> set of websockets
        self.user_connections: Dict[str, Set] = {}
        # 连接信息映射: websocket -> user_info
        self.connection_info: Dict = {}
        # 活跃连接数
        self.active_connections = 0
        
    async def register_connection(self, websocket, user_id: str, user_info: dict = None):
        """注册新连接"""
        try:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            
            self.user_connections[user_id].add(websocket)
            self.connection_info[websocket] = {
                'user_id': user_id,
                'user_info': user_info or {},
                'connected_at': datetime.now(),
                'connection_id': str(uuid.uuid4())
            }
            
            self.active_connections += 1
            
            logger.info(f"用户 {user_id} 建立WebSocket连接，当前活跃连接数: {self.active_connections}")
            
            # 发送连接成功消息
            await self.send_to_connection(websocket, {
                'type': 'connection_established',
                'data': {
                    'user_id': user_id,
                    'connection_id': self.connection_info[websocket]['connection_id'],
                    'server_time': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"注册WebSocket连接失败: {e}")
            raise
    
    async def unregister_connection(self, websocket):
        """注销连接"""
        try:
            if websocket in self.connection_info:
                user_id = self.connection_info[websocket]['user_id']
                
                # 从用户连接集合中移除
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(websocket)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                # 移除连接信息
                del self.connection_info[websocket]
                self.active_connections -= 1
                
                logger.info(f"用户 {user_id} 断开WebSocket连接，当前活跃连接数: {self.active_connections}")
                
        except Exception as e:
            logger.error(f"注销WebSocket连接失败: {e}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """向指定用户发送消息"""
        if user_id not in self.user_connections:
            logger.warning(f"用户 {user_id} 没有活跃的WebSocket连接")
            return False
        
        success_count = 0
        failed_connections = []
        
        for websocket in self.user_connections[user_id].copy():
            try:
                await self.send_to_connection(websocket, message)
                success_count += 1
            except Exception as e:
                logger.error(f"向用户 {user_id} 发送消息失败: {e}")
                failed_connections.append(websocket)
        
        # 清理失败的连接
        for websocket in failed_connections:
            await self.unregister_connection(websocket)
        
        return success_count > 0
    
    async def send_to_connection(self, websocket, message: dict):
        """向指定连接发送消息"""
        try:
            message_str = json.dumps({
                **message,
                'timestamp': datetime.now().isoformat(),
                'server_id': 'stock-ai-trading'
            }, ensure_ascii=False)
            
            await websocket.send(message_str)
            
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket连接已关闭")
            raise
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
            raise
    
    async def broadcast_to_all(self, message: dict, exclude_user: str = None):
        """向所有用户广播消息"""
        success_count = 0
        
        for user_id in list(self.user_connections.keys()):
            if exclude_user and user_id == exclude_user:
                continue
                
            if await self.send_to_user(user_id, message):
                success_count += 1
        
        logger.info(f"广播消息给 {success_count} 个用户")
        return success_count
    
    async def send_quote_update(self, user_id: str, quote_data: dict):
        """发送行情更新"""
        message = {
            'type': RealTimeDataType.QUOTE_UPDATE,
            'data': quote_data
        }
        return await self.send_to_user(user_id, message)
    
    async def send_order_update(self, user_id: str, order_data: dict):
        """发送订单更新"""
        message = {
            'type': RealTimeDataType.ORDER_UPDATE,
            'data': order_data
        }
        return await self.send_to_user(user_id, message)
    
    async def send_position_update(self, user_id: str, position_data: dict):
        """发送持仓更新"""
        message = {
            'type': RealTimeDataType.POSITION_UPDATE,
            'data': position_data
        }
        return await self.send_to_user(user_id, message)
    
    async def send_risk_alert(self, user_id: str, alert_data: dict):
        """发送风险警报"""
        message = {
            'type': RealTimeDataType.RISK_ALERT,
            'data': alert_data
        }
        return await self.send_to_user(user_id, message)
    
    async def send_system_status(self, status_data: dict):
        """广播系统状态"""
        message = {
            'type': RealTimeDataType.SYSTEM_STATUS,
            'data': status_data
        }
        return await self.broadcast_to_all(message)
    
    async def send_strategy_update(self, user_id: str, strategy_data: dict):
        """发送策略更新"""
        message = {
            'type': RealTimeDataType.STRATEGY_UPDATE,
            'data': strategy_data
        }
        return await self.send_to_user(user_id, message)
    
    async def send_ai_decision(self, user_id: str, decision_data: dict):
        """发送AI决策"""
        message = {
            'type': RealTimeDataType.AI_DECISION,
            'data': decision_data
        }
        return await self.send_to_user(user_id, message)
    
    def get_connection_stats(self) -> dict:
        """获取连接统计信息"""
        return {
            'active_connections': self.active_connections,
            'connected_users': len(self.user_connections),
            'connections_per_user': {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            }
        }


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()


async def authenticate_websocket_connection(websocket):
    """WebSocket连接认证
    兼容 websockets 新版仅传递单参数的处理器签名。
    从 websocket.path 读取查询参数。
    """
    try:
        # 从查询参数中获取token（新版在 websocket.path 上提供路径信息）
        path = getattr(websocket, 'path', '') or ''
        query_params = parse_qs(path.split('?', 1)[1] if '?' in path else '')
        token = query_params.get('token', [None])[0]
        
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return None, None
        
        # 验证token (这里需要导入你的token验证逻辑)
        # 暂时使用简单验证，实际应该调用JWT验证
        from ..models.user_db import db_user_manager
        
        # 简单的token验证 - 实际应该使用JWT
        user = db_user_manager.verify_token(token)
        if not user:
            await websocket.close(code=4002, reason="Invalid token")
            return None, None
        
        return str(user['id']), user
        
    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        await websocket.close(code=4003, reason="Authentication failed")
        return None, None


async def websocket_handler(websocket):
    """WebSocket连接处理器（新版 websockets 仅传递 websocket 参数）"""
    user_id = None
    
    try:
        # 认证连接
        user_id, user_info = await authenticate_websocket_connection(websocket)
        if not user_id:
            return
        
        # 注册连接
        await websocket_manager.register_connection(websocket, user_id, user_info)
        
        # 保持连接并处理消息
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_websocket_message(websocket, user_id, data)
            except json.JSONDecodeError:
                logger.error(f"收到无效的JSON消息: {message}")
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket连接正常关闭: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket连接异常: {e}")
    finally:
        # 清理连接
        if user_id:
            await websocket_manager.unregister_connection(websocket)


async def handle_websocket_message(websocket, user_id: str, data: dict):
    """处理WebSocket消息"""
    try:
        message_type = data.get('type')
        payload = data.get('data', {})
        
        if message_type == 'ping':
            # 心跳检测
            await websocket_manager.send_to_connection(websocket, {
                'type': 'pong',
                'data': {'server_time': datetime.now().isoformat()}
            })
        elif message_type == 'subscribe':
            # 订阅特定数据类型
            subscription_type = payload.get('subscription_type')
            logger.info(f"用户 {user_id} 订阅 {subscription_type}")
            # 这里可以实现订阅逻辑
        elif message_type == 'unsubscribe':
            # 取消订阅
            subscription_type = payload.get('subscription_type')
            logger.info(f"用户 {user_id} 取消订阅 {subscription_type}")
            # 这里可以实现取消订阅逻辑
        else:
            logger.warning(f"未知的消息类型: {message_type}")
            
    except Exception as e:
        logger.error(f"处理WebSocket消息失败: {e}")


async def start_websocket_server(host='localhost', port=8765):
    """启动WebSocket服务器"""
    logger.info(f"启动WebSocket服务器: ws://{host}:{port}")
    
    server = await websockets.serve(
        websocket_handler,
        host,
        port,
        ping_interval=30,  # 30秒心跳
        ping_timeout=10,   # 10秒超时
        close_timeout=10   # 10秒关闭超时
    )
    
    logger.info("WebSocket服务器启动成功")
    return server


if __name__ == "__main__":
    # 测试运行
    asyncio.run(start_websocket_server())