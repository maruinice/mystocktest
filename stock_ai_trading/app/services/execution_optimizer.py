"""
执行优化算法模块
实现订单拆分执行、VWAP/TWAP算法、智能再报价等功能
"""

import asyncio
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import logging

from .trading_engine import (
    Order, Trade, Position, OrderSide, OrderType, OrderStatus,
    BaseTradingEngine
)

logger = logging.getLogger(__name__)


class AlgorithmType(Enum):
    """算法类型"""
    VWAP = "vwap"
    TWAP = "twap"
    POV = "pov"  # Percentage of Volume
    ICEBERG = "iceberg"
    SMART_ORDER = "smart_order"


@dataclass
class MarketData:
    """市场数据"""
    symbol: str
    price: Decimal
    volume: int
    bid_price: Decimal
    ask_price: Decimal
    bid_size: int
    ask_size: int
    timestamp: datetime
    vwap: Optional[Decimal] = None
    volatility: Optional[float] = None


@dataclass
class AlgorithmConfig:
    """算法配置"""
    algorithm_type: AlgorithmType
    symbol: str
    total_quantity: Decimal
    side: OrderSide
    
    # 时间参数
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: int = 60
    
    # 执行参数
    max_participation_rate: float = 0.1  # 最大参与率
    min_order_size: Decimal = Decimal("100")
    max_order_size: Optional[Decimal] = None
    price_limit: Optional[Decimal] = None
    
    # VWAP参数
    vwap_lookback_minutes: int = 20
    
    # TWAP参数
    twap_intervals: int = 10
    
    # POV参数
    pov_target_rate: float = 0.05
    
    # Iceberg参数
    iceberg_visible_size: Decimal = Decimal("500")
    
    # 智能订单参数
    smart_aggressiveness: float = 0.5  # 0-1, 0最保守，1最激进
    smart_adapt_interval: int = 30  # 适应间隔（秒）
    
    # 风控参数
    max_slippage_bps: int = 50  # 最大滑点（基点）
    stop_loss_bps: Optional[int] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionReport:
    """执行报告"""
    algorithm_id: str
    symbol: str
    total_quantity: Decimal
    executed_quantity: Decimal
    remaining_quantity: Decimal
    avg_execution_price: Decimal
    vwap_benchmark: Optional[Decimal]
    slippage_bps: float
    participation_rate: float
    execution_time: timedelta
    orders: List[Order]
    trades: List[Trade]
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    @property
    def fill_rate(self) -> float:
        """成交率"""
        if self.total_quantity == 0:
            return 0.0
        return float(self.executed_quantity / self.total_quantity)
    
    @property
    def is_completed(self) -> bool:
        """是否完成"""
        return self.remaining_quantity == 0


