"""
策略相关数据模型

包括回测请求、回测结果、交易信号、策略等数据结构
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class StrategyStatus(Enum):
    """策略状态"""
    AVAILABLE = "available"      # 可用
    ACTIVE = "active"           # 活跃
    STOPPED = "stopped"         # 已停止
    PAUSED = "paused"          # 已暂停
    ERROR = "error"            # 错误


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"        # 买入
    SELL = "sell"      # 卖出
    HOLD = "hold"      # 持有


@dataclass
class BacktestRequest:
    """回测请求"""
    user_id: str
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    stock_pool: List[str] = field(default_factory=list)
    benchmark: str = "000300"  # 默认沪深300
    commission_rate: float = 0.0003
    slippage: float = 0.001
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'strategy_name': self.strategy_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'parameters': self.parameters,
            'stock_pool': self.stock_pool,
            'benchmark': self.benchmark,
            'commission_rate': self.commission_rate,
            'slippage': self.slippage
        }


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_return: float
    annualized_return: float
    benchmark_return: float
    alpha: float
    beta: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    profit_factor: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'benchmark_return': self.benchmark_return,
            'alpha': self.alpha,
            'beta': self.beta,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor
        }


@dataclass
class BacktestResult:
    """回测结果"""
    backtest_id: str
    user_id: str
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    benchmark_return: float
    alpha: float
    beta: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    stock_pool: List[str] = field(default_factory=list)
    benchmark: str = "000300"
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'backtest_id': self.backtest_id,
            'user_id': self.user_id,
            'strategy_name': self.strategy_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'benchmark_return': self.benchmark_return,
            'alpha': self.alpha,
            'beta': self.beta,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss,
            'parameters': self.parameters,
            'stock_pool': self.stock_pool,
            'benchmark': self.benchmark,
            'equity_curve': self.equity_curve,
            'trades': self.trades,
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def performance_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        return PerformanceMetrics(
            total_return=self.total_return,
            annualized_return=self.annualized_return,
            benchmark_return=self.benchmark_return,
            alpha=self.alpha,
            beta=self.beta,
            sharpe_ratio=self.sharpe_ratio,
            sortino_ratio=self.sortino_ratio,
            max_drawdown=self.max_drawdown,
            volatility=self.volatility,
            win_rate=self.win_rate,
            profit_factor=self.profit_factor
        )


# 创建策略管理器实例
class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies = {}
        self.templates = {}
    
    def create_strategy(self, user_id: str, name: str, description: str, 
                      strategy_type: str, parameters: Dict[str, Any] = None,
                      risk_level: str = 'medium') -> Dict[str, Any]:
        """创建策略"""
        strategy_id = f"STR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        strategy = {
            'strategy_id': strategy_id,
            'name': name,
            'description': description,
            'strategy_type': strategy_type,
            'parameters': parameters or {},
            'risk_level': risk_level,
            'status': 'draft',
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.strategies[strategy_id] = strategy
        return strategy
    
    def get_strategies(self, user_id: str, status: str = None, 
                      strategy_type: str = None, page: int = 1, 
                      page_size: int = 20) -> Dict[str, Any]:
        """获取策略列表"""
        user_strategies = [s for s in self.strategies.values() if s['user_id'] == user_id]
        
        if status:
            user_strategies = [s for s in user_strategies if s['status'] == status]
        
        if strategy_type:
            user_strategies = [s for s in user_strategies if s['strategy_type'] == strategy_type]
        
        total = len(user_strategies)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        strategies = user_strategies[start_idx:end_idx]
        
        return {
            'strategies': strategies,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    def get_strategy(self, user_id: str, strategy_id: str) -> Optional[Dict[str, Any]]:
        """获取策略详情"""
        strategy = self.strategies.get(strategy_id)
        if strategy and strategy['user_id'] == user_id:
            return strategy
        return None
    
    def update_strategy(self, user_id: str, strategy_id: str, 
                       update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新策略"""
        strategy = self.strategies.get(strategy_id)
        if not strategy or strategy['user_id'] != user_id:
            return None
        
        updated_fields = []
        for key, value in update_data.items():
            if key in ['name', 'description', 'parameters', 'risk_level']:
                strategy[key] = value
                updated_fields.append(key)
        
        strategy['updated_at'] = datetime.now().isoformat()
        
        return {
            'strategy_id': strategy_id,
            'updated_fields': updated_fields,
            'updated_at': strategy['updated_at']
        }
    
    def delete_strategy(self, user_id: str, strategy_id: str) -> Optional[Dict[str, Any]]:
        """删除策略"""
        strategy = self.strategies.get(strategy_id)
        if not strategy or strategy['user_id'] != user_id:
            return None
        
        del self.strategies[strategy_id]
        
        return {
            'strategy_id': strategy_id,
            'deleted_at': datetime.now().isoformat()
        }
    
    def start_strategy(self, user_id: str, strategy_id: str) -> Optional[Dict[str, Any]]:
        """启动策略"""
        strategy = self.strategies.get(strategy_id)
        if not strategy or strategy['user_id'] != user_id:
            return None
        
        strategy['status'] = 'active'
        strategy['updated_at'] = datetime.now().isoformat()
        
        return {
            'strategy_id': strategy_id,
            'status': 'active',
            'started_at': strategy['updated_at']
        }
    
    def stop_strategy(self, user_id: str, strategy_id: str) -> Optional[Dict[str, Any]]:
        """停止策略"""
        strategy = self.strategies.get(strategy_id)
        if not strategy or strategy['user_id'] != user_id:
            return None
        
        strategy['status'] = 'stopped'
        strategy['updated_at'] = datetime.now().isoformat()
        
        return {
            'strategy_id': strategy_id,
            'status': 'stopped',
            'stopped_at': strategy['updated_at']
        }


