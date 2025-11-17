"""
交易相关数据模型

包括订单、持仓、成交记录等数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"      # 市价单
    LIMIT = "limit"        # 限价单
    STOP = "stop"          # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"    # 待成交
    PARTIAL = "partial"    # 部分成交
    FILLED = "filled"      # 已成交
    CANCELLED = "cancelled"  # 已撤销
    REJECTED = "rejected"  # 已拒绝


class OrderSide(Enum):
    """交易方向"""
    BUY = "buy"    # 买入
    SELL = "sell"  # 卖出


@dataclass
class Order:
    """订单模型"""
    order_id: str
    user_id: str
    code: str
    name: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float = 0.0
    stop_price: float = 0.0
    filled_quantity: int = 0
    avg_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    time_in_force: str = "day"  # day, gtc, ioc, fok
    notes: str = ""
    commission: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def remaining_quantity(self) -> int:
        """剩余数量"""
        return self.quantity - self.filled_quantity
    
    @property
    def filled_amount(self) -> float:
        """已成交金额"""
        return self.filled_quantity * self.avg_price
    
    @property
    def total_amount(self) -> float:
        """订单总金额"""
        return self.quantity * (self.price if self.price > 0 else self.avg_price)
    
    @property
    def is_buy(self) -> bool:
        """是否为买入订单"""
        return self.side == OrderSide.BUY
    
    @property
    def is_sell(self) -> bool:
        """是否为卖出订单"""
        return self.side == OrderSide.SELL
    
    @property
    def is_pending(self) -> bool:
        """是否为待成交状态"""
        return self.status == OrderStatus.PENDING
    
    @property
    def is_filled(self) -> bool:
        """是否已完全成交"""
        return self.status == OrderStatus.FILLED
    
    @property
    def is_cancelled(self) -> bool:
        """是否已撤销"""
        return self.status == OrderStatus.CANCELLED
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'user_id': self.user_id,
            'code': self.code,
            'name': self.name,
            'side': self.side.value,
            'type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'stop_price': self.stop_price,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'avg_price': self.avg_price,
            'filled_amount': self.filled_amount,
            'total_amount': self.total_amount,
            'status': self.status.value,
            'time_in_force': self.time_in_force,
            'notes': self.notes,
            'commission': self.commission,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Position:
    """持仓模型"""
    position_id: str
    user_id: str
    code: str
    name: str
    quantity: int
    available_quantity: int  # 可用数量（扣除冻结）
    avg_cost: float
    last_price: float
    market_value: float
    profit_loss: float
    profit_loss_pct: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def frozen_quantity(self) -> int:
        """冻结数量"""
        return self.quantity - self.available_quantity
    
    @property
    def cost_basis(self) -> float:
        """成本基础"""
        return self.quantity * self.avg_cost
    
    @property
    def is_profitable(self) -> bool:
        """是否盈利"""
        return self.profit_loss > 0
    
    @property
    def is_loss(self) -> bool:
        """是否亏损"""
        return self.profit_loss < 0
    
    def update_market_data(self, last_price: float):
        """更新市场数据"""
        self.last_price = last_price
        self.market_value = self.quantity * last_price
        self.profit_loss = self.market_value - self.cost_basis
        self.profit_loss_pct = (self.profit_loss / self.cost_basis * 100 
                               if self.cost_basis > 0 else 0)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'position_id': self.position_id,
            'user_id': self.user_id,
            'code': self.code,
            'name': self.name,
            'quantity': self.quantity,
            'available_quantity': self.available_quantity,
            'frozen_quantity': self.frozen_quantity,
            'avg_cost': self.avg_cost,
            'last_price': self.last_price,
            'market_value': self.market_value,
            'cost_basis': self.cost_basis,
            'profit_loss': self.profit_loss,
            'profit_loss_pct': self.profit_loss_pct,
            'is_profitable': self.is_profitable,
            'is_loss': self.is_loss,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class Trade:
    """成交记录模型"""
    trade_id: str
    order_id: str
    user_id: str
    code: str
    name: str
    side: OrderSide
    quantity: int
    price: float
    amount: float
    commission: float
    trade_time: datetime = field(default_factory=datetime.now)
    
    @property
    def net_amount(self) -> float:
        """净金额（扣除手续费）"""
        if self.side == OrderSide.BUY:
            return self.amount + self.commission  # 买入时加上手续费
        else:
            return self.amount - self.commission  # 卖出时减去手续费
    
    @property
    def is_buy(self) -> bool:
        """是否为买入成交"""
        return self.side == OrderSide.BUY
    
    @property
    def is_sell(self) -> bool:
        """是否为卖出成交"""
        return self.side == OrderSide.SELL
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'code': self.code,
            'name': self.name,
            'side': self.side.value,
            'quantity': self.quantity,
            'price': self.price,
            'amount': self.amount,
            'commission': self.commission,
            'net_amount': self.net_amount,
            'trade_time': self.trade_time.isoformat()
        }


@dataclass
class Account:
    """账户模型"""
    user_id: str
    total_assets: float = 0.0      # 总资产
    available_cash: float = 0.0    # 可用资金
    frozen_cash: float = 0.0       # 冻结资金
    market_value: float = 0.0      # 持仓市值
    profit_loss: float = 0.0       # 浮动盈亏
    profit_loss_pct: float = 0.0   # 盈亏比例
    buying_power: float = 0.0      # 购买力
    margin_used: float = 0.0       # 已用保证金
    margin_available: float = 0.0  # 可用保证金
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_cash(self) -> float:
        """总现金"""
        return self.available_cash + self.frozen_cash
    
    @property
    def asset_allocation_cash_pct(self) -> float:
        """现金资产占比"""
        return (self.total_cash / self.total_assets * 100 
                if self.total_assets > 0 else 0)
    
    @property
    def asset_allocation_stock_pct(self) -> float:
        """股票资产占比"""
        return (self.market_value / self.total_assets * 100 
                if self.total_assets > 0 else 0)
    
    @property
    def is_profitable(self) -> bool:
        """是否盈利"""
        return self.profit_loss > 0
    
    @property
    def is_loss(self) -> bool:
        """是否亏损"""
        return self.profit_loss < 0
    
    def update_market_data(self, market_value: float, profit_loss: float):
        """更新市场数据"""
        self.market_value = market_value
        self.profit_loss = profit_loss
        self.total_assets = self.total_cash + market_value
        self.profit_loss_pct = (profit_loss / (market_value - profit_loss) * 100 
                               if market_value > profit_loss else 0)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'total_assets': self.total_assets,
            'available_cash': self.available_cash,
            'frozen_cash': self.frozen_cash,
            'total_cash': self.total_cash,
            'market_value': self.market_value,
            'profit_loss': self.profit_loss,
            'profit_loss_pct': self.profit_loss_pct,
            'buying_power': self.buying_power,
            'margin_used': self.margin_used,
            'margin_available': self.margin_available,
            'asset_allocation_cash_pct': self.asset_allocation_cash_pct,
            'asset_allocation_stock_pct': self.asset_allocation_stock_pct,
            'is_profitable': self.is_profitable,
            'is_loss': self.is_loss,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class OrderBook:
    """订单簿模型"""
    code: str
    name: str
    bids: list = field(default_factory=list)  # 买盘 [(price, quantity), ...]
    asks: list = field(default_factory=list)  # 卖盘 [(price, quantity), ...]
    last_price: float = 0.0
    volume: int = 0
    turnover: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def best_bid(self) -> Optional[tuple]:
        """最优买价"""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[tuple]:
        """最优卖价"""
        return self.asks[0] if self.asks else None
    
    @property
    def spread(self) -> float:
        """买卖价差"""
        if self.best_bid and self.best_ask:
            return self.best_ask[0] - self.best_bid[0]
        return 0.0
    
    @property
    def mid_price(self) -> float:
        """中间价"""
        if self.best_bid and self.best_ask:
            return (self.best_bid[0] + self.best_ask[0]) / 2
        return self.last_price
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'bids': self.bids,
            'asks': self.asks,
            'best_bid': self.best_bid,
            'best_ask': self.best_ask,
            'spread': self.spread,
            'mid_price': self.mid_price,
            'last_price': self.last_price,
            'volume': self.volume,
            'turnover': self.turnover,
            'timestamp': self.timestamp.isoformat()
        }