class ExecutionAlgorithm(ABC):
    """执行算法基类"""

    def __init__(self, config: AlgorithmConfig, trading_engine: BaseTradingEngine):
        self.config = config
        self.trading_engine = trading_engine
        self.algorithm_id = f"{config.algorithm_type.value}_{config.symbol}_{int(datetime.now().timestamp())}"
        
        self.is_running = False
        self.is_paused = False
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
        self.market_data_history: List[MarketData] = []
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{self.algorithm_id}")

    @abstractmethod
    async def execute(self) -> ExecutionReport:
        """执行算法"""
        pass

    @abstractmethod
    async def pause(self):
        """暂停算法"""
        pass

    @abstractmethod
    async def resume(self):
        """恢复算法"""
        pass

    @abstractmethod
    async def stop(self):
        """停止算法"""
        pass

    async def update_market_data(self, market_data: MarketData):
        """更新市场数据"""
        self.market_data_history.append(market_data)
        
        # 保持历史数据在合理范围内
        if len(self.market_data_history) > 1000:
            self.market_data_history = self.market_data_history[-500:]

    def get_current_market_data(self) -> Optional[MarketData]:
        """获取当前市场数据"""
        return self.market_data_history[-1] if self.market_data_history else None

    def calculate_vwap(self, lookback_minutes: int = 20) -> Optional[Decimal]:
        """计算VWAP"""
        if not self.market_data_history:
            return None
        
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        recent_data = [md for md in self.market_data_history if md.timestamp >= cutoff_time]
        
        if not recent_data:
            return None
        
        total_value = sum(md.price * md.volume for md in recent_data)
        total_volume = sum(md.volume for md in recent_data)
        
        if total_volume == 0:
            return None
        
        return total_value / total_volume

    def calculate_volatility(self, lookback_minutes: int = 60) -> float:
        """计算价格波动率"""
        if len(self.market_data_history) < 2:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        recent_data = [md for md in self.market_data_history if md.timestamp >= cutoff_time]
        
        if len(recent_data) < 2:
            return 0.0
        
        prices = [float(md.price) for md in recent_data]
        returns = [np.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
        
        return float(np.std(returns)) if returns else 0.0

    async def validate_order(self, order: Order) -> bool:
        """验证订单"""
        # 检查价格限制
        if self.config.price_limit:
            if self.config.side == OrderSide.BUY and order.price > self.config.price_limit:
                return False
            elif self.config.side == OrderSide.SELL and order.price < self.config.price_limit:
                return False
        
        # 检查订单大小
        if order.quantity < self.config.min_order_size:
            return False
        
        if self.config.max_order_size and order.quantity > self.config.max_order_size:
            return False
        
        return True

    def generate_execution_report(self) -> ExecutionReport:
        """生成执行报告"""
        executed_quantity = sum(trade.quantity for trade in self.trades)
        remaining_quantity = self.config.total_quantity - executed_quantity
        
        # 计算平均执行价格
        if self.trades:
            total_value = sum(trade.price * trade.quantity for trade in self.trades)
            avg_execution_price = total_value / executed_quantity
        else:
            avg_execution_price = Decimal("0")
        
        # 计算VWAP基准
        vwap_benchmark = self.calculate_vwap(self.config.vwap_lookback_minutes)
        
        # 计算滑点
        slippage_bps = 0.0
        if vwap_benchmark and avg_execution_price > 0:
            slippage = float((avg_execution_price - vwap_benchmark) / vwap_benchmark)
            if self.config.side == OrderSide.SELL:
                slippage = -slippage
            slippage_bps = slippage * 10000
        
        # 计算参与率
        total_market_volume = sum(md.volume for md in self.market_data_history)
        participation_rate = float(executed_quantity) / total_market_volume if total_market_volume > 0 else 0.0
        
        # 计算执行时间
        if self.trades:
            start_time = min(trade.timestamp for trade in self.trades)
            end_time = max(trade.timestamp for trade in self.trades)
            execution_time = end_time - start_time
        else:
            execution_time = timedelta(0)
        
        return ExecutionReport(
            algorithm_id=self.algorithm_id,
            symbol=self.config.symbol,
            total_quantity=self.config.total_quantity,
            executed_quantity=executed_quantity,
            remaining_quantity=remaining_quantity,
            avg_execution_price=avg_execution_price,
            vwap_benchmark=vwap_benchmark,
            slippage_bps=slippage_bps,
            participation_rate=participation_rate,
            execution_time=execution_time,
            orders=self.orders.copy(),
            trades=self.trades.copy(),
            status="completed" if remaining_quantity == 0 else "partial",
            created_at=datetime.now(),
            completed_at=datetime.now() if remaining_quantity == 0 else None
        )


class VWAPAlgorithm(ExecutionAlgorithm):
    """VWAP算法"""

    async def execute(self) -> ExecutionReport:
        """执行VWAP算法"""
        self.is_running = True
        self.logger.info(f"开始执行VWAP算法: {self.algorithm_id}")
        
        try:
            remaining_quantity = self.config.total_quantity
            end_time = datetime.now() + timedelta(minutes=self.config.duration_minutes)
            
            while remaining_quantity > 0 and datetime.now() < end_time and self.is_running:
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue
                
                # 获取当前市场数据
                market_data = self.get_current_market_data()
                if not market_data:
                    await asyncio.sleep(5)
                    continue
                
                # 计算当前VWAP
                current_vwap = self.calculate_vwap(self.config.vwap_lookback_minutes)
                if not current_vwap:
                    current_vwap = market_data.price
                
                # 计算订单大小（基于历史成交量分布）
                target_participation = min(self.config.max_participation_rate, 0.1)
                order_size = min(
                    remaining_quantity,
                    Decimal(str(market_data.volume * target_participation))
                )
                order_size = max(order_size, self.config.min_order_size)
                
                # 确定订单价格（接近VWAP）
                if self.config.side == OrderSide.BUY:
                    order_price = min(current_vwap, market_data.ask_price)
                else:
                    order_price = max(current_vwap, market_data.bid_price)
                
                # 创建订单
                order = Order(
                    symbol=self.config.symbol,
                    side=self.config.side,
                    order_type=OrderType.LIMIT,
                    quantity=order_size,
                    price=order_price
                )
                
                if await self.validate_order(order):
                    try:
                        order_id = await self.trading_engine.place_order(order)
                        order.order_id = order_id
                        self.orders.append(order)
                        
                        # 等待订单执行
                        await asyncio.sleep(10)
                        
                        # 检查订单状态
                        updated_order = await self.trading_engine.get_order_status(order_id)
                        if updated_order:
                            if updated_order.status == OrderStatus.FILLED:
                                # 创建成交记录
                                trade = Trade(
                                    trade_id=f"trade_{order_id}",
                                    order_id=order_id,
                                    symbol=self.config.symbol,
                                    side=self.config.side,
                                    quantity=updated_order.filled_quantity,
                                    price=updated_order.avg_fill_price,
                                    timestamp=datetime.now()
                                )
                                self.trades.append(trade)
                                remaining_quantity -= updated_order.filled_quantity
                            elif updated_order.status == OrderStatus.PARTIALLY_FILLED:
                                # 部分成交
                                trade = Trade(
                                    trade_id=f"trade_{order_id}",
                                    order_id=order_id,
                                    symbol=self.config.symbol,
                                    side=self.config.side,
                                    quantity=updated_order.filled_quantity,
                                    price=updated_order.avg_fill_price,
                                    timestamp=datetime.now()
                                )
                                self.trades.append(trade)
                                remaining_quantity -= updated_order.filled_quantity
                    
                    except Exception as e:
                        self.logger.error(f"VWAP订单执行失败: {str(e)}")
                
                await asyncio.sleep(30)  # 等待30秒再下一个订单
            
            self.is_running = False
            return self.generate_execution_report()
            
        except Exception as e:
            self.logger.error(f"VWAP算法执行失败: {str(e)}")
            self.is_running = False
            raise

    async def pause(self):
        """暂停VWAP算法"""
        self.is_paused = True
        self.logger.info(f"VWAP算法已暂停: {self.algorithm_id}")

    async def resume(self):
        """恢复VWAP算法"""
        self.is_paused = False
        self.logger.info(f"VWAP算法已恢复: {self.algorithm_id}")

    async def stop(self):
        """停止VWAP算法"""
        self.is_running = False
        
        # 撤销所有未成交订单
        for order in self.orders:
            if order.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]:
                await self.trading_engine.cancel_order(order.order_id)
        
        self.logger.info(f"VWAP算法已停止: {self.algorithm_id}")


