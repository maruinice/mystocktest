"""
指令生成模块
负责将AI决策转换为标准交易指令，包括订单构造、仓位计算和执行策略选择
"""
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from enum import Enum
import json
import math

from app.models.ai_decision_models import (
    TradingDecision, 
    TradingAction,
    ExecutionStrategy,
    ConfidenceLevel
)
from app.services.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """订单类型"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"    # 限价单
    STOP = "stop"      # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单

class TimeInForce(Enum):
    """订单有效期"""
    DAY = "day"        # 当日有效
    GTC = "gtc"        # 撤销前有效
    IOC = "ioc"        # 立即成交或撤销
    FOK = "fok"        # 全部成交或撤销

@dataclass
class TradingOrder:
    """标准交易订单"""
    symbol: str
    action: TradingAction  # BUY, SELL, HOLD
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    
    # 风险控制
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # 执行参数
    execution_strategy: ExecutionStrategy = ExecutionStrategy.IMMEDIATE
    max_slippage: float = 0.01  # 最大滑点
    min_fill_size: Optional[int] = None  # 最小成交数量
    
    # 元数据
    order_id: Optional[str] = None
    parent_decision_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None

@dataclass
class PositionSizing:
    """仓位计算结果"""
    recommended_quantity: int
    max_quantity: int
    min_quantity: int
    position_ratio: float  # 占总资产比例
    risk_amount: float     # 风险金额
    confidence_adjusted_quantity: int  # 置信度调整后数量
    reasoning: str

@dataclass
class ExecutionPlan:
    """执行计划"""
    primary_order: TradingOrder
    contingent_orders: List[TradingOrder] = field(default_factory=list)
    execution_timeline: List[Tuple[datetime, str]] = field(default_factory=list)
    risk_parameters: Dict[str, Any] = field(default_factory=dict)
    expected_cost: float = 0.0
    expected_slippage: float = 0.0

class InstructionGenerator:
    """指令生成器"""
    
    def __init__(self, llm_gateway: LLMGateway):
        self.llm_gateway = llm_gateway
        
        # 仓位管理配置
        self.position_config = {
            'max_single_position': 0.1,    # 单个股票最大仓位比例
            'max_total_equity': 0.8,       # 股票总仓位比例
            'min_cash_reserve': 0.2,       # 最小现金储备
            'risk_per_trade': 0.02,        # 单笔交易风险比例
            'confidence_multiplier': 2.0,   # 置信度乘数
        }
        
        # 执行策略配置
        self.execution_config = {
            'market_impact_threshold': 0.01,  # 市场冲击阈值
            'liquidity_threshold': 10000,     # 流动性阈值
            'volatility_threshold': 0.3,      # 波动率阈值
            'spread_threshold': 0.005,        # 价差阈值
        }
        
        # 订单类型选择规则
        self.order_type_rules = {
            'high_confidence': OrderType.MARKET,
            'medium_confidence': OrderType.LIMIT,
            'low_confidence': OrderType.LIMIT,
            'high_volatility': OrderType.LIMIT,
            'low_liquidity': OrderType.LIMIT,
        }

    async def generate_instruction(
        self,
        decision: TradingDecision,
        portfolio_context: Dict[str, Any],
        market_data: Dict[str, Any],
        risk_parameters: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        生成交易指令
        
        Args:
            decision: AI决策结果
            portfolio_context: 投资组合上下文
            market_data: 市场数据
            risk_parameters: 风险参数
            
        Returns:
            ExecutionPlan: 执行计划
        """
        try:
            logger.info(f"开始生成交易指令: {decision.symbol} {decision.action}")
            
            # 1. 智能仓位计算
            position_sizing = self._calculate_position_size(
                decision, portfolio_context, market_data, risk_parameters
            )
            
            # 2. 选择执行策略
            execution_strategy = self._select_execution_strategy(
                decision, market_data, position_sizing
            )
            
            # 3. 构造主要订单
            primary_order = await self._construct_primary_order(
                decision, position_sizing, market_data, execution_strategy
            )
            
            # 4. 生成风险控制订单
            contingent_orders = self._generate_contingent_orders(
                primary_order, decision, market_data
            )
            
            # 5. 制定执行时间线
            execution_timeline = self._create_execution_timeline(
                primary_order, contingent_orders, execution_strategy
            )
            
            # 6. 计算执行成本
            expected_cost, expected_slippage = self._estimate_execution_cost(
                primary_order, market_data
            )
            
            return ExecutionPlan(
                primary_order=primary_order,
                contingent_orders=contingent_orders,
                execution_timeline=execution_timeline,
                risk_parameters=risk_parameters or {},
                expected_cost=expected_cost,
                expected_slippage=expected_slippage
            )
            
        except Exception as e:
            logger.error(f"指令生成失败: {e}")
            return self._create_fallback_plan(decision, str(e))

    def _calculate_position_size(
        self,
        decision: TradingDecision,
        portfolio_context: Dict[str, Any],
        market_data: Dict[str, Any],
        risk_parameters: Optional[Dict[str, Any]] = None
    ) -> PositionSizing:
        """智能仓位计算"""
        
        try:
            # 获取投资组合信息
            total_value = portfolio_context.get('total_value', 100000)
            cash_available = portfolio_context.get('cash_available', total_value * 0.5)
            current_positions = portfolio_context.get('positions', {})
            
            # 获取市场数据
            current_price = market_data.get('current_price', decision.price or 100)
            volatility = market_data.get('volatility', 0.2)
            avg_volume = market_data.get('avg_volume', 100000)
            
            # 1. 基于风险的仓位计算
            risk_based_quantity = self._calculate_risk_based_position(
                total_value, current_price, volatility, decision
            )
            
            # 2. 基于流动性的仓位限制
            liquidity_based_quantity = self._calculate_liquidity_based_position(
                avg_volume, current_price, cash_available
            )
            
            # 3. 基于投资组合的仓位限制
            portfolio_based_quantity = self._calculate_portfolio_based_position(
                decision.symbol, total_value, current_price, current_positions
            )
            
            # 4. 基于置信度的仓位调整
            confidence_adjusted_quantity = self._adjust_position_by_confidence(
                decision.confidence, min(risk_based_quantity, liquidity_based_quantity, portfolio_based_quantity)
            )
            
            # 5. 确定最终推荐数量
            max_quantity = min(risk_based_quantity, liquidity_based_quantity, portfolio_based_quantity)
            min_quantity = max(1, int(max_quantity * 0.1))  # 最小为最大数量的10%
            recommended_quantity = max(min_quantity, confidence_adjusted_quantity)
            
            # 如果是卖出，检查持仓数量
            if decision.action == TradingAction.SELL:
                current_holding = current_positions.get(decision.symbol, {}).get('quantity', 0)
                recommended_quantity = min(recommended_quantity, current_holding)
                max_quantity = min(max_quantity, current_holding)
            
            # 计算仓位比例和风险金额
            position_value = recommended_quantity * current_price
            position_ratio = position_value / total_value if total_value > 0 else 0
            risk_amount = position_value * volatility * 1.645  # 95% VaR
            
            # 生成推理说明
            reasoning = self._generate_position_reasoning(
                risk_based_quantity, liquidity_based_quantity, portfolio_based_quantity,
                confidence_adjusted_quantity, recommended_quantity, decision.confidence
            )
            
            return PositionSizing(
                recommended_quantity=recommended_quantity,
                max_quantity=max_quantity,
                min_quantity=min_quantity,
                position_ratio=position_ratio,
                risk_amount=risk_amount,
                confidence_adjusted_quantity=confidence_adjusted_quantity,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"仓位计算失败: {e}")
            # 返回保守的默认仓位
            return PositionSizing(
                recommended_quantity=100,
                max_quantity=100,
                min_quantity=10,
                position_ratio=0.01,
                risk_amount=1000,
                confidence_adjusted_quantity=100,
                reasoning=f"仓位计算出错，使用默认值: {str(e)}"
            )

    def _calculate_risk_based_position(
        self, 
        total_value: float, 
        current_price: float, 
        volatility: float, 
        decision: TradingDecision
    ) -> int:
        """基于风险的仓位计算"""
        
        # 风险预算
        risk_budget = total_value * self.position_config['risk_per_trade']
        
        # 止损距离
        if decision.stop_loss and current_price:
            stop_distance = abs(current_price - decision.stop_loss) / current_price
        else:
            stop_distance = volatility * 2  # 默认2倍波动率作为止损距离
        
        # 基于止损的最大仓位
        if stop_distance > 0:
            max_position_value = risk_budget / stop_distance
            max_quantity = int(max_position_value / current_price)
        else:
            max_quantity = int(risk_budget / (current_price * 0.1))  # 默认10%止损
        
        return max(1, max_quantity)

    def _calculate_liquidity_based_position(
        self, 
        avg_volume: float, 
        current_price: float, 
        cash_available: float
    ) -> int:
        """基于流动性的仓位计算"""
        
        # 不超过日均成交量的5%
        max_volume_quantity = int(avg_volume * 0.05)
        
        # 不超过可用现金
        max_cash_quantity = int(cash_available / current_price) if current_price > 0 else 0
        
        return max(1, min(max_volume_quantity, max_cash_quantity))

    def _calculate_portfolio_based_position(
        self, 
        symbol: str, 
        total_value: float, 
        current_price: float, 
        current_positions: Dict[str, Any]
    ) -> int:
        """基于投资组合的仓位计算"""
        
        # 单个股票最大仓位限制
        max_single_position_value = total_value * self.position_config['max_single_position']
        
        # 当前持仓价值
        current_position = current_positions.get(symbol, {})
        current_quantity = current_position.get('quantity', 0)
        current_value = current_quantity * current_price
        
        # 剩余可投资金额
        remaining_value = max_single_position_value - current_value
        
        if remaining_value > 0:
            max_quantity = int(remaining_value / current_price)
        else:
            max_quantity = 0  # 已达到仓位上限
        
        return max(0, max_quantity)

    def _adjust_position_by_confidence(self, confidence: float, base_quantity: int) -> int:
        """基于置信度调整仓位"""
        
        # 置信度调整因子
        confidence_factor = confidence * self.position_config['confidence_multiplier']
        
        # 调整后数量
        adjusted_quantity = int(base_quantity * confidence_factor)
        
        return max(1, min(adjusted_quantity, base_quantity))

    def _generate_position_reasoning(
        self,
        risk_based: int,
        liquidity_based: int,
        portfolio_based: int,
        confidence_adjusted: int,
        final_quantity: int,
        confidence: float
    ) -> str:
        """生成仓位推理说明"""
        
        reasoning_parts = [
            f"风险限制: {risk_based}股",
            f"流动性限制: {liquidity_based}股",
            f"组合限制: {portfolio_based}股",
            f"置信度调整({confidence:.1%}): {confidence_adjusted}股",
            f"最终推荐: {final_quantity}股"
        ]
        
        return "; ".join(reasoning_parts)

    def _select_execution_strategy(
        self,
        decision: TradingDecision,
        market_data: Dict[str, Any],
        position_sizing: PositionSizing
    ) -> ExecutionStrategy:
        """选择执行策略"""
        
        try:
            volatility = market_data.get('volatility', 0.2)
            volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', volume)
            spread = market_data.get('spread', 0.01)
            
            # 高置信度 + 低波动率 -> 立即执行
            if decision.confidence > 0.8 and volatility < 0.2:
                return ExecutionStrategy.IMMEDIATE
            
            # 大单 + 高波动率 -> 分批执行
            volume_ratio = position_sizing.recommended_quantity / avg_volume if avg_volume > 0 else 0
            if volume_ratio > 0.05 or volatility > 0.3:
                return ExecutionStrategy.BATCH
            
            # 低流动性 -> 耐心执行
            if volume < avg_volume * 0.5 or spread > 0.01:
                return ExecutionStrategy.PATIENT
            
            # 默认策略
            return ExecutionStrategy.IMMEDIATE
            
        except Exception as e:
            logger.error(f"执行策略选择失败: {e}")
            return ExecutionStrategy.IMMEDIATE

    async def _construct_primary_order(
        self,
        decision: TradingDecision,
        position_sizing: PositionSizing,
        market_data: Dict[str, Any],
        execution_strategy: ExecutionStrategy
    ) -> TradingOrder:
        """构造主要订单"""
        
        try:
            # 确定订单类型
            order_type = self._determine_order_type(decision, market_data)
            
            # 确定价格
            order_price = self._determine_order_price(
                decision, market_data, order_type
            )
            
            # 确定有效期
            time_in_force = self._determine_time_in_force(execution_strategy)
            
            # 计算滑点限制
            max_slippage = self._calculate_max_slippage(market_data, decision.confidence)
            
            return TradingOrder(
                symbol=decision.symbol,
                action=decision.action,
                order_type=order_type,
                quantity=position_sizing.recommended_quantity,
                price=order_price,
                time_in_force=time_in_force,
                stop_loss=decision.stop_loss,
                take_profit=decision.take_profit,
                execution_strategy=execution_strategy,
                max_slippage=max_slippage,
                parent_decision_id=getattr(decision, 'id', None),
                notes=f"基于AI决策生成，置信度: {decision.confidence:.1%}"
            )
            
        except Exception as e:
            logger.error(f"主要订单构造失败: {e}")
            # 返回简单的市价单
            return TradingOrder(
                symbol=decision.symbol,
                action=decision.action,
                order_type=OrderType.MARKET,
                quantity=100,  # 默认数量
                time_in_force=TimeInForce.DAY
            )

    def _determine_order_type(self, decision: TradingDecision, market_data: Dict[str, Any]) -> OrderType:
        """确定订单类型"""
        
        volatility = market_data.get('volatility', 0.2)
        spread = market_data.get('spread', 0.01)
        volume = market_data.get('volume', 0)
        avg_volume = market_data.get('avg_volume', volume)
        
        # 高置信度 + 正常市场条件 -> 市价单
        if (decision.confidence > 0.8 and 
            volatility < self.execution_config['volatility_threshold'] and
            spread < self.execution_config['spread_threshold']):
            return OrderType.MARKET
        
        # 低流动性 -> 限价单
        if volume < avg_volume * 0.5:
            return OrderType.LIMIT
        
        # 高波动率 -> 限价单
        if volatility > self.execution_config['volatility_threshold']:
            return OrderType.LIMIT
        
        # 默认限价单（更安全）
        return OrderType.LIMIT

    def _determine_order_price(
        self,
        decision: TradingDecision,
        market_data: Dict[str, Any],
        order_type: OrderType
    ) -> Optional[float]:
        """确定订单价格"""
        
        current_price = market_data.get('current_price', decision.price)
        spread = market_data.get('spread', 0.01)
        
        if order_type == OrderType.MARKET:
            return None  # 市价单不需要指定价格
        
        if decision.price:
            # 使用决策中的价格，但要考虑市场条件
            price_diff = abs(decision.price - current_price) / current_price
            if price_diff < 0.05:  # 价格差异小于5%，使用决策价格
                return decision.price
        
        # 根据买卖方向调整价格
        if decision.action == TradingAction.BUY:
            # 买入时略高于当前价格
            return current_price * (1 + spread / 2)
        elif decision.action == TradingAction.SELL:
            # 卖出时略低于当前价格
            return current_price * (1 - spread / 2)
        
        return current_price

    def _determine_time_in_force(self, execution_strategy: ExecutionStrategy) -> TimeInForce:
        """确定订单有效期"""
        
        if execution_strategy == ExecutionStrategy.IMMEDIATE:
            return TimeInForce.IOC  # 立即成交或撤销
        elif execution_strategy == ExecutionStrategy.PATIENT:
            return TimeInForce.GTC  # 撤销前有效
        else:
            return TimeInForce.DAY  # 当日有效

    def _calculate_max_slippage(self, market_data: Dict[str, Any], confidence: float) -> float:
        """计算最大滑点"""
        
        volatility = market_data.get('volatility', 0.2)
        spread = market_data.get('spread', 0.01)
        
        # 基础滑点
        base_slippage = spread * 2
        
        # 根据波动率调整
        volatility_adjustment = volatility * 0.5
        
        # 根据置信度调整（高置信度允许更大滑点）
        confidence_adjustment = confidence * 0.01
        
        max_slippage = base_slippage + volatility_adjustment + confidence_adjustment
        
        return min(0.05, max_slippage)  # 最大不超过5%

    def _generate_contingent_orders(
        self,
        primary_order: TradingOrder,
        decision: TradingDecision,
        market_data: Dict[str, Any]
    ) -> List[TradingOrder]:
        """生成风险控制订单"""
        
        contingent_orders = []
        
        try:
            # 只为买入订单生成止损和止盈单
            if primary_order.action == TradingAction.BUY:
                
                # 止损单
                if decision.stop_loss:
                    stop_order = TradingOrder(
                        symbol=primary_order.symbol,
                        action=TradingAction.SELL,
                        order_type=OrderType.STOP,
                        quantity=primary_order.quantity,
                        stop_price=decision.stop_loss,
                        time_in_force=TimeInForce.GTC,
                        notes="自动止损单"
                    )
                    contingent_orders.append(stop_order)
                
                # 止盈单
                if decision.take_profit:
                    profit_order = TradingOrder(
                        symbol=primary_order.symbol,
                        action=TradingAction.SELL,
                        order_type=OrderType.LIMIT,
                        quantity=primary_order.quantity,
                        price=decision.take_profit,
                        time_in_force=TimeInForce.GTC,
                        notes="自动止盈单"
                    )
                    contingent_orders.append(profit_order)
            
        except Exception as e:
            logger.error(f"生成风险控制订单失败: {e}")
        
        return contingent_orders

    def _create_execution_timeline(
        self,
        primary_order: TradingOrder,
        contingent_orders: List[TradingOrder],
        execution_strategy: ExecutionStrategy
    ) -> List[Tuple[datetime, str]]:
        """制定执行时间线"""
        
        timeline = []
        now = datetime.now()
        
        try:
            if execution_strategy == ExecutionStrategy.IMMEDIATE:
                timeline.append((now, f"立即提交主要订单: {primary_order.action.value} {primary_order.quantity}股"))
                for i, order in enumerate(contingent_orders):
                    timeline.append((now + timedelta(seconds=30 + i*10), f"提交风险控制订单: {order.notes}"))
            
            elif execution_strategy == ExecutionStrategy.BATCH:
                # 分批执行
                batch_size = primary_order.quantity // 3
                for i in range(3):
                    exec_time = now + timedelta(minutes=i*5)
                    quantity = batch_size if i < 2 else primary_order.quantity - batch_size * 2
                    timeline.append((exec_time, f"提交第{i+1}批订单: {primary_order.action.value} {quantity}股"))
            
            elif execution_strategy == ExecutionStrategy.PATIENT:
                timeline.append((now, f"提交限价订单: {primary_order.action.value} {primary_order.quantity}股"))
                timeline.append((now + timedelta(minutes=30), "检查订单执行状态"))
                timeline.append((now + timedelta(hours=1), "如未成交，考虑调整价格"))
            
        except Exception as e:
            logger.error(f"执行时间线制定失败: {e}")
            timeline.append((now, "立即执行订单"))
        
        return timeline

    def _estimate_execution_cost(
        self,
        primary_order: TradingOrder,
        market_data: Dict[str, Any]
    ) -> Tuple[float, float]:
        """估算执行成本"""
        
        try:
            current_price = market_data.get('current_price', primary_order.price or 100)
            spread = market_data.get('spread', 0.01)
            volatility = market_data.get('volatility', 0.2)
            
            # 基础交易成本（手续费等）
            base_cost = current_price * primary_order.quantity * 0.001  # 0.1%手续费
            
            # 滑点成本
            if primary_order.order_type == OrderType.MARKET:
                expected_slippage = spread / 2 + volatility * 0.1
            else:
                expected_slippage = spread / 4
            
            slippage_cost = current_price * primary_order.quantity * expected_slippage
            
            total_cost = base_cost + slippage_cost
            
            return total_cost, expected_slippage
            
        except Exception as e:
            logger.error(f"执行成本估算失败: {e}")
            return 0.0, 0.01

    def _create_fallback_plan(self, decision: TradingDecision, error_msg: str) -> ExecutionPlan:
        """创建回退执行计划"""
        
        fallback_order = TradingOrder(
            symbol=decision.symbol,
            action=TradingAction.HOLD,  # 保守策略
            order_type=OrderType.MARKET,
            quantity=0,
            notes=f"指令生成失败，采用保守策略: {error_msg}"
        )
        
        return ExecutionPlan(
            primary_order=fallback_order,
            contingent_orders=[],
            execution_timeline=[(datetime.now(), "执行失败，暂停交易")],
            risk_parameters={},
            expected_cost=0.0,
            expected_slippage=0.0
        )

    async def batch_generate_instructions(
        self,
        decisions: List[TradingDecision],
        portfolio_context: Dict[str, Any],
        market_data_batch: List[Dict[str, Any]],
        risk_parameters: Optional[Dict[str, Any]] = None
    ) -> List[ExecutionPlan]:
        """批量生成交易指令"""
        
        tasks = []
        for decision, market_data in zip(decisions, market_data_batch):
            task = self.generate_instruction(
                decision, portfolio_context, market_data, risk_parameters
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)

    def update_position_config(self, config_updates: Dict[str, Any]):
        """更新仓位管理配置"""
        self.position_config.update(config_updates)

    def update_execution_config(self, config_updates: Dict[str, Any]):
        """更新执行策略配置"""
        self.execution_config.update(config_updates)