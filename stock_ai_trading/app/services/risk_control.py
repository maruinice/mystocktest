"""
智能风控系统

实现多层风控机制：
1. 事前风控（决策阶段）
2. 事中风控（执行阶段）
3. 事后风控（持仓阶段）
4. 紧急干预机制
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(Enum):
    """风险类型"""
    POSITION_LIMIT = "position_limit"
    CONCENTRATION = "concentration"
    FREQUENCY = "frequency"
    LIQUIDITY = "liquidity"
    MARKET_IMPACT = "market_impact"
    PNL = "pnl"
    DRAWDOWN = "drawdown"
    VAR = "var"


class EmergencyAction(Enum):
    """紧急操作类型"""
    FORCE_CLOSE = "force_close"
    SUSPEND_TRADING = "suspend_trading"
    ADJUST_PARAMS = "adjust_params"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class RiskConfig:
    """风控配置"""
    # 事前风控配置
    max_single_position_ratio: Decimal = Decimal("0.20")  # 单票最大仓位比例
    max_total_positions: int = 5  # 最大持仓数量
    max_industry_concentration: Decimal = Decimal("0.40")  # 行业最大集中度
    max_daily_trades: int = 10  # 每日最大交易次数
    min_trade_interval: int = 300  # 最小交易间隔（秒）
    
    # 事中风控配置
    price_deviation_threshold: Decimal = Decimal("0.05")  # 价格偏离阈值
    liquidity_threshold: Decimal = Decimal("1000000")  # 流动性阈值
    market_impact_threshold: Decimal = Decimal("0.02")  # 市场冲击阈值
    
    # 事后风控配置
    max_daily_loss: Decimal = Decimal("0.05")  # 最大日损失
    max_total_loss: Decimal = Decimal("0.20")  # 最大总损失
    stop_loss_ratio: Decimal = Decimal("0.10")  # 止损比例
    take_profit_ratio: Decimal = Decimal("0.20")  # 止盈比例
    var_confidence: Decimal = Decimal("0.95")  # VaR置信度
    var_threshold: Decimal = Decimal("0.03")  # VaR阈值


@dataclass
class RiskAlert:
    """风险预警"""
    risk_type: RiskType
    risk_level: RiskLevel
    message: str
    timestamp: datetime
    model_id: str
    symbol: Optional[str] = None
    current_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    suggested_action: Optional[str] = None


@dataclass
class TradeRiskCheck:
    """交易风险检查结果"""
    is_allowed: bool
    risk_alerts: List[RiskAlert] = field(default_factory=list)
    adjusted_quantity: Optional[Decimal] = None
    reason: Optional[str] = None


class PreTradeRiskControl:
    """事前风控系统"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.trade_history: Dict[str, List[datetime]] = defaultdict(list)
    
    def check_trade_risk(self, model_id: str, symbol: str, quantity: Decimal, 
                        price: Decimal, side: str, portfolio_data: Dict) -> TradeRiskCheck:
        """检查交易风险"""
        alerts = []
        is_allowed = True
        adjusted_quantity = quantity
        
        # 检查单票仓位限制
        position_alert = self._check_position_limit(
            model_id, symbol, quantity, price, side, portfolio_data
        )
        if position_alert:
            alerts.append(position_alert)
            if position_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                is_allowed = False
        
        # 检查总持仓限制
        total_positions_alert = self._check_total_positions(
            model_id, symbol, side, portfolio_data
        )
        if total_positions_alert:
            alerts.append(total_positions_alert)
            if total_positions_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                is_allowed = False
        
        # 检查行业集中度
        concentration_alert = self._check_industry_concentration(
            model_id, symbol, quantity, price, side, portfolio_data
        )
        if concentration_alert:
            alerts.append(concentration_alert)
            if concentration_alert.risk_level == RiskLevel.CRITICAL:
                is_allowed = False
        
        # 检查交易频率
        frequency_alert = self._check_trading_frequency(model_id)
        if frequency_alert:
            alerts.append(frequency_alert)
            if frequency_alert.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                is_allowed = False
        
        return TradeRiskCheck(
            is_allowed=is_allowed,
            risk_alerts=alerts,
            adjusted_quantity=adjusted_quantity,
            reason="风控检查完成" if is_allowed else "触发风控限制"
        )
    
    def _check_position_limit(self, model_id: str, symbol: str, quantity: Decimal,
                            price: Decimal, side: str, portfolio_data: Dict) -> Optional[RiskAlert]:
        """检查单票仓位限制"""
        account_data = portfolio_data.get('accounts', {}).get(model_id, {})
        total_assets = Decimal(str(account_data.get('total_assets', 0)))
        
        if total_assets <= 0:
            return None
        
        # 计算当前持仓市值
        positions = account_data.get('positions', {})
        current_position = positions.get(symbol, {})
        current_market_value = Decimal(str(current_position.get('market_value', 0)))
        
        # 计算交易后的持仓市值
        trade_value = quantity * price
        if side == 'buy':
            new_market_value = current_market_value + trade_value
        else:
            new_market_value = max(Decimal('0'), current_market_value - trade_value)
        
        # 计算仓位比例
        position_ratio = new_market_value / total_assets
        
        if position_ratio > self.config.max_single_position_ratio:
            risk_level = RiskLevel.CRITICAL if position_ratio > self.config.max_single_position_ratio * Decimal('1.5') else RiskLevel.HIGH
            return RiskAlert(
                risk_type=RiskType.POSITION_LIMIT,
                risk_level=risk_level,
                message=f"单票仓位超限: {symbol}",
                timestamp=datetime.now(),
                model_id=model_id,
                symbol=symbol,
                current_value=position_ratio,
                threshold_value=self.config.max_single_position_ratio,
                suggested_action="减少交易数量或分批建仓"
            )
        
        return None
    
    def _check_total_positions(self, model_id: str, symbol: str, side: str,
                             portfolio_data: Dict) -> Optional[RiskAlert]:
        """检查总持仓限制"""
        account_data = portfolio_data.get('accounts', {}).get(model_id, {})
        positions = account_data.get('positions', {})
        
        current_positions_count = len([p for p in positions.values() 
                                     if Decimal(str(p.get('quantity', 0))) > 0])
        
        # 如果是买入新股票
        if side == 'buy' and symbol not in positions:
            new_positions_count = current_positions_count + 1
            if new_positions_count > self.config.max_total_positions:
                return RiskAlert(
                    risk_type=RiskType.CONCENTRATION,
                    risk_level=RiskLevel.HIGH,
                    message=f"总持仓数量超限",
                    timestamp=datetime.now(),
                    model_id=model_id,
                    current_value=Decimal(str(new_positions_count)),
                    threshold_value=Decimal(str(self.config.max_total_positions)),
                    suggested_action="先平仓部分股票再建新仓"
                )
        
        return None
    
    def _check_industry_concentration(self, model_id: str, symbol: str, quantity: Decimal,
                                    price: Decimal, side: str, portfolio_data: Dict) -> Optional[RiskAlert]:
        """检查行业集中度（简化实现，实际需要股票行业数据）"""
        # 这里简化处理，实际应该根据股票代码获取行业信息
        # 假设前缀相同的股票属于同一行业
        industry = symbol[:2] if len(symbol) >= 2 else symbol
        
        account_data = portfolio_data.get('accounts', {}).get(model_id, {})
        total_assets = Decimal(str(account_data.get('total_assets', 0)))
        
        if total_assets <= 0:
            return None
        
        # 计算同行业持仓市值
        positions = account_data.get('positions', {})
        industry_market_value = Decimal('0')
        
        for pos_symbol, position in positions.items():
            if pos_symbol.startswith(industry):
                industry_market_value += Decimal(str(position.get('market_value', 0)))
        
        # 计算交易后的行业集中度
        if side == 'buy' and symbol.startswith(industry):
            industry_market_value += quantity * price
        
        industry_ratio = industry_market_value / total_assets
        
        if industry_ratio > self.config.max_industry_concentration:
            return RiskAlert(
                risk_type=RiskType.CONCENTRATION,
                risk_level=RiskLevel.MEDIUM,
                message=f"行业集中度过高: {industry}",
                timestamp=datetime.now(),
                model_id=model_id,
                current_value=industry_ratio,
                threshold_value=self.config.max_industry_concentration,
                suggested_action="分散投资到其他行业"
            )
        
        return None
    
    def _check_trading_frequency(self, model_id: str) -> Optional[RiskAlert]:
        """检查交易频率"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 清理历史记录
        self.trade_history[model_id] = [
            t for t in self.trade_history[model_id] if t >= today_start
        ]
        
        # 检查日交易次数
        daily_trades = len(self.trade_history[model_id])
        if daily_trades >= self.config.max_daily_trades:
            return RiskAlert(
                risk_type=RiskType.FREQUENCY,
                risk_level=RiskLevel.HIGH,
                message="日交易次数超限",
                timestamp=now,
                model_id=model_id,
                current_value=Decimal(str(daily_trades)),
                threshold_value=Decimal(str(self.config.max_daily_trades)),
                suggested_action="暂停交易或调整策略频率"
            )
        
        # 检查交易间隔
        if self.trade_history[model_id]:
            last_trade_time = max(self.trade_history[model_id])
            time_since_last = (now - last_trade_time).total_seconds()
            
            if time_since_last < self.config.min_trade_interval:
                return RiskAlert(
                    risk_type=RiskType.FREQUENCY,
                    risk_level=RiskLevel.MEDIUM,
                    message="交易间隔过短",
                    timestamp=now,
                    model_id=model_id,
                    current_value=Decimal(str(time_since_last)),
                    threshold_value=Decimal(str(self.config.min_trade_interval)),
                    suggested_action="等待足够时间间隔后再交易"
                )
        
        return None
    
    def record_trade(self, model_id: str):
        """记录交易时间"""
        self.trade_history[model_id].append(datetime.now())


class InTradeRiskControl:
    """事中风控系统"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
    
    def monitor_price_deviation(self, symbol: str, expected_price: Decimal,
                              current_price: Decimal) -> Optional[RiskAlert]:
        """监控价格偏离"""
        deviation = abs(current_price - expected_price) / expected_price
        
        if deviation > self.config.price_deviation_threshold:
            risk_level = RiskLevel.HIGH if deviation > self.config.price_deviation_threshold * 2 else RiskLevel.MEDIUM
            return RiskAlert(
                risk_type=RiskType.MARKET_IMPACT,
                risk_level=risk_level,
                message=f"价格偏离过大: {symbol}",
                timestamp=datetime.now(),
                model_id="",
                symbol=symbol,
                current_value=deviation,
                threshold_value=self.config.price_deviation_threshold,
                suggested_action="调整订单价格或分批执行"
            )
        
        return None
    
    def check_liquidity(self, symbol: str, volume: Decimal, avg_volume: Decimal) -> Optional[RiskAlert]:
        """检查流动性"""
        if avg_volume < self.config.liquidity_threshold:
            return RiskAlert(
                risk_type=RiskType.LIQUIDITY,
                risk_level=RiskLevel.MEDIUM,
                message=f"流动性不足: {symbol}",
                timestamp=datetime.now(),
                model_id="",
                symbol=symbol,
                current_value=avg_volume,
                threshold_value=self.config.liquidity_threshold,
                suggested_action="减少交易量或选择流动性更好的时段"
            )
        
        return None
    
    def assess_market_impact(self, symbol: str, trade_volume: Decimal,
                           market_volume: Decimal) -> Optional[RiskAlert]:
        """评估市场冲击"""
        if market_volume > 0:
            impact_ratio = trade_volume / market_volume
            
            if impact_ratio > self.config.market_impact_threshold:
                return RiskAlert(
                    risk_type=RiskType.MARKET_IMPACT,
                    risk_level=RiskLevel.MEDIUM,
                    message=f"市场冲击过大: {symbol}",
                    timestamp=datetime.now(),
                    model_id="",
                    symbol=symbol,
                    current_value=impact_ratio,
                    threshold_value=self.config.market_impact_threshold,
                    suggested_action="分批执行或调整交易时机"
                )
        
        return None