class TWAPAlgorithm(ExecutionAlgorithm):
    """TWAP算法"""

    async def execute(self) -> ExecutionReport:
        """执行TWAP算法"""
        self.is_running = True
        self.logger.info(f"开始执行TWAP算法: {self.algorithm_id}")
        
        try:
            # 计算每个时间间隔的订单大小
            interval_duration = self.config.duration_minutes / self.config.twap_intervals
            quantity_per_interval = self.config.total_quantity / self.config.twap_intervals
            
            for interval in range(self.config.twap_intervals):
                if not self.is_running:
                    break
                
                while self.is_paused:
                    await asyncio.sleep(1)
                
                # 获取当前市场数据
                market_data = self.get_current_market_data()
                if not market_data:
                    await asyncio.sleep(5)
                    continue
                
                # 确定订单价格（市价或接近市价）
                if self.config.side == OrderSide.BUY:
                    order_price = market_data.ask_price
                else:
                    order_price = market_data.bid_price
                
                # 创建订单
                order = Order(
                    symbol=self.config.symbol,
                    side=self.config.side,
                    order_type=OrderType.LIMIT,
                    quantity=quantity_per_interval,
                    price=order_price
                )
                
                if await self.validate_order(order):
                    try:
                        order_id = await self.trading_engine.place_order(order)
                        order.order_id = order_id
                        self.orders.append(order)
                        
                        # 等待订单执行
                        await asyncio.sleep(5)
                        
                        # 检查订单状态
                        updated_order = await self.trading_engine.get_order_status(order_id)
                        if updated_order and updated_order.filled_quantity > 0:
                            trade = Trade(
                                trade_id=f"trade_{order_id}",
                                order_id=order_id,
                                symbol=self.config.symbol,
                                side=self.config.side,
                                quantity=updated_order.filled_quantity,
                                price=updated_order.avg_fill_price,
                                timestamp=datetime.now()
                            )
                            self.trades.append(trade)
                    
                    except Exception as e:
                        self.logger.error(f"TWAP订单执行失败: {str(e)}")
                
                # 等待到下一个时间间隔
                await asyncio.sleep(interval_duration * 60)
            
            self.is_running = False
            return self.generate_execution_report()
            
        except Exception as e:
            self.logger.error(f"TWAP算法执行失败: {str(e)}")
            self.is_running = False
            raise

    async def pause(self):
        """暂停TWAP算法"""
        self.is_paused = True
        self.logger.info(f"TWAP算法已暂停: {self.algorithm_id}")

    async def resume(self):
        """恢复TWAP算法"""
        self.is_paused = False
        self.logger.info(f"TWAP算法已恢复: {self.algorithm_id}")

    async def stop(self):
        """停止TWAP算法"""
        self.is_running = False
        
        # 撤销所有未成交订单
        for order in self.orders:
            if order.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]:
                await self.trading_engine.cancel_order(order.order_id)
        
        self.logger.info(f"TWAP算法已停止: {self.algorithm_id}")


