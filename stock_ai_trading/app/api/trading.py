# -*- coding: utf-8 -*-
"""
交易API模块
提供交易引擎的REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
import logging
import uuid

router = APIRouter(prefix="/api/trading", tags=["交易"])

# 数据模型定义
class OrderRequest(BaseModel):
    """订单请求模型"""
    symbol: str = Field(..., description="股票代码")
    side: str = Field(..., description="买卖方向: buy, sell")
    order_type: str = Field(..., description="订单类型: market, limit, stop")
    quantity: int = Field(..., description="数量")
    price: Optional[float] = Field(None, description="价格")
    stop_price: Optional[float] = Field(None, description="止损价格")

class OrderResponse(BaseModel):
    """订单响应模型"""
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="股票代码")
    side: str = Field(..., description="买卖方向")
    order_type: str = Field(..., description="订单类型")
    quantity: int = Field(..., description="数量")
    price: Optional[float] = Field(None, description="价格")
    stop_price: Optional[float] = Field(None, description="止损价格")
    status: str = Field(..., description="订单状态")
    filled_quantity: int = Field(0, description="已成交数量")
    avg_fill_price: Optional[float] = Field(None, description="平均成交价格")
    commission: float = Field(0.0, description="手续费")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

class TradeResponse(BaseModel):
    """交易响应模型"""
    trade_id: str = Field(..., description="交易ID")
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="股票代码")
    side: str = Field(..., description="买卖方向")
    quantity: int = Field(..., description="数量")
    price: float = Field(..., description="成交价格")
    commission: float = Field(..., description="手续费")
    timestamp: datetime = Field(..., description="成交时间")

class PositionResponse(BaseModel):
    """持仓响应模型"""
    symbol: str = Field(..., description="股票代码")
    quantity: int = Field(..., description="持仓数量")
    avg_cost: float = Field(..., description="平均成本")
    market_value: float = Field(..., description="市值")
    unrealized_pnl: float = Field(..., description="未实现盈亏")
    realized_pnl: float = Field(..., description="已实现盈亏")
    updated_at: datetime = Field(..., description="更新时间")

class AccountInfoResponse(BaseModel):
    """账户信息响应模型"""
    account_id: str = Field(..., description="账户ID")
    total_value: float = Field(..., description="总资产")
    available_cash: float = Field(..., description="可用现金")
    used_margin: float = Field(..., description="已用保证金")
    total_margin: float = Field(..., description="总保证金")
    free_margin: float = Field(..., description="可用保证金")
    positions: Dict[str, PositionResponse] = Field(..., description="持仓信息")
    updated_at: datetime = Field(..., description="更新时间")

class MarketDataResponse(BaseModel):
    """市场数据响应模型"""
    symbol: str = Field(..., description="股票代码")
    bid_price: float = Field(..., description="买一价")
    ask_price: float = Field(..., description="卖一价")
    last_price: float = Field(..., description="最新价")
    volume: int = Field(..., description="成交量")
    mid_price: float = Field(..., description="中间价")
    spread: float = Field(..., description="价差")
    spread_bps: float = Field(..., description="价差基点")
    timestamp: datetime = Field(..., description="时间戳")

class TradingStatsResponse(BaseModel):
    """交易统计响应模型"""
    total_orders: int = Field(..., description="总订单数")
    filled_orders: int = Field(..., description="已成交订单数")
    fill_rate: float = Field(..., description="成交率")
    total_trades: int = Field(..., description="总交易数")
    positions_count: int = Field(..., description="持仓数量")
    mode: str = Field(..., description="交易模式")
    is_running: bool = Field(..., description="是否运行中")

# 模拟交易引擎
class MockTradingEngine:
    def __init__(self):
        self.orders = {}
        self.trades = {}
        self.positions = {}
        self.account_info = {
            "account_id": "MOCK_ACCOUNT",
            "total_value": 1000000.0,
            "available_cash": 500000.0,
            "used_margin": 0.0,
            "total_margin": 0.0,
            "free_margin": 500000.0,
            "positions": {},
            "updated_at": datetime.now()
        }
        self.is_running = False
        self.stats = {
            "total_orders": 0,
            "filled_orders": 0,
            "fill_rate": 0.0,
            "total_trades": 0,
            "positions_count": 0,
            "mode": "simulation",
            "is_running": False
        }
    
    def place_order(self, order_request: OrderRequest) -> OrderResponse:
        """下单"""
        order_id = str(uuid.uuid4())
        
        order = OrderResponse(
            order_id=order_id,
            symbol=order_request.symbol,
            side=order_request.side,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=order_request.price,
            stop_price=order_request.stop_price,
            status="pending",
            filled_quantity=0,
            avg_fill_price=None,
            commission=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.orders[order_id] = order
        self.stats["total_orders"] += 1
        
        # 模拟立即成交
        if order_request.order_type == "market":
            self._fill_order(order_id, order_request.price or 100.0)
        
        return order
    
    def _fill_order(self, order_id: str, fill_price: float):
        """成交订单"""
        if order_id not in self.orders:
            return
        
        order = self.orders[order_id]
        order.status = "filled"
        order.filled_quantity = order.quantity
        order.avg_fill_price = fill_price
        order.commission = order.quantity * fill_price * 0.0003  # 0.03% 手续费
        order.updated_at = datetime.now()
        
        # 创建交易记录
        trade_id = str(uuid.uuid4())
        trade = TradeResponse(
            trade_id=trade_id,
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=order.commission,
            timestamp=datetime.now()
        )
        
        self.trades[trade_id] = trade
        self.stats["filled_orders"] += 1
        self.stats["total_trades"] += 1
        
        # 更新持仓
        self._update_position(order.symbol, order.side, order.quantity, fill_price)
        
        # 更新成交率
        if self.stats["total_orders"] > 0:
            self.stats["fill_rate"] = self.stats["filled_orders"] / self.stats["total_orders"]
    
    def _update_position(self, symbol: str, side: str, quantity: int, price: float):
        """更新持仓"""
        if symbol not in self.positions:
            self.positions[symbol] = PositionResponse(
                symbol=symbol,
                quantity=0,
                avg_cost=0.0,
                market_value=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                updated_at=datetime.now()
            )
        
        position = self.positions[symbol]
        
        if side == "buy":
            # 买入
            total_cost = position.quantity * position.avg_cost + quantity * price
            position.quantity += quantity
            position.avg_cost = total_cost / position.quantity if position.quantity > 0 else 0.0
        else:
            # 卖出
            position.quantity -= quantity
            if position.quantity < 0:
                position.quantity = 0
        
        position.market_value = position.quantity * price
        position.unrealized_pnl = position.market_value - (position.quantity * position.avg_cost)
        position.updated_at = datetime.now()
        
        self.stats["positions_count"] = len([p for p in self.positions.values() if p.quantity > 0])
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == "pending":
                order.status = "cancelled"
                order.updated_at = datetime.now()
                return True
        return False
    
    def get_order(self, order_id: str) -> Optional[OrderResponse]:
        """获取订单"""
        return self.orders.get(order_id)
    
    def get_orders(self, symbol: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[OrderResponse]:
        """获取订单列表"""
        orders = list(self.orders.values())
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        if status:
            orders = [o for o in orders if o.status == status]
        
        return orders[:limit]
    
    def get_positions(self) -> Dict[str, PositionResponse]:
        """获取持仓"""
        return {k: v for k, v in self.positions.items() if v.quantity > 0}
    
    def get_position(self, symbol: str) -> Optional[PositionResponse]:
        """获取单个持仓"""
        return self.positions.get(symbol)
    
    def get_account_info(self) -> AccountInfoResponse:
        """获取账户信息"""
        self.account_info["positions"] = self.get_positions()
        self.account_info["updated_at"] = datetime.now()
        return AccountInfoResponse(**self.account_info)
    
    def get_trades(self, symbol: Optional[str] = None, limit: int = 100) -> List[TradeResponse]:
        """获取交易记录"""
        trades = list(self.trades.values())
        
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        
        return trades[:limit]
    
    def get_market_data(self, symbol: str) -> MarketDataResponse:
        """获取市场数据"""
        # 模拟市场数据
        last_price = 100.0
        spread = 0.02
        
        return MarketDataResponse(
            symbol=symbol,
            bid_price=last_price - spread/2,
            ask_price=last_price + spread/2,
            last_price=last_price,
            volume=1000000,
            mid_price=last_price,
            spread=spread,
            spread_bps=spread * 10000 / last_price,
            timestamp=datetime.now()
        )
    
    def get_stats(self) -> TradingStatsResponse:
        """获取统计信息"""
        self.stats["is_running"] = self.is_running
        return TradingStatsResponse(**self.stats)
    
    def start(self):
        """启动交易引擎"""
        self.is_running = True
    
    def stop(self):
        """停止交易引擎"""
        self.is_running = False

# 全局交易引擎实例
_trading_engine = None

def get_trading_engine() -> MockTradingEngine:
    """获取交易引擎实例"""
    global _trading_engine
    if _trading_engine is None:
        _trading_engine = MockTradingEngine()
    return _trading_engine

# API路由定义
@router.post("/orders", summary="下单")
async def place_order(order_request: OrderRequest):
    """下单"""
    try:
        engine = get_trading_engine()
        order = engine.place_order(order_request)
        
        return {
            "success": True,
            "message": "订单提交成功",
            "data": order.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下单失败: {str(e)}")

@router.delete("/orders/{order_id}", summary="取消订单")
async def cancel_order(order_id: str):
    """取消订单"""
    try:
        engine = get_trading_engine()
        success = engine.cancel_order(order_id)
        
        if success:
            return {
                "success": True,
                "message": "订单取消成功"
            }
        else:
            raise HTTPException(status_code=404, detail="订单不存在或无法取消")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消订单失败: {str(e)}")

@router.get("/orders/{order_id}", summary="获取订单状态")
async def get_order_status(order_id: str):
    """获取订单状态"""
    try:
        engine = get_trading_engine()
        order = engine.get_order(order_id)
        
        if order:
            return {
                "success": True,
                "data": order.dict()
            }
        else:
            raise HTTPException(status_code=404, detail="订单不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单状态失败: {str(e)}")

@router.get("/orders", summary="获取订单列表")
async def get_orders(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """获取订单列表"""
    try:
        engine = get_trading_engine()
        orders = engine.get_orders(symbol, status, limit)
        
        return {
            "success": True,
            "data": {
                "orders": [order.dict() for order in orders],
                "count": len(orders)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")

@router.get("/positions", summary="获取持仓")
async def get_positions():
    """获取持仓"""
    try:
        engine = get_trading_engine()
        positions = engine.get_positions()
        
        return {
            "success": True,
            "data": {
                "positions": {k: v.dict() for k, v in positions.items()},
                "count": len(positions)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")

@router.get("/positions/{symbol}", summary="获取单个持仓")
async def get_position(symbol: str):
    """获取单个持仓"""
    try:
        engine = get_trading_engine()
        position = engine.get_position(symbol)
        
        if position:
            return {
                "success": True,
                "data": position.dict()
            }
        else:
            raise HTTPException(status_code=404, detail="持仓不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")

@router.get("/account", summary="获取账户信息")
async def get_account_info():
    """获取账户信息"""
    try:
        engine = get_trading_engine()
        account_info = engine.get_account_info()
        
        return {
            "success": True,
            "data": account_info.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取账户信息失败: {str(e)}")

@router.get("/trades", summary="获取交易记录")
async def get_trades(
    symbol: Optional[str] = None,
    limit: int = 100
):
    """获取交易记录"""
    try:
        engine = get_trading_engine()
        trades = engine.get_trades(symbol, limit)
        
        return {
            "success": True,
            "data": {
                "trades": [trade.dict() for trade in trades],
                "count": len(trades)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易记录失败: {str(e)}")

@router.get("/market-data/{symbol}", summary="获取市场数据")
async def get_market_data(symbol: str):
    """获取市场数据"""
    try:
        engine = get_trading_engine()
        market_data = engine.get_market_data(symbol)
        
        return {
            "success": True,
            "data": market_data.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场数据失败: {str(e)}")

@router.get("/stats", summary="获取交易统计")
async def get_engine_stats():
    """获取交易引擎统计信息"""
    try:
        engine = get_trading_engine()
        stats = engine.get_stats()
        
        return {
            "success": True,
            "data": stats.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/start", summary="启动交易引擎")
async def start_engine():
    """启动交易引擎"""
    try:
        engine = get_trading_engine()
        engine.start()
        
        return {
            "success": True,
            "message": "交易引擎启动成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动交易引擎失败: {str(e)}")

@router.post("/stop", summary="停止交易引擎")
async def stop_engine():
    """停止交易引擎"""
    try:
        engine = get_trading_engine()
        engine.stop()
        
        return {
            "success": True,
            "message": "交易引擎停止成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止交易引擎失败: {str(e)}")

@router.get("/health", summary="健康检查")
async def health_check():
    """交易引擎健康检查"""
    try:
        engine = get_trading_engine()
        stats = engine.get_stats()
        
        return {
            "success": True,
            "message": "交易引擎运行正常",
            "data": {
                "status": "healthy",
                "is_running": stats.is_running,
                "stats": stats.dict(),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

@router.post("/test", summary="测试交易功能")
async def test_trading():
    """测试交易功能"""
    try:
        engine = get_trading_engine()
        
        # 执行测试订单
        test_order_request = OrderRequest(
            symbol="TEST001",
            side="buy",
            order_type="market",
            quantity=100,
            price=100.0
        )
        
        order = engine.place_order(test_order_request)
        
        return {
            "success": True,
            "message": "交易功能测试成功",
            "data": {
                "test_order": order.dict(),
                "engine_stats": engine.get_stats().dict()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"交易功能测试失败: {str(e)}")








