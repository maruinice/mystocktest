"""
仿真交易引擎
实现虚拟订单簿撮合、滑点模型、大单冲击模拟等功能
"""

import asyncio
import random
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from .trading_engine import (
    BaseTradingEngine, Order, Trade, Position, AccountInfo, ExecutionReport,
    OrderSide, OrderType, OrderStatus, TradingMode
)

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    bid_price: Decimal
    ask_price: Decimal
    last_price: Decimal
    volume: Decimal
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def mid_price(self) -> Decimal:
        """中间价"""
        return (self.bid_price + self.ask_price) / 2

    @property
    def spread(self) -> Decimal:
        """买卖价差"""
        return self.ask_price - self.bid_price

    @property
    def spread_bps(self) -> float:
        """价差基点"""
        if self.mid_price == 0:
            return 0
        return float(self.spread / self.mid_price * 10000)


@dataclass
class OrderBookLevel:
    """订单簿层级"""
    price: Decimal
    quantity: Decimal


@dataclass
class OrderBook:
    """虚拟订单簿"""
    symbol: str
    bids: List[OrderBookLevel] = field(default_factory=list)
    asks: List[OrderBookLevel] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)

    def get_best_bid(self) -> Optional[OrderBookLevel]:
        """获取最优买价"""
        return self.bids[0] if self.bids else None

    def get_best_ask(self) -> Optional[OrderBookLevel]:
        """获取最优卖价"""
        return self.asks[0] if self.asks else None

    def get_market_data(self) -> Optional[MarketData]:
        """获取市场数据"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if not best_bid or not best_ask:
            return None
        
        return MarketData(
            symbol=self.symbol,
            bid_price=best_bid.price,
            ask_price=best_ask.price,
            last_price=(best_bid.price + best_ask.price) / 2,
            volume=Decimal('0')  # 简化处理
        )


class SlippageModel:
    """滑点模型"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.fixed_slippage_bps = self.config.get('fixed_slippage_bps', 5)  # 固定滑点5bp
        self.impact_coefficient = self.config.get('impact_coefficient', 0.1)  # 冲击系数
        self.volatility_factor = self.config.get('volatility_factor', 1.0)  # 波动率因子

    def calculate_slippage(self, order: Order, market_data: MarketData, 
                          order_book: OrderBook) -> Decimal:
        """计算滑点"""
        # 基础固定滑点
        base_slippage_bps = self.fixed_slippage_bps
        
        # 大单冲击滑点
        impact_slippage = self._calculate_market_impact(order, market_data, order_book)
        
        # 随机滑点（模拟市场波动）
        random_slippage = self._calculate_random_slippage(market_data)
        
        total_slippage_bps = base_slippage_bps + impact_slippage + random_slippage
        
        # 转换为价格滑点
        slippage_price = market_data.mid_price * Decimal(str(total_slippage_bps / 10000))
        
        # 买单向上滑点，卖单向下滑点
        if order.side == OrderSide.BUY:
            return slippage_price
        else:
            return -slippage_price

    def _calculate_market_impact(self, order: Order, market_data: MarketData, 
                               order_book: OrderBook) -> float:
        """计算市场冲击滑点"""
        # 简化的市场冲击模型：基于订单大小相对于订单簿深度
        total_depth = sum(level.quantity for level in order_book.bids[:5]) + \
                     sum(level.quantity for level in order_book.asks[:5])
        
        if total_depth == 0:
            return 0
        
        # 订单相对大小
        relative_size = float(order.quantity / total_depth)
        
        # 冲击滑点 = 冲击系数 * sqrt(相对大小) * 100 (转换为bp)
        impact_bps = self.impact_coefficient * math.sqrt(relative_size) * 100
        
        return min(impact_bps, 50)  # 最大冲击滑点50bp

    def _calculate_random_slippage(self, market_data: MarketData) -> float:
        """计算随机滑点"""
        # 基于价差的随机滑点
        spread_factor = min(market_data.spread_bps / 10, 2.0)  # 最大2bp
        random_factor = random.uniform(-1, 1) * self.volatility_factor
        
        return spread_factor * random_factor


