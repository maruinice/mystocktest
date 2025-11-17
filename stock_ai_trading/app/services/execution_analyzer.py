"""
执行质量分析模块
实现执行质量分析、极端行情测试、交易成本分析等功能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import random

from .trading_engine import Order, Trade, Position, OrderSide, OrderStatus, OrderType
from .execution_optimizer import ExecutionReport, MarketData

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场状态"""
    NORMAL = "normal"
    VOLATILE = "volatile"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    CRASH = "crash"
    RALLY = "rally"
    LOW_LIQUIDITY = "low_liquidity"


@dataclass
class ExecutionMetrics:
    """执行指标"""
    # 基础指标
    total_quantity: Decimal
    executed_quantity: Decimal
    fill_rate: float
    avg_execution_price: Decimal
    
    # 成本指标
    total_commission: Decimal
    market_impact_bps: float
    timing_cost_bps: float
    opportunity_cost_bps: float
    total_cost_bps: float
    
    # 效率指标
    execution_time: timedelta
    order_count: int
    avg_order_size: Decimal
    participation_rate: float
    
    # 质量指标
    price_improvement_bps: float
    slippage_bps: float
    volatility_adjusted_cost: float
    implementation_shortfall: float
    
    # 基准比较
    vwap_benchmark: Optional[Decimal] = None
    twap_benchmark: Optional[Decimal] = None
    arrival_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    
    # 风险指标
    max_adverse_excursion: float = 0.0
    max_favorable_excursion: float = 0.0
    tracking_error: float = 0.0


@dataclass
class StressTestScenario:
    """压力测试场景"""
    name: str
    description: str
    market_regime: MarketRegime
    
    # 价格参数
    price_volatility: float  # 价格波动率
    price_trend: float  # 价格趋势 (-1到1)
    price_gap_probability: float  # 跳空概率
    price_gap_magnitude: float  # 跳空幅度
    
    # 流动性参数
    liquidity_reduction: float  # 流动性减少比例
    bid_ask_spread_multiplier: float  # 买卖价差倍数
    market_depth_reduction: float  # 市场深度减少
    
    # 时间参数
    duration_minutes: int = 60
    
    # 其他参数
    order_rejection_rate: float = 0.0  # 订单拒绝率
    latency_multiplier: float = 1.0  # 延迟倍数


