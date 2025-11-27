#!/usr/bin/env python3
"""
手动触发订单撮合测试脚本
用于测试订单撮合功能，不受交易时间限制
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db
from app.models.trading_db import DBOrder
from app.services.order_matching_service import OrderMatchingService
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("开始手动触发订单撮合...")
    
    # 创建撮合服务实例
    matching_service = OrderMatchingService()
    
    # 查询待成交订单
    db = next(get_db())
    try:
        pending_orders = db.query(DBOrder).filter(
            DBOrder.status == 'pending'
        ).all()
        
        logger.info(f"发现 {len(pending_orders)} 个待成交订单")
        
        if not pending_orders:
            logger.info("没有待成交订单")
            return
        
        # 显示订单信息
        for order in pending_orders:
            logger.info(f"订单 {order.order_id}: {order.stock_code} {order.side} "
                       f"{order.quantity}股 @ ¥{order.price} ({order.order_type})")
        
        # 手动处理每个订单（不检查交易时间）
        for order in pending_orders:
            # 为每个订单创建独立的数据库会话
            db_order = next(get_db())
            try:
                logger.info(f"处理订单 {order.order_id}...")
                # 重新查询订单以确保在新会话中
                order_to_process = db_order.query(DBOrder).filter(
                    DBOrder.order_id == order.order_id
                ).first()
                
                if order_to_process:
                    matching_service._match_order(db_order, order_to_process)
                    db_order.commit()
                    logger.info(f"订单 {order.order_id} 处理完成")
            except Exception as e:
                db_order.rollback()
                logger.error(f"处理订单 {order.order_id} 失败: {e}", exc_info=True)
            finally:
                db_order.close()
        
        logger.info("订单撮合完成")
        
        # 查询更新后的订单状态
        db_check = next(get_db())
        try:
            for order in pending_orders:
                updated_order = db_check.query(DBOrder).filter(
                    DBOrder.order_id == order.order_id
                ).first()
                if updated_order:
                    logger.info(f"订单 {order.order_id} 状态: {updated_order.status}")
        finally:
            db_check.close()
        
    except Exception as e:
        db.rollback()
        logger.error(f"订单撮合失败: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == '__main__':
    main()
