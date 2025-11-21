"""
基于数据库的交易服务
提供订单管理、持仓管理、账户信息等功能（使用真实数据库）
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import uuid
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..core.database import get_db
from ..models.trading_db import DBAccount, DBPosition, DBOrder
from ..models.stock_models import StockBasic

logger = logging.getLogger(__name__)


class DatabaseTradeService:
    """基于数据库的交易服务类"""
    
    def __init__(self):
        """初始化服务"""
        pass
    
    def _get_or_create_account(self, db: Session, user_id: str) -> DBAccount:
        """获取或创建账户"""
        user_id_int = int(user_id)
        account = db.query(DBAccount).filter(DBAccount.user_id == user_id_int).first()
        
        if not account:
            # 创建新账户，初始资金10万
            account = DBAccount(
                user_id=user_id_int,
                total_assets=Decimal('100000.00'),
                available_cash=Decimal('100000.00'),
                buying_power=Decimal('100000.00')
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"为用户 {user_id} 创建新账户，初始资金 100000.00")
        
        return account
    
    def get_account_info(self, user_id: str) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            db = next(get_db())
            account = self._get_or_create_account(db, user_id)
            
            # 更新持仓市值和盈亏
            positions = db.query(DBPosition).filter(
                DBPosition.user_id == int(user_id),
                DBPosition.quantity > 0
            ).all()
            
            total_market_value = sum(float(pos.market_value) for pos in positions)
            total_profit_loss = sum(float(pos.profit_loss) for pos in positions)
            
            # 更新账户
            account.market_value = Decimal(str(total_market_value))
            account.profit_loss = Decimal(str(total_profit_loss))
            account.total_assets = account.available_cash + account.frozen_cash + account.market_value
            
            if total_market_value > total_profit_loss:
                account.profit_loss_pct = Decimal(str(total_profit_loss / (total_market_value - total_profit_loss) * 100))
            else:
                account.profit_loss_pct = Decimal('0')
            
            account.updated_at = datetime.now()
            db.commit()
            
            return account.to_dict()
            
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}", exc_info=True)
            raise
        finally:
            db.close()
    
    def get_positions(self, user_id: str, code: str = '') -> List[DBPosition]:
        """获取持仓列表"""
        try:
            db = next(get_db())
            query = db.query(DBPosition).filter(DBPosition.user_id == int(user_id))
            
            if code:
                query = query.filter(DBPosition.stock_code == code)
            
            # 只返回有持仓的
            positions = query.filter(DBPosition.quantity > 0).all()
            
            # 更新实时价格（这里简化处理，实际应该从行情服务获取）
            for position in positions:
                # TODO: 从行情服务获取实时价格
                position.market_value = Decimal(str(position.quantity)) * position.last_price
                position.cost_basis = Decimal(str(position.quantity)) * position.avg_cost
                position.profit_loss = position.market_value - position.cost_basis
                
                if position.cost_basis > 0:
                    position.profit_loss_pct = Decimal(str(float(position.profit_loss) / float(position.cost_basis) * 100))
                else:
                    position.profit_loss_pct = Decimal('0')
            
            db.commit()
            return positions
            
        except Exception as e:
            logger.error(f"获取持仓列表失败: {e}", exc_info=True)
            return []
        finally:
            db.close()
    
    def get_orders(self, user_id: str, status: str = '', code: str = '',
                  page: int = 1, size: int = 20) -> Tuple[List[DBOrder], int]:
        """获取订单列表"""
        try:
            db = next(get_db())
            query = db.query(DBOrder).filter(DBOrder.user_id == int(user_id))
            
            if status:
                query = query.filter(DBOrder.status == status)
            
            if code:
                query = query.filter(DBOrder.stock_code == code)
            
            # 获取总数
            total = query.count()
            
            # 分页
            orders = query.order_by(desc(DBOrder.created_at)).offset((page - 1) * size).limit(size).all()
            
            return orders, total
            
        except Exception as e:
            logger.error(f"获取订单列表失败: {e}", exc_info=True)
            return [], 0
        finally:
            db.close()
    
    def place_order(self, user_id: int, symbol: str, side: str, order_type: str,
                   quantity: int, price: float = None) -> Dict[str, Any]:
        """
        下单
        
        Args:
            user_id: 用户ID
            symbol: 股票代码（如603387.SH）
            side: 方向（buy/sell）
            order_type: 订单类型（limit/market）
            quantity: 数量
            price: 价格（限价单必须）
            
        Returns:
            订单信息字典
        """
        try:
            db = next(get_db())
            user_id_str = str(user_id)
            user_id_int = int(user_id_str)
            
            # 去掉后缀：603387.SH -> 603387
            code = symbol.split('.')[0] if '.' in symbol else symbol
            
            # 获取股票名称
            stock = db.query(StockBasic).filter(StockBasic.symbol == code).first()
            stock_name = stock.name if stock else f'股票{code}'
            
            # 检查账户
            account = self._get_or_create_account(db, user_id_str)
            
            # 估算订单金额
            estimated_price = price if price else 10.0  # 市价单使用估算价
            estimated_amount = quantity * estimated_price
            
            # 买入检查资金
            if side.lower() == 'buy':
                if float(account.available_cash) < estimated_amount:
                    raise ValueError(f"可用资金不足: {account.available_cash} < {estimated_amount}")
            
            # 卖出检查持仓
            if side.lower() == 'sell':
                position = db.query(DBPosition).filter(
                    DBPosition.user_id == user_id_int,
                    DBPosition.stock_code == code
                ).first()
                
                if not position or position.available_quantity < quantity:
                    available = position.available_quantity if position else 0
                    raise ValueError(f"可用持仓不足: {available} < {quantity}")
            
            # 创建订单
            order = DBOrder(
                order_id=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}",
                user_id=user_id_int,
                stock_code=code,
                stock_name=stock_name,
                side=side.lower(),
                order_type=order_type.lower(),
                quantity=quantity,
                price=Decimal(str(price)) if price else Decimal('0'),
                status='pending'
            )
            
            db.add(order)
            
            # 冻结资金或持仓
            if side.lower() == 'buy':
                account.available_cash -= Decimal(str(estimated_amount))
                account.frozen_cash += Decimal(str(estimated_amount))
            else:
                position = db.query(DBPosition).filter(
                    DBPosition.user_id == user_id_int,
                    DBPosition.stock_code == code
                ).first()
                if position:
                    position.available_quantity -= quantity
                    position.frozen_quantity += quantity
            
            db.commit()
            db.refresh(order)
            
            logger.info(f"订单创建成功: {order.order_id}, 用户: {user_id}, 股票: {code}, 方向: {side}, 数量: {quantity}")
            
            return order.to_dict()
            
        except Exception as e:
            db.rollback()
            logger.error(f"下单失败: {e}", exc_info=True)
            raise
        finally:
            db.close()
    
    def cancel_order(self, user_id: str, order_id: str) -> bool:
        """撤销订单"""
        try:
            db = next(get_db())
            order = db.query(DBOrder).filter(
                DBOrder.order_id == order_id,
                DBOrder.user_id == int(user_id)
            ).first()
            
            if not order:
                return False
            
            if order.status not in ['pending', 'partial']:
                return False
            
            # 更新订单状态
            order.status = 'cancelled'
            order.updated_at = datetime.now()
            
            # 释放冻结资金或持仓
            account = db.query(DBAccount).filter(DBAccount.user_id == int(user_id)).first()
            if account and order.side == 'buy':
                unfilled_amount = (order.quantity - order.filled_quantity) * float(order.price)
                account.available_cash += Decimal(str(unfilled_amount))
                account.frozen_cash -= Decimal(str(unfilled_amount))
            elif order.side == 'sell':
                position = db.query(DBPosition).filter(
                    DBPosition.user_id == int(user_id),
                    DBPosition.stock_code == order.stock_code
                ).first()
                if position:
                    unfilled_quantity = order.quantity - order.filled_quantity
                    position.available_quantity += unfilled_quantity
                    position.frozen_quantity -= unfilled_quantity
            
            db.commit()
            logger.info(f"订单撤销成功: {order_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"撤销订单失败: {e}", exc_info=True)
            return False
        finally:
            db.close()


# 全局实例
db_trade_service = DatabaseTradeService()

