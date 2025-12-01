"""
交易系统数据库模型
定义订单、持仓、账户的SQLAlchemy模型
"""

from sqlalchemy import Column, BigInteger, Integer, String, Enum, DECIMAL, TIMESTAMP, Text, ForeignKey, Index
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from ..core.database import Base

# 导入User模型，确保SQLAlchemy能够识别外键关系
try:
    from .user_db import User
except ImportError:
    pass  # 如果导入失败，继续执行


class DBAccount(Base):
    """账户数据库模型"""
    __tablename__ = 'accounts'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, comment='用户ID')
    total_assets = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='总资产')
    available_cash = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='可用资金')
    frozen_cash = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='冻结资金')
    market_value = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='持仓市值')
    profit_loss = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='浮动盈亏')
    profit_loss_pct = Column(DECIMAL(10, 4), nullable=False, default=0.0000, comment='盈亏比例(%)')
    buying_power = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='购买力')
    margin_used = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='已用保证金')
    margin_available = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='可用保证金')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'user_id': str(self.user_id),
            'total_assets': float(self.total_assets),
            'available_cash': float(self.available_cash),
            'frozen_cash': float(self.frozen_cash),
            'market_value': float(self.market_value),
            'profit_loss': float(self.profit_loss),
            'profit_loss_pct': float(self.profit_loss_pct),
            'total_pnl': float(self.profit_loss),
            'total_pnl_ratio': float(self.profit_loss_pct),
            'buying_power': float(self.buying_power),
            'margin_used': float(self.margin_used),
            'margin_available': float(self.margin_available),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DBPosition(Base):
    """持仓数据库模型"""
    __tablename__ = 'positions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    stock_name = Column(String(50), nullable=False, comment='股票名称')
    quantity = Column(Integer, nullable=False, default=0, comment='持仓数量')
    available_quantity = Column(Integer, nullable=False, default=0, comment='可用数量')
    frozen_quantity = Column(Integer, nullable=False, default=0, comment='冻结数量')
    avg_cost = Column(DECIMAL(10, 3), nullable=False, comment='平均成本')
    last_price = Column(DECIMAL(10, 3), nullable=False, default=0.000, comment='最新价格')
    market_value = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='市值')
    cost_basis = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='成本基础')
    profit_loss = Column(DECIMAL(20, 2), nullable=False, default=0.00, comment='浮动盈亏')
    profit_loss_pct = Column(DECIMAL(10, 4), nullable=False, default=0.0000, comment='盈亏比例(%)')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='建仓时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    
    __table_args__ = (
        Index('uk_user_stock', 'user_id', 'stock_code', unique=True),
        Index('idx_user_id', 'user_id'),
        Index('idx_stock_code', 'stock_code'),
        Index('idx_updated_at', 'updated_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'symbol': self.stock_code,
            'code': self.stock_code,
            'name': self.stock_name,
            'quantity': self.quantity,
            'available_quantity': self.available_quantity,
            'frozen_quantity': self.frozen_quantity,
            'avg_cost': float(self.avg_cost),
            'last_price': float(self.last_price),
            'market_value': float(self.market_value),
            'cost_basis': float(self.cost_basis),
            'profit_loss': float(self.profit_loss),
            'profit_loss_pct': float(self.profit_loss_pct),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DBOrder(Base):
    """订单数据库模型"""
    __tablename__ = 'orders'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, comment='订单号')
    user_id = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    stock_name = Column(String(50), nullable=False, comment='股票名称')
    side = Column(Enum('buy', 'sell'), nullable=False, comment='买卖方向')
    order_type = Column(Enum('market', 'limit', 'stop', 'stop_limit'), nullable=False, default='limit', comment='订单类型')
    quantity = Column(Integer, nullable=False, comment='委托数量')
    price = Column(DECIMAL(10, 3), nullable=False, default=0.000, comment='委托价格')
    stop_price = Column(DECIMAL(10, 3), default=0.000, comment='止损价格')
    filled_quantity = Column(Integer, nullable=False, default=0, comment='已成交数量')
    avg_price = Column(DECIMAL(10, 3), nullable=False, default=0.000, comment='成交均价')
    status = Column(Enum('pending', 'partial', 'filled', 'cancelled', 'rejected'), nullable=False, default='pending', comment='订单状态')
    time_in_force = Column(String(10), default='day', comment='有效期')
    commission = Column(DECIMAL(10, 2), default=0.00, comment='手续费')
    notes = Column(Text, comment='备注')
    strategy_id = Column(BigInteger, ForeignKey('trading_strategies.id', ondelete='SET NULL'), comment='策略ID')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')
    filled_at = Column(TIMESTAMP, nullable=True, comment='成交时间')
    
    __table_args__ = (
        Index('idx_order_id', 'order_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_stock_code', 'stock_code'),
        Index('idx_status', 'status'),
        Index('idx_side', 'side'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_user_stock', 'user_id', 'stock_code'),
        Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'user_id': str(self.user_id),
            'symbol': self.stock_code,
            'code': self.stock_code,
            'name': self.stock_name,
            'side': self.side,
            'order_type': self.order_type,
            'quantity': self.quantity,
            'price': float(self.price),
            'stop_price': float(self.stop_price) if self.stop_price else 0.0,
            'filled_quantity': self.filled_quantity,
            'avg_price': float(self.avg_price),
            'status': self.status,
            'time_in_force': self.time_in_force,
            'commission': float(self.commission),
            'notes': self.notes,
            'strategy_id': self.strategy_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'filled_at': self.filled_at.isoformat() if self.filled_at else None
        }

