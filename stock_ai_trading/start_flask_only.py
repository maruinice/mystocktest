#!/usr/bin/env python3
"""
纯Flask服务器启动脚本
解决FastAPI和Flask重复问题
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 导入Flask应用创建函数
        from app.main import create_flask_app, FLASK_APIS_AVAILABLE
        
        if not FLASK_APIS_AVAILABLE:
            logger.error("Flask APIs not available. Please check imports.")
            return 1
        
        # 创建Flask应用
        app = create_flask_app()
        
        if not app:
            logger.error("Failed to create Flask app")
            return 1
        
        logger.info("Flask应用创建成功")
        logger.info("启动Flask服务器...")
        
        # 启动Flask服务器
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True,
            use_reloader=True
        )
        
    except ImportError as e:
        logger.error(f"导入错误: {e}")
        logger.info("尝试安装缺失的依赖...")
        
        # 尝试安装Flask
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Flask', 'Flask-CORS'])
            logger.info("Flask依赖安装成功，请重新运行脚本")
        except Exception as install_error:
            logger.error(f"安装依赖失败: {install_error}")
            logger.info("请手动安装Flask依赖: pip install Flask Flask-CORS")
        
        return 1
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)