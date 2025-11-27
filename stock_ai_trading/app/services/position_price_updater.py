#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
持仓价格更新服务
定期更新所有持仓的实时价格、市值和盈亏
"""

import logging
import time
from datetime import datetime, time as dt_time
from typing import List, Dict, Any
from decimal import Decimal
import threading

from app.core.database import SessionLocal
from app.models.trading_db import DBPosition
from app.services.realtime_quote_service import realtime_quote_service
from sqlalchemy import text

logger = logging.getLogger(__name__)


class PositionPriceUpdater:
    """持仓价格更新服务"""
    
    def __init__(self, update_interval: int = 3):
        """
        初始化服务
        
        Args:
            update_interval: 更新间隔（秒），默认3秒
        """
        self.update_interval = update_interval
        self.is_running = False
        self.update_thread = None
        self.last_update_time = None
        self.update_count = 0
        self.error_count = 0
        
    def start(self):
        """启动更新服务"""
        if self.is_running:
            logger.warning("持仓价格更新服务已在运行")
            return
        
        self.is_running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        logger.info(f"持仓价格更新服务已启动，更新间隔: {self.update_interval}秒")
    
    def stop(self):
        """停止更新服务"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("持仓价格更新服务已停止")
    
    def _is_trading_time(self) -> bool:
        """
        检查是否在交易时间
        交易时间: 周一至周五 9:30-11:30, 13:00-15:00
        """
        now = datetime.now()
        
        # 周末不交易
        if now.weekday() >= 5:  # 5=周六, 6=周日
            return False
        
        current_time = now.time()
        
        # 上午交易时间 9:30-11:30
        morning_start = dt_time(9, 30)
        morning_end = dt_time(11, 30)
        
        # 下午交易时间 13:00-15:00
        afternoon_start = dt_time(13, 0)
        afternoon_end = dt_time(15, 0)
        
        return (morning_start <= current_time <= morning_end or 
                afternoon_start <= current_time <= afternoon_end)
    
    def _update_loop(self):
        """更新循环"""
        while self.is_running:
            try:
                # 只在交易时间更新（可选，如果想全天更新可以注释掉这个检查）
                # if not self._is_trading_time():
                #     logger.debug("非交易时间，跳过更新")
                #     time.sleep(60)  # 非交易时间每分钟检查一次
                #     continue
                
                # 执行更新
                self._update_all_positions()
                
                # 等待下次更新
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"持仓价格更新失败: {e}", exc_info=True)
                time.sleep(self.update_interval)
    
    def _update_all_positions(self):
        """更新所有持仓的价格"""
        db = SessionLocal()
        try:
            # 获取所有有持仓的记录
            positions = db.query(DBPosition).filter(DBPosition.quantity > 0).all()
            
            if not positions:
                logger.debug("没有持仓需要更新")
                return
            
            # 收集所有股票代码
            stock_codes = list(set([pos.stock_code for pos in positions]))
            
            # 批量获取实时价格
            prices_data = realtime_quote_service.get_batch_realtime_prices(stock_codes)
            
            # 更新每个持仓
            updated_count = 0
            for position in positions:
                try:
                    price_data = prices_data.get(position.stock_code)
                    if not price_data:
                        logger.warning(f"无法获取股票 {position.stock_code} 的实时价格")
                        continue
                    
                    current_price = price_data.get('current', 0)
                    if current_price <= 0:
                        logger.warning(f"股票 {position.stock_code} 价格无效: {current_price}")
                        continue
                    
                    # 更新价格和市值
                    position.last_price = Decimal(str(current_price))
                    position.market_value = position.quantity * position.last_price
                    position.profit_loss = position.market_value - position.cost_basis
                    
                    # 计算盈亏率
                    if position.cost_basis > 0:
                        position.profit_loss_pct = Decimal(
                            str(float(position.profit_loss) / float(position.cost_basis) * 100)
                        )
                    else:
                        position.profit_loss_pct = Decimal('0')
                    
                    position.updated_at = datetime.now()
                    updated_count += 1
                    
                    logger.debug(
                        f"更新持仓: {position.stock_code} "
                        f"价格={current_price:.3f} "
                        f"市值={float(position.market_value):.2f} "
                        f"盈亏={float(position.profit_loss):.2f}"
                    )
                    
                except Exception as e:
                    logger.error(f"更新持仓 {position.stock_code} 失败: {e}")
                    continue
            
            # 提交更新
            db.commit()
            
            self.update_count += 1
            self.last_update_time = datetime.now()
            
            logger.info(
                f"持仓价格更新完成: 更新 {updated_count}/{len(positions)} 个持仓 "
                f"(总更新次数: {self.update_count})"
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"更新所有持仓失败: {e}", exc_info=True)
            raise
        finally:
            db.close()
    
    def update_once(self) -> Dict[str, Any]:
        """
        手动触发一次更新
        
        Returns:
            更新结果统计
        """
        try:
            start_time = datetime.now()
            self._update_all_positions()
            end_time = datetime.now()
            
            return {
                'success': True,
                'update_time': self.last_update_time.isoformat() if self.last_update_time else None,
                'duration': (end_time - start_time).total_seconds(),
                'total_updates': self.update_count,
                'total_errors': self.error_count
            }
        except Exception as e:
            logger.error(f"手动更新失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_updates': self.update_count,
                'total_errors': self.error_count
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'is_running': self.is_running,
            'update_interval': self.update_interval,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'update_count': self.update_count,
            'error_count': self.error_count,
            'is_trading_time': self._is_trading_time()
        }


# 全局实例
position_price_updater = PositionPriceUpdater(update_interval=3)


if __name__ == '__main__':
    # 测试代码
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    updater = PositionPriceUpdater(update_interval=5)
    
    print("=" * 80)
    print("持仓价格更新服务测试")
    print("=" * 80)
    
    # 手动更新一次
    print("\n执行手动更新...")
    result = updater.update_once()
    print(f"更新结果: {result}")
    
    # 启动自动更新
    print("\n启动自动更新服务...")
    updater.start()
    
    # 运行30秒
    try:
        for i in range(6):
            time.sleep(5)
            status = updater.get_status()
            print(f"\n状态检查 {i+1}: {status}")
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        updater.stop()
        print("\n服务已停止")