class SmartOrderAlgorithm(ExecutionAlgorithm):
    """智能订单算法"""

    def __init__(self, config: AlgorithmConfig, trading_engine: BaseTradingEngine):
        super().__init__(config, trading_engine)
        self.price_history: List[Decimal] = []
        self.volume_history: List[int] = []
        self.last_adapt_time = datetime.now()

    async def execute(self) -> ExecutionReport:
        """执行智能订单算法"""
        self.is_running = True
        self.logger.info(f"开始执行智能订单算法: {self.algorithm_id}")
        
        try:
            remaining_quantity = self.config.total_quantity
            
            while remaining_quantity > 0 and self.is_running:
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue
                
                # 获取当前市场数据
                market_data = self.get_current_market_data()
                if not market_data:
                    await asyncio.sleep(5)
                    continue
                
                # 更新历史数据
                self.price_history.append(market_data.price)
                self.volume_history.append(market_data.volume)
                
                # 保持历史数据在合理范围内
                if len(self.price_history) > 100:
                    self.price_history = self.price_history[-50:]
                    self.volume_history = self.volume_history[-50:]
                
                # 自适应调整策略
                if datetime.now() - self.last_adapt_time >= timedelta(seconds=self.config.smart_adapt_interval):
                    await self.adapt_strategy()
                    self.last_adapt_time = datetime.now()
                
                # 计算订单参数
                order_size, order_price = await self.calculate_smart_order_params(
                    market_data, remaining_quantity
                )
                
                if order_size > 0:
                    # 创建订单
                    order = Order(
                        symbol=self.config.symbol,
                        side=self.config.side,
                        order_type=OrderType.LIMIT,
                        quantity=order_size,
                        price=order_price
                    )
                    
                    if await self.validate_order(order):
                        try:
                            order_id = await self.trading_engine.place_order(order)
                            order.order_id = order_id
                            self.orders.append(order)
                            
                            # 等待订单执行
                            await asyncio.sleep(10)
                            
                            # 检查订单状态
                            updated_order = await self.trading_engine.get_order_status(order_id)
                            if updated_order and updated_order.filled_quantity > 0:
                                trade = Trade(
                                    trade_id=f"trade_{order_id}",
                                    order_id=order_id,
                                    symbol=self.config.symbol,
                                    side=self.config.side,
                                    quantity=updated_order.filled_quantity,
                                    price=updated_order.avg_fill_price,
                                    timestamp=datetime.now()
                                )
                                self.trades.append(trade)
                                remaining_quantity -= updated_order.filled_quantity
                        
                        except Exception as e:
                            self.logger.error(f"智能订单执行失败: {str(e)}")
                
                await asyncio.sleep(15)  # 等待15秒再下一个订单
            
            self.is_running = False
            return self.generate_execution_report()
            
        except Exception as e:
            self.logger.error(f"智能订单算法执行失败: {str(e)}")
            self.is_running = False
            raise

    async def calculate_smart_order_params(self, market_data: MarketData, 
                                         remaining_quantity: Decimal) -> Tuple[Decimal, Decimal]:
        """计算智能订单参数"""
        # 计算市场状态指标
        volatility = self.calculate_volatility(30)
        spread = float(market_data.ask_price - market_data.bid_price)
        spread_bps = (spread / float(market_data.price)) * 10000
        
        # 基于激进程度调整订单大小
        base_size = min(remaining_quantity, self.config.min_order_size * 5)
        
        if volatility > 0.02:  # 高波动率
            order_size = base_size * Decimal(str(0.5))  # 减小订单
        elif spread_bps > 20:  # 大价差
            order_size = base_size * Decimal(str(0.7))  # 适度减小
        else:
            order_size = base_size
        
        # 确定订单价格
        aggressiveness = self.config.smart_aggressiveness
        
        if self.config.side == OrderSide.BUY:
            if aggressiveness > 0.8:  # 非常激进
                order_price = market_data.ask_price
            elif aggressiveness > 0.5:  # 中等激进
                order_price = market_data.bid_price + Decimal(str(spread * 0.5))
            else:  # 保守
                order_price = market_data.bid_price
        else:  # SELL
            if aggressiveness > 0.8:  # 非常激进
                order_price = market_data.bid_price
            elif aggressiveness > 0.5:  # 中等激进
                order_price = market_data.ask_price - Decimal(str(spread * 0.5))
            else:  # 保守
                order_price = market_data.ask_price
        
        return order_size, order_price

    async def adapt_strategy(self):
        """自适应调整策略"""
        if len(self.price_history) < 10:
            return
        
        # 分析最近的价格趋势
        recent_prices = self.price_history[-10:]
        price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # 分析成交情况
        fill_rate = len(self.trades) / max(len(self.orders), 1)
        
        # 根据成交率调整激进程度
        if fill_rate < 0.3:  # 成交率低，增加激进程度
            self.config.smart_aggressiveness = min(1.0, self.config.smart_aggressiveness + 0.1)
        elif fill_rate > 0.8:  # 成交率高，可以降低激进程度
            self.config.smart_aggressiveness = max(0.1, self.config.smart_aggressiveness - 0.05)
        
        self.logger.info(f"策略自适应调整: 激进程度={self.config.smart_aggressiveness:.2f}, "
                        f"成交率={fill_rate:.2f}, 价格趋势={price_trend:.4f}")

    async def pause(self):
        """暂停智能订单算法"""
        self.is_paused = True
        self.logger.info(f"智能订单算法已暂停: {self.algorithm_id}")

    async def resume(self):
        """恢复智能订单算法"""
        self.is_paused = False
        self.logger.info(f"智能订单算法已恢复: {self.algorithm_id}")

    async def stop(self):
        """停止智能订单算法"""
        self.is_running = False
        
        # 撤销所有未成交订单
        for order in self.orders:
            if order.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]:
                await self.trading_engine.cancel_order(order.order_id)
        
        self.logger.info(f"智能订单算法已停止: {self.algorithm_id}")