# 创建全局策略管理器实例
strategy_manager = StrategyManager()


@dataclass
class TradingSignal:
    """交易信号"""
    signal_id: str
    user_id: str
    strategy_name: str
    code: str
    name: str
    signal_type: SignalType
    confidence: float
    target_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float = 0.1
    reason: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_executed: bool = False
    executed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'signal_id': self.signal_id,
            'user_id': self.user_id,
            'strategy_name': self.strategy_name,
            'code': self.code,
            'name': self.name,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'reason': self.reason,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_executed': self.is_executed,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }
    
    @property
    def is_expired(self) -> bool:
        """检查信号是否过期"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """检查信号是否有效"""
        return not self.is_expired and not self.is_executed


@dataclass
class Strategy:
    """策略"""
    strategy_id: str
    name: str
    display_name: str
    description: str
    category: str
    risk_level: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    stock_pool: List[str] = field(default_factory=list)
    auto_trade: bool = False
    status: StrategyStatus = StrategyStatus.AVAILABLE
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'strategy_id': self.strategy_id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'risk_level': self.risk_level,
            'parameters': self.parameters,
            'stock_pool': self.stock_pool,
            'auto_trade': self.auto_trade,
            'status': self.status.value,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None
        }
    
    @property
    def is_active(self) -> bool:
        """检查策略是否活跃"""
        return self.status == StrategyStatus.ACTIVE
    
    @property
    def is_available(self) -> bool:
        """检查策略是否可用"""
        return self.status == StrategyStatus.AVAILABLE
    
    def update_status(self, status: StrategyStatus):
        """更新策略状态"""
        self.status = status
        self.updated_at = datetime.now()
    
    def update_parameters(self, parameters: Dict[str, Any]):
        """更新策略参数"""
        self.parameters.update(parameters)
        self.updated_at = datetime.now()


@dataclass
class StrategyTemplate:
    """策略模板"""
    name: str
    display_name: str
    description: str
    category: str
    risk_level: str
    parameter_schema: Dict[str, Any] = field(default_factory=dict)
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    min_capital: float = 10000.0
    supported_markets: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'risk_level': self.risk_level,
            'parameter_schema': self.parameter_schema,
            'default_parameters': self.default_parameters,
            'min_capital': self.min_capital,
            'supported_markets': self.supported_markets
        }
    
    def create_strategy(self, user_id: str, parameters: Dict[str, Any] = None) -> Strategy:
        """创建策略实例"""
        import uuid
        
        strategy_parameters = self.default_parameters.copy()
        if parameters:
            strategy_parameters.update(parameters)
        
        return Strategy(
            strategy_id=str(uuid.uuid4()),
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            category=self.category,
            risk_level=self.risk_level,
            parameters=strategy_parameters,
            user_id=user_id,
            status=StrategyStatus.AVAILABLE
        )