class SimulationEngine(BaseTradingEngine):
    """仿真交易引擎"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(TradingMode.SIMULATION, config)
        
        # 仿真配置
        self.initial_cash = Decimal(str(self.config.get('initial_cash', 1000000)))  # 初始资金100万
        self.commission_rate = Decimal(str(self.config.get('commission_rate', 0.0003)))  # 手续费率0.03%
        self.min_commission = Decimal(str(self.config.get('min_commission', 5)))  # 最小手续费5元
        
        # 市场数据和订单簿
        self.market_data: Dict[str, MarketData] = {}
        self.order_books: Dict[str, OrderBook] = {}
        
        # 滑点模型
        self.slippage_model = SlippageModel(self.config.get('slippage_config', {}))
        
        # 初始化账户
        self.account = AccountInfo(
            account_id="simulation_account",
            total_value=self.initial_cash,
            available_cash=self.initial_cash,
            used_margin=Decimal('0')
        )

    async def start(self):
        """启动仿真引擎"""
        await super().start()
        
        # 启动市场数据模拟
        asyncio.create_task(self._simulate_market_data())

    async def place_order(self, order: Order) -> str:
        """下单"""
        await self.validate_order(order)
        
        # 生成订单ID
        if not order.order_id:
            order.order_id = self.generate_order_id()
        
        # 检查资金充足性
        if not await self._check_buying_power(order):
            order.status = OrderStatus.REJECTED
            self.orders[order.order_id] = order
            raise ValueError("资金不足")
        
        # 添加到订单列表
        order.status = OrderStatus.SUBMITTED
        self.orders[order.order_id] = order
        
        # 异步执行订单
        asyncio.create_task(self._execute_order(order))
        
        self.logger.info(f"订单提交: {order.order_id} - {order.symbol} {order.side.value} {order.quantity}")
        return order.order_id

    async def cancel_order(self, order_id: str) -> bool:
        """撤单"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        # 只能撤销未成交或部分成交的订单
        if order.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILLED]:
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            self.logger.info(f"订单撤销: {order_id}")
            return True
        
        return False

    async def get_account_info(self) -> AccountInfo:
        """获取账户信息"""
        # 更新账户信息
        await self._update_account_info()
        return self.account

    async def _check_buying_power(self, order: Order) -> bool:
        """检查购买力"""
        if order.side == OrderSide.SELL:
            # 卖单检查持仓
            position = self.positions.get(order.symbol)
            if not position or position.quantity < order.quantity:
                return False
        else:
            # 买单检查资金
            estimated_cost = order.quantity * (order.price or self._get_market_price(order.symbol, order.side))
            commission = self._calculate_commission(estimated_cost)
            total_cost = estimated_cost + commission
            
            if self.account.available_cash < total_cost:
                return False
        
        return True

    async def _execute_order(self, order: Order):
        """执行订单"""
        try:
            # 模拟订单处理延迟
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # 获取市场数据
            market_data = self.market_data.get(order.symbol)
            if not market_data:
                await self._generate_market_data(order.symbol)
                market_data = self.market_data.get(order.symbol)
            
            if not market_data:
                order.status = OrderStatus.REJECTED
                return
            
            # 确定执行价格
            execution_price = await self._determine_execution_price(order, market_data)
            
            if execution_price is None:
                order.status = OrderStatus.REJECTED
                return
            
            # 创建成交记录
            trade = Trade(
                trade_id=self.generate_trade_id(),
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=execution_price,
                commission=self._calculate_commission(order.quantity * execution_price)
            )
            
            # 更新订单状态
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.avg_fill_price = execution_price
            order.commission = trade.commission
            order.updated_at = datetime.now()
            
            # 添加成交记录
            await self.add_trade(trade)
            
            # 更新账户资金
            await self._update_account_balance(trade)
            
        except Exception as e:
            self.logger.error(f"订单执行失败: {order.order_id} - {str(e)}")
            order.status = OrderStatus.REJECTED

    async def _determine_execution_price(self, order: Order, market_data: MarketData) -> Optional[Decimal]:
        """确定执行价格"""
        order_book = self.order_books.get(order.symbol)
        if not order_book:
            order_book = self._generate_order_book(order.symbol, market_data)
        
        # 基础执行价格
        if order.order_type == OrderType.MARKET:
            if order.side == OrderSide.BUY:
                base_price = market_data.ask_price
            else:
                base_price = market_data.bid_price
        elif order.order_type == OrderType.LIMIT:
            # 限价单检查是否能成交
            if order.side == OrderSide.BUY and order.price < market_data.ask_price:
                return None  # 买入限价低于卖价，无法成交
            elif order.side == OrderSide.SELL and order.price > market_data.bid_price:
                return None  # 卖出限价高于买价，无法成交
            base_price = order.price
        else:
            # 其他订单类型暂不支持
            return None
        
        # 计算滑点
        slippage = self.slippage_model.calculate_slippage(order, market_data, order_book)
        
        # 最终执行价格
        execution_price = base_price + slippage
        
        # 确保价格为正
        return max(execution_price, Decimal('0.01'))

    def _get_market_price(self, symbol: str, side: OrderSide) -> Decimal:
        """获取市场价格"""
        market_data = self.market_data.get(symbol)
        if not market_data:
            return Decimal('10.0')  # 默认价格
        
        if side == OrderSide.BUY:
            return market_data.ask_price
        else:
            return market_data.bid_price

    def _calculate_commission(self, trade_value: Decimal) -> Decimal:
        """计算手续费"""
        commission = trade_value * self.commission_rate
        return max(commission, self.min_commission)

    async def _update_account_balance(self, trade: Trade):
        """更新账户余额"""
        if trade.side == OrderSide.BUY:
            # 买入：减少现金
            cost = trade.quantity * trade.price + trade.commission
            self.account.available_cash -= cost
        else:
            # 卖出：增加现金
            proceeds = trade.quantity * trade.price - trade.commission
            self.account.available_cash += proceeds

    async def _update_account_info(self):
        """更新账户信息"""
        # 计算持仓市值
        total_position_value = Decimal('0')
        for symbol, position in self.positions.items():
            if not position.is_flat:
                market_data = self.market_data.get(symbol)
                if market_data:
                    position.market_value = position.quantity * market_data.last_price
                    position.unrealized_pnl = position.market_value - (position.avg_cost * position.quantity)
                    total_position_value += abs(position.market_value)
        
        # 更新账户总值
        self.account.total_value = self.account.available_cash + total_position_value
        self.account.positions = self.positions.copy()
        self.account.updated_at = datetime.now()

    async def _simulate_market_data(self):
        """模拟市场数据"""
        while self.is_running:
            try:
                # 为所有交易过的股票更新市场数据
                symbols = set(order.symbol for order in self.orders.values())
                
                for symbol in symbols:
                    await self._generate_market_data(symbol)
                
                await asyncio.sleep(1)  # 每秒更新一次
                
            except Exception as e:
                self.logger.error(f"市场数据模拟错误: {str(e)}")
                await asyncio.sleep(5)

    async def _generate_market_data(self, symbol: str):
        """生成市场数据"""
        current_data = self.market_data.get(symbol)
        
        if current_data:
            # 基于当前价格生成新价格（随机游走）
            price_change_pct = random.uniform(-0.02, 0.02)  # ±2%的价格变动
            new_price = current_data.last_price * (1 + Decimal(str(price_change_pct)))
        else:
            # 初始价格
            new_price = Decimal(str(random.uniform(8, 50)))
        
        # 生成买卖价差
        spread_pct = random.uniform(0.001, 0.005)  # 0.1%-0.5%的价差
        spread = new_price * Decimal(str(spread_pct))
        
        market_data = MarketData(
            symbol=symbol,
            bid_price=new_price - spread / 2,
            ask_price=new_price + spread / 2,
            last_price=new_price,
            volume=Decimal(str(random.randint(1000, 100000)))
        )
        
        self.market_data[symbol] = market_data
        
        # 生成对应的订单簿
        self.order_books[symbol] = self._generate_order_book(symbol, market_data)

    def _generate_order_book(self, symbol: str, market_data: MarketData) -> OrderBook:
        """生成虚拟订单簿"""
        order_book = OrderBook(symbol=symbol)
        
        # 生成买盘
        for i in range(5):
            price = market_data.bid_price - Decimal(str(i * 0.01))
            quantity = Decimal(str(random.randint(100, 10000)))
            order_book.bids.append(OrderBookLevel(price=price, quantity=quantity))
        
        # 生成卖盘
        for i in range(5):
            price = market_data.ask_price + Decimal(str(i * 0.01))
            quantity = Decimal(str(random.randint(100, 10000)))
            order_book.asks.append(OrderBookLevel(price=price, quantity=quantity))
        
        return order_book

    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """获取市场数据"""
        return self.market_data.get(symbol)

    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """获取订单簿"""
        return self.order_books.get(symbol)

    async def run_stress_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """运行极端行情测试"""
        self.logger.info("开始极端行情测试")
        
        test_results = {
            "start_time": datetime.now(),
            "test_scenarios": [],
            "performance_metrics": {}
        }
        
        # 测试场景1：价格暴跌
        await self._test_price_crash(test_results)
        
        # 测试场景2：价格暴涨
        await self._test_price_surge(test_results)
        
        # 测试场景3：高波动率
        await self._test_high_volatility(test_results)
        
        # 测试场景4：流动性枯竭
        await self._test_liquidity_crisis(test_results)
        
        test_results["end_time"] = datetime.now()
        test_results["duration"] = (test_results["end_time"] - test_results["start_time"]).total_seconds()
        
        self.logger.info("极端行情测试完成")
        return test_results

    async def _test_price_crash(self, results: Dict[str, Any]):
        """测试价格暴跌场景"""
        scenario = {"name": "price_crash", "description": "价格暴跌-20%"}
        
        # 模拟所有股票价格下跌20%
        for symbol, market_data in self.market_data.items():
            crash_factor = Decimal('0.8')  # 下跌20%
            market_data.bid_price *= crash_factor
            market_data.ask_price *= crash_factor
            market_data.last_price *= crash_factor
        
        # 更新持仓盈亏
        await self._update_account_info()
        
        scenario["account_value_after"] = float(self.account.total_value)
        results["test_scenarios"].append(scenario)

    async def _test_price_surge(self, results: Dict[str, Any]):
        """测试价格暴涨场景"""
        scenario = {"name": "price_surge", "description": "价格暴涨+30%"}
        
        # 模拟所有股票价格上涨30%
        for symbol, market_data in self.market_data.items():
            surge_factor = Decimal('1.3')  # 上涨30%
            market_data.bid_price *= surge_factor
            market_data.ask_price *= surge_factor
            market_data.last_price *= surge_factor
        
        await self._update_account_info()
        
        scenario["account_value_after"] = float(self.account.total_value)
        results["test_scenarios"].append(scenario)

    async def _test_high_volatility(self, results: Dict[str, Any]):
        """测试高波动率场景"""
        scenario = {"name": "high_volatility", "description": "高波动率环境"}
        
        # 增加滑点模型的波动率因子
        original_factor = self.slippage_model.volatility_factor
        self.slippage_model.volatility_factor = 5.0
        
        # 模拟一些交易
        test_orders = []
        for i in range(10):
            symbol = f"TEST{i:03d}"
            await self._generate_market_data(symbol)
            
            order = Order(
                order_id="",
                symbol=symbol,
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=Decimal('1000')
            )
            
            try:
                order_id = await self.place_order(order)
                test_orders.append(order_id)
            except Exception as e:
                self.logger.warning(f"高波动率测试订单失败: {str(e)}")
        
        # 等待订单执行
        await asyncio.sleep(2)
        
        # 恢复原始波动率因子
        self.slippage_model.volatility_factor = original_factor
        
        scenario["orders_placed"] = len(test_orders)
        scenario["orders_filled"] = len([o for o in self.orders.values() if o.status == OrderStatus.FILLED])
        results["test_scenarios"].append(scenario)

    async def _test_liquidity_crisis(self, results: Dict[str, Any]):
        """测试流动性危机场景"""
        scenario = {"name": "liquidity_crisis", "description": "流动性枯竭"}
        
        # 减少订单簿深度
        for symbol, order_book in self.order_books.items():
            # 将订单簿深度减少90%
            for level in order_book.bids:
                level.quantity *= Decimal('0.1')
            for level in order_book.asks:
                level.quantity *= Decimal('0.1')
        
        # 增加市场冲击系数
        original_coefficient = self.slippage_model.impact_coefficient
        self.slippage_model.impact_coefficient = 1.0
        
        # 尝试大单交易
        large_orders = []
        for symbol in list(self.market_data.keys())[:3]:
            order = Order(
                order_id="",
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal('50000')  # 大单
            )
            
            try:
                order_id = await self.place_order(order)
                large_orders.append(order_id)
            except Exception as e:
                self.logger.warning(f"流动性危机测试订单失败: {str(e)}")
        
        await asyncio.sleep(2)
        
        # 恢复原始冲击系数
        self.slippage_model.impact_coefficient = original_coefficient
        
        scenario["large_orders_placed"] = len(large_orders)
        scenario["large_orders_filled"] = len([o for o in self.orders.values() 
                                            if o.order_id in large_orders and o.status == OrderStatus.FILLED])
        results["test_scenarios"].append(scenario)