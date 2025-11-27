#!/usr/bin/env python3
"""
一键启动迅龙AI股票交易系统所有后端服务

包含以下服务：
1. Flask API服务器 (端口5000)
2. WebSocket服务器 (端口8765)
3. 可选：Redis服务器 (端口6379)
4. 可选：数据库服务 (如果需要)
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.services = {}
        self.running = True
        self.base_dir = Path(__file__).parent
        
    def start_service(self, name, command, cwd=None, env=None):
        """启动服务"""
        try:
            logger.info(f"正在启动服务: {name}")
            
            # 设置工作目录
            work_dir = cwd or self.base_dir
            
            # 设置环境变量
            service_env = os.environ.copy()
            if env:
                service_env.update(env)
            
            # 启动进程
            process = subprocess.Popen(
                command,
                cwd=work_dir,
                env=service_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.services[name] = {
                'process': process,
                'command': command,
                'start_time': datetime.now()
            }
            
            # 启动日志监控线程
            log_thread = threading.Thread(
                target=self._monitor_service_logs,
                args=(name, process),
                daemon=True
            )
            log_thread.start()
            
            logger.info(f"✅ 服务 {name} 启动成功 (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动服务 {name} 失败: {e}")
            return False
    
    def _monitor_service_logs(self, name, process):
        """监控服务日志"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    logger.info(f"[{name}] {line.strip()}")
                if not self.running:
                    break
        except Exception as e:
            logger.error(f"监控服务 {name} 日志失败: {e}")
    
    def stop_all_services(self):
        """停止所有服务"""
        logger.info("正在停止所有服务...")
        self.running = False
        
        for name, service_info in self.services.items():
            try:
                process = service_info['process']
                if process.poll() is None:  # 进程仍在运行
                    logger.info(f"正在停止服务: {name}")
                    
                    # 尝试优雅关闭
                    process.terminate()
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=5)
                        logger.info(f"✅ 服务 {name} 已停止")
                    except subprocess.TimeoutExpired:
                        # 强制杀死进程
                        process.kill()
                        process.wait()
                        logger.warning(f"⚠️ 强制停止服务: {name}")
                        
            except Exception as e:
                logger.error(f"停止服务 {name} 失败: {e}")
    
    def check_service_status(self):
        """检查服务状态"""
        logger.info("\n=== 服务状态检查 ===")
        
        for name, service_info in self.services.items():
            process = service_info['process']
            start_time = service_info['start_time']
            uptime = datetime.now() - start_time
            
            if process.poll() is None:
                logger.info(f"✅ {name}: 运行中 (PID: {process.pid}, 运行时间: {uptime})")
            else:
                logger.error(f"❌ {name}: 已停止 (退出码: {process.returncode})")
    
    def wait_for_services(self):
        """等待服务运行"""
        try:
            logger.info("所有服务已启动，按 Ctrl+C 停止所有服务")
            
            while self.running:
                time.sleep(1)
                
                # 检查是否有服务意外退出
                for name, service_info in self.services.items():
                    process = service_info['process']
                    if process.poll() is not None:
                        logger.error(f"❌ 服务 {name} 意外退出 (退出码: {process.returncode})")
                        self.running = False
                        break
                        
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            self.stop_all_services()

def check_python_environment():
    """检查Python环境"""
    logger.info("检查Python环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("❌ 需要Python 3.8或更高版本")
        return False
    
    logger.info(f"✅ Python版本: {sys.version}")
    
    # 检查必要的包
    required_packages = ['flask', 'websockets', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package}: 已安装")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package}: 未安装")
    
    if missing_packages:
        logger.error(f"请安装缺失的包: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_ports():
    """检查端口占用情况"""
    import socket
    
    ports_to_check = [5000, 8765]
    occupied_ports = []
    
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                occupied_ports.append(port)
                logger.warning(f"⚠️ 端口 {port} 已被占用")
            else:
                logger.info(f"✅ 端口 {port} 可用")
        except Exception as e:
            logger.error(f"检查端口 {port} 失败: {e}")
        finally:
            sock.close()
    
    if occupied_ports:
        logger.warning(f"以下端口被占用: {occupied_ports}")
        response = input("是否继续启动服务? (y/N): ")
        if response.lower() != 'y':
            return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 迅龙AI股票交易系统 - 一键启动所有后端服务")
    print("=" * 60)
    
    # 检查环境
    if not check_python_environment():
        sys.exit(1)
    
    # 检查端口
    if not check_ports():
        sys.exit(1)
    
    # 创建服务管理器
    manager = ServiceManager()
    
    # 注册信号处理器
    def signal_handler(signum, frame):
        logger.info("收到停止信号")
        manager.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("开始启动所有服务...")
        
        # 1. 启动Flask API服务器
        flask_success = manager.start_service(
            name="Flask API服务器",
            command=[sys.executable, "run_flask.py", "--port", "5000", "--debug"],
            cwd=manager.base_dir
        )
        
        if not flask_success:
            logger.error("Flask API服务器启动失败，退出")
            sys.exit(1)
        
        # 等待Flask服务器启动
        time.sleep(3)
        
        # 2. 启动WebSocket服务器
        websocket_success = manager.start_service(
            name="WebSocket服务器",
            command=[sys.executable, "simple_websocket_server.py"],
            cwd=manager.base_dir
        )
        
        if not websocket_success:
            logger.error("WebSocket服务器启动失败")
        
        # 等待WebSocket服务器启动
        time.sleep(2)
        
        # 3. 可选：启动其他服务
        # 如果有Redis或其他服务，可以在这里添加
        
        # 显示启动结果
        print("\n" + "=" * 60)
        print("🎉 服务启动完成!")
        print("=" * 60)
        print("📊 服务地址:")
        print("  🔧 Flask API服务器: http://localhost:5000")
        print("  📡 WebSocket服务器: ws://localhost:8765")
        print("  📖 API文档: http://localhost:5000/docs")
        print("=" * 60)
        
        # 检查服务状态
        manager.check_service_status()
        
        # 等待服务运行
        manager.wait_for_services()
        
    except Exception as e:
        logger.error(f"启动服务时发生错误: {e}")
        manager.stop_all_services()
        sys.exit(1)
    
    logger.info("所有服务已停止")

if __name__ == "__main__":
    main()