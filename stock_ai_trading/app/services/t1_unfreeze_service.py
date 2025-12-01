"""
T+1持仓解冻服务
每日开盘前自动解冻前一交易日买入的股票
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.trading_db import DBPosition

logger = logging.getLogger(__name__)


class T1UnfreezeService:
    """T+1持仓解冻服务"""
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def unfreeze_positions(self):
        """解冻所有T+1持仓"""
        db = next(get_db())
        try:
            # 查询所有有冻结持仓的记录
            positions = db.query(DBPosition).filter(
                DBPosition.frozen_quantity > 0
            ).all()
            
            if not positions:
                logger.info("没有需要解冻的持仓")
                return
            
            unfrozen_count = 0
            for position in positions:
                # 检查是否满足T+1条件（更新时间是否超过1个交易日）
                # 简化处理：如果更新时间是昨天或更早，就解冻
                if position.updated_at.date() < datetime.now().date():
                    # 解冻持仓
                    position.available_quantity += position.frozen_quantity
                    position.frozen_quantity = 0
                    position.updated_at = datetime.now()
                    unfrozen_count += 1
                    logger.info(f"解冻持仓: {position.stock_code} ({position.stock_name}), "
                              f"数量: {position.available_quantity}")
            
            db.commit()
            logger.info(f"T+1解冻完成，共解冻 {unfrozen_count} 个持仓")
            
        except Exception as e:
            db.rollback()
            logger.error(f"T+1解冻失败: {e}", exc_info=True)
        finally:
            db.close()


# 全局实例
t1_unfreeze_service = T1UnfreezeService()