class ExecutionOptimizer:
    """执行优化器"""

    def __init__(self, trading_engine: BaseTradingEngine):
        self.trading_engine = trading_engine
        self.running_algorithms: Dict[str, ExecutionAlgorithm] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    async def start_algorithm(self, config: AlgorithmConfig) -> str:
        """启动执行算法"""
        try:
            # 创建算法实例
            if config.algorithm_type == AlgorithmType.VWAP:
                algorithm = VWAPAlgorithm(config, self.trading_engine)
            elif config.algorithm_type == AlgorithmType.TWAP:
                algorithm = TWAPAlgorithm(config, self.trading_engine)
            elif config.algorithm_type == AlgorithmType.SMART_ORDER:
                algorithm = SmartOrderAlgorithm(config, self.trading_engine)
            else:
                raise ValueError(f"不支持的算法类型: {config.algorithm_type}")
            
            # 启动算法
            self.running_algorithms[algorithm.algorithm_id] = algorithm
            
            # 异步执行算法
            asyncio.create_task(self._run_algorithm(algorithm))
            
            self.logger.info(f"算法启动成功: {algorithm.algorithm_id}")
            return algorithm.algorithm_id
            
        except Exception as e:
            self.logger.error(f"算法启动失败: {str(e)}")
            raise

    async def _run_algorithm(self, algorithm: ExecutionAlgorithm):
        """运行算法"""
        try:
            report = await algorithm.execute()
            self.logger.info(f"算法执行完成: {algorithm.algorithm_id}, "
                           f"成交率: {report.fill_rate:.2%}")
        except Exception as e:
            self.logger.error(f"算法执行失败: {algorithm.algorithm_id}, 错误: {str(e)}")
        finally:
            # 清理算法实例
            if algorithm.algorithm_id in self.running_algorithms:
                del self.running_algorithms[algorithm.algorithm_id]

    async def pause_algorithm(self, algorithm_id: str) -> bool:
        """暂停算法"""
        if algorithm_id not in self.running_algorithms:
            return False
        
        await self.running_algorithms[algorithm_id].pause()
        return True

    async def resume_algorithm(self, algorithm_id: str) -> bool:
        """恢复算法"""
        if algorithm_id not in self.running_algorithms:
            return False
        
        await self.running_algorithms[algorithm_id].resume()
        return True

    async def stop_algorithm(self, algorithm_id: str) -> bool:
        """停止算法"""
        if algorithm_id not in self.running_algorithms:
            return False
        
        await self.running_algorithms[algorithm_id].stop()
        return True

    def get_algorithm_status(self, algorithm_id: str) -> Optional[Dict[str, Any]]:
        """获取算法状态"""
        if algorithm_id not in self.running_algorithms:
            return None
        
        algorithm = self.running_algorithms[algorithm_id]
        return {
            "algorithm_id": algorithm_id,
            "algorithm_type": algorithm.config.algorithm_type.value,
            "symbol": algorithm.config.symbol,
            "is_running": algorithm.is_running,
            "is_paused": algorithm.is_paused,
            "orders_count": len(algorithm.orders),
            "trades_count": len(algorithm.trades),
            "executed_quantity": sum(trade.quantity for trade in algorithm.trades)
        }

    def get_all_algorithms_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有算法状态"""
        return {
            algorithm_id: self.get_algorithm_status(algorithm_id)
            for algorithm_id in self.running_algorithms.keys()
        }

    async def update_market_data(self, symbol: str, market_data: MarketData):
        """更新市场数据"""
        for algorithm in self.running_algorithms.values():
            if algorithm.config.symbol == symbol:
                await algorithm.update_market_data(market_data)