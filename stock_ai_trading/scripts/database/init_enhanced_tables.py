"""
初始化增强数据表
"""
from sqlalchemy import create_engine
from database_models_enhanced import Base
from app.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_enhanced_tables():
    """创建增强数据表"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        
        # 创建所有表
        Base.metadata.create_all(engine)
        
        logger.info("增强数据表创建成功！")
        logger.info("已创建表：")
        logger.info("  - industry_classification (行业分类)")
        logger.info("  - limit_prices (涨跌停价格)")
        logger.info("  - suspend_info (停复牌信息)")
        logger.info("  - audit_opinions (审计意见)")
        
        return True
        
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        return False


if __name__ == "__main__":
    create_enhanced_tables()