class PostTradeRiskControl:
    """事后风控系统"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
    
    def monitor_pnl(self, model_id: str, portfolio_data: Dict) -> List[RiskAlert]:
        """监控盈亏"""
        alerts = []
        account_data = portfolio_data.get('accounts', {}).get(model_id, {})
        
        # 检查日损失
        daily_pnl = Decimal(str(account_data.get('daily_pnl', 0)))
        total_assets = Decimal(str(account_data.get('total_assets', 0)))
        
        if total_assets > 0 and daily_pnl < 0:
            daily_loss_ratio = abs(daily_pnl) / total_assets
            
            if daily_loss_ratio > self.config.max_daily_loss:
                alerts.append(RiskAlert(
                    risk_type=RiskType.PNL,
                    risk_level=RiskLevel.HIGH,
                    message="日损失超限",
                    timestamp=datetime.now(),
                    model_id=model_id,
                    current_value=daily_loss_ratio,
                    threshold_value=self.config.max_daily_loss,
                    suggested_action="暂停交易或调整策略"
                ))
        
        # 检查总损失
        total_pnl = Decimal(str(account_data.get('total_pnl', 0)))
        if total_assets > 0 and total_pnl < 0:
            total_loss_ratio = abs(total_pnl) / total_assets
            
            if total_loss_ratio > self.config.max_total_loss:
                alerts.append(RiskAlert(
                    risk_type=RiskType.PNL,
                    risk_level=RiskLevel.CRITICAL,
                    message="总损失超限",
                    timestamp=datetime.now(),
                    model_id=model_id,
                    current_value=total_loss_ratio,
                    threshold_value=self.config.max_total_loss,
                    suggested_action="立即停止交易并评估策略"
                ))
        
        return alerts
    
    def check_stop_loss_take_profit(self, model_id: str, portfolio_data: Dict) -> List[RiskAlert]:
        """检查止损止盈"""
        alerts = []
        account_data = portfolio_data.get('accounts', {}).get(model_id, {})
        positions = account_data.get('positions', {})
        
        for symbol, position in positions.items():
            quantity = Decimal(str(position.get('quantity', 0)))
            if quantity <= 0:
                continue
            
            avg_cost = Decimal(str(position.get('avg_cost', 0)))
            current_price = Decimal(str(position.get('last_price', 0)))
            
            if avg_cost > 0 and current_price > 0:
                pnl_ratio = (current_price - avg_cost) / avg_cost
                
                # 检查止损
                if pnl_ratio <= -self.config.stop_loss_ratio:
                    alerts.append(RiskAlert(
                        risk_type=RiskType.PNL,
                        risk_level=RiskLevel.HIGH,
                        message=f"触发止损: {symbol}",
                        timestamp=datetime.now(),
                        model_id=model_id,
                        symbol=symbol,
                        current_value=pnl_ratio,
                        threshold_value=-self.config.stop_loss_ratio,
                        suggested_action="执行止损卖出"
                    ))
                
                # 检查止盈
                elif pnl_ratio >= self.config.take_profit_ratio:
                    alerts.append(RiskAlert(
                        risk_type=RiskType.PNL,
                        risk_level=RiskLevel.MEDIUM,
                        message=f"可执行止盈: {symbol}",
                        timestamp=datetime.now(),
                        model_id=model_id,
                        symbol=symbol,
                        current_value=pnl_ratio,
                        threshold_value=self.config.take_profit_ratio,
                        suggested_action="考虑止盈卖出"
                    ))
        
        return alerts
    
    def calculate_var(self, returns: List[Decimal]) -> Decimal:
        """计算风险价值（VaR）"""
        if not returns:
            return Decimal('0')
        
        # 简化的VaR计算（历史模拟法）
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * (1 - self.config.var_confidence))
        
        if var_index < len(sorted_returns):
            return abs(sorted_returns[var_index])
        
        return Decimal('0')


class EmergencyControl:
    """紧急干预系统"""
    
    def __init__(self):
        self.emergency_status: Dict[str, bool] = {}
        self.suspended_models: set = set()
    
    def force_close_position(self, model_id: str, symbol: str, reason: str) -> bool:
        """强制平仓"""
        try:
            logger.warning(f"强制平仓: 模型={model_id}, 股票={symbol}, 原因={reason}")
            # 这里应该调用实际的平仓逻辑
            return True
        except Exception as e:
            logger.error(f"强制平仓失败: {e}")
            return False
    
    def suspend_model_trading(self, model_id: str, reason: str) -> bool:
        """暂停模型交易"""
        try:
            self.suspended_models.add(model_id)
            logger.warning(f"暂停模型交易: 模型={model_id}, 原因={reason}")
            return True
        except Exception as e:
            logger.error(f"暂停模型交易失败: {e}")
            return False
    
    def resume_model_trading(self, model_id: str) -> bool:
        """恢复模型交易"""
        try:
            self.suspended_models.discard(model_id)
            logger.info(f"恢复模型交易: 模型={model_id}")
            return True
        except Exception as e:
            logger.error(f"恢复模型交易失败: {e}")
            return False
    
    def emergency_stop_all(self, reason: str) -> bool:
        """系统紧急停止"""
        try:
            self.emergency_status['system'] = True
            logger.critical(f"系统紧急停止: 原因={reason}")
            return True
        except Exception as e:
            logger.error(f"系统紧急停止失败: {e}")
            return False
    
    def is_model_suspended(self, model_id: str) -> bool:
        """检查模型是否被暂停"""
        return model_id in self.suspended_models
    
    def is_system_emergency_stopped(self) -> bool:
        """检查系统是否紧急停止"""
        return self.emergency_status.get('system', False)


class RiskControlSystem:
    """智能风控系统主类"""
    
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.pre_trade_control = PreTradeRiskControl(self.config)
        self.in_trade_control = InTradeRiskControl(self.config)
        self.post_trade_control = PostTradeRiskControl(self.config)
        self.emergency_control = EmergencyControl()
        self.risk_alerts: List[RiskAlert] = []
    
    def check_pre_trade_risk(self, model_id: str, symbol: str, quantity: Decimal,
                           price: Decimal, side: str, portfolio_data: Dict) -> TradeRiskCheck:
        """事前风控检查"""
        if self.emergency_control.is_system_emergency_stopped():
            return TradeRiskCheck(
                is_allowed=False,
                reason="系统紧急停止中"
            )
        
        if self.emergency_control.is_model_suspended(model_id):
            return TradeRiskCheck(
                is_allowed=False,
                reason="模型交易已暂停"
            )
        
        result = self.pre_trade_control.check_trade_risk(
            model_id, symbol, quantity, price, side, portfolio_data
        )
        
        # 记录风险预警
        self.risk_alerts.extend(result.risk_alerts)
        
        # 如果通过检查，记录交易
        if result.is_allowed:
            self.pre_trade_control.record_trade(model_id)
        
        return result
    
    def monitor_in_trade_risk(self, symbol: str, expected_price: Decimal,
                            current_price: Decimal, volume: Decimal,
                            avg_volume: Decimal, market_volume: Decimal) -> List[RiskAlert]:
        """事中风控监控"""
        alerts = []
        
        # 价格偏离监控
        price_alert = self.in_trade_control.monitor_price_deviation(
            symbol, expected_price, current_price
        )
        if price_alert:
            alerts.append(price_alert)
        
        # 流动性检查
        liquidity_alert = self.in_trade_control.check_liquidity(
            symbol, volume, avg_volume
        )
        if liquidity_alert:
            alerts.append(liquidity_alert)
        
        # 市场冲击评估
        impact_alert = self.in_trade_control.assess_market_impact(
            symbol, volume, market_volume
        )
        if impact_alert:
            alerts.append(impact_alert)
        
        self.risk_alerts.extend(alerts)
        return alerts
    
    def monitor_post_trade_risk(self, model_id: str, portfolio_data: Dict) -> List[RiskAlert]:
        """事后风控监控"""
        alerts = []
        
        # 盈亏监控
        pnl_alerts = self.post_trade_control.monitor_pnl(model_id, portfolio_data)
        alerts.extend(pnl_alerts)
        
        # 止损止盈检查
        stop_alerts = self.post_trade_control.check_stop_loss_take_profit(
            model_id, portfolio_data
        )
        alerts.extend(stop_alerts)
        
        # 处理高风险预警
        for alert in alerts:
            if alert.risk_level == RiskLevel.CRITICAL:
                if alert.risk_type == RiskType.PNL:
                    # 自动暂停交易
                    self.emergency_control.suspend_model_trading(
                        model_id, f"触发风控: {alert.message}"
                    )
        
        self.risk_alerts.extend(alerts)
        return alerts
    
    def get_risk_summary(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """获取风险摘要"""
        alerts = self.risk_alerts
        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]
        
        # 按风险等级统计
        risk_counts = {level.value: 0 for level in RiskLevel}
        for alert in alerts:
            risk_counts[alert.risk_level.value] += 1
        
        # 按风险类型统计
        risk_types = {rtype.value: 0 for rtype in RiskType}
        for alert in alerts:
            risk_types[alert.risk_type.value] += 1
        
        return {
            'total_alerts': len(alerts),
            'risk_level_counts': risk_counts,
            'risk_type_counts': risk_types,
            'recent_alerts': alerts[-10:] if alerts else [],
            'suspended_models': list(self.emergency_control.suspended_models),
            'system_emergency_stopped': self.emergency_control.is_system_emergency_stopped()
        }
    
    def clear_old_alerts(self, hours: int = 24):
        """清理旧的风险预警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.risk_alerts = [
            alert for alert in self.risk_alerts 
            if alert.timestamp > cutoff_time
        ]