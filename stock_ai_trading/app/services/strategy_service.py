"""
策略服务

提供回测、信号生成、策略管理等功能
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import random
import math

from app.models.strategy import (
    BacktestRequest, BacktestResult, TradingSignal, Strategy,
    StrategyStatus, SignalType, PerformanceMetrics
)


class StrategyService:
    """策略服务类"""
    
    def __init__(self):
        # 模拟数据存储
        self.backtest_results: Dict[str, BacktestResult] = {}
        self.trading_signals: Dict[str, TradingSignal] = {}
        self.active_strategies: Dict[str, Dict[str, Strategy]] = {}  # user_id -> strategy_name -> strategy
        self.available_strategies: List[Strategy] = []
        
        # 初始化示例数据
        self._init_sample_data()
    
    def _init_sample_data(self):
        """初始化示例数据"""
        # 创建可用策略
        sample_strategies = [
            {
                'name': 'MA_Cross',
                'display_name': '双均线策略',
                'description': '基于短期和长期移动平均线交叉的趋势跟踪策略',
                'category': 'trend_following',
                'risk_level': 'medium',
                'parameters': {
                    'short_period': {'type': 'int', 'default': 5, 'min': 3, 'max': 20},
                    'long_period': {'type': 'int', 'default': 20, 'min': 10, 'max': 60},
                    'position_size': {'type': 'float', 'default': 0.1, 'min': 0.01, 'max': 0.5}
                }
            },
            {
                'name': 'RSI_Reversal',
                'display_name': 'RSI反转策略',
                'description': '基于RSI指标的均值回归策略',
                'category': 'mean_reversion',
                'risk_level': 'medium',
                'parameters': {
                    'rsi_period': {'type': 'int', 'default': 14, 'min': 5, 'max': 30},
                    'oversold_threshold': {'type': 'float', 'default': 30, 'min': 20, 'max': 40},
                    'overbought_threshold': {'type': 'float', 'default': 70, 'min': 60, 'max': 80},
                    'position_size': {'type': 'float', 'default': 0.15, 'min': 0.01, 'max': 0.5}
                }
            },
            {
                'name': 'MACD_Momentum',
                'display_name': 'MACD动量策略',
                'description': '基于MACD指标的动量策略',
                'category': 'momentum',
                'risk_level': 'high',
                'parameters': {
                    'fast_period': {'type': 'int', 'default': 12, 'min': 8, 'max': 20},
                    'slow_period': {'type': 'int', 'default': 26, 'min': 20, 'max': 40},
                    'signal_period': {'type': 'int', 'default': 9, 'min': 5, 'max': 15},
                    'position_size': {'type': 'float', 'default': 0.2, 'min': 0.01, 'max': 0.5}
                }
            },
            {
                'name': 'Bollinger_Bands',
                'display_name': '布林带策略',
                'description': '基于布林带的突破和回归策略',
                'category': 'volatility',
                'risk_level': 'medium',
                'parameters': {
                    'period': {'type': 'int', 'default': 20, 'min': 10, 'max': 50},
                    'std_dev': {'type': 'float', 'default': 2.0, 'min': 1.0, 'max': 3.0},
                    'position_size': {'type': 'float', 'default': 0.12, 'min': 0.01, 'max': 0.5}
                }
            },
            {
                'name': 'Multi_Factor',
                'display_name': '多因子策略',
                'description': '基于多个技术和基本面因子的综合策略',
                'category': 'multi_factor',
                'risk_level': 'low',
                'parameters': {
                    'momentum_weight': {'type': 'float', 'default': 0.3, 'min': 0.0, 'max': 1.0},
                    'value_weight': {'type': 'float', 'default': 0.3, 'min': 0.0, 'max': 1.0},
                    'quality_weight': {'type': 'float', 'default': 0.4, 'min': 0.0, 'max': 1.0},
                    'rebalance_frequency': {'type': 'str', 'default': 'monthly', 'options': ['weekly', 'monthly', 'quarterly']}
                }
            }
        ]
        
        for strategy_data in sample_strategies:
            strategy = Strategy(
                strategy_id=str(uuid.uuid4()),
                name=strategy_data['name'],
                display_name=strategy_data['display_name'],
                description=strategy_data['description'],
                category=strategy_data['category'],
                risk_level=strategy_data['risk_level'],
                parameters=strategy_data['parameters'],
                status=StrategyStatus.AVAILABLE,
                created_at=datetime.now() - timedelta(days=random.randint(30, 365)),
                updated_at=datetime.now()
            )
            self.available_strategies.append(strategy)
        
        # 创建示例交易信号
        sample_user_id = "user_001"
        sample_codes = ['000001', '000002', '000858', '002415', '600036', '600519']
        
        for i in range(20):
            signal = TradingSignal(
                signal_id=str(uuid.uuid4()),
                user_id=sample_user_id,
                strategy_name=random.choice(['MA_Cross', 'RSI_Reversal', 'MACD_Momentum']),
                code=random.choice(sample_codes),
                name=self._get_stock_name(random.choice(sample_codes)),
                signal_type=SignalType(random.choice(['buy', 'sell', 'hold'])),
                confidence=round(random.uniform(0.6, 0.95), 2),
                target_price=round(random.uniform(10, 50), 2),
                stop_loss=round(random.uniform(8, 15), 2),
                take_profit=round(random.uniform(55, 80), 2),
                position_size=round(random.uniform(0.05, 0.2), 2),
                reason=f"技术指标显示{random.choice(['强烈买入', '卖出', '持有'])}信号",
                generated_at=datetime.now() - timedelta(minutes=random.randint(1, 1440))
            )
            self.trading_signals[signal.signal_id] = signal
    
    def run_backtest(self, request: BacktestRequest) -> Optional[BacktestResult]:
        """运行策略回测"""
        try:
            # 模拟回测计算
            start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
            
            # 计算回测天数
            trading_days = (end_date - start_date).days
            
            # 模拟回测结果
            total_return = self._simulate_return(request.strategy_name, trading_days)
            benchmark_return = random.uniform(-0.1, 0.3)  # 基准收益
            
            # 计算性能指标
            sharpe_ratio = random.uniform(0.5, 2.5)
            max_drawdown = random.uniform(0.05, 0.25)
            volatility = random.uniform(0.15, 0.35)
            
            # 创建回测结果
            result = BacktestResult(
                backtest_id=str(uuid.uuid4()),
                user_id=request.user_id,
                strategy_name=request.strategy_name,
                start_date=request.start_date,
                end_date=request.end_date,
                initial_capital=request.initial_capital,
                final_capital=request.initial_capital * (1 + total_return),
                total_return=total_return,
                annualized_return=total_return * (365 / trading_days),
                benchmark_return=benchmark_return,
                alpha=total_return - benchmark_return,
                beta=random.uniform(0.8, 1.2),
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sharpe_ratio * 1.2,
                max_drawdown=max_drawdown,
                volatility=volatility,
                win_rate=random.uniform(0.45, 0.65),
                profit_factor=random.uniform(1.1, 2.5),
                total_trades=random.randint(50, 500),
                winning_trades=random.randint(25, 300),
                losing_trades=random.randint(20, 200),
                avg_win=random.uniform(0.02, 0.08),
                avg_loss=random.uniform(-0.05, -0.01),
                largest_win=random.uniform(0.1, 0.3),
                largest_loss=random.uniform(-0.15, -0.05),
                parameters=request.parameters,
                stock_pool=request.stock_pool,
                benchmark=request.benchmark,
                created_at=datetime.now()
            )
            
            # 生成每日净值曲线（模拟）
            result.equity_curve = self._generate_equity_curve(
                request.initial_capital, total_return, trading_days
            )
            
            # 生成交易记录（模拟）
            result.trades = self._generate_trade_records(
                result.total_trades, request.stock_pool
            )
            
            # 保存回测结果
            self.backtest_results[result.backtest_id] = result
            
            return result
            
        except Exception as e:
            print(f"回测运行失败: {e}")
            return None
    
    def get_backtest_result(self, user_id: str, backtest_id: str) -> Optional[BacktestResult]:
        """获取回测结果"""
        result = self.backtest_results.get(backtest_id)
        if result and result.user_id == user_id:
            return result
        return None
    
    def get_backtest_history(self, user_id: str, strategy_name: str = '', 
                           start_date: str = '', end_date: str = '',
                           page: int = 1, size: int = 20) -> Tuple[List[BacktestResult], int]:
        """获取回测历史"""
        try:
            # 过滤回测结果
            filtered_results = []
            for result in self.backtest_results.values():
                if result.user_id != user_id:
                    continue
                
                if strategy_name and result.strategy_name != strategy_name:
                    continue
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if result.created_at < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if result.created_at > end_dt:
                        continue
                
                filtered_results.append(result)
            
            # 按创建时间倒序排序
            filtered_results.sort(key=lambda x: x.created_at, reverse=True)
            
            # 分页
            total = len(filtered_results)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            results = filtered_results[start_idx:end_idx]
            
            return results, total
            
        except Exception as e:
            print(f"获取回测历史失败: {e}")
            return [], 0
    
    def get_trading_signals(self, user_id: str, codes: List[str] = None,
                          strategy_names: List[str] = None, signal_types: List[str] = None,
                          start_time: str = '', end_time: str = '') -> List[TradingSignal]:
        """获取交易信号"""
        try:
            # 过滤交易信号
            filtered_signals = []
            for signal in self.trading_signals.values():
                if signal.user_id != user_id:
                    continue
                
                if codes and signal.code not in codes:
                    continue
                
                if strategy_names and signal.strategy_name not in strategy_names:
                    continue
                
                if signal_types and signal.signal_type.value not in signal_types:
                    continue
                
                if start_time:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if signal.generated_at < start_dt:
                        continue
                
                if end_time:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    if signal.generated_at > end_dt:
                        continue
                
                filtered_signals.append(signal)
            
            return filtered_signals
            
        except Exception as e:
            print(f"获取交易信号失败: {e}")
            return []
    
    def get_latest_signals(self, user_id: str, limit: int = 50, 
                          min_confidence: float = 0.6) -> List[TradingSignal]:
        """获取最新交易信号"""
        try:
            # 过滤用户信号
            user_signals = [
                signal for signal in self.trading_signals.values()
                if signal.user_id == user_id and signal.confidence >= min_confidence
            ]
            
            # 按生成时间倒序排序
            user_signals.sort(key=lambda x: x.generated_at, reverse=True)
            
            # 限制数量
            return user_signals[:limit]
            
        except Exception as e:
            print(f"获取最新信号失败: {e}")
            return []
    
    def select_strategy(self, user_id: str, strategy_name: str, parameters: Dict[str, Any] = None,
                       stock_pool: List[str] = None, auto_trade: bool = False,
                       risk_level: str = 'medium') -> bool:
        """选择交易策略"""
        try:
            # 检查策略是否存在
            strategy_template = None
            for strategy in self.available_strategies:
                if strategy.name == strategy_name:
                    strategy_template = strategy
                    break
            
            if not strategy_template:
                return False
            
            # 创建用户策略实例
            user_strategy = Strategy(
                strategy_id=str(uuid.uuid4()),
                name=strategy_name,
                display_name=strategy_template.display_name,
                description=strategy_template.description,
                category=strategy_template.category,
                risk_level=risk_level,
                parameters=parameters or {},
                stock_pool=stock_pool or [],
                auto_trade=auto_trade,
                status=StrategyStatus.ACTIVE,
                user_id=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存用户策略
            if user_id not in self.active_strategies:
                self.active_strategies[user_id] = {}
            
            self.active_strategies[user_id][strategy_name] = user_strategy
            
            return True
            
        except Exception as e:
            print(f"选择策略失败: {e}")
            return False
    
    def get_strategies(self, user_id: str, status: str = None) -> List[Dict[str, Any]]:
        """获取策略列表"""
        try:
            if status == 'active':
                # 获取活跃策略
                user_strategies = self.active_strategies.get(user_id, {})
                strategies = []
                for strategy in user_strategies.values():
                    strategies.append({
                        'id': strategy.name,
                        'name': strategy.display_name,
                        'description': strategy.description,
                        'status': 'active',
                        'category': strategy.category,
                        'risk_level': strategy.risk_level,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })
                return strategies
            else:
                # 获取所有可用策略
                strategies = []
                for strategy in self.available_strategies:
                    try:
                        strategies.append({
                            'id': strategy.name,
                            'name': strategy.display_name,
                            'description': strategy.description,
                            'status': 'available',
                            'category': getattr(strategy, 'category', 'unknown'),
                            'risk_level': getattr(strategy, 'risk_level', 'medium'),
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        })
                    except Exception as e:
                        print(f"处理策略 {getattr(strategy, 'name', 'unknown')} 时出错: {e}")
                        continue
                return strategies
        except Exception as e:
            print(f"获取策略列表失败: {e}")
            return []

    def get_active_strategies(self, user_id: str) -> List[Strategy]:
        """获取活跃策略"""
        user_strategies = self.active_strategies.get(user_id, {})
        return list(user_strategies.values())
    
    def get_available_strategies(self) -> List[Strategy]:
        """获取可用策略列表"""
        return self.available_strategies.copy()
    
    def get_strategy_performance(self, user_id: str, strategy_name: str = '', 
                               period: str = '30d') -> Dict[str, Any]:
        """获取策略表现"""
        try:
            # 计算时间范围
            period_days = {
                '1d': 1,
                '7d': 7,
                '30d': 30,
                '90d': 90,
                '1y': 365
            }.get(period, 30)
            
            start_date = datetime.now() - timedelta(days=period_days)
            
            # 模拟策略表现数据
            performance = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat(),
                'total_return': round(random.uniform(-0.1, 0.3), 4),
                'annualized_return': round(random.uniform(-0.2, 0.5), 4),
                'volatility': round(random.uniform(0.1, 0.4), 4),
                'sharpe_ratio': round(random.uniform(0.5, 2.0), 2),
                'max_drawdown': round(random.uniform(0.02, 0.2), 4),
                'win_rate': round(random.uniform(0.4, 0.7), 2),
                'profit_factor': round(random.uniform(1.0, 2.5), 2),
                'total_trades': random.randint(10, 100),
                'winning_trades': random.randint(5, 60),
                'losing_trades': random.randint(5, 40)
            }
            
            # 生成每日收益率曲线
            performance['daily_returns'] = self._generate_daily_returns(period_days)
            
            # 策略对比
            if strategy_name:
                performance['strategy_name'] = strategy_name
                performance['benchmark_return'] = round(random.uniform(-0.05, 0.2), 4)
                performance['alpha'] = performance['total_return'] - performance['benchmark_return']
                performance['beta'] = round(random.uniform(0.8, 1.2), 2)
            
            return performance
            
        except Exception as e:
            print(f"获取策略表现失败: {e}")
            return {}
    
    def stop_strategy(self, user_id: str, strategy_name: str) -> bool:
        """停止策略"""
        try:
            user_strategies = self.active_strategies.get(user_id, {})
            strategy = user_strategies.get(strategy_name)
            
            if not strategy or strategy.status != StrategyStatus.ACTIVE:
                return False
            
            strategy.status = StrategyStatus.STOPPED
            strategy.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            print(f"停止策略失败: {e}")
            return False
    
    def start_strategy(self, user_id: str, strategy_name: str) -> bool:
        """启动策略"""
        try:
            user_strategies = self.active_strategies.get(user_id, {})
            strategy = user_strategies.get(strategy_name)
            
            if not strategy or strategy.status == StrategyStatus.ACTIVE:
                return False
            
            strategy.status = StrategyStatus.ACTIVE
            strategy.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            print(f"启动策略失败: {e}")
            return False
    
    def _simulate_return(self, strategy_name: str, trading_days: int) -> float:
        """模拟策略收益"""
        # 不同策略的基础收益特征
        strategy_params = {
            'MA_Cross': {'base_return': 0.08, 'volatility': 0.2},
            'RSI_Reversal': {'base_return': 0.12, 'volatility': 0.25},
            'MACD_Momentum': {'base_return': 0.15, 'volatility': 0.3},
            'Bollinger_Bands': {'base_return': 0.1, 'volatility': 0.22},
            'Multi_Factor': {'base_return': 0.06, 'volatility': 0.15}
        }
        
        params = strategy_params.get(strategy_name, {'base_return': 0.1, 'volatility': 0.2})
        
        # 年化收益转换为期间收益
        period_return = params['base_return'] * (trading_days / 365)
        
        # 添加随机波动
        volatility = params['volatility'] * math.sqrt(trading_days / 365)
        random_factor = random.gauss(0, volatility)
        
        return period_return + random_factor
    
    def _generate_equity_curve(self, initial_capital: float, total_return: float, 
                             trading_days: int) -> List[Dict[str, Any]]:
        """生成净值曲线"""
        curve = []
        current_value = initial_capital
        daily_return = total_return / trading_days
        
        for i in range(trading_days + 1):
            date = datetime.now() - timedelta(days=trading_days - i)
            
            if i > 0:
                # 添加随机波动
                daily_change = daily_return + random.gauss(0, 0.02)
                current_value *= (1 + daily_change)
            
            curve.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(current_value, 2),
                'return': round((current_value - initial_capital) / initial_capital, 4)
            })
        
        return curve
    
    def _generate_trade_records(self, total_trades: int, stock_pool: List[str]) -> List[Dict[str, Any]]:
        """生成交易记录"""
        trades = []
        available_codes = stock_pool if stock_pool else ['000001', '000002', '000858', '002415']
        
        for i in range(min(total_trades, 50)):  # 限制返回的交易记录数量
            code = random.choice(available_codes)
            side = random.choice(['buy', 'sell'])
            quantity = random.randint(1, 10) * 100
            price = round(random.uniform(10, 50), 2)
            
            trade = {
                'trade_id': str(uuid.uuid4()),
                'date': (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
                'code': code,
                'name': self._get_stock_name(code),
                'side': side,
                'quantity': quantity,
                'price': price,
                'amount': quantity * price,
                'commission': round(quantity * price * 0.0003, 2),
                'profit_loss': round(random.uniform(-500, 1000), 2) if side == 'sell' else 0
            }
            trades.append(trade)
        
        return sorted(trades, key=lambda x: x['date'], reverse=True)
    
    def _generate_daily_returns(self, days: int) -> List[Dict[str, Any]]:
        """生成每日收益率"""
        returns = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i - 1)
            daily_return = random.gauss(0.001, 0.02)  # 平均0.1%，标准差2%
            
            returns.append({
                'date': date.strftime('%Y-%m-%d'),
                'return': round(daily_return, 4)
            })
        
        return returns
    
    def _get_stock_name(self, code: str) -> str:
        """获取股票名称（模拟）"""
        names = {
            '000001': '平安银行',
            '000002': '万科A',
            '000858': '五粮液',
            '002415': '海康威视',
            '600036': '招商银行',
            '600519': '贵州茅台'
        }
        return names.get(code, f'股票{code}')
    
    def create_strategy(self, user_id: str, strategy_data: Dict[str, Any]) -> Optional[Strategy]:
        """创建新策略"""
        try:
            strategy = Strategy(
                strategy_id=str(uuid.uuid4()),
                name=strategy_data['name'],
                display_name=strategy_data.get('display_name', strategy_data['name']),
                description=strategy_data['description'],
                category=strategy_data['category'],
                risk_level=strategy_data['risk_level'],
                parameters=strategy_data.get('parameters', {}),
                status=StrategyStatus.AVAILABLE,
                user_id=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存到用户策略
            if user_id not in self.active_strategies:
                self.active_strategies[user_id] = {}
            
            self.active_strategies[user_id][strategy.name] = strategy
            
            return strategy
            
        except Exception as e:
            print(f"创建策略失败: {e}")
            return None
    
    def update_strategy(self, user_id: str, strategy_id: str, update_data: Dict[str, Any]) -> Optional[Strategy]:
        """更新策略"""
        try:
            # 查找策略
            strategy = None
            for user_strategies in self.active_strategies.values():
                for s in user_strategies.values():
                    if s.strategy_id == strategy_id and s.user_id == user_id:
                        strategy = s
                        break
                if strategy:
                    break
            
            if not strategy:
                return None
            
            # 更新字段
            for key, value in update_data.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
            
            strategy.updated_at = datetime.now()
            
            return strategy
            
        except Exception as e:
            print(f"更新策略失败: {e}")
            return None
    
    def copy_strategy(self, user_id: str, strategy_id: str) -> Optional[Strategy]:
        """复制策略"""
        try:
            # 查找原策略
            original_strategy = None
            for user_strategies in self.active_strategies.values():
                for s in user_strategies.values():
                    if s.strategy_id == strategy_id:
                        original_strategy = s
                        break
                if original_strategy:
                    break
            
            if not original_strategy:
                return None
            
            # 创建副本
            new_strategy = Strategy(
                strategy_id=str(uuid.uuid4()),
                name=f"{original_strategy.name}_副本",
                display_name=f"{original_strategy.display_name}_副本",
                description=original_strategy.description,
                category=original_strategy.category,
                risk_level=original_strategy.risk_level,
                parameters=original_strategy.parameters.copy(),
                status=StrategyStatus.AVAILABLE,
                user_id=user_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 保存副本
            if user_id not in self.active_strategies:
                self.active_strategies[user_id] = {}
            
            self.active_strategies[user_id][new_strategy.name] = new_strategy
            
            return new_strategy
            
        except Exception as e:
            print(f"复制策略失败: {e}")
            return None
    
    def delete_strategy(self, user_id: str, strategy_id: str) -> bool:
        """删除策略"""
        try:
            # 查找并删除策略
            for user_strategies in self.active_strategies.values():
                for name, strategy in list(user_strategies.items()):
                    if strategy.strategy_id == strategy_id and strategy.user_id == user_id:
                        del user_strategies[name]
                        return True
            
            return False
            
        except Exception as e:
            print(f"删除策略失败: {e}")
            return False
    
    def export_strategy(self, user_id: str, strategy_id: str) -> Optional[Dict[str, Any]]:
        """导出策略"""
        try:
            # 查找策略
            strategy = None
            for user_strategies in self.active_strategies.values():
                for s in user_strategies.values():
                    if s.strategy_id == strategy_id and s.user_id == user_id:
                        strategy = s
                        break
                if strategy:
                    break
            
            if not strategy:
                return None
            
            return strategy.to_dict()
            
        except Exception as e:
            print(f"导出策略失败: {e}")
            return None
    
    def import_strategies(self, user_id: str, strategies_data: List[Dict[str, Any]]) -> int:
        """导入策略"""
        try:
            imported_count = 0
            
            for strategy_data in strategies_data:
                # 生成新的策略ID
                strategy_data['strategy_id'] = str(uuid.uuid4())
                strategy_data['user_id'] = user_id
                strategy_data['created_at'] = datetime.now()
                strategy_data['updated_at'] = datetime.now()
                
                strategy = Strategy(**strategy_data)
                
                # 保存策略
                if user_id not in self.active_strategies:
                    self.active_strategies[user_id] = {}
                
                self.active_strategies[user_id][strategy.name] = strategy
                imported_count += 1
            
            return imported_count
            
        except Exception as e:
            print(f"导入策略失败: {e}")
            return 0
    
    def validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """验证策略代码"""
        try:
            errors = []
            warnings = []
            suggestions = []
            
            # 基本语法检查
            if not code.strip():
                errors.append("代码不能为空")
                return {"valid": False, "errors": errors}
            
            # 检查必需函数
            if 'def initialize(context):' not in code:
                errors.append("缺少 initialize(context) 函数")
            
            if 'def handle_data(context, data):' not in code:
                errors.append("缺少 handle_data(context, data) 函数")
            
            # 检查常见问题
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # 检查缩进
                if stripped and not line.startswith((' ', '\t', 'def', '#', 'import', 'from')):
                    if not any(keyword in stripped for keyword in ['class ', 'if __name__']):
                        warnings.append(f"第 {i} 行可能存在缩进问题")
                
                # 检查常见错误
                if 'order(' in stripped and 'order_target' not in stripped:
                    suggestions.append(f"第 {i} 行建议使用 order_target_percent() 进行仓位管理")
            
            # 检查导入语句
            if 'import' not in code and 'from' not in code:
                suggestions.append("建议添加必要的导入语句，如 import pandas as pd")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"代码验证失败: {str(e)}"]
            }
    
    def format_strategy_code(self, code: str) -> str:
        """格式化策略代码"""
        try:
            # 简单的代码格式化
            lines = code.split('\n')
            formatted_lines = []
            
            for line in lines:
                # 移除行尾空格
                line = line.rstrip()
                
                # 保持原有缩进结构
                if line.strip():
                    formatted_lines.append(line)
                else:
                    formatted_lines.append('')
            
            # 移除多余的空行
            while formatted_lines and not formatted_lines[-1]:
                formatted_lines.pop()
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            print(f"代码格式化失败: {e}")
            return code
    
    def generate_ai_strategy(self, user_id: str, prompt: str, options: Dict[str, Any] = None) -> Optional[Strategy]:
        """AI生成策略"""
        try:
            options = options or {}
            
            # 分析提示词，确定策略类型
            strategy_type = options.get('strategy_type', 'custom')
            risk_level = options.get('risk_level', 'medium')
            indicators = options.get('indicators', [])
            
            # 根据提示词生成策略名称和描述
            if 'rsi' in prompt.lower():
                name = 'AI生成RSI策略'
                description = '基于RSI指标的AI生成策略'
                strategy_type = 'mean_reversion'
                indicators = ['RSI']
            elif '均线' in prompt or 'ma' in prompt.lower():
                name = 'AI生成均线策略'
                description = '基于移动平均线的AI生成策略'
                strategy_type = 'trend_following'
                indicators = ['MA', 'EMA']
            else:
                name = f'AI生成策略_{datetime.now().strftime("%m%d_%H%M")}'
                description = '基于用户需求的AI生成策略'
            
            # 生成策略代码
            code = self._generate_strategy_code(strategy_type, indicators, prompt)
            
            # 创建策略
            strategy_data = {
                'name': name,
                'description': description,
                'category': strategy_type,
                'risk_level': risk_level,
                'parameters': {
                    'position_size': 0.1,
                    'stop_loss': 5.0,
                    'take_profit': 15.0
                },
                'code': code
            }
            
            return self.create_strategy(user_id, strategy_data)
            
        except Exception as e:
            print(f"AI生成策略失败: {e}")
            return None
    
    def _generate_strategy_code(self, strategy_type: str, indicators: List[str], prompt: str) -> str:
        """生成策略代码"""
        templates = {
            'mean_reversion': '''def initialize(context):
    # RSI反转策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.rsi_period = 14
    context.rsi_overbought = 70
    context.rsi_oversold = 30
    context.position_size = 0.1

def handle_data(context, data):
    for stock in context.stocks:
        # 计算RSI
        hist = data.history(stock, 'close', context.rsi_period + 1)
        rsi = calculate_rsi(hist, context.rsi_period)
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：RSI < 30
        if rsi < context.rsi_oversold and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：RSI > 70
        elif rsi > context.rsi_overbought and current_position > 0:
            order_target_percent(stock, 0)

def calculate_rsi(prices, period):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]''',
            
            'trend_following': '''def initialize(context):
    # 双均线策略
    context.stocks = ['000001.XSHE', '000002.XSHE']
    context.short_period = 5
    context.long_period = 20
    context.position_size = 0.1

def handle_data(context, data):
    for stock in context.stocks:
        # 获取历史价格数据
        hist = data.history(stock, 'close', context.long_period + 1)
        
        # 计算均线
        short_ma = hist[-context.short_period:].mean()
        long_ma = hist.mean()
        
        current_position = context.portfolio.positions[stock].amount
        
        # 买入信号：短均线上穿长均线
        if short_ma > long_ma and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出信号：短均线下穿长均线
        elif short_ma < long_ma and current_position > 0:
            order_target_percent(stock, 0)''',
            
            'default': '''def initialize(context):
    # 自定义策略
    context.stocks = ['000001.XSHE']
    context.position_size = 0.1

def handle_data(context, data):
    # 策略逻辑
    for stock in context.stocks:
        current_position = context.portfolio.positions[stock].amount
        
        # 买入条件
        if should_buy(context, data, stock) and current_position == 0:
            order_target_percent(stock, context.position_size)
            
        # 卖出条件
        elif should_sell(context, data, stock) and current_position > 0:
            order_target_percent(stock, 0)

def should_buy(context, data, stock):
    # 在这里实现买入逻辑
    return False

def should_sell(context, data, stock):
    # 在这里实现卖出逻辑
    return False'''
        }
        
        return templates.get(strategy_type, templates['default'])
    
    def get_strategy_templates(self) -> List[Dict[str, Any]]:
        """获取策略模板"""
        templates = [
            {
                'name': 'ma_cross',
                'display_name': '双均线交叉策略',
                'description': '基于短期和长期移动平均线交叉的经典趋势跟踪策略',
                'category': 'trend_following',
                'risk_level': 'medium',
                'parameters': {
                    'short_period': 5,
                    'long_period': 20,
                    'position_size': 0.1
                },
                'indicators': ['MA'],
                'code_template': self._generate_strategy_code('trend_following', ['MA'], '')
            },
            {
                'name': 'rsi_reversal',
                'display_name': 'RSI反转策略',
                'description': '基于RSI指标的均值回归策略，在超买超卖区域进行反向交易',
                'category': 'mean_reversion',
                'risk_level': 'medium',
                'parameters': {
                    'rsi_period': 14,
                    'rsi_overbought': 70,
                    'rsi_oversold': 30,
                    'position_size': 0.15
                },
                'indicators': ['RSI'],
                'code_template': self._generate_strategy_code('mean_reversion', ['RSI'], '')
            },
            {
                'name': 'bollinger_bands',
                'display_name': '布林带策略',
                'description': '基于布林带的突破和回归策略',
                'category': 'volatility',
                'risk_level': 'medium',
                'parameters': {
                    'period': 20,
                    'std_dev': 2.0,
                    'position_size': 0.12
                },
                'indicators': ['BOLL'],
                'code_template': '''def initialize(context):
    context.stocks = ['000001.XSHE']
    context.period = 20
    context.std_dev = 2

def handle_data(context, data):
    for stock in context.stocks:
        hist = data.history(stock, 'close', context.period + 1)
        ma = hist.mean()
        std = hist.std()
        upper_band = ma + context.std_dev * std
        lower_band = ma - context.std_dev * std
        
        current_price = data.current(stock, 'close')
        current_position = context.portfolio.positions[stock].amount
        
        if current_price <= lower_band and current_position == 0:
            order_target_percent(stock, 0.4)
        elif current_price >= upper_band and current_position > 0:
            order_target_percent(stock, 0)'''
            }
        ]
        
        return templates