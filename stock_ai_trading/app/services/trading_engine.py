"""
交易执行引擎
提供统一的交易接口，支持仿真交易和实盘对接
"""

import asyncio
import uuid
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"    # 限价单
    STOP = "stop"      # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"        # 待提交
    SUBMITTED = "submitted"    # 已提交
    PARTIAL_FILLED = "partial_filled"  # 部分成交
    FILLED = "filled"         # 完全成交
    CANCELLED = "cancelled"   # 已撤销
    REJECTED = "rejected"     # 已拒绝
    EXPIRED = "expired"       # 已过期


class TradingMode(Enum):
    """交易模式"""
    SIMULATION = "simulation"  # 仿真交易
    LIVE = "live"             # 实盘交易


@dataclass
class Order:
    """订单模型"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: Decimal = Decimal('0')
    avg_fill_price: Optional[Decimal] = None
    commission: Decimal = Decimal('0')
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def remaining_quantity(self) -> Decimal:
        """剩余数量"""
        return self.quantity - self.filled_quantity

    @property
    def is_filled(self) -> bool:
        """是否完全成交"""
        return self.filled_quantity >= self.quantity

    @property
    def fill_ratio(self) -> float:
        """成交比例"""
        if self.quantity == 0:
            return 0.0
        return float(self.filled_quantity / self.quantity)


@dataclass
class Trade:
    """成交记录"""
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal = Decimal('0')
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def is_long(self) -> bool:
        """是否多头持仓"""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """是否空头持仓"""
        return self.quantity < 0

    @property
    def is_flat(self) -> bool:
        """是否平仓"""
        return self.quantity == 0


@dataclass
class AccountInfo:
    """账户信息"""
    account_id: str
    total_value: Decimal
    available_cash: Decimal
    used_margin: Decimal
    positions: Dict[str, Position] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_margin(self) -> Decimal:
        """总保证金"""
        return sum(pos.market_value for pos in self.positions.values() if pos.quantity != 0)

    @property
    def free_margin(self) -> Decimal:
        """可用保证金"""
        return self.available_cash


@dataclass
class ExecutionReport:
    """执行报告"""
    order_id: str
    execution_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    commission: Decimal
    execution_time: datetime
    slippage: Optional[Decimal] = None
    market_impact: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TradingEngineInterface(ABC):
    """交易引擎接口"""

    @abstractmethod
    async def place_order(self, order: Order) -> str:
        """下单"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取订单状态"""
        pass

    @abstractmethod
    async def get_positions(self) -> Dict[str, Position]:
        """获取持仓"""
        pass

    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        pass

    @abstractmethod
    async def get_trades(self, symbol: Optional[str] = None, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """获取成交记录"""
        pass


class BaseTradingEngine(TradingEngineInterface):
    """交易引擎基类"""

    def __init__(self, mode: TradingMode, config: Dict[str, Any] = None):
        self.mode = mode
        self.config = config or {}
        self.orders: Dict[str, Order] = {}
        self.trades: List[Trade] = []
        self.positions: Dict[str, Position] = {}
        self.account: Optional[AccountInfo] = None
        self.is_running = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    async def start(self):
        """启动引擎"""
        self.is_running = True
        self.logger.info(f"交易引擎启动 - 模式: {self.mode.value}")

    async def stop(self):
        """停止引擎"""
        self.is_running = False
        self.logger.info("交易引擎停止")

    def generate_order_id(self) -> str:
        """生成订单ID"""
        return f"order_{uuid.uuid4().hex[:8]}_{int(time.time())}"

    def generate_trade_id(self) -> str:
        """生成成交ID"""
        return f"trade_{uuid.uuid4().hex[:8]}_{int(time.time())}"

    async def validate_order(self, order: Order) -> bool:
        """验证订单"""
        if not order.symbol:
            raise ValueError("股票代码不能为空")
        
        if order.quantity <= 0:
            raise ValueError("订单数量必须大于0")
        
        if order.order_type == OrderType.LIMIT and (not order.price or order.price <= 0):
            raise ValueError("限价单必须指定有效价格")
        
        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and (not order.stop_price or order.stop_price <= 0):
            raise ValueError("止损单必须指定有效止损价格")
        
        return True

    async def update_order_status(self, order_id: str, status: OrderStatus, 
                                 filled_quantity: Optional[Decimal] = None,
                                 avg_fill_price: Optional[Decimal] = None):
        """更新订单状态"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        order.status = status
        order.updated_at = datetime.now()
        
        if filled_quantity is not None:
            order.filled_quantity = filled_quantity
        
        if avg_fill_price is not None:
            order.avg_fill_price = avg_fill_price
        
        self.logger.info(f"订单状态更新: {order_id} -> {status.value}")
        return True

    async def add_trade(self, trade: Trade):
        """添加成交记录"""
        self.trades.append(trade)
        
        # 更新持仓
        await self.update_position(trade)
        
        self.logger.info(f"新增成交: {trade.trade_id} - {trade.symbol} {trade.side.value} {trade.quantity}@{trade.price}")

    async def update_position(self, trade: Trade):
        """更新持仓"""
        symbol = trade.symbol
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=Decimal('0'),
                avg_cost=Decimal('0'),
                market_value=Decimal('0'),
                unrealized_pnl=Decimal('0')
            )
        
        position = self.positions[symbol]
        
        # 计算新的持仓数量和成本
        if trade.side == OrderSide.BUY:
            new_quantity = position.quantity + trade.quantity
            if new_quantity != 0:
                position.avg_cost = (position.avg_cost * position.quantity + trade.price * trade.quantity) / new_quantity
            position.quantity = new_quantity
        else:  # SELL
            position.quantity -= trade.quantity
            # 计算已实现盈亏
            if position.quantity >= 0:
                realized_pnl = (trade.price - position.avg_cost) * trade.quantity
                position.realized_pnl += realized_pnl
        
        position.updated_at = datetime.now()

    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取订单状态"""
        return self.orders.get(order_id)

    async def get_positions(self) -> Dict[str, Position]:
        """获取持仓"""
        return self.positions.copy()

    async def get_trades(self, symbol: Optional[str] = None, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> List[Trade]:
        """获取成交记录"""
        trades = self.trades
        
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        
        if start_time:
            trades = [t for t in trades if t.timestamp >= start_time]
        
        if end_time:
            trades = [t for t in trades if t.timestamp <= end_time]
        
        return trades

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_orders = len(self.orders)
        filled_orders = len([o for o in self.orders.values() if o.status == OrderStatus.FILLED])
        total_trades = len(self.trades)
        
        return {
            "total_orders": total_orders,
            "filled_orders": filled_orders,
            "fill_rate": filled_orders / total_orders if total_orders > 0 else 0,
            "total_trades": total_trades,
            "positions_count": len([p for p in self.positions.values() if not p.is_flat]),
            "mode": self.mode.value,
            "is_running": self.is_running
        }