class MarketDataGenerator:
    """市场数据生成器"""

    def __init__(self, initial_price: Decimal = Decimal("100.0")):
        self.current_price = initial_price
        self.current_volume = 10000
        self.current_spread = float(initial_price) * 0.001  # 0.1%价差
        
    def generate_normal_data(self, count: int = 100) -> List[MarketData]:
        """生成正常市场数据"""
        data = []
        timestamp = datetime.now()
        
        for i in range(count):
            # 价格随机游走
            price_change = np.random.normal(0, float(self.current_price) * 0.001)
            self.current_price += Decimal(str(price_change))
            
            # 成交量变化
            volume_change = np.random.normal(0, self.current_volume * 0.1)
            self.current_volume = max(1000, int(self.current_volume + volume_change))
            
            # 买卖价差
            spread = self.current_spread
            bid_price = self.current_price - Decimal(str(spread / 2))
            ask_price = self.current_price + Decimal(str(spread / 2))
            
            market_data = MarketData(
                symbol="TEST",
                price=self.current_price,
                volume=self.current_volume,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_size=self.current_volume // 10,
                ask_size=self.current_volume // 10,
                timestamp=timestamp + timedelta(seconds=i * 30)
            )
            data.append(market_data)
        
        return data

    def generate_stress_data(self, scenario: StressTestScenario, count: int = 100) -> List[MarketData]:
        """生成压力测试数据"""
        data = []
        timestamp = datetime.now()
        
        for i in range(count):
            # 根据场景调整价格
            if scenario.market_regime == MarketRegime.CRASH:
                price_change = np.random.normal(-float(self.current_price) * 0.01, 
                                              float(self.current_price) * scenario.price_volatility)
            elif scenario.market_regime == MarketRegime.RALLY:
                price_change = np.random.normal(float(self.current_price) * 0.01, 
                                              float(self.current_price) * scenario.price_volatility)
            elif scenario.market_regime == MarketRegime.VOLATILE:
                price_change = np.random.normal(0, float(self.current_price) * scenario.price_volatility)
            else:
                price_change = np.random.normal(float(self.current_price) * scenario.price_trend * 0.001,
                                              float(self.current_price) * scenario.price_volatility)
            
            # 跳空处理
            if np.random.random() < scenario.price_gap_probability:
                gap_direction = 1 if np.random.random() > 0.5 else -1
                gap_size = float(self.current_price) * scenario.price_gap_magnitude * gap_direction
                price_change += gap_size
            
            self.current_price += Decimal(str(price_change))
            self.current_price = max(Decimal("1.0"), self.current_price)  # 价格不能为负
            
            # 调整流动性
            base_volume = int(self.current_volume * (1 - scenario.liquidity_reduction))
            volume_change = np.random.normal(0, base_volume * 0.2)
            self.current_volume = max(100, int(base_volume + volume_change))
            
            # 调整价差
            spread = self.current_spread * scenario.bid_ask_spread_multiplier
            bid_price = self.current_price - Decimal(str(spread / 2))
            ask_price = self.current_price + Decimal(str(spread / 2))
            
            # 调整市场深度
            depth_multiplier = 1 - scenario.market_depth_reduction
            bid_size = max(10, int(self.current_volume // 10 * depth_multiplier))
            ask_size = max(10, int(self.current_volume // 10 * depth_multiplier))
            
            market_data = MarketData(
                symbol="TEST",
                price=self.current_price,
                volume=self.current_volume,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_size=bid_size,
                ask_size=ask_size,
                timestamp=timestamp + timedelta(seconds=i * 30)
            )
            data.append(market_data)
        
        return data


class ExecutionAnalyzer:
    """执行质量分析器"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_execution(self, report: ExecutionReport, 
                         market_data_history: List[MarketData]) -> ExecutionMetrics:
        """分析执行质量"""
        try:
            # 基础指标
            fill_rate = float(report.executed_quantity / report.total_quantity) if report.total_quantity > 0 else 0.0
            
            # 计算基准价格
            vwap_benchmark = self._calculate_vwap(market_data_history)
            twap_benchmark = self._calculate_twap(market_data_history)
            arrival_price = market_data_history[0].price if market_data_history else None
            close_price = market_data_history[-1].price if market_data_history else None
            
            # 成本分析
            total_commission = sum(trade.commission for trade in report.trades)
            market_impact_bps = self._calculate_market_impact(report, market_data_history)
            timing_cost_bps = self._calculate_timing_cost(report, arrival_price)
            opportunity_cost_bps = self._calculate_opportunity_cost(report, close_price)
            total_cost_bps = market_impact_bps + timing_cost_bps + opportunity_cost_bps
            
            # 效率指标
            order_count = len(report.orders)
            avg_order_size = report.executed_quantity / order_count if order_count > 0 else Decimal("0")
            
            # 质量指标
            price_improvement_bps = self._calculate_price_improvement(report, vwap_benchmark)
            slippage_bps = report.slippage_bps
            volatility_adjusted_cost = self._calculate_volatility_adjusted_cost(
                total_cost_bps, market_data_history
            )
            implementation_shortfall = self._calculate_implementation_shortfall(
                report, arrival_price, close_price
            )
            
            # 风险指标
            max_adverse_excursion, max_favorable_excursion = self._calculate_excursions(
                report, market_data_history
            )
            tracking_error = self._calculate_tracking_error(report, vwap_benchmark)
            
            return ExecutionMetrics(
                total_quantity=report.total_quantity,
                executed_quantity=report.executed_quantity,
                fill_rate=fill_rate,
                avg_execution_price=report.avg_execution_price,
                total_commission=total_commission,
                market_impact_bps=market_impact_bps,
                timing_cost_bps=timing_cost_bps,
                opportunity_cost_bps=opportunity_cost_bps,
                total_cost_bps=total_cost_bps,
                execution_time=report.execution_time,
                order_count=order_count,
                avg_order_size=avg_order_size,
                participation_rate=report.participation_rate,
                price_improvement_bps=price_improvement_bps,
                slippage_bps=slippage_bps,
                volatility_adjusted_cost=volatility_adjusted_cost,
                implementation_shortfall=implementation_shortfall,
                vwap_benchmark=vwap_benchmark,
                twap_benchmark=twap_benchmark,
                arrival_price=arrival_price,
                close_price=close_price,
                max_adverse_excursion=max_adverse_excursion,
                max_favorable_excursion=max_favorable_excursion,
                tracking_error=tracking_error
            )
            
        except Exception as e:
            self.logger.error(f"执行质量分析失败: {str(e)}")
            raise

    def _calculate_vwap(self, market_data: List[MarketData]) -> Optional[Decimal]:
        """计算VWAP"""
        if not market_data:
            return None
        
        total_value = sum(md.price * md.volume for md in market_data)
        total_volume = sum(md.volume for md in market_data)
        
        return total_value / total_volume if total_volume > 0 else None

    def _calculate_twap(self, market_data: List[MarketData]) -> Optional[Decimal]:
        """计算TWAP"""
        if not market_data:
            return None
        
        return sum(md.price for md in market_data) / len(market_data)

    def _calculate_market_impact(self, report: ExecutionReport, 
                               market_data: List[MarketData]) -> float:
        """计算市场冲击成本"""
        if not report.trades or not market_data:
            return 0.0
        
        # 简化的市场冲击模型
        total_volume = sum(md.volume for md in market_data)
        avg_volume = total_volume / len(market_data) if market_data else 1
        
        participation_rate = float(report.executed_quantity) / avg_volume
        
        # 市场冲击与参与率的平方根成正比
        market_impact = participation_rate ** 0.5 * 10  # 基点
        
        return min(market_impact, 100)  # 最大100基点

    def _calculate_timing_cost(self, report: ExecutionReport, 
                             arrival_price: Optional[Decimal]) -> float:
        """计算时机成本"""
        if not arrival_price or report.avg_execution_price == 0:
            return 0.0
        
        price_diff = float((report.avg_execution_price - arrival_price) / arrival_price)
        
        # 买入时价格上涨为正成本，卖出时价格下跌为正成本
        if report.symbol:  # 假设从report中可以获取方向信息
            # 这里需要根据实际的订单方向调整
            timing_cost_bps = price_diff * 10000
        else:
            timing_cost_bps = abs(price_diff) * 10000
        
        return timing_cost_bps

    def _calculate_opportunity_cost(self, report: ExecutionReport, 
                                  close_price: Optional[Decimal]) -> float:
        """计算机会成本"""
        if not close_price or report.remaining_quantity == 0:
            return 0.0
        
        # 未成交部分的机会成本
        remaining_ratio = float(report.remaining_quantity / report.total_quantity)
        
        if report.avg_execution_price > 0:
            price_diff = float((close_price - report.avg_execution_price) / report.avg_execution_price)
            opportunity_cost_bps = remaining_ratio * abs(price_diff) * 10000
        else:
            opportunity_cost_bps = 0.0
        
        return opportunity_cost_bps

    def _calculate_price_improvement(self, report: ExecutionReport, 
                                   vwap_benchmark: Optional[Decimal]) -> float:
        """计算价格改善"""
        if not vwap_benchmark or report.avg_execution_price == 0:
            return 0.0
        
        improvement = float((vwap_benchmark - report.avg_execution_price) / vwap_benchmark)
        return improvement * 10000  # 转换为基点

    def _calculate_volatility_adjusted_cost(self, total_cost_bps: float, 
                                          market_data: List[MarketData]) -> float:
        """计算波动率调整成本"""
        if not market_data or len(market_data) < 2:
            return total_cost_bps
        
        # 计算价格波动率
        prices = [float(md.price) for md in market_data]
        returns = [np.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
        volatility = np.std(returns) if returns else 0.0
        
        # 波动率调整
        if volatility > 0:
            return total_cost_bps / (volatility * 100)  # 标准化
        else:
            return total_cost_bps

    def _calculate_implementation_shortfall(self, report: ExecutionReport,
                                          arrival_price: Optional[Decimal],
                                          close_price: Optional[Decimal]) -> float:
        """计算实施缺口"""
        if not arrival_price or not close_price:
            return 0.0
        
        # 实施缺口 = (实际成本 - 理想成本) / 理想成本
        if report.executed_quantity > 0:
            actual_cost = float(report.avg_execution_price * report.executed_quantity)
            ideal_cost = float(arrival_price * report.total_quantity)
            
            if ideal_cost > 0:
                shortfall = (actual_cost - ideal_cost) / ideal_cost
                return shortfall * 10000  # 转换为基点
        
        return 0.0

    def _calculate_excursions(self, report: ExecutionReport, 
                            market_data: List[MarketData]) -> Tuple[float, float]:
        """计算最大不利/有利偏移"""
        if not market_data or not report.trades:
            return 0.0, 0.0
        
        # 获取执行期间的价格数据
        execution_start = min(trade.timestamp for trade in report.trades)
        execution_end = max(trade.timestamp for trade in report.trades)
        
        execution_data = [
            md for md in market_data 
            if execution_start <= md.timestamp <= execution_end
        ]
        
        if not execution_data:
            return 0.0, 0.0
        
        avg_price = float(report.avg_execution_price)
        prices = [float(md.price) for md in execution_data]
        
        max_adverse = max((price - avg_price) / avg_price for price in prices) * 10000
        max_favorable = min((price - avg_price) / avg_price for price in prices) * 10000
        
        return abs(max_adverse), abs(max_favorable)

    def _calculate_tracking_error(self, report: ExecutionReport, 
                                vwap_benchmark: Optional[Decimal]) -> float:
        """计算跟踪误差"""
        if not vwap_benchmark or not report.trades:
            return 0.0
        
        # 计算每笔交易与基准的偏差
        deviations = []
        for trade in report.trades:
            deviation = float((trade.price - vwap_benchmark) / vwap_benchmark)
            deviations.append(deviation)
        
        # 跟踪误差为偏差的标准差
        if len(deviations) > 1:
            tracking_error = np.std(deviations) * 10000  # 转换为基点
        else:
            tracking_error = 0.0
        
        return tracking_error

    def generate_analysis_report(self, metrics: ExecutionMetrics) -> Dict[str, Any]:
        """生成分析报告"""
        return {
            "execution_summary": {
                "total_quantity": str(metrics.total_quantity),
                "executed_quantity": str(metrics.executed_quantity),
                "fill_rate": f"{metrics.fill_rate:.2%}",
                "avg_execution_price": str(metrics.avg_execution_price),
                "execution_time": str(metrics.execution_time)
            },
            "cost_analysis": {
                "total_commission": str(metrics.total_commission),
                "market_impact_bps": f"{metrics.market_impact_bps:.2f}",
                "timing_cost_bps": f"{metrics.timing_cost_bps:.2f}",
                "opportunity_cost_bps": f"{metrics.opportunity_cost_bps:.2f}",
                "total_cost_bps": f"{metrics.total_cost_bps:.2f}"
            },
            "efficiency_metrics": {
                "order_count": metrics.order_count,
                "avg_order_size": str(metrics.avg_order_size),
                "participation_rate": f"{metrics.participation_rate:.2%}"
            },
            "quality_metrics": {
                "price_improvement_bps": f"{metrics.price_improvement_bps:.2f}",
                "slippage_bps": f"{metrics.slippage_bps:.2f}",
                "volatility_adjusted_cost": f"{metrics.volatility_adjusted_cost:.2f}",
                "implementation_shortfall": f"{metrics.implementation_shortfall:.2f}"
            },
            "benchmark_comparison": {
                "vwap_benchmark": str(metrics.vwap_benchmark) if metrics.vwap_benchmark else None,
                "twap_benchmark": str(metrics.twap_benchmark) if metrics.twap_benchmark else None,
                "arrival_price": str(metrics.arrival_price) if metrics.arrival_price else None,
                "close_price": str(metrics.close_price) if metrics.close_price else None
            },
            "risk_metrics": {
                "max_adverse_excursion": f"{metrics.max_adverse_excursion:.2f}",
                "max_favorable_excursion": f"{metrics.max_favorable_excursion:.2f}",
                "tracking_error": f"{metrics.tracking_error:.2f}"
            }
        }


class StressTester:
    """压力测试器"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.market_generator = MarketDataGenerator()

    def create_stress_scenarios(self) -> List[StressTestScenario]:
        """创建压力测试场景"""
        scenarios = [
            # 正常市场
            StressTestScenario(
                name="正常市场",
                description="正常的市场条件",
                market_regime=MarketRegime.NORMAL,
                price_volatility=0.01,
                price_trend=0.0,
                price_gap_probability=0.01,
                price_gap_magnitude=0.005,
                liquidity_reduction=0.0,
                bid_ask_spread_multiplier=1.0,
                market_depth_reduction=0.0
            ),
            
            # 高波动市场
            StressTestScenario(
                name="高波动市场",
                description="价格剧烈波动的市场环境",
                market_regime=MarketRegime.VOLATILE,
                price_volatility=0.05,
                price_trend=0.0,
                price_gap_probability=0.05,
                price_gap_magnitude=0.02,
                liquidity_reduction=0.2,
                bid_ask_spread_multiplier=2.0,
                market_depth_reduction=0.3
            ),
            
            # 市场崩盘
            StressTestScenario(
                name="市场崩盘",
                description="急剧下跌的市场环境",
                market_regime=MarketRegime.CRASH,
                price_volatility=0.08,
                price_trend=-0.8,
                price_gap_probability=0.1,
                price_gap_magnitude=0.05,
                liquidity_reduction=0.5,
                bid_ask_spread_multiplier=3.0,
                market_depth_reduction=0.6,
                order_rejection_rate=0.1
            ),
            
            # 市场暴涨
            StressTestScenario(
                name="市场暴涨",
                description="急剧上涨的市场环境",
                market_regime=MarketRegime.RALLY,
                price_volatility=0.06,
                price_trend=0.8,
                price_gap_probability=0.08,
                price_gap_magnitude=0.03,
                liquidity_reduction=0.3,
                bid_ask_spread_multiplier=2.5,
                market_depth_reduction=0.4
            ),
            
            # 低流动性
            StressTestScenario(
                name="低流动性市场",
                description="流动性严重不足的市场环境",
                market_regime=MarketRegime.LOW_LIQUIDITY,
                price_volatility=0.03,
                price_trend=0.0,
                price_gap_probability=0.03,
                price_gap_magnitude=0.01,
                liquidity_reduction=0.8,
                bid_ask_spread_multiplier=5.0,
                market_depth_reduction=0.9,
                order_rejection_rate=0.2,
                latency_multiplier=3.0
            )
        ]
        
        return scenarios

    async def run_stress_test(self, scenario: StressTestScenario, 
                            algorithm_config: Any) -> Dict[str, Any]:
        """运行压力测试"""
        self.logger.info(f"开始压力测试: {scenario.name}")
        
        try:
            # 生成压力测试数据
            stress_data = self.market_generator.generate_stress_data(
                scenario, count=scenario.duration_minutes * 2
            )
            
            # 模拟执行结果（这里简化处理，实际应该运行真实的算法）
            execution_result = await self._simulate_execution(
                scenario, algorithm_config, stress_data
            )
            
            # 分析执行质量
            analyzer = ExecutionAnalyzer()
            metrics = analyzer.analyze_execution(execution_result, stress_data)
            
            # 生成测试报告
            test_report = {
                "scenario": {
                    "name": scenario.name,
                    "description": scenario.description,
                    "market_regime": scenario.market_regime.value,
                    "parameters": {
                        "price_volatility": scenario.price_volatility,
                        "price_trend": scenario.price_trend,
                        "liquidity_reduction": scenario.liquidity_reduction,
                        "bid_ask_spread_multiplier": scenario.bid_ask_spread_multiplier
                    }
                },
                "execution_metrics": analyzer.generate_analysis_report(metrics),
                "stress_impact": {
                    "fill_rate_impact": max(0, 1.0 - metrics.fill_rate),
                    "cost_increase_bps": max(0, metrics.total_cost_bps - 10),  # 假设正常成本10bp
                    "volatility_impact": metrics.volatility_adjusted_cost,
                    "liquidity_impact": scenario.liquidity_reduction
                },
                "risk_assessment": self._assess_risk_level(metrics, scenario),
                "recommendations": self._generate_recommendations(metrics, scenario)
            }
            
            self.logger.info(f"压力测试完成: {scenario.name}, "
                           f"成交率: {metrics.fill_rate:.2%}, "
                           f"总成本: {metrics.total_cost_bps:.2f}bp")
            
            return test_report
            
        except Exception as e:
            self.logger.error(f"压力测试失败: {scenario.name}, 错误: {str(e)}")
            raise

    async def _simulate_execution(self, scenario: StressTestScenario,
                                algorithm_config: Any, 
                                market_data: List[MarketData]) -> ExecutionReport:
        """模拟执行过程"""
        # 这里简化模拟执行过程
        # 实际应该调用真实的执行算法
        
        total_quantity = Decimal("10000")
        executed_quantity = total_quantity * Decimal(str(max(0.1, 1.0 - scenario.liquidity_reduction)))
        
        # 模拟订单和成交
        orders = []
        trades = []
        
        order_count = max(1, int(10 * (1 - scenario.liquidity_reduction)))
        quantity_per_order = executed_quantity / order_count
        
        for i in range(order_count):
            # 模拟订单拒绝
            if random.random() < scenario.order_rejection_rate:
                continue
                
            order = Order(
                order_id=f"order_{i}",
                symbol="TEST",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=quantity_per_order,
                price=market_data[i % len(market_data)].price,
                status=OrderStatus.FILLED
            )
            orders.append(order)
            
            # 计算成交价格（考虑市场冲击）
            market_impact = float(quantity_per_order) / market_data[i % len(market_data)].volume
            impact_adjustment = market_impact * 0.1  # 简化的冲击模型
            
            execution_price = order.price * (1 + Decimal(str(impact_adjustment)))
            
            trade = Trade(
                trade_id=f"trade_{i}",
                order_id=order.order_id,
                symbol="TEST",
                side=OrderSide.BUY,
                quantity=quantity_per_order,
                price=execution_price,
                timestamp=market_data[i % len(market_data)].timestamp,
                commission=Decimal("0.001")  # 添加佣金参数
            )
            trades.append(trade)
        
        # 计算平均执行价格
        if trades:
            total_value = sum(trade.price * trade.quantity for trade in trades)
            avg_execution_price = total_value / executed_quantity
        else:
            avg_execution_price = market_data[0].price
        
        return ExecutionReport(
            algorithm_id="stress_test",
            symbol="TEST",
            total_quantity=total_quantity,
            executed_quantity=executed_quantity,
            remaining_quantity=total_quantity - executed_quantity,
            avg_execution_price=avg_execution_price,
            vwap_benchmark=None,
            slippage_bps=0.0,
            participation_rate=0.1,
            execution_time=timedelta(minutes=scenario.duration_minutes),
            orders=orders,
            trades=trades,
            status="completed",
            created_at=datetime.now()
        )

    def _assess_risk_level(self, metrics: ExecutionMetrics, 
                          scenario: StressTestScenario) -> str:
        """评估风险等级"""
        risk_score = 0
        
        # 成交率风险
        if metrics.fill_rate < 0.5:
            risk_score += 3
        elif metrics.fill_rate < 0.8:
            risk_score += 1
        
        # 成本风险
        if metrics.total_cost_bps > 100:
            risk_score += 3
        elif metrics.total_cost_bps > 50:
            risk_score += 2
        elif metrics.total_cost_bps > 20:
            risk_score += 1
        
        # 市场冲击风险
        if metrics.market_impact_bps > 50:
            risk_score += 2
        elif metrics.market_impact_bps > 20:
            risk_score += 1
        
        # 跟踪误差风险
        if metrics.tracking_error > 100:
            risk_score += 2
        elif metrics.tracking_error > 50:
            risk_score += 1
        
        if risk_score >= 6:
            return "高风险"
        elif risk_score >= 3:
            return "中风险"
        else:
            return "低风险"

    def _generate_recommendations(self, metrics: ExecutionMetrics, 
                                scenario: StressTestScenario) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if metrics.fill_rate < 0.8:
            recommendations.append("建议增加订单的激进程度或延长执行时间")
        
        if metrics.total_cost_bps > 50:
            recommendations.append("建议优化订单拆分策略，减少市场冲击")
        
        if metrics.market_impact_bps > 30:
            recommendations.append("建议降低单笔订单大小，分散执行")
        
        if scenario.liquidity_reduction > 0.5:
            recommendations.append("在低流动性环境下，建议使用更保守的执行策略")
        
        if scenario.price_volatility > 0.05:
            recommendations.append("在高波动环境下，建议使用限价单并设置合理的价格容忍度")
        
        if metrics.tracking_error > 50:
            recommendations.append("建议改进基准跟踪算法，减少跟踪误差")
        
        if not recommendations:
            recommendations.append("当前执行策略在该场景下表现良好")
        
        return recommendations

    async def run_comprehensive_stress_test(self, algorithm_configs: List[Any]) -> Dict[str, Any]:
        """运行综合压力测试"""
        scenarios = self.create_stress_scenarios()
        comprehensive_results = {}
        
        for config in algorithm_configs:
            algorithm_results = {}
            
            for scenario in scenarios:
                try:
                    result = await self.run_stress_test(scenario, config)
                    algorithm_results[scenario.name] = result
                except Exception as e:
                    self.logger.error(f"算法 {config} 在场景 {scenario.name} 下测试失败: {str(e)}")
                    algorithm_results[scenario.name] = {"error": str(e)}
            
            comprehensive_results[f"algorithm_{id(config)}"] = algorithm_results
        
        # 生成综合评估
        comprehensive_results["summary"] = self._generate_comprehensive_summary(comprehensive_results)
        
        return comprehensive_results

    def _generate_comprehensive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合评估摘要"""
        summary = {
            "total_scenarios": len(self.create_stress_scenarios()),
            "algorithm_performance": {},
            "scenario_difficulty": {},
            "overall_recommendations": []
        }
        
        # 分析每个算法的表现
        for algo_key, algo_results in results.items():
            if algo_key == "summary":
                continue
                
            performance_scores = []
            for scenario_name, scenario_result in algo_results.items():
                if "error" not in scenario_result:
                    # 简化的性能评分
                    metrics = scenario_result.get("execution_metrics", {})
                    fill_rate = float(metrics.get("execution_summary", {}).get("fill_rate", "0%").rstrip("%")) / 100
                    cost_bps = float(metrics.get("cost_analysis", {}).get("total_cost_bps", "0"))
                    
                    # 性能评分 (0-100)
                    score = fill_rate * 50 + max(0, 50 - cost_bps / 2)
                    performance_scores.append(score)
            
            if performance_scores:
                summary["algorithm_performance"][algo_key] = {
                    "average_score": np.mean(performance_scores),
                    "min_score": np.min(performance_scores),
                    "max_score": np.max(performance_scores),
                    "consistency": 100 - np.std(performance_scores)
                }
        
        return summary