#!/usr/bin/env python3
"""
快速启动脚本 - 简化版

一键启动股票AI交易系统的核心服务
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

def run_service(name, command, cwd=None):
    """在后台运行服务"""
    try:
        print(f"🚀 启动 {name}...")
        
        work_dir = cwd or Path(__file__).parent
        
        # 启动进程
        process = subprocess.Popen(
            command,
            cwd=work_dir,
            shell=True if os.name == 'nt' else False,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        print(f"✅ {name} 已启动 (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ 启动 {name} 失败: {e}")
        return None

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 股票AI交易系统 - 快速启动")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    processes = []
    
    try:
        # 1. 启动Flask API服务器
        flask_cmd = f"{sys.executable} run_flask.py --port 5000 --debug"
        flask_process = run_service("Flask API服务器", flask_cmd, base_dir)
        if flask_process:
            processes.append(flask_process)
        
        # 等待Flask启动
        time.sleep(3)
        
        # 2. 启动WebSocket服务器
        ws_cmd = f"{sys.executable} simple_websocket_server.py"
        ws_process = run_service("WebSocket服务器", ws_cmd, base_dir)
        if ws_process:
            processes.append(ws_process)
        
        # 等待WebSocket启动
        time.sleep(2)
        
        print("\n" + "=" * 50)
        print("🎉 所有服务已启动!")
        print("=" * 50)
        print("📊 服务地址:")
        print("  🔧 Flask API: http://localhost:5000")
        print("  📡 WebSocket: ws://localhost:8765")
        print("  📖 API文档: http://localhost:5000/docs")
        print("=" * 50)
        print("💡 提示: 各服务在独立的控制台窗口中运行")
        print("   关闭对应窗口即可停止服务")
        print("=" * 50)
        
        # 运行服务状态检查
        check_cmd = f"{sys.executable} check_services.py"
        print("\n🔍 运行服务状态检查...")
        subprocess.run(check_cmd, shell=True, cwd=base_dir)
        
    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止服务...")
        for process in processes:
            try:
                process.terminate()
            except:
                pass
    except Exception as e:
        print(f"❌ 启动过程中发生错误: {e}")

if __name__ == "__main__":
    main()