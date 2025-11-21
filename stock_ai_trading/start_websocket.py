#!/usr/bin/env python3
"""
WebSocket服务器启动脚本
"""

import asyncio
import logging
import signal
import sys
import os
from app.services.websocket_manager import start_websocket_server

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def main():
    """主函数"""
    try:
        logger.info("正在启动WebSocket服务器...")

        # 从环境变量读取端口，默认为 8765
        port = int(os.environ.get('WS_PORT', '8765'))

        # 启动WebSocket服务器
        server = await start_websocket_server(host='0.0.0.0', port=port)

        logger.info(f"WebSocket服务器启动成功，监听端口: {port}")
        logger.info(f"WebSocket URL: ws://localhost:{port}")
        
        # 等待服务器运行
        await server.wait_closed()
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭WebSocket服务器...")
    except Exception as e:
        logger.error(f"WebSocket服务器启动失败: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    """信号处理器"""
    logger.info("收到停止信号，正在关闭服务器...")
    sys.exit(0)

if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("WebSocket服务器已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)