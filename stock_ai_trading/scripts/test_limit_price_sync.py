"""
测试涨跌停价格同步功能
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.sync_services.limit_price_sync import LimitPriceSyncService
from app.core.database import get_db
from sqlalchemy import text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_limit_price_sync():
    """测试涨跌停价格同步"""
    try:
        # 初始化服务
        service = LimitPriceSyncService()
        
        # 检查Tushare API是否初始化
        if not service.pro:
            logger.error("Tushare API未初始化，请检查TUSHARE_TOKEN环境变量")
            return False
        
        logger.info("Tushare API初始化成功")
        
        # 检查数据库中的现有数据
        db = next(get_db())
        try:
            count_sql = text("SELECT COUNT(*) as cnt FROM limit_prices")
            result = db.execute(count_sql).first()
            current_count = result.cnt if result else 0
            logger.info(f"当前数据库中的涨跌停价格记录数: {current_count}")
            
            # 获取最新日期
            max_date_sql = text("SELECT MAX(trade_date) as max_date FROM limit_prices")
            max_result = db.execute(max_date_sql).first()
            max_date = max_result.max_date if max_result and max_result.max_date else None
            logger.info(f"数据库中的最新日期: {max_date}")
        finally:
            db.close()
        
        # 测试向后同步（最新数据）- 只同步最近3天
        logger.info("\n=== 测试向后同步（最新数据）===")
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y%m%d')
        
        result = await service.sync(
            start_date=start_date,
            end_date=end_date,
            direction='forward',
            days=3
        )
        
        logger.info(f"同步结果: {result}")
        
        # 检查同步后的数据
        db = next(get_db())
        try:
            count_sql = text("SELECT COUNT(*) as cnt FROM limit_prices")
            count_result = db.execute(count_sql).first()
            new_count = count_result.cnt if count_result else 0
            logger.info(f"同步后数据库中的涨跌停价格记录数: {new_count}")
            logger.info(f"新增记录数: {new_count - current_count}")
            
            # 检查最近的数据
            recent_sql = text("""
                SELECT trade_date, COUNT(*) as cnt 
                FROM limit_prices 
                WHERE trade_date >= :start_date
                GROUP BY trade_date 
                ORDER BY trade_date DESC 
                LIMIT 5
            """)
            recent_result = db.execute(recent_sql, {'start_date': start_date}).fetchall()
            logger.info("最近5个交易日的数据:")
            for row in recent_result:
                logger.info(f"  日期: {row[0]}, 记录数: {row[1]}")
        finally:
            db.close()
        
        # 获取同步结果
        sync_success = result.get('success', False) if isinstance(result, dict) else False
        return sync_success
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_limit_price_sync())
    sys.exit(0 if success else 1)

