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

logger = logging.getLogger(__name__)


class OrderMatchingService:
    """订单撮合服务"""
    
    def __init__(self):
        """初始化服务"""
        self.data_service = DataService()
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
        # 使用DataService获取实时价格
        try:
            # 构造完整的股票代码
            stock_code = order.stock_code
            # 如果代码不包含市场后缀，尝试添加
            if '.' not in stock_code:
                # 根据代码前缀判断市场
                if stock_code.startswith('6'):
                    stock_code = f"{stock_code}.SH"
                elif stock_code.startswith(('0', '3')):
                    stock_code = f"{stock_code}.SZ"
                elif stock_code.startswith(('4', '8')):
                    stock_code = f"{stock_code}.BJ"
            
            # 获取实时行情
            quotes = self.data_service.fetch_realtime_quotes([stock_code])
            
            if not quotes or stock_code not in quotes:
                logger.warning(f"无法获取股票 {stock_code} 的实时行情")
                return
            
            quote_data = quotes[stock_code]
            current_price = quote_data.get('current_price', 0)
            
            if current_price <= 0:
                logger.warning(f"股票 {stock_code} 价格无效: {current_price}")
                return
            
            logger.info(f"股票 {stock_code} ({quote_data.get('name', '')}) 当前价: ¥{current_price:.2f}, "
                       f"涨跌: {quote_data.get('change_percent', 0):.2f}%")
            
        except Exception as e:
            logger.error(f"获取股票 {order.stock_code} 实时行情失败: {e}")
            return
        
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
                    fill_price = min(float(order.price), current_price)
            else:  # sell
                # 卖出：限价 <= 当前价
                if order.price <= current_price:
                    can_fill = True
                    fill_price = max(float(order.price), current_price)
        
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
            
            # 计算手续费
            # 1. 佣金：万分之三，最低5元
            commission_rate = Decimal('0.0003')
            commission = max(trade_amount * commission_rate, Decimal('5.00'))
            
            # 2. 印花税：卖出时收取千分之一
            stamp_duty = Decimal('0')
            if order.side == 'sell':
                stamp_duty = trade_amount * Decimal('0.001')
            
            # 3. 过户费：成交金额的万分之0.2（双向收取）
            transfer_fee = trade_amount * Decimal('0.00002')
            
            # 总手续费
            total_commission = commission + stamp_duty + transfer_fee
            
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
            order.commission = total_commission
            order.filled_at = datetime.now()
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
                # 扣除冻结资金
                frozen_amount = Decimal(str(order.quantity)) * Decimal(str(order.price))
                account.frozen_cash -= frozen_amount
                
                # 实际成交金额（含手续费）
                total_cost = trade_amount + total_commission
                actual_cash_needed = total_cost - frozen_amount
                
                # 如果实际需要的资金大于冻结资金，从可用资金中扣除差额
                if actual_cash_needed > 0:
                    if account.available_cash < actual_cash_needed:
                        logger.error(f"账户资金不足: 需要额外 {actual_cash_needed}, 可用 {account.available_cash}")
                        order.status = 'rejected'
                        # 恢复冻结资金
                        account.frozen_cash += frozen_amount
                        return
                    account.available_cash -= actual_cash_needed
                else:
                    # 如果冻结资金有剩余，返还到可用资金
                    account.available_cash += abs(actual_cash_needed)
                
                # 更新持仓
                if position:
                    # 已有持仓，更新成本
                    total_quantity = position.quantity + order.quantity
                    total_cost_value = (position.avg_cost * position.quantity + 
                                      fill_price * order.quantity)
                    position.avg_cost = total_cost_value / total_quantity
                    position.quantity = total_quantity
                    # 买入的股票T+1才能卖出，所以不增加available_quantity
                    # position.available_quantity 保持不变
                    position.frozen_quantity += order.quantity  # 标记为冻结（T+1解冻）
                    position.updated_at = datetime.now()
                else:
                    # 新建持仓
                    position = DBPosition(
                        user_id=order.user_id,
                        stock_code=order.stock_code,
                        stock_name=order.stock_name,
                        quantity=order.quantity,
                        available_quantity=0,  # T+1，今天买入的不可用
                        frozen_quantity=order.quantity,  # 标记为冻结
                        avg_cost=fill_price,
                        last_price=fill_price,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(position)
            
            else:  # sell
                # 卖出
                if not position or position.available_quantity < order.quantity:
                    logger.error(f"可用持仓不足: 需要 {order.quantity}, 可用 {position.available_quantity if position else 0}")
                    order.status = 'rejected'
                    # 恢复冻结持仓
                    if position:
                        position.available_quantity += order.quantity
                        position.frozen_quantity -= order.quantity
                    return
                
                # 解冻持仓
                position.frozen_quantity -= order.quantity
                
                # 增加资金（扣除手续费）
                total_income = trade_amount - total_commission
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
                       f"{order.quantity}股 @ ¥{fill_price:.2f}, "
                       f"手续费 ¥{total_commission:.2f} (佣金:{commission:.2f} 印花税:{stamp_duty:.2f} 过户费:{transfer_fee:.2f})")
            
        except Exception as e:
            logger.error(f"执行订单成交失败: {e}", exc_info=True)
            raise


# 全局实例
order_matching_service = OrderMatchingService()
