"""
订单撮合服务
模拟Paper交易的订单撮合，自动成交待成交订单
"""

import time
import threading
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.trading_db import DBOrder, DBPosition, DBAccount
from .data_service import DataService
from .realtime_quote_service import RealtimeQuoteService

logger = logging.getLogger(__name__)


class OrderMatchingService:
    """订单撮合服务"""
    
    def __init__(self):
        """初始化服务"""
        self.data_service = DataService()
        self.realtime_quote_service = RealtimeQuoteService()  # 实时行情服务
        self.is_running = False
        self.matching_thread = None
    
    def start(self):
        """启动撮合服务"""
        if self.is_running:
            logger.warning("订单撮合服务已在运行")
            return
        
        self.is_running = True
        self.matching_thread = threading.Thread(target=self._matching_loop, daemon=True)
        self.matching_thread.start()
        logger.info("订单撮合服务已启动")
    
    def stop(self):
        """停止撮合服务"""
        self.is_running = False
        if self.matching_thread:
            self.matching_thread.join(timeout=10)
        logger.info("订单撮合服务已停止")
    
    def _matching_loop(self):
        """撮合循环"""
        while self.is_running:
            try:
                # 每5秒检查一次待成交订单
                time.sleep(5)
                
                # 检查是否在交易时间
                is_trading, _ = self.data_service.is_trading_time()
                if not is_trading:
                    continue
                
                # 处理待成交订单
                self._process_pending_orders()
                
            except Exception as e:
                logger.error(f"订单撮合循环出错: {e}", exc_info=True)
    
    def _process_pending_orders(self):
        """处理待成交订单"""
        db = next(get_db())
        try:
            # 查询所有待成交订单
            pending_orders = db.query(DBOrder).filter(
                DBOrder.status == 'pending'
            ).all()
            
            if not pending_orders:
                return
            
            logger.info(f"发现 {len(pending_orders)} 个待成交订单")
            
            for order in pending_orders:
                try:
                    self._match_order(db, order)
                except Exception as e:
                    logger.error(f"撮合订单 {order.order_id} 失败: {e}", exc_info=True)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"处理待成交订单失败: {e}", exc_info=True)
        finally:
            db.close()
    
    def _match_order(self, db: Session, order: DBOrder):
        """撮合单个订单"""
        # 使用实时行情服务获取价格
        quote_data = self.realtime_quote_service.get_realtime_price(order.stock_code)
        
        if not quote_data:
            logger.warning(f"无法获取股票 {order.stock_code} 的实时行情")
            return
        
        current_price = quote_data.get('current', 0)
        if current_price <= 0:
            logger.warning(f"股票 {order.stock_code} 价格无效: {current_price}")
            return
        
        logger.info(f"股票 {order.stock_code} ({quote_data.get('name', '')}) 当前价: ¥{current_price:.2f}, "
                   f"涨跌: {quote_data.get('change_pct', 0):.2f}%")
        
        # 判断是否可以成交
        can_fill = False
        fill_price = None
        
        if order.order_type == 'market':
            # 市价单立即成交
            can_fill = True
            fill_price = current_price
        elif order.order_type == 'limit':
            # 限价单判断价格
            if order.side == 'buy':
                # 买入：限价 >= 当前价
                if order.price >= current_price:
                    can_fill = True
                    fill_price = min(order.price, current_price)
            else:  # sell
                # 卖出：限价 <= 当前价
                if order.price <= current_price:
                    can_fill = True
                    fill_price = max(order.price, current_price)
        
        if not can_fill:
            return
        
        # 执行成交
        self._fill_order(db, order, fill_price)
    
    def _fill_order(self, db: Session, order: DBOrder, fill_price: float):
        """执行订单成交"""
        try:
            # 将价格转换为Decimal
            fill_price = Decimal(str(fill_price))
            
            # 计算交易金额
            trade_amount = fill_price * order.quantity
            
            # 计算手续费（万分之三）
            commission = trade_amount * Decimal('0.0003')
            
            # 获取账户
            account = db.query(DBAccount).filter(
                DBAccount.user_id == order.user_id
            ).first()
            
            if not account:
                logger.error(f"用户 {order.user_id} 账户不存在")
                return
            
            # 更新订单状态
            order.status = 'filled'
            order.filled_quantity = order.quantity
            order.avg_price = fill_price
            order.commission = commission
            order.updated_at = datetime.now()
            
            # 更新持仓
            position = db.query(DBPosition).filter(
                and_(
                    DBPosition.user_id == order.user_id,
                    DBPosition.stock_code == order.stock_code
                )
            ).first()
            
            if order.side == 'buy':
                # 买入
                # 扣除资金
                total_cost = trade_amount + commission
                if account.available_cash < total_cost:
                    logger.error(f"账户资金不足: 需要 {total_cost}, 可用 {account.available_cash}")
                    order.status = 'rejected'
                    return
                
                account.available_cash -= total_cost
                
                # 更新持仓
                if position:
                    # 已有持仓，更新成本
                    total_quantity = position.quantity + order.quantity
                    total_cost_value = (position.avg_cost * position.quantity + 
                                      fill_price * order.quantity)
                    position.avg_cost = total_cost_value / total_quantity
                    position.quantity = total_quantity
                    position.updated_at = datetime.now()
                else:
                    # 新建持仓
                    position = DBPosition(
                        user_id=order.user_id,
                        stock_code=order.stock_code,
                        stock_name=order.stock_name,
                        quantity=order.quantity,
                        available_quantity=order.quantity,  # 设置可用数量
                        avg_cost=fill_price,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(position)
            
            else:  # sell
                # 卖出
                if not position or position.quantity < order.quantity:
                    logger.error(f"持仓不足: 需要 {order.quantity}, 持有 {position.quantity if position else 0}")
                    order.status = 'rejected'
                    return
                
                # 增加资金
                total_income = trade_amount - commission
                account.available_cash += total_income
                
                # 更新持仓
                position.quantity -= order.quantity
                position.updated_at = datetime.now()
                
                # 如果持仓清空，删除记录
                if position.quantity == 0:
                    db.delete(position)
            
            # 更新账户总资产
            account.updated_at = datetime.now()
            
            logger.info(f"订单 {order.order_id} 成交: {order.stock_code} {order.side} "
                       f"{order.quantity}股 @ ¥{fill_price:.2f}, 手续费 ¥{commission:.2f}")
            
        except Exception as e:
            logger.error(f"执行订单成交失败: {e}", exc_info=True)
            raise


# 全局实例
order_matching_service = OrderMatchingService()
