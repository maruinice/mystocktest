#!/usr/bin/env python3
"""
AI股票交易系统启动脚本
"""
import os
import sys
import logging
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault("PYTHONPATH", str(project_root))

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )

def check_dependencies():
    """检查必要的依赖"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'redis',
        'celery',
        'tushare',
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主启动函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("正在启动AI股票交易系统...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # 启动FastAPI应用
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"启动应用